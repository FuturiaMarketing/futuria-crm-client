# Direct API — foundation & troubleshooting

The direct API is the **primary channel** for operating the user's Futuria CRM account. This file carries the request foundation shared by every area reference, plus the error matrix.

> **Technical-host note.** The platform's underlying technical host may appear only in this reference and in the bundled API helpers, because it is part of real endpoint URLs and error payloads. It is infrastructure, not a brand: **never surface the host name to the user, and never use it as the name of the platform.** To the user, everything here is **Futuria CRM**. See `references/terminology-and-voice.md`.

## Secure request rules

- Base URL: `https://services.leadconnectorhq.com` — every path in the area references is relative to it.
- Use the bundled helper for every API request. It loads the PIT internally from Windows DPAPI, macOS Keychain, or the environment fallback, and accepts only relative paths on the fixed Futuria CRM API host.
- The helper adds the Authorization, Version and Accept headers. It adds the JSON content type on writes. It defaults to the validated V2 date header used by the endpoint tables; pass `-Version v3` on Windows or set `FUTURIA_CRM_API_VERSION=v3` on macOS only for an endpoint whose reference explicitly requires V3.
- Never construct or display a raw Authorization header in the conversation.

Windows:

```powershell
& "<skill-dir>\scripts\crm-api.ps1" -Method GET -Path "/locations/{location}"
```

macOS:

```bash
bash "<skill-dir>/scripts/crm-api.sh" GET "/locations/{location}"
```

Use `{location}` wherever an endpoint requires the account id; the helper replaces it without exposing the PIT. On Windows use `-Body` or `-BodyFile` for JSON. On macOS pass a small JSON body as the third argument.

## Parameter conventions per endpoint family (validated)

The account id parameter is **not uniform** across families — this table prevents the most common 422s:

| Family | How the account id is passed |
| --- | --- |
| Contacts search | JSON body: `"locationId": "..."` |
| Contacts create/upsert | JSON body: `"locationId": "..."` |
| Conversations, calendars, blogs, emails, tags, custom fields | query string: `?locationId=...` |
| **Opportunities search** | query string **snake_case**: `?location_id=...` — `locationId` here returns `422 property locationId should not exist` |
| **Payments** | query string: `?altId=<account id>&altType=location` |
| Social posting | in the path: `/social-media-posting/{locationId}/...` |

Other validated quirks:

- `GET /calendars/events` requires `startTime`/`endTime` in **epoch milliseconds** and **one of** `calendarId`, `userId` or `groupId` — omitting all three returns `422 Either of userId, calendarId or groupId is required`.
- `POST /social-media-posting/{locationId}/posts/list` wants `skip`/`limit` as **strings** (`"0"`, `"10"`), not numbers.
- Email templates live under `GET /emails/builder` — a `/emails/templates` path does **not** exist (404).

## Pagination patterns

- **Contacts search:** `pageLimit` (≤ 100 recommended) + cursor — each returned contact carries a `searchAfter` array; pass the last one as `"searchAfter"` in the next request body until you reach `total`.
- **Blogs, authors, categories, emails builder:** `limit` + `offset` query params.
- **Blog sites:** `limit` + `skip`.
- **Payments:** `limit` + `offset`, response has `totalCount`.
- Insert a short pause (~100–150 ms) between pages on bulk reads: the API enforces burst rate limits.

## Credential and account diagnostics

1. Run the protected setup script with `-Status` on Windows or `status` on macOS. It reports only presence or absence.
2. Confirm that the account id is separate from the PIT and is passed where the endpoint family requires it.
3. Probe one low-risk read (`GET /locations/{location}`, else `POST /contacts/search` with `pageLimit` 1) through the helper and classify the result before changing credentials or code.
4. Do not retrieve the PIT for visual inspection, even in masked form.

## Error matrix

### 401 Unauthorized
- Token invalid, expired, revoked, or wrong scope.
- Confirm the helper is using the expected protected credential source.
- Do not assume the requested object is missing until the token is verified.
- User-facing: "errore di autorizzazione sul tuo account Futuria CRM" — never name the host.

### 403 Forbidden
- Token is valid but lacks access to the requested resource: the integration token may not include that area's permissions.
- User-facing: suggest asking il referente Futuria to extend the token's permissions for that area.

### 404 Not Found
- Object id wrong or already deleted — but also returned for a **wrong path** (e.g. `/emails/templates`). Re-check the endpoint against the area reference before concluding the object is gone.

### 422 Unprocessable Entity
- Request shape incomplete or invalid. Read the `message` array — it names the offending fields.
- First suspects: account id passed in the wrong form for that family (see the conventions table) or a family-specific quirk (epoch ms, string skip/limit).
- Some list endpoints enforce small `limit` values — reduce the limit before changing auth assumptions.

### 429 Too Many Requests
- Burst rate limit hit. Wait a couple of seconds and retry with backoff; slow the loop (pause between pages).

### 200 OK but no visible change
- Treat as partial/no-op until independently verified.
- Re-read through the canonical surface: API detail/list for metadata, the public page for published content, the web interface for builder-only internals.

## Custom field folders (contacts)

- Create a folder: `POST /locations/{locationId}/customFields` with `{ "name": "<folder>", "model": "contact", "documentType": "folder", "position": <n> }`. Success key is `customFieldFolder`.
- Link a field to a folder: `PUT /locations/{locationId}/customFields/{id}` including the field details plus `"parentId": "<folder id>"`.
- The list endpoint exposes `parentId`, not `folderId`. If create returns `400 Folder already exists`, reuse `meta.existingId` from the body.

## Reporting

After any API work, report in Italian what you did and which area it touched — described as Futuria CRM — without exposing the host or any vendor name.
