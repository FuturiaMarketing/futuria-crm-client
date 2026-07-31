#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Questo launcher apre una finestra Terminale su macOS." >&2
  exit 2
fi

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
setup_script="${script_dir}/setup-credentials.sh"
if [[ ! -f "${setup_script}" ]]; then
  echo "Script di configurazione Futuria CRM non trovato." >&2
  exit 2
fi

printf -v quoted_setup "%q" "${setup_script}"
terminal_command="bash ${quoted_setup}; echo; echo 'Configurazione conclusa. Premi Invio per chiudere questa finestra...'; read _"
apple_command="${terminal_command//\\/\\\\}"
apple_command="${apple_command//\"/\\\"}"

osascript \
  -e 'tell application "Terminal"' \
  -e 'activate' \
  -e "do script \"${apple_command}\"" \
  -e 'end tell' >/dev/null

echo "Finestra Terminale protetta aperta. Attendi che l'utente completi la configurazione."
