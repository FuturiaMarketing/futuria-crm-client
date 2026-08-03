#!/usr/bin/env python3
"""Read Futuria CRM credentials without writing the PIT to stdout or logs."""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from pathlib import Path


class CredentialError(RuntimeError):
    pass


TOKEN_RE = re.compile(r"^pit-[A-Za-z0-9._-]{6,2048}$")
LOCATION_RE = re.compile(r"^[A-Za-z0-9_-]{6,128}$")


def _windows_powershell_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in tuple(environment):
        if key.casefold() == "psmodulepath":
            environment.pop(key, None)
    return environment


def _config_path() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
        return base / "Futuria CRM" / "config.json"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Futuria CRM" / "config.json"
    base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / "futuria-crm" / "config.json"


def _read_location() -> str:
    env_value = (os.environ.get("FUTURIA_CRM_LOCATION")
                 or os.environ.get("FUTURIA_CRM_LOCATION_ID") or "").strip()
    if env_value:
        return env_value
    path = _config_path()
    if not path.exists():
        return ""
    try:
        return str(json.loads(path.read_text(encoding="utf-8-sig")).get("location") or "").strip()
    except (OSError, ValueError) as exc:
        raise CredentialError("Configurazione locale Futuria CRM non leggibile.") from exc


def _read_windows_token() -> str:
    credential_path = _config_path().with_name("credential.xml")
    if not credential_path.exists():
        return ""
    script = (
        "$c=Import-Clixml -LiteralPath $args[0];"
        "if($c -isnot [System.Management.Automation.PSCredential]){exit 3};"
        "[Console]::Out.Write($c.GetNetworkCredential().Password)"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script,
         str(credential_path)],
        capture_output=True,
        text=True,
        check=False,
        env=_windows_powershell_environment(),
    )
    if result.returncode != 0:
        raise CredentialError("La chiave privata protetta di Windows non è leggibile dall'utente corrente.")
    return result.stdout.strip()


def _read_macos_token() -> str:
    result = subprocess.run(
        ["security", "find-generic-password", "-a", "default", "-s",
         "com.futuriamarketing.futuria-crm.pit", "-w"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def load_credentials(require_location: bool = True) -> tuple[str, str]:
    token = (os.environ.get("FUTURIA_CRM_TOKEN") or "").strip()
    if not token:
        system = platform.system()
        if system == "Windows":
            token = _read_windows_token()
        elif system == "Darwin":
            token = _read_macos_token()

    location = _read_location()
    missing = []
    if not token:
        missing.append("chiave privata")
    if require_location and not location:
        missing.append("ID account")
    if missing:
        raise CredentialError(
            "Configurazione Futuria CRM mancante: " + ", ".join(missing)
            + ". Avvia il configuratore protetto."
        )
    if token and not TOKEN_RE.fullmatch(token):
        raise CredentialError("La chiave privata configurata non ha il formato atteso.")
    if location and not LOCATION_RE.fullmatch(location):
        raise CredentialError("L'ID account configurato non ha il formato atteso.")
    return token, location
