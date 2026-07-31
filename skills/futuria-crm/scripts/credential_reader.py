#!/usr/bin/env python3
"""Read Futuria CRM credentials without writing the PIT to stdout or logs."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path


class CredentialError(RuntimeError):
    pass


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
    )
    if result.returncode != 0:
        raise CredentialError("Il PIT protetto di Windows non è leggibile dall'utente corrente.")
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
        missing.append("PIT")
    if require_location and not location:
        missing.append("ID account")
    if missing:
        raise CredentialError(
            "Configurazione Futuria CRM mancante: " + ", ".join(missing)
            + ". Avvia lo script di configurazione protetta in una finestra separata."
        )
    if token and not token.startswith("pit-"):
        raise CredentialError("Il PIT configurato non ha il formato atteso.")
    return token, location
