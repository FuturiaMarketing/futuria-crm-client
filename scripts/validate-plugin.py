#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validator del plugin futuria-crm-client. Eseguito in CI e prima di ogni release.

Controlli:
  1. White-label: nessun nome del vendor fuori dal file di terminologia controllato;
     l'host tecnico solo nei file dove e' inevitabile.
  2. JSON del repo tutti validi.
  3. SKILL.md: frontmatter con name (= cartella) e description; niente doppi apici
     nella description (il parser frontmatter di alcuni runtime scarta la skill).
  4. Ogni skill ha agents/openai.yaml e un command wrapper commands/<name>.md.
  5. I path `references/...` citati nelle skill esistono davvero.
  6. Niente placeholder TODO/FIXME nei contenuti distribuiti.

Uso:  python scripts/validate-plugin.py
Exit 0 = tutto ok; exit 1 = violazioni (elencate).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []

TEXT_EXT = {".md", ".json", ".yaml", ".yml", ".py", ".ps1", ".sh", ".html", ".css", ".js", ".mjs", ".txt"}
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__"}
SELF = Path(__file__).resolve()

# Nomi del vendor: MAI nel repo, tranne la tabella di riconoscimento nella
# reference di terminologia. Pattern composti a runtime per non auto-matcharsi.
BRAND_PAT = re.compile("|".join(["go" + "highlevel", "high" + "level", r"\bg" + r"hl\b"]),
                       re.IGNORECASE)
BRAND_ALLOW = {"skills/futuria-crm/references/terminology-and-voice.md"}

# Host tecnico: tollerato solo dove e' parte di endpoint reali.
HOST_PAT = re.compile("lead" + "connector", re.IGNORECASE)
HOST_ALLOW = BRAND_ALLOW | {
    "skills/futuria-crm/references/api-and-troubleshooting.md",
    "skills/futuria-crm/scripts/crm-api.ps1",
    "skills/futuria-crm/scripts/crm-api.sh",
    "skills/futuria-crm/scripts/credential-wizard.mjs",
    "skills/pulisci-liste-crm/scripts/crm-list-cleanup.py",
}

PLACEHOLDER_PAT = re.compile(r"\bTODO\b|\bFIXME\b|\bXXX\b")


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def iter_files():
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.resolve() == SELF:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in TEXT_EXT:
            yield p


def check_branding():
    for p in iter_files():
        text = p.read_text(encoding="utf-8", errors="replace")
        r = rel(p)
        for i, line in enumerate(text.splitlines(), 1):
            if BRAND_PAT.search(line) and r not in BRAND_ALLOW:
                ERRORS.append(f"[brand] {r}:{i} contiene un nome vendor: {line.strip()[:90]}")
            if HOST_PAT.search(line) and r not in HOST_ALLOW:
                ERRORS.append(f"[host]  {r}:{i} espone l'host tecnico fuori dai file consentiti")


def check_json():
    for p in iter_files():
        if p.suffix.lower() != ".json":
            continue
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            ERRORS.append(f"[json]  {rel(p)} non valido: {e}")


def check_packaging():
    required = [
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / ".codex-plugin" / "plugin.json",
        ROOT / ".agents" / "plugins" / "marketplace.json",
        ROOT / "INSTALL.md",
        ROOT / "PRIVACY.md",
        ROOT / "SECURITY.md",
    ]
    for path in required:
        if not path.exists():
            ERRORS.append(f"[pack]  manca {rel(path)}")
    if any(not p.exists() for p in required[:3]):
        return

    claude = json.loads(required[0].read_text(encoding="utf-8"))
    claude_market = json.loads(required[1].read_text(encoding="utf-8"))
    codex = json.loads(required[2].read_text(encoding="utf-8"))
    market_plugins = claude_market.get("plugins") or []
    market_version = market_plugins[0].get("version") if market_plugins else None
    versions = {claude.get("version"), codex.get("version"), market_version}
    if len(versions) != 1 or None in versions:
        ERRORS.append(f"[pack]  versioni divergenti: Claude={claude.get('version')}, "
                      f"Codex={codex.get('version')}, marketplace={market_version}")
    if claude.get("name") != "futuria-crm" or codex.get("name") != "futuria-crm":
        ERRORS.append("[pack]  il nome plugin deve essere futuria-crm in entrambi i runtime")

    manifest_version = claude.get("version")
    for version_path in [
        ROOT / "skills" / "futuria-crm" / "VERSION",
        ROOT / "skills" / "pulisci-liste-crm" / "VERSION",
    ]:
        if not version_path.exists():
            ERRORS.append(f"[pack]  manca {rel(version_path)}")
            continue
        skill_version = version_path.read_text(encoding="utf-8").strip()
        if skill_version != manifest_version:
            ERRORS.append(f"[pack]  {rel(version_path)}={skill_version} ma manifest={manifest_version}")

    privacy_url = (codex.get("interface") or {}).get("privacyPolicyURL", "")
    if not privacy_url.endswith("/PRIVACY.md"):
        ERRORS.append("[pack]  privacyPolicyURL Codex mancante o non canonico")


