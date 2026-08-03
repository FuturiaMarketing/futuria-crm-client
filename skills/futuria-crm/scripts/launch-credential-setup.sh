#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Questo launcher avvia il configuratore protetto su macOS." >&2
  exit 2
fi

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
wizard_script="${script_dir}/credential-wizard.mjs"
setup_script="${script_dir}/setup-credentials.sh"

if [[ -f "${wizard_script}" ]] && command -v node >/dev/null 2>&1; then
  nohup node "${wizard_script}" >/dev/null 2>&1 &
  echo "Configuratore grafico Futuria CRM aperto nel browser."
  exit 0
fi

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

echo "Node.js non è disponibile: aperta la configurazione protetta in Terminale."
