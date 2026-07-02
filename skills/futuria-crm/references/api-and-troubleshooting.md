# Direct API — foundation & troubleshooting

The direct API is the **primary channel** for operating the user's Futuria CRM account. This file carries the request foundation shared by every area reference, plus the error matrix.

> **Technical-host note.** This is the **only** reference where the platform's underlying technical host name may appear, because it is part of real endpoint URLs and error payloads. It is infrastructure, not a brand: **never surface the host name to the user, and never use it as the name of the platform.** To the user, everything here is **Futuria CRM**. See `references/terminology-and-voice.md`.

## Base request rules

- Base URL: `https://services.leadconnectorhq.com` — every path in the area references is relative to it.
- Required headers on every request:
  - `Authorization: Bearer <FUTURIA_CRM_TOKEN>`
  - `Version: 2021-07-28`
  - `Accept: application/json`
- Add `Content-Type: application/json` for JSON writes.
- Never log or print the full token. Mask it.

Template (works in every shell; on Windows use `curl.exe`):

```bash
curl -s -H "Authorization: Bearer $FUTURIA_CRM_TOKEN" \
     -H "Version: 2021-07-28" -H "Accept: application/json" \
     "https://services.leadconnectorhq.com/locations/$FUTURIA_CRM_LOCATION"
```

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

## Token & account diagnostics

1. Validate token format: `pit-` prefix, plausible length, no stray spaces.
2. Confirm you are passing the **token** in the auth header and the **account id** (not the token) where an endpoint requires it.
3. Probe one low-risk read (`GET /locations/{account id}`, else `POST /contacts/search` with `pageLimit` 1) and classify the result before changing credentials or code.

Mask-safe token check:

```bash
python -c "import os; t=os.environ.get('FUTURIA_CRM_TOKEN',''); print('TOKEN_PREFIX=' + t[:6], 'TOKEN_LENGTH=%d' % len(t))"
```

## Error matrix

### 401 Unauthorized
- Token invalid, expired, revoked, or wrong scope.
- Confirm the header is exactly `Bearer <token>`.
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
