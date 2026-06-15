# Direct API & troubleshooting

Fallback for when the Futuria CRM MCP doesn't cover a resource, is ambiguous, or you need exact request/response control and deterministic verification.

> **Technical-host note.** This is the **only** reference where the platform's underlying technical host name may appear, because it is part of real endpoint URLs and error payloads. It is infrastructure, not a brand: **never surface the host name to the user, and never use it as the name of the platform.** To the user, everything here is **Futuria CRM**. See `references/terminology-and-voice.md`.

## Base request rules

- Base URL: `https://services.leadconnectorhq.com`
- Required headers:
  - `Authorization: Bearer <token>` — the user's Private Integration Token (`FUTURIA_CRM_TOKEN`)
  - `Version: 2021-07-28`
  - `Accept: application/json`
- Add `Content-Type: application/json` for JSON writes.
- Never log or print the full token. Mask it.

## Token & account diagnostics

1. Validate token format: correct prefix, plausible length, no stray spaces.
2. Confirm you are passing the **token** in the auth header and the **`locationId`** (not the token) where an endpoint requires an account id.
3. Probe one low-risk read endpoint with explicit headers and classify the result before changing credentials or code.

Mask-safe token check (PowerShell):

```powershell
$tokenPrefix = $token.Substring(0, [Math]::Min(8, $token.Length))
"TOKEN_PREFIX=$tokenPrefix"
"TOKEN_LENGTH=$($token.Length)"
```

Low-risk read probe (PowerShell):

```powershell
curl.exe -s -i `
  -H "Authorization: Bearer $token" `
  -H "Version: 2021-07-28" `
  -H "Accept: application/json" `
  "https://services.leadconnectorhq.com/users/?locationId=$locationId"
```

## Error matrix

### 401 Unauthorized
- Token invalid, expired, revoked, or wrong scope.
- Confirm the header is exactly `Bearer <token>`.
- Do not assume the requested object is missing until the token is verified.
- User-facing: "errore di autorizzazione sul tuo account Futuria CRM" — never name the host.

### 403 Forbidden
- Token is valid but lacks access to the requested resource.
- Confirm the token has the scope for that area.

### 422 Unprocessable Entity
- Request shape is incomplete or invalid.
- For account-scoped endpoints, add the explicit `locationId`.
- Some list endpoints enforce small `limit` values — reduce the limit before changing auth assumptions.

### 200 OK but no visible change
- Treat as partial/no-op until independently verified.
- Re-read through the canonical surface: API detail/list for metadata, the public page for published content, the web interface for builder-only internals.

## Custom field folders (contacts)

- Create a folder: `POST /locations/:locationId/customFields` with `{ "name": "<folder>", "model": "contact", "documentType": "folder", "position": <n> }`. Success key is `customFieldFolder`.
- Link a field to a folder: `PUT /locations/:locationId/customFields/:id` including the field details plus `"parentId": "<folder id>"`.
- The list endpoint exposes `parentId`, not `folderId`. If create returns `400 Folder already exists`, reuse `meta.existingId` from the body.

## Reporting

After any API fallback, report in Italian what you did and which area it touched — described as Futuria CRM — without exposing the host or any vendor name.