def check_credential_contract():
    distributed_docs = [ROOT / "README.md", ROOT / "INSTALL.md"]
    unsafe = [
        re.compile(r"\bsetx\s+FUTURIA_CRM_TOKEN", re.IGNORECASE),
        re.compile(r"\bexport\s+FUTURIA_CRM_TOKEN\s*=", re.IGNORECASE),
        re.compile(r"i dati (?:del tuo account )?viaggiano solo", re.IGNORECASE),
    ]
    for path in distributed_docs:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in unsafe:
            if pattern.search(text):
                ERRORS.append(f"[cred]  {rel(path)} contiene onboarding o promessa privacy non sicuri")

    scripts = [
        ROOT / "skills" / "futuria-crm" / "scripts" / "setup-credentials.ps1",
        ROOT / "skills" / "futuria-crm" / "scripts" / "setup-credentials.sh",
        ROOT / "skills" / "futuria-crm" / "scripts" / "crm-api.ps1",
        ROOT / "skills" / "futuria-crm" / "scripts" / "crm-api.sh",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential_reader.py",
        ROOT / "skills" / "futuria-crm" / "scripts" / "launch-credential-setup.ps1",
        ROOT / "skills" / "futuria-crm" / "scripts" / "launch-credential-setup.sh",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard.mjs",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard" / "index.html",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard" / "styles.css",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard" / "app.js",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard" / "assets" / "futuria-crm-logo.png",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard" / "assets" / "step-1-private-integrations.png",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard" / "assets" / "step-2-integration-details.png",
        ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard" / "assets" / "step-3-paste-here.png",
    ]
    for path in scripts:
        if not path.exists():
            ERRORS.append(f"[cred]  helper credenziali mancante: {rel(path)}")

    mac_setup = scripts[1]
    mac_api = scripts[3]
    if mac_setup.exists():
        text = mac_setup.read_text(encoding="utf-8", errors="replace")
        if re.search(r"-w\s+[\"']?\$\{?pit\b", text, re.IGNORECASE):
            ERRORS.append("[cred]  setup macOS passa il PIT come argomento di processo")
    if mac_api.exists():
        text = mac_api.read_text(encoding="utf-8", errors="replace")
        if "${1^^}" in text:
            ERRORS.append("[compat] crm-api.sh usa sintassi non supportata da Bash 3 di macOS")

    wizard = ROOT / "skills" / "futuria-crm" / "scripts" / "credential-wizard.mjs"
    if wizard.exists():
        text = wizard.read_text(encoding="utf-8", errors="replace")
        lower_text = text.lower()
        if not all(marker in lower_text for marker in ["127.0.0.1", "samesite=strict", "x-futuria-csrf", "cache-control"]):
            ERRORS.append("[cred]  il configuratore locale non dichiara tutte le protezioni richieste")
        unsafe_mac_args = re.search(
            r'runChild\(\s*"/usr/bin/security"\s*,\s*\[[^\]]*privateKey',
            text,
            re.DOTALL,
        )
        if unsafe_mac_args:
            ERRORS.append("[cred]  il configuratore macOS passa la chiave negli argomenti di processo")


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def check_skills():
    skills_dir = ROOT / "skills"
    for sk in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
        name = sk.name
        skill_md = sk / "SKILL.md"
        if not skill_md.exists():
            ERRORS.append(f"[skill] {name}: manca SKILL.md")
            continue
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if not fm:
            ERRORS.append(f"[skill] {name}: frontmatter assente in SKILL.md")
        else:
            if fm.get("name", "").strip("\"'") != name:
                ERRORS.append(f"[skill] {name}: frontmatter name != nome cartella")
            desc = fm.get("description", "")
            if not desc:
                ERRORS.append(f"[skill] {name}: description mancante")
            if '"' in desc:
                ERRORS.append(f"[skill] {name}: doppi apici nella description (rompe il parser)")
        if not (sk / "agents" / "openai.yaml").exists():
            ERRORS.append(f"[skill] {name}: manca agents/openai.yaml")
        if not (ROOT / "commands" / f"{name}.md").exists():
            ERRORS.append(f"[skill] {name}: manca il command wrapper commands/{name}.md")


def check_reference_paths():
    # I path `references/...` sono relativi alla RADICE della skill (dir di SKILL.md),
    # anche quando citati dentro una reference; si accetta pure il path dal file stesso.
    ref_pat = re.compile(r"`((?:\.\./)?(?:[\w-]+/)?references/[\w./-]+\.md)`")
    for p in (ROOT / "skills").rglob("*.md"):
        skill_dir = p.parent
        while skill_dir.parent.name != "skills" and skill_dir.name != "skills":
            skill_dir = skill_dir.parent
        text = p.read_text(encoding="utf-8", errors="replace")
        for refpath in ref_pat.findall(text):
            candidates = [(p.parent / refpath), (skill_dir / refpath)]
            if not any(c.resolve().exists() for c in candidates):
                ERRORS.append(f"[ref]   {rel(p)}: riferimento inesistente {refpath}")


def check_placeholders():
    for p in iter_files():
        if p.suffix.lower() not in {".md", ".yaml", ".yml"}:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if PLACEHOLDER_PAT.search(line):
                ERRORS.append(f"[todo]  {rel(p)}:{i} placeholder da rimuovere: {line.strip()[:80]}")


def main():
    check_branding()
    check_json()
    check_packaging()
    check_credential_contract()
    check_skills()
    check_reference_paths()
    check_placeholders()
    if ERRORS:
        print(f"VALIDAZIONE FALLITA — {len(ERRORS)} violazioni:")
        for e in ERRORS:
            print("  " + e)
        sys.exit(1)
    print("Validazione OK: white-label, JSON, skill, reference e placeholder tutti a posto.")


if __name__ == "__main__":
    main()
