# Getting started — connect and verify

How to get the agent operating on the user's Futuria CRM account. Read this once per environment, then move to the area reference for the actual task.

## 1. The two credentials

The connection to the account is two environment variables on the user's machine:

| Variable | What it is | Format |
| --- | --- | --- |
| `FUTURIA_CRM_TOKEN` | Private integration token of the account | starts with `pit-`, ~40 chars |
| `FUTURIA_CRM_LOCATION` | The account id (some endpoints call it `locationId`) | ~20 alphanumeric chars |

- The **token** goes in the `Authorization` header; the **account id** goes in the request parameters. Confusing the two is the most common cause of errors.
- `FUTURIA_CRM_LOCATION_ID` is accepted as an alias by the bundled scripts, but prefer `FUTURIA_CRM_LOCATION`.
- Never print the token in clear text. When diagnosing, show only a masked prefix (first few characters).
- The user provides their own credentials; there are no shared credentials in this skill.

Check availability without exposing values (any shell):

```bash
python -c "import os; t=os.environ.get('FUTURIA_CRM_TOKEN',''); l=os.environ.get('FUTURIA_CRM_LOCATION',''); print('token:', (t[:6]+'...') if t else 'MANCANTE', '| account id:', 'ok' if l else 'MANCANTE')"
```

## 2. If a credential is missing — guided setup (do not dead-end)

The typical user is **not technical**. If a variable is missing, walk them through it in simple Italian, one step at a time:

1. Explain what is missing: «Per collegarmi al tuo account Futuria CRM mi servono due codici: il token di accesso e l'ID del tuo account.»
2. Where to get the values: **il referente Futuria Marketing li fornisce all'attivazione** (è il canale consigliato). Both values also exist in the account settings, but do not send a non-technical user hunting for them — suggest writing to Futuria instead.
3. Set them, then **restart the agent app** so it sees the new variables:
   - **Windows (PowerShell):** `setx FUTURIA_CRM_TOKEN "pit-..."` and `setx FUTURIA_CRM_LOCATION "..."` — then close and reopen the agent.
   - **macOS/Linux (zsh/bash):** append `export FUTURIA_CRM_TOKEN="pit-..."` and `export FUTURIA_CRM_LOCATION="..."` to the shell profile (`~/.zshrc` or `~/.bashrc`), open a new terminal, relaunch the agent.
4. Re-run the availability check above, then the sanity read below.

If the user prefers, you may run the `setx`/profile commands for them — show what you are about to run and never echo the full values back in chat.

## 3. First sanity read

Before a session's first write, confirm the account is reachable (base URL and headers in `references/api-and-troubleshooting.md`):

1. `GET /locations/{FUTURIA_CRM_LOCATION}` → returns the account card (name, company data). Confirm in Italian: «Sono collegato al tuo account Futuria CRM "<nome>".»
2. If that fails for scope reasons, fall back to one low-risk read: `POST /contacts/search` with body `{"locationId": "<account id>", "pageLimit": 1, "filters": []}`.
3. If both fail, classify the failure with the error matrix in `references/api-and-troubleshooting.md` before changing anything. Do not assume an object is missing until the token is verified.

## 4. Reporting

- Always reply in **Italian**, calling the platform **Futuria CRM**.
- After a write, report the exact fields changed and the object's identifier, and confirm you re-read the result.
- If wording about the platform, the account, or costs comes up, follow `references/terminology-and-voice.md`.
