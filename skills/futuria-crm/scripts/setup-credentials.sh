#!/usr/bin/env bash
set -euo pipefail
set +x

service="com.futuriamarketing.futuria-crm.pit"
account="default"
config_dir="${HOME}/Library/Application Support/Futuria CRM"
config_file="${config_dir}/config.json"
action="${1:-setup}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Questo script protetto usa il Portachiavi di macOS." >&2
  echo "Su Linux configura le variabili d'ambiente in un terminale separato." >&2
  exit 2
fi

case "${action}" in
  status)
    if [[ -f "${config_file}" ]] && security find-generic-password -a "${account}" -s "${service}" >/dev/null 2>&1; then
      echo "PIT protetto: presente"
      echo "ID account: presente"
      exit 0
    fi
    echo "Configurazione Futuria CRM incompleta."
    exit 1
    ;;
  remove)
    security delete-generic-password -a "${account}" -s "${service}" >/dev/null 2>&1 || true
    rm -f -- "${config_file}"
    rmdir "${config_dir}" >/dev/null 2>&1 || true
    echo "Credenziali locali Futuria CRM rimosse. Il PIT remoto non è stato revocato."
    exit 0
    ;;
  setup) ;;
  *)
    echo "Uso: setup-credentials.sh [setup|status|remove]" >&2
    exit 2
    ;;
esac

echo "Configurazione protetta Futuria CRM"
echo "Inserisci i valori in questa finestra. Il PIT non verrà mostrato né scritto nella chat."
printf "ID del tuo account Futuria CRM: "
IFS= read -r location

if [[ ! "${location}" =~ ^[A-Za-z0-9_-]{6,128}$ ]]; then
  echo "ID account non valido: usa soltanto lettere, numeri, trattino o underscore." >&2
  exit 2
fi

echo "Il Portachiavi chiederà ora il PIT con input nascosto. Incollalo e premi Invio."
# Con -w senza valore, `security` legge il segreto direttamente dal terminale:
# durante l'inserimento il PIT non diventa un argomento di processo.
security add-generic-password -U -a "${account}" -s "${service}" -w >/dev/null

stored_pit="$(security find-generic-password -a "${account}" -s "${service}" -w 2>/dev/null || true)"
if [[ "${stored_pit}" != pit-* ]] || (( ${#stored_pit} < 10 )); then
  unset stored_pit
  security delete-generic-password -a "${account}" -s "${service}" >/dev/null 2>&1 || true
  echo "Il PIT non ha il formato atteso. Deve iniziare con pit-. Nessun valore è stato conservato." >&2
  exit 2
fi
unset stored_pit

mkdir -p -- "${config_dir}"
chmod 700 "${config_dir}"
printf '{\n  "location": "%s",\n  "storage": "macos-keychain"\n}\n' "${location}" > "${config_file}"
chmod 600 "${config_file}"

echo "Configurazione salvata nel Portachiavi dell'utente macOS corrente."
echo "Puoi chiudere questa finestra e tornare all'agente."
