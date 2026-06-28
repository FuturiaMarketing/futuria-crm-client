#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pulisci-liste-crm — pulizia liste contatti Futuria CRM (GoHighLevel).

Comando universale e account-agnostic: il cliente e' solo un parametro a runtime
(`--client <slug>`), nessun dato cliente e' cablato qui. Tre fasi:

  detect  --client <slug>            pull contatti -> scoring -> candidates.json (+ snapshot)
  review  --candidates <file>        server locale 127.0.0.1 -> pagina browser -> decisions.json
  delete  --decisions <file>         dry-run di default; con --execute cancella via REST

Sicurezza: dry-run di default, protect-list obbligatoria, snapshot prima di ogni
write, DELETE tollerante a 404, ri-lettura di verifica.

Solo stdlib Python 3 (urllib, http.server, pathlib, webbrowser) -> gira identico
su macOS e Windows. Le credenziali arrivano da env.local (Secret Manager via pull.py):
  SHARED_GHL_TOKEN_SUBACCOUNT_<SLUG>  /  SHARED_GHL_ID_LOCATION_<SLUG>
con alias non-SHARED come fallback.
"""
import argparse
import json
import os
import re
import sys
import threading
import time
import unicodedata
import webbrowser
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

BASE = "https://services.leadconnectorhq.com"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
API_VERSION = "2021-07-28"

# Provider email usa-e-getta / temporanei: lista UNIVERSALE (mai domini vanity
# visti su un singolo cliente). Aggiornabile, non specifica di un account.
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "guerrillamail.info", "sharklasers.com",
    "yopmail.com", "tempmail.com", "temp-mail.org", "10minutemail.com",
    "trashmail.com", "getnada.com", "dispostable.com", "fakeinbox.com",
    "throwawaymail.com", "maildrop.cc", "mintemail.com", "mohmal.com",
    "spam4.me", "moakt.com", "emailondeck.com", "tempmailo.com",
    "discard.email", "mailnesia.com", "mytemp.email", "wailo.cloud",
    "sendproud.com", "njaemail.com",
}

# Tag che indicano un contatto da PROTEGGERE sempre (cliente reale / relazione viva).
# Default universali; estendibili a runtime con --protect-tags.
DEFAULT_PROTECT_TAGS = {
    "cliente", "cliente ricorrente", "customer", "recurring customer",
    "vip", "partner", "fornitore",
}

# Keyword di scam/spam tipiche in nomi/campi (universali).
SCAM_KEYWORDS = (
    "bitcoin", "btc", "usdt", "crypto", "wallet", "binance", "payment",
    "deposit", "withdraw", "recovery", "wire transfer", "loan", "casino",
    "viagra", "porn", "sexy", "telegram", "whatsapp +", "t.me/",
)
URL_FRAGMENTS = ("http://", "https://", "bit.ly", "t.me/", "telegra.ph", "graph.org", "wa.me/")

# TLD esotici frequenti nello spam (segnale debole).
EXOTIC_TLDS = {".top", ".xyz", ".icu", ".click", ".country", ".zip", ".tk",
               ".ml", ".ga", ".cf", ".gq", ".su", ".ru", ".work", ".buzz"}


# ----------------------------------------------------------------------------
# Credenziali / ambiente (portabile macOS + Windows)
# ----------------------------------------------------------------------------
def operator_env_local():
    """Legge il campo env_local dal profilo operatore ~/.futuria/operator-profile.md, se esiste."""
    prof = Path.home() / ".futuria" / "operator-profile.md"
    if prof.exists():
        try:
            for line in prof.read_text(encoding="utf-8").splitlines():
                m = re.match(r"\s*env_local\s*[:=]\s*(.+?)\s*$", line)
                if m:
                    return Path(m.group(1).strip().strip('"').strip("'"))
        except OSError:
            pass
    return None


def resolve_env_path():
    cand = os.environ.get("FUTURIA_ENV_LOCAL")
    if cand:
        return Path(cand)
    local = Path.cwd() / "_local" / "env.local"
    if local.exists():
        return local
    prof = operator_env_local()
    if prof:
        return prof
    return local  # path inesistente: load_env segnala


def load_env():
    env = dict(os.environ)
    path = resolve_env_path()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env, path


def resolve_creds(env, client):
    """Due modalita', entrambe universali:
    - agency: --client <slug> -> SHARED_GHL_TOKEN_SUBACCOUNT_<SLUG> / SHARED_GHL_ID_LOCATION_<SLUG>
    - single-account (client plugin): nessuno slug -> FUTURIA_CRM_TOKEN / FUTURIA_CRM_LOCATION
    """
    if client:
        slug = client.strip().upper().replace("-", "_")
        token = env.get(f"SHARED_GHL_TOKEN_SUBACCOUNT_{slug}") or env.get(f"GHL_TOKEN_SUBACCOUNT_{slug}")
        loc = env.get(f"SHARED_GHL_ID_LOCATION_{slug}") or env.get(f"GHL_ID_LOCATION_{slug}")
        return token, loc
    token = env.get("FUTURIA_CRM_TOKEN") or env.get("GHL_TOKEN_SUBACCOUNT") or env.get("GHL_TOKEN")
    loc = env.get("FUTURIA_CRM_LOCATION") or env.get("GHL_ID_LOCATION") or env.get("FUTURIA_CRM_LOCATION_ID")
    return token, loc


def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Version": API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": BROWSER_UA,
    }


def api(method, path, token, body=None, timeout=60):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urlrequest.Request(BASE + path, data=data, headers=headers(token), method=method)
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return resp.status, (json.loads(raw) if raw else {})


# ----------------------------------------------------------------------------
# Pull contatti
# ----------------------------------------------------------------------------
def fetch_all_contacts(token, location_id):
    out, search_after, page = [], None, 0
    while True:
        body = {"locationId": location_id, "pageLimit": 100, "filters": []}
        if search_after is not None:
            body["searchAfter"] = search_after
        status, res = api("POST", "/contacts/search", token, body)
        contacts = res.get("contacts", [])
        if not contacts:
            break
        out.extend(contacts)
        page += 1
        sys.stderr.write(f"  page {page}: +{len(contacts)} (tot {len(out)} / {res.get('total')})\n")
        sa = contacts[-1].get("searchAfter")
        if not sa or len(out) >= int(res.get("total", len(out))):
            break
        search_after = sa
        if page > 200:
            break
    return out


# ----------------------------------------------------------------------------
# Scoring (universale, a segnali combinati)
# ----------------------------------------------------------------------------
def _is_nonlatin_math(s):
    for ch in s or "":
        if ch.isalpha():
            try:
                nm = unicodedata.name(ch)
            except ValueError:
                continue
            if any(t in nm for t in ("MATHEMATICAL", "FULLWIDTH", "DOUBLE-STRUCK", "SCRIPT CAPITAL")):
                return True
    return False


def _random_token(name):
    """True solo se UN singolo token e' chiaramente generato (no struttura linguistica).
    Opera per-token: i nomi reali multi-parola in Title Case NON devono scattare."""
    for tok in re.split(r"[\s|/()\-_.,]+", name or ""):
        t = "".join(ch for ch in tok if ch.isalnum())
        letters = [c for c in t if c.isalpha()]
        if len(t) < 9 or len(letters) < 6:
            continue
        low = t.lower()
        vowels = sum(c in "aeiou" for c in low if c.isalpha())
        vowel_ratio = vowels / max(1, len(letters))
        run = maxrun = 0
        for c in low:
            if c.isalpha() and c not in "aeiou":
                run += 1
                maxrun = max(maxrun, run)
            else:
                run = 0
        digits = sum(c.isdigit() for c in t)
        case_sw = sum(1 for a, b in zip(tok, tok[1:])
                      if a.isalpha() and b.isalpha() and a.islower() != b.islower())
        # token random = pochissime vocali, OPPURE lunga run di consonanti,
        # OPPURE mix cifre+case-switch tipico di handle generati.
        if vowel_ratio < 0.22 or maxrun >= 5 or (digits >= 2 and case_sw >= 3):
            return True
    return False


def minute_buckets(contacts):
    c = Counter()
    for ct in contacts:
        da = (ct.get("dateAdded") or "")[:16]
        if da:
            c[da] += 1
    return c


def classify(contact, buckets, protect_tags, min_batch):
    """Ritorna (grade, signals). grade in {'protect','delete', None}. v1: solo delete-grade.

    Alta precisione: si segnala solo su segnali STRUTTURALI forti o su profili senza
    alcuna identita. Un contatto con nome reale o telefono NON viene mai segnalato se
    non colpisce un segnale hard (dominio usa-e-getta / scam). Forma del nome/email
    (Unicode stilizzato, email puntata) e' solo una NOTA, mai un trigger da sola:
    lezione vault -> i creator con nomi stilizzati e le email molto puntate sono spesso
    legittimi.
    """
    tags = [t.lower() for t in (contact.get("tags") or [])]
    if any(t in protect_tags for t in tags):
        return "protect", ["tag protetto"]

    fn = (contact.get("firstName") or "").strip()
    ln = (contact.get("lastName") or "").strip()
    cn = (contact.get("contactName") or "").strip()
    email = (contact.get("email") or "").strip().lower()
    local, _, domain = email.partition("@")
    phone = contact.get("phone")
    da16 = (contact.get("dateAdded") or "")[:16]
    las = contact.get("lastAttributionSource") or {}
    medium = (las.get("medium") or "").lower()
    no_name = not (fn or ln)
    empty_profile = no_name and not phone
    name_blob = f"{fn} {ln} {cn}".lower()
    tld = "." + domain.rsplit(".", 1)[-1] if "." in domain else ""
    exotic = tld in EXOTIC_TLDS
    gen_local = bool(local) and (
        _random_token(local) or local.count(".") >= 3 or sum(c.isdigit() for c in local) >= 5)

    hard = []
    if domain in DISPOSABLE_DOMAINS:
        hard.append(f"dominio usa-e-getta {domain}")
    if any(k in name_blob for k in SCAM_KEYWORDS) or any(u in name_blob for u in URL_FRAGMENTS):
        hard.append("scam/URL nei dati")
    if empty_profile and da16 and buckets.get(da16, 0) >= min_batch:
        hard.append(f"batch-per-minuto ({buckets[da16]} nello stesso minuto) + profilo vuoto")
    if not email and no_name and ("whatsapp" in medium or "instagram" in medium):
        hard.append("no-email + social/whatsapp + senza nome")
    if empty_profile and not email:
        hard.append("profilo completamente vuoto (no nome, email, telefono)")
    if empty_profile and email and (gen_local or exotic):
        hard.append("nessuna identita + email generata")

    if not hard:
        return None, []

    notes = []
    if _is_nonlatin_math(fn) or _is_nonlatin_math(ln) or _is_nonlatin_math(cn):
        notes.append("nota: nome stilizzato Unicode")
    if exotic and "nessuna identita + email generata" not in hard:
        notes.append("nota: TLD esotico")
    return "delete", hard + notes


def to_candidate(contact, signals):
    fn = (contact.get("firstName") or "").strip()
    ln = (contact.get("lastName") or "").strip()
    name = (f"{fn} {ln}".strip()) or (contact.get("contactName") or "").strip() or "(senza nome)"
    return {
        "id": contact.get("id"),
        "name": name,
        "email": contact.get("email") or "",
        "phone": contact.get("phone") or "",
        "source": contact.get("source") or "",
        "dateAdded": (contact.get("dateAdded") or "")[:16],
        "tags": [t for t in (contact.get("tags") or [])],
        "signals": signals,
    }


# ----------------------------------------------------------------------------
# Fasi
# ----------------------------------------------------------------------------
def workdir(client):
    d = Path.home() / ".futuria" / "crm-cleanup" / f"{client}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cmd_detect(args):
    env, env_path = load_env()
    label = args.client or "account"
    token, loc = resolve_creds(env, args.client)
    if not token or not loc:
        hint = (f"Attese SHARED_GHL_TOKEN_SUBACCOUNT_{args.client.upper()} / SHARED_GHL_ID_LOCATION_{args.client.upper()}."
                if args.client else "Attese FUTURIA_CRM_TOKEN / FUTURIA_CRM_LOCATION.")
        sys.exit(f"Credenziali Futuria CRM mancanti per '{label}' (env: {env_path}). {hint}")
    protect = set(DEFAULT_PROTECT_TAGS)
    if args.protect_tags:
        protect |= {t.strip().lower() for t in args.protect_tags.split(",") if t.strip()}

    sys.stderr.write(f"[detect] account '{label}' loc={loc} token={token[:6]}…\n")
    contacts = fetch_all_contacts(token, loc)
    buckets = minute_buckets(contacts)

    candidates, protected = [], 0
    for ct in contacts:
        grade, sig = classify(ct, buckets, protect, args.min_batch)
        if grade == "protect":
            protected += 1
        elif grade == "delete":
            candidates.append(to_candidate(ct, sig))

    out = Path(args.out) if args.out else workdir(label)
    out.mkdir(parents=True, exist_ok=True)
    (out / "contacts_snapshot.json").write_text(
        json.dumps(contacts, ensure_ascii=False, indent=1), encoding="utf-8")
    payload = {
        "client": args.client, "label": label, "location_id": loc,
        "total_contacts": len(contacts), "protected": protected,
        "candidate_count": len(candidates), "min_batch": args.min_batch,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidates": candidates,
    }
    cand_path = out / "candidates.json"
    cand_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.stderr.write(
        f"[detect] {len(contacts)} contatti, {protected} protetti, "
        f"{len(candidates)} candidati delete-grade.\n")
    print(str(cand_path))


def cmd_review(args):
    cand_path = Path(args.candidates)
    payload = json.loads(cand_path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates", [])
    if not candidates:
        sys.exit("Nessun candidato da rivedere.")
    if len(candidates) > 300:
        sys.stderr.write(f"[review] ATTENZIONE: {len(candidates)} candidati: la pagina li rende tutti, "
                         f"valuta filtri se rallenta.\n")
    decisions_path = cand_path.with_name("decisions.json")
    page = build_page(candidates, payload)

    done = threading.Event()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype):
            b = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            try:
                self.wfile.write(b)
            except OSError:
                pass

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, page, "text/html; charset=utf-8")
            else:
                self._send(404, "not found", "text/plain")

        def do_POST(self):
            if self.path == "/submit":
                n = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(n).decode("utf-8"))
                decisions_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
                self._send(200, json.dumps({"ok": True}), "application/json")
                threading.Thread(target=lambda: (time.sleep(0.4), done.set()), daemon=True).start()
            else:
                self._send(404, "not found", "text/plain")

    httpd, port = None, None
    for p in range(args.port, args.port + 8):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), H)
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        sys.exit("Nessuna porta libera per il server di review.")
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://localhost:{port}/"
    sys.stderr.write(f"[review] server su {url} ({len(candidates)} candidati). Apro il browser…\n")
    try:
        webbrowser.open(url)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[review] apri manualmente {url} ({e})\n")

    if done.wait(timeout=args.timeout):
        httpd.shutdown()
        data = json.loads(decisions_path.read_text(encoding="utf-8"))
        sys.stderr.write(f"[review] ricevuto: {len(data.get('delete', []))} elimina, "
                         f"{len(data.get('keep', []))} tieni.\n")
        print(str(decisions_path))
    else:
        httpd.shutdown()
        sys.exit("[review] timeout: nessuna decisione ricevuta.")


def cmd_delete(args):
    dec_path = Path(args.decisions)
    data = json.loads(dec_path.read_text(encoding="utf-8"))
    to_delete = data.get("delete", [])
    client = data.get("client") or args.client
    if not client:
        sys.exit("Client non determinabile: passa --client.")
    env, env_path = load_env()
    token, _ = resolve_creds(env, client)
    if not token:
        sys.exit(f"Token GHL mancante per '{client}' (env: {env_path}).")

    if not args.execute:
        sys.stderr.write(f"[delete] DRY-RUN — {len(to_delete)} contatti verrebbero eliminati:\n")
        for c in to_delete:
            print(f"WOULD_DELETE {c.get('id')}  {c.get('email') or c.get('name')}")
        sys.stderr.write("[delete] nessuna chiamata API. Rilancia con --execute per eseguire.\n")
        return

    ok, missing, failed = 0, 0, 0
    for c in to_delete:
        cid = c.get("id")
        try:
            status, _ = api("DELETE", f"/contacts/{cid}", token)
            ok += 1
            print(f"DELETED {cid}  {c.get('email') or c.get('name')}")
        except HTTPError as e:
            if e.code == 404:
                missing += 1
                print(f"ALREADY_GONE {cid}")
            else:
                failed += 1
                sys.stderr.write(f"  FAIL {cid}: HTTP {e.code}\n")
        except URLError as e:
            failed += 1
            sys.stderr.write(f"  FAIL {cid}: {e}\n")
        time.sleep(0.15)
    sys.stderr.write(f"[delete] eliminati {ok}, gia-assenti {missing}, falliti {failed}.\n")


# ----------------------------------------------------------------------------
# Pagina review (template caricato da file, dati iniettati come JSON)
# ----------------------------------------------------------------------------
def build_page(candidates, payload):
    tpl = (Path(__file__).parent / "review-page.html").read_text(encoding="utf-8")
    data_json = json.dumps({
        "candidates": candidates,
        "client": payload.get("client", ""),
        "total": payload.get("total_contacts", 0),
    }, ensure_ascii=False)
    return tpl.replace("/*__DATA__*/null", data_json)


def main():
    ap = argparse.ArgumentParser(prog="crm-list-cleanup", description="Pulizia liste contatti Futuria CRM")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="trova candidati spam delete-grade")
    d.add_argument("--client", default="", help="slug account (agency); omettilo per single-account (FUTURIA_CRM_TOKEN)")
    d.add_argument("--protect-tags", default="", help="tag extra da proteggere, separati da virgola")
    d.add_argument("--min-batch", type=int, default=8, help="soglia contatti nello stesso minuto per batch-injection")
    d.add_argument("--out", default="", help="cartella di output (default ~/.futuria/crm-cleanup/...)")
    d.set_defaults(func=cmd_detect)

    r = sub.add_parser("review", help="apri la pagina di review nel browser")
    r.add_argument("--candidates", required=True, help="path a candidates.json")
    r.add_argument("--port", type=int, default=8731)
    r.add_argument("--timeout", type=int, default=900)
    r.set_defaults(func=cmd_review)

    x = sub.add_parser("delete", help="elimina i contatti marcati (dry-run di default)")
    x.add_argument("--decisions", required=True, help="path a decisions.json")
    x.add_argument("--client", default="", help="slug account (se non nel file)")
    x.add_argument("--execute", action="store_true", help="esegue le DELETE reali")
    x.set_defaults(func=cmd_delete)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
