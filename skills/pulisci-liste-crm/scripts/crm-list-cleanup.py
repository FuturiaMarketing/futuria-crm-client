#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pulisci-liste-crm — pulizia liste contatti del tuo account Futuria CRM.

Fasi, sempre nell'ordine:

  detect                              scarica i contatti -> scoring -> candidates.json (+ snapshot)
  decide  --candidates <file> ...     registra le decisioni della review (fatta in chat) -> decisions.json
  delete  --decisions <file>          dry-run di default; con --execute elimina davvero

  checklist --candidates <file>       (fallback, candidati numerosi) genera una checklist Excel
                                      con menu a tendina Elimina/Tieni; si rilegge con
                                      decide --from-checklist <file.xlsx>

La review avviene in chat: l'agente mostra i candidati coi segnali, il cliente risponde.
Nessun server locale, nessuna pagina browser, nessun processo in background.

Credenziali: archivio protetto della skill Futuria CRM su Windows/macOS;
variabili FUTURIA_CRM_TOKEN e FUTURIA_CRM_LOCATION come fallback tecnico.

Sicurezza: dry-run di default, protect-list sempre attiva, snapshot completo in detect,
decisions.json scritto solo da `decide` che accetta esclusivamente ID presenti tra i
candidati, ri-lettura di ogni contatto prima dell'eliminazione (con nuovo skip se nel
frattempo è diventato protetto), eliminazioni tolleranti se un contatto è già sparito.
Solo stdlib Python 3: gira identico su macOS e Windows (anche la checklist Excel).
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from xml.sax.saxutils import escape

BASE = "https://services.leadconnectorhq.com"
USER_AGENT = "futuria-crm-client/1.0"
API_VERSION = "2021-07-28"

# Provider email usa-e-getta / temporanei: lista UNIVERSALE (mai domini vanity
# visti su un singolo account). Aggiornabile, non specifica di un account.
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

# TLD esotici frequenti nello spam (segnale debole, mai trigger da solo).
EXOTIC_TLDS = {".top", ".xyz", ".icu", ".click", ".country", ".zip", ".tk",
               ".ml", ".ga", ".cf", ".gq", ".su", ".ru", ".work", ".buzz"}


# ----------------------------------------------------------------------------
# Credenziali (archivio OS protetto, con fallback variabili d'ambiente)
# ----------------------------------------------------------------------------
def resolve_creds(need_location=True):
    scripts_dir = Path(__file__).resolve().parents[2] / "futuria-crm" / "scripts"
    if scripts_dir.exists():
        sys.path.insert(0, str(scripts_dir))
        try:
            from credential_reader import CredentialError, load_credentials
            return load_credentials(require_location=need_location)
        except ImportError:
            pass
        except CredentialError as exc:
            sys.exit(str(exc))

    token = (os.environ.get("FUTURIA_CRM_TOKEN") or "").strip()
    loc = (os.environ.get("FUTURIA_CRM_LOCATION")
           or os.environ.get("FUTURIA_CRM_LOCATION_ID") or "").strip()
    return token, loc


def require_creds(need_location=True):
    token, loc = resolve_creds(need_location=need_location)
    missing = []
    if not token:
        missing.append("FUTURIA_CRM_TOKEN")
    if need_location and not loc:
        missing.append("FUTURIA_CRM_LOCATION")
    if missing:
        sys.exit(
            "Credenziali del tuo account Futuria CRM mancanti: "
            + ", ".join(missing)
            + ".\nAvvia la configurazione protetta della skill Futuria CRM in una finestra "
              "separata. Se non hai i valori, chiedili al tuo referente Futuria."
        )
    return token, loc


# ----------------------------------------------------------------------------
# HTTP (stdlib, con retry prudente su rate-limit / errori transitori)
# ----------------------------------------------------------------------------
def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Version": API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }


