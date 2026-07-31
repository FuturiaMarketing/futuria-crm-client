#!/usr/bin/env bash
set -euo pipefail
set +x

if (( $# < 2 || $# > 3 )); then
  echo "Uso: crm-api.sh METHOD /percorso[/...] [corpo-json]" >&2
  exit 2
fi

method="$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')"
path="$2"
body="${3:-}"
version="${FUTURIA_CRM_API_VERSION:-2021-07-28}"

case "${method}" in
  GET|POST|PUT|PATCH|DELETE) ;;
  *) echo "Metodo API non consentito." >&2; exit 2 ;;
esac
if [[ "${path}" != /* ]] || [[ "${path}" == *"://"* ]]; then
  echo "Il percorso API deve essere relativo e iniziare con /. URL esterni non sono consentiti." >&2
  exit 2
fi

location="${FUTURIA_CRM_LOCATION:-${FUTURIA_CRM_LOCATION_ID:-}}"
token="${FUTURIA_CRM_TOKEN:-}"

if [[ "$(uname -s)" == "Darwin" ]]; then
  config_file="${HOME}/Library/Application Support/Futuria CRM/config.json"
  if [[ -z "${location}" && -f "${config_file}" ]]; then
    location="$(sed -nE 's/.*"location"[[:space:]]*:[[:space:]]*"([A-Za-z0-9_-]+)".*/\1/p' "${config_file}" | head -n 1)"
  fi
  if [[ -z "${token}" ]]; then
    token="$(security find-generic-password -a default -s com.futuriamarketing.futuria-crm.pit -w 2>/dev/null || true)"
  fi
fi

if [[ -z "${token}" || -z "${location}" ]]; then
  echo "Credenziali Futuria CRM mancanti. Esegui prima lo script di configurazione protetta." >&2
  exit 3
fi
if [[ "${token}" != pit-* ]]; then
  unset token
  echo "Il PIT configurato non ha il formato atteso." >&2
  exit 3
fi
if [[ ! "${location}" =~ ^[A-Za-z0-9_-]{6,128}$ ]]; then
  unset token
  echo "L'ID account configurato non ha il formato atteso." >&2
  exit 3
fi
if [[ ! "${version}" =~ ^(v[0-9]+|[0-9]{4}-[0-9]{2}-[0-9]{2})$ ]]; then
  unset token
  echo "La versione API richiesta non ha il formato atteso." >&2
  exit 2
fi

path="${path//\{location\}/${location}}"
body="${body//\{location\}/${location}}"
url="https://services.leadconnectorhq.com${path}"

curl_args=(--silent --show-error --fail-with-body --request "${method}" --url "${url}")
if [[ -n "${body}" ]]; then
  curl_args+=(--data-binary "${body}")
fi

{
  printf 'header = "Authorization: Bearer %s"\n' "${token//\"/\\\"}"
  printf 'header = "Version: %s"\n' "${version}"
  printf 'header = "Accept: application/json"\n'
  if [[ -n "${body}" ]]; then
    printf 'header = "Content-Type: application/json"\n'
  fi
} | curl --config - "${curl_args[@]}"

unset token
