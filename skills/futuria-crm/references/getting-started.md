# Getting started — protected connection and verification

Use this reference when the agent must connect the user's Futuria CRM account for the first time or diagnose missing credentials.

## 1. Connection model

The account uses two distinct values:

| Value | Purpose | Secret? |
| --- | --- | --- |
| PIT | Authorises API requests; starts with `pit-` | Yes |
| Account id | Identifies the user's Futuria CRM account | No |

Preferred storage:

- Windows: PIT encrypted with Windows DPAPI for the current user; account id in local config.
- macOS: PIT in macOS Keychain; account id in local config.
- Linux or automated environments: environment variables as an explicit fallback.

Never ask the user to paste the PIT in chat, a prompt, a shell command, a file in the workspace, or an issue. Never retrieve it merely to inspect or mask it.

## 2. Protected setup for a non-technical user

The credential prompt must run in a **separate visible terminal window**, outside the chat capture. The user types or pastes both values there; the PIT input is hidden.

Resolve the scripts relative to this skill directory.

### Windows

Run the launcher from the agent terminal. It opens a separate visible PowerShell window:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<skill-dir>\scripts\launch-credential-setup.ps1"
```

Status check, which never returns the PIT:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<skill-dir>\scripts\setup-credentials.ps1" -Status
```

### macOS

Run the launcher from the agent terminal. It opens a separate visible Terminal window:

```bash
bash "<skill-dir>/scripts/launch-credential-setup.sh"
```

Status check:

```bash
bash "<skill-dir>/scripts/setup-credentials.sh" status
```

### Environment fallback

Advanced users and non-interactive environments may provide `FUTURIA_CRM_TOKEN` plus `FUTURIA_CRM_LOCATION`. The user must set them personally outside the conversation. Do not propose a command containing their real values and do not write them into shell profiles on their behalf.

## 3. First sanity read

Use the secure helper; never build a raw Authorization header in the conversation.

Windows:

```powershell
& "<skill-dir>\scripts\crm-api.ps1" -Method GET -Path "/locations/{location}"
```

macOS:

```bash
bash "<skill-dir>/scripts/crm-api.sh" GET "/locations/{location}"
```

If the account endpoint fails for scope reasons, fall back to a one-contact read:

Windows:

```powershell
& "<skill-dir>\scripts\crm-api.ps1" -Method POST -Path "/contacts/search" -Body '{"locationId":"{location}","pageLimit":1,"filters":[]}'
```

macOS:

```bash
bash "<skill-dir>/scripts/crm-api.sh" POST "/contacts/search" '{"locationId":"{location}","pageLimit":1,"filters":[]}'
```

Confirm in Italian only the account name and the successful connection. If both reads fail, classify the HTTP response with `references/api-and-troubleshooting.md` before changing credentials.

## 4. Removing local credentials

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<skill-dir>\scripts\setup-credentials.ps1" -Remove
```

macOS:

```bash
bash "<skill-dir>/scripts/setup-credentials.sh" remove
```

This removes only the local copy. Revoking the PIT itself is a separate action in the user's Futuria CRM account.

## 5. Reporting

- Always reply in Italian and call the platform Futuria CRM.
- Report whether protected credentials are present; never report their value or prefix.
- After a write, report the exact fields changed, the object identifier, and the verification surface.