def api(method, path, token, body=None, timeout=60, retries=3):
    """Chiama l'API del tuo account Futuria CRM. Ritenta su 429/5xx con backoff."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    attempt = 0
    while True:
        req = urlrequest.Request(BASE + path, data=data, headers=headers(token), method=method)
        try:
            with urlrequest.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, (json.loads(raw) if raw else {})
        except HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = 2.0 * (attempt + 1)
                sys.stderr.write(f"  [api] HTTP {e.code} su {method} {path}: riprovo tra {wait:.0f}s…\n")
                time.sleep(wait)
                attempt += 1
                continue
            raise
        except URLError:
            if attempt < retries:
                time.sleep(2.0 * (attempt + 1))
                attempt += 1
                continue
            raise


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
        total = res.get("total")
        if not sa or (isinstance(total, int) and len(out) >= total):
            break
        search_after = sa
        if page >= 200:  # guardia: max ~20.000 contatti in v1
            sys.stderr.write("  [detect] raggiunto il limite di 200 pagine: mi fermo qui.\n")
            break
        time.sleep(0.12)  # rispetto dei limiti di frequenza dell'API
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


def protected_by_tags(contact, protect_tags):
    tags = [t.lower() for t in (contact.get("tags") or [])]
    return any(t in protect_tags for t in tags)


def classify(contact, buckets, protect_tags, min_batch):
    """Ritorna (grade, signals). grade in {'protect','delete', None}. v1: solo delete-grade.

    Alta precisione: si segnala solo su segnali STRUTTURALI forti o su profili senza
    alcuna identita. Un contatto con nome reale o telefono NON viene mai segnalato se
    non colpisce un segnale hard (dominio usa-e-getta / scam). Forma del nome/email
    (Unicode stilizzato, email puntata) e' solo una NOTA, mai un trigger da sola:
    i creator con nomi stilizzati e le email molto puntate sono spesso legittimi.
    """
    if protected_by_tags(contact, protect_tags):
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

    # Trigger HARD (v1, alta precisione): solo fake strutturali.
    # NON sono trigger: contatto WhatsApp/social senza nome (persona reale che ha
    # scritto senza lasciare i dati) e import in batch di contatti solo-email
    # (una lista newsletter caricata dal titolare sembra identica). Restano note.
    hard = []
    if domain in DISPOSABLE_DOMAINS:
        hard.append(f"dominio usa-e-getta {domain}")
    if any(k in name_blob for k in SCAM_KEYWORDS) or any(u in name_blob for u in URL_FRAGMENTS):
        hard.append("scam/URL nei dati")
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
    if da16 and buckets.get(da16, 0) >= min_batch:
        notes.append(f"nota: creato in batch ({buckets[da16]} nello stesso minuto)")
    if ("whatsapp" in medium or "instagram" in medium) and no_name:
        notes.append("nota: arrivato da social/WhatsApp senza nome")
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
# Checklist Excel (fallback review su file — scrittura e rilettura, solo stdlib)
# ----------------------------------------------------------------------------
CHECKLIST_HEADERS = ("N.", "Nome", "Email", "Telefono", "Origine", "Creato il",
                     "Perché è sospetto", "Decisione", "ID (non modificare)")
XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col(idx):
    # 0 -> A, 1 -> B, ...
    s = ""
    idx += 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def _c_str(col, row, text, style):
    return (f'<c r="{col}{row}" s="{style}" t="inlineStr">'
            f'<is><t xml:space="preserve">{escape(str(text))}</t></is></c>')


def _c_num(col, row, value, style):
    return f'<c r="{col}{row}" s="{style}"><v>{value}</v></c>'


def write_checklist_xlsx(path, candidates):
    """Genera la checklist Excel con menu a tendina Elimina/Tieni per riga."""
    n = len(candidates)
    first_data, last_data = 5, 4 + n
    dec_col, id_col = "H", "I"
    sig_width = 52  # larghezza colonna segnali, usata per stimare l'altezza riga

    rows = []
    rows.append(f'<row r="1" ht="28" customHeight="1">{_c_str("A", 1, "Pulizia liste — Futuria CRM", 1)}</row>')
    instr = ("Tutte le righe partono su ELIMINA: apri il menu a tendina nella colonna Decisione "
             "e metti TIENI sui contatti da conservare. Poi salva il file e torna in chat. "
             "Da questo file non parte nessuna eliminazione: l'assistente farà prima una prova a vuoto "
             "e ti chiederà conferma.")
    rows.append(f'<row r="2" ht="42" customHeight="1">{_c_str("A", 2, instr, 2)}</row>')
    rows.append('<row r="3" ht="8" customHeight="1"></row>')
    head = "".join(_c_str(_col(i), 4, h, 3) for i, h in enumerate(CHECKLIST_HEADERS))
    rows.append(f'<row r="4" ht="22" customHeight="1">{head}</row>')

    for i, c in enumerate(candidates):
        r = first_data + i
        signals = "; ".join(c.get("signals") or [])
        cells = [
            _c_num("A", r, i + 1, 4),
            _c_str("B", r, c.get("name") or "(senza nome)", 4),
            _c_str("C", r, c.get("email") or "—", 4),
            _c_str("D", r, c.get("phone") or "—", 4),
            _c_str("E", r, c.get("source") or "—", 4),
            _c_str("F", r, (c.get("dateAdded") or "—").replace("T", " "), 4),
            _c_str("G", r, signals, 5),
            _c_str("H", r, "Elimina", 6),
            _c_str("I", r, c.get("id") or "", 7),
        ]
        lines = max(1, -(-len(signals) // sig_width))  # ceil: righe stimate col wrap
        attrs = f' ht="{14 + 16 * lines}" customHeight="1"' if lines > 1 else ""
        rows.append(f'<row r="{r}"{attrs}>{"".join(cells)}</row>')

    widths = (5, 26, 34, 17, 15, 17, sig_width, 14, 26)
    cols = "".join(f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>'
                   for i, w in enumerate(widths))

    sheet = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetViews><sheetView workbookViewId="0" showGridLines="0">
<pane ySplit="4" topLeftCell="A5" activePane="bottomLeft" state="frozen"/>
<selection pane="bottomLeft" activeCell="{dec_col}{first_data}" sqref="{dec_col}{first_data}"/>
</sheetView></sheetViews>
<sheetFormatPr defaultRowHeight="17"/>
<cols>{cols}</cols>
<sheetData>{"".join(rows)}</sheetData>
<autoFilter ref="A4:{id_col}{last_data}"/>
<mergeCells count="2"><mergeCell ref="A1:{id_col}1"/><mergeCell ref="A2:{id_col}2"/></mergeCells>
<conditionalFormatting sqref="{dec_col}{first_data}:{dec_col}{last_data}">
<cfRule type="cellIs" dxfId="0" priority="1" operator="equal"><formula>"Elimina"</formula></cfRule>
<cfRule type="cellIs" dxfId="1" priority="2" operator="equal"><formula>"Tieni"</formula></cfRule>
</conditionalFormatting>
<dataValidations count="1">
<dataValidation type="list" allowBlank="1" showErrorMessage="1" errorStyle="stop"
 errorTitle="Valore non valido" error="Scegli Elimina o Tieni dal menu a tendina."
 sqref="{dec_col}{first_data}:{dec_col}{last_data}"><formula1>"Elimina,Tieni"</formula1></dataValidation>
</dataValidations>
<pageMargins left="0.5" right="0.5" top="0.5" bottom="0.5" header="0.3" footer="0.3"/>
</worksheet>'''

    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="6">
<font><sz val="11"/><color rgb="FF1F2937"/><name val="Calibri"/></font>
<font><b/><sz val="16"/><color rgb="FF103D66"/><name val="Calibri"/></font>
<font><sz val="10.5"/><color rgb="FF4B5563"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
<font><sz val="9"/><color rgb="FF94A3B8"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><color rgb="FF1F2937"/><name val="Calibri"/></font>
</fonts>
<fills count="4">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF103D66"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFF7F8FA"/></patternFill></fill>
</fills>
<borders count="2">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border><left/><right/><top/><bottom style="thin"><color rgb="FFE4E8EE"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="8">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="3" fillId="2" borderId="0" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
<xf numFmtId="0" fontId="5" fillId="0" borderId="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
<xf numFmtId="0" fontId="4" fillId="3" borderId="1" applyAlignment="1"><alignment vertical="center"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normale" xfId="0" builtinId="0"/></cellStyles>
<dxfs count="2">
<dxf><font><b/><color rgb="FFB91C1C"/></font><fill><patternFill><bgColor rgb="FFFEE2E2"/></patternFill></fill></dxf>
<dxf><font><b/><color rgb="FF3D6B22"/></font><fill><patternFill><bgColor rgb="FFEAF2E1"/></patternFill></fill></dxf>
</dxfs>
</styleSheet>'''

    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Pulizia liste" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''

    wb_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return path


def read_checklist_decisions(path):
    """Legge la checklist compilata (anche dopo il re-save di Excel, che converte
    i testi in sharedStrings). Ritorna dict {contact_id: 'elimina'|'tieni'}.
    Solo 'Elimina' esplicito conta come eliminazione; vuoto o altro = tieni."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{XLSX_NS}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{XLSX_NS}t")))
        sheet_name = next((n for n in sorted(z.namelist())
                           if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")), None)
        if not sheet_name:
            raise ValueError("il file Excel non contiene fogli")
        root = ET.fromstring(z.read(sheet_name))

    def cell_text(c):
        t = c.get("t")
        if t == "inlineStr":
            return "".join(x.text or "" for x in c.iter(f"{XLSX_NS}t"))
        v = c.find(f"{XLSX_NS}v")
        if v is None or v.text is None:
            return ""
        if t == "s":
            try:
                return shared[int(v.text)]
            except (ValueError, IndexError):
                return ""
        return v.text

    def col_of(c):
        return "".join(ch for ch in (c.get("r") or "") if ch.isalpha())

    rows = root.findall(f"{XLSX_NS}sheetData/{XLSX_NS}row")
    dec_col = id_col = header_row_idx = None
    for i, row in enumerate(rows):
        for c in row.findall(f"{XLSX_NS}c"):
            txt = cell_text(c).strip().lower()
            if txt == "decisione":
                dec_col, header_row_idx = col_of(c), i
            elif txt.startswith("id ") or txt == "id":
                id_col = col_of(c)
        if dec_col and id_col:
            break
    if not (dec_col and id_col):
        raise ValueError("checklist non riconosciuta: mancano le colonne Decisione e ID")

    out = {}
    for row in rows[header_row_idx + 1:]:
        cid = dec = ""
        for c in row.findall(f"{XLSX_NS}c"):
            col = col_of(c)
            if col == id_col:
                cid = cell_text(c).strip()
            elif col == dec_col:
                dec = cell_text(c).strip().lower()
        if cid:
            out[cid] = "elimina" if dec == "elimina" else "tieni"
    return out


# ----------------------------------------------------------------------------
# Fasi
# ----------------------------------------------------------------------------
def workdir():
    d = Path.home() / ".futuria" / "crm-cleanup" / f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_candidates(path):
    cand_path = Path(path)
    payload = json.loads(cand_path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates", [])
    if not candidates:
        sys.exit("Nessun candidato in questo file: le liste risultano già pulite.")
    return cand_path, payload, candidates


def cmd_detect(args):
    token, loc = require_creds()
    protect = set(DEFAULT_PROTECT_TAGS)
    if args.protect_tags:
        protect |= {t.strip().lower() for t in args.protect_tags.split(",") if t.strip()}

    sys.stderr.write(f"[detect] account {loc}; PIT protetto disponibile.\n")
    contacts = fetch_all_contacts(token, loc)
    buckets = minute_buckets(contacts)

    candidates, protected = [], 0
    for ct in contacts:
        grade, sig = classify(ct, buckets, protect, args.min_batch)
        if grade == "protect":
            protected += 1
        elif grade == "delete":
            candidates.append(to_candidate(ct, sig))

    out = Path(args.out) if args.out else workdir()
    out.mkdir(parents=True, exist_ok=True)
    (out / "contacts_snapshot.json").write_text(
        json.dumps(contacts, ensure_ascii=False, indent=1), encoding="utf-8")
    payload = {
        "location_id": loc,
        "total_contacts": len(contacts), "protected": protected,
        "candidate_count": len(candidates), "min_batch": args.min_batch,
        "protect_tags": sorted(protect),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidates": candidates,
    }
    cand_path = out / "candidates.json"
    cand_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.stderr.write(
        f"[detect] {len(contacts)} contatti, {protected} protetti, "
        f"{len(candidates)} candidati delete-grade.\n")
    print(str(cand_path))


def cmd_checklist(args):
    cand_path, _, candidates = load_candidates(args.candidates)
    out = cand_path.with_name("pulizia-liste-checklist.xlsx")
    write_checklist_xlsx(out, candidates)
    sys.stderr.write(f"[checklist] {len(candidates)} candidati nel file. Il cliente apre il file, "
                     "imposta Tieni sulle righe da conservare, salva e torna in chat.\n")
    print(str(out))


def cmd_decide(args):
    cand_path, _, candidates = load_candidates(args.candidates)
    by_id = {c["id"]: c for c in candidates if c.get("id")}

    modes = [bool(args.delete), args.delete_all, args.keep_all, bool(args.from_checklist)]
    if sum(modes) != 1:
        sys.exit("Indica una sola modalità: --delete <id,...>, --delete-all, --keep-all "
                 "oppure --from-checklist <file.xlsx>.")

    if args.from_checklist:
        decided = read_checklist_decisions(Path(args.from_checklist))
        unknown = sorted(set(decided) - set(by_id))
        if unknown:
            sys.exit("La checklist contiene ID che non sono tra i candidati di questo giro: "
                     + ", ".join(unknown[:5]) + ("…" if len(unknown) > 5 else "")
                     + ". Rigenera la checklist con il comando checklist e falla ricompilare.")
        missing = len(by_id) - len(decided)
        if missing:
            sys.stderr.write(f"[decide] {missing} candidati assenti dalla checklist: "
                             "li considero da tenere.\n")
        delete_ids = {cid for cid, d in decided.items() if d == "elimina"}
        via = "checklist"
    elif args.delete_all:
        delete_ids, via = set(by_id), "chat"
    elif args.keep_all:
        delete_ids, via = set(), "chat"
    else:
        requested = [t for t in re.split(r"[,\s]+", args.delete) if t]
        unknown = sorted(set(requested) - set(by_id))
        if unknown:
            sys.exit("Questi ID non sono tra i candidati: " + ", ".join(unknown)
                     + ". Si possono marcare solo contatti presenti in candidates.json.")
        delete_ids, via = set(requested), "chat"

    delete, keep = [], []
    for c in candidates:
        entry = {"id": c.get("id"), "email": c.get("email") or "", "name": c.get("name") or ""}
        (delete if c.get("id") in delete_ids else keep).append(entry)

    decisions_path = cand_path.with_name("decisions.json")
    if decisions_path.exists():
        # decisioni di un giro precedente: mai sovrascriverle in silenzio
        stale = decisions_path.with_name(
            f"decisions-stale-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.json")
        decisions_path.rename(stale)
        sys.stderr.write(f"[decide] decisioni precedenti spostate in {stale.name}\n")
    decisions_path.write_text(json.dumps({
        "delete": delete, "keep": keep, "decided_via": via,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.stderr.write(f"[decide] registrato: {len(delete)} elimina, {len(keep)} tieni (via {via}).\n")
    print(str(decisions_path))


def cmd_delete(args):
    dec_path = Path(args.decisions)
    data = json.loads(dec_path.read_text(encoding="utf-8"))
    to_delete = data.get("delete", [])
    token, _ = require_creds(need_location=False)

    if not to_delete:
        sys.stderr.write("[delete] nessun contatto marcato per l'eliminazione: nulla da fare.\n")
        return

    if not args.execute:
        sys.stderr.write(f"[delete] DRY-RUN — {len(to_delete)} contatti verrebbero eliminati:\n")
        for c in to_delete:
            print(f"WOULD_DELETE {c.get('id')}  {c.get('email') or c.get('name')}")
        sys.stderr.write("[delete] nessuna chiamata API. Rilancia con --execute per eseguire.\n")
        return

    protect = set(DEFAULT_PROTECT_TAGS)
    snapshot, ok, missing, skipped, failed = [], 0, 0, 0, 0
    snap_path = dec_path.with_name(
        f"pre-delete-snapshot-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.json")
    for c in to_delete:
        cid = c.get("id")
        # 1) Ri-leggo il contatto: snapshot di rollback + guardia se nel frattempo
        #    è diventato protetto (nuovo tag cliente, ecc.).
        try:
            _, res = api("GET", f"/contacts/{cid}", token)
            current = res.get("contact") or res
            snapshot.append(current)
            if protected_by_tags(current, protect):
                skipped += 1
                print(f"PROTECTED_SKIP {cid}  ora ha un tag protetto: non lo elimino")
                continue
        except HTTPError as e:
            if e.code == 404:
                missing += 1
                print(f"ALREADY_GONE {cid}")
                continue
            failed += 1
            sys.stderr.write(f"  FAIL(read) {cid}: HTTP {e.code}\n")
            continue
        except URLError as e:
            failed += 1
            sys.stderr.write(f"  FAIL(read) {cid}: {e}\n")
            continue
        # 2) Elimino (tollerante se già sparito).
        try:
            api("DELETE", f"/contacts/{cid}", token)
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
    if snapshot:
        snap_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
        sys.stderr.write(f"[delete] snapshot pre-eliminazione: {snap_path}\n")
    sys.stderr.write(f"[delete] eliminati {ok}, gia-assenti {missing}, "
                     f"protetti-saltati {skipped}, falliti {failed}.\n")


def main():
    ap = argparse.ArgumentParser(prog="crm-list-cleanup",
                                 description="Pulizia liste contatti del tuo account Futuria CRM")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="trova candidati spam delete-grade")
    d.add_argument("--protect-tags", default="", help="tag extra da proteggere, separati da virgola")
    d.add_argument("--min-batch", type=int, default=8, help="soglia contatti nello stesso minuto per batch-injection")
    d.add_argument("--out", default="", help="cartella di output (default ~/.futuria/crm-cleanup/...)")
    d.set_defaults(func=cmd_detect)

    c = sub.add_parser("checklist", help="genera la checklist Excel (fallback con molti candidati)")
    c.add_argument("--candidates", required=True, help="path a candidates.json")
    c.set_defaults(func=cmd_checklist)

    e = sub.add_parser("decide", help="registra le decisioni della review e scrive decisions.json")
    e.add_argument("--candidates", required=True, help="path a candidates.json")
    e.add_argument("--delete", default="", help="ID dei contatti da eliminare, separati da virgola")
    e.add_argument("--delete-all", action="store_true", help="marca tutti i candidati da eliminare")
    e.add_argument("--keep-all", action="store_true", help="tieni tutti i candidati")
    e.add_argument("--from-checklist", default="", help="path alla checklist Excel compilata")
    e.set_defaults(func=cmd_decide)

    x = sub.add_parser("delete", help="elimina i contatti marcati (dry-run di default)")
    x.add_argument("--decisions", required=True, help="path a decisions.json")
    x.add_argument("--execute", action="store_true", help="esegue le eliminazioni reali")
    x.set_defaults(func=cmd_delete)

    args = ap.parse_args()
    try:
        args.func(args)
    except HTTPError as e:
        if e.code in (401, 403):
            sys.exit(f"Accesso negato dal tuo account Futuria CRM (HTTP {e.code}): il token non è "
                     "valido o non ha i permessi per questa operazione. "
                     "Chiedi al referente Futuria di verificarlo.")
        sys.exit(f"Errore dal tuo account Futuria CRM (HTTP {e.code}). Riprova tra qualche minuto; "
                 "se persiste, contatta il referente Futuria.")
    except URLError as e:
        sys.exit(f"Connessione al tuo account Futuria CRM non riuscita ({getattr(e, 'reason', e)}). "
                 "Verifica la connessione internet e riprova.")
    except FileNotFoundError as e:
        sys.exit(f"File non trovato: {e.filename or e}. Controlla il percorso e riprova.")
    except (zipfile.BadZipFile, json.JSONDecodeError) as e:
        sys.exit(f"File non leggibile o corrotto: {e}. Se è la checklist, rigenerala con il "
                 "comando checklist e falla ricompilare.")
    except ValueError as e:
        sys.exit(f"File non utilizzabile: {e}")
    except KeyboardInterrupt:
        sys.exit("Operazione interrotta.")


if __name__ == "__main__":
    main()
