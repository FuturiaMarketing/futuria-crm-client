# Contacts, tags & tasks

Operate on people in the user's Futuria CRM account: contacts, their tags, tasks and notes. Base URL, headers and pagination in `references/api-and-troubleshooting.md`.

## Endpoints (validated)

| Action | Request |
| --- | --- |
| Search/list contacts | `POST /contacts/search` — body `{"locationId": "...", "pageLimit": 100, "filters": [], "query": "<testo>"}`; paginate with each contact's `searchAfter` cursor |
| Read one contact | `GET /contacts/{contactId}` → `{contact}` |
| Create | `POST /contacts/` — body includes `locationId` plus the fields |
| Update | `PUT /contacts/{contactId}` — send only the fields to change |
| Create-or-update | `POST /contacts/upsert` — body with `locationId` + unique key (email/phone). Prefer over blind create |
| Delete | `DELETE /contacts/{contactId}` — destructive: confirm first, snapshot before |
| Add / remove tags | `POST /contacts/{contactId}/tags` / `DELETE /contacts/{contactId}/tags` — body `{"tags": ["..."]}` |
| Tags existing in the account | `GET /locations/{locationId}/tags` |
| Contact tasks | `GET /contacts/{contactId}/tasks`; create with `POST /contacts/{contactId}/tasks` (`title`, `dueDate` ISO, `completed`) |
| Contact notes | `GET /contacts/{contactId}/notes`; create with `POST /contacts/{contactId}/notes` (`body`) |
| Custom fields of the account | `GET /locations/{locationId}/customFields` |

Write bodies not listed field-by-field here can vary: on a `422`, read the `message` array — it names the fields — and adjust.

## Working rules

- **Avoid duplicates.** Before creating, search by email or phone; if a match exists, use upsert or update instead of create.
- **Custom fields:** never assume a field exists because you saw it in an old export or template. Read the account's custom fields first and use the real field id.
- **Tags:** adding a tag creates it implicitly — read `GET /locations/{locationId}/tags` first and reuse the existing spelling instead of inventing near-duplicates.
- **Write safety:** read the contact → apply the smallest change → re-read to confirm → report the changed fields and the contact id, in Italian.
- **Bulk deletions / list cleanup:** never improvise — use the `pulisci-liste-crm` flow (`references/contacts-pulizia-liste.md`).

## Imports, segmentation and protection

Isolate an import using created-date/time windows plus stable source/tag criteria, then validate sample contacts and record filters, counts and exact IDs before a bulk action. A cluster created in the same minute is a batch clue, not proof of spam: legitimate imports have the same pattern.

Styled/Unicode names, dotted emails, missing email or social/WhatsApp-only identity are not deletion criteria. Genuine contacts with no engagement are candidates for suppression or re-engagement, not fake contacts; engagement must come from actual email-event data rather than the contact object. Read orders, opportunities and relationship evidence before deciding a contact is disposable; tags alone do not establish the absence of a valid relationship. Keep the existing `pulisci-liste-crm` detection, chat review and dry-run flow: these audit criteria do not silently expand its automated deletion rules.

Retain review decisions, before/after evidence and the minimum exports needed to reproduce the approved operation in the user's protected workspace. Remove only temporary files created by the current task once the retained report can be reproduced; do not delete unrelated files or store contact exports in the skill package.

## Output example (Italian)

> Ho aggiornato il contatto **Maria Bianchi** nel tuo account Futuria CRM: aggiunto il tag `cliente-2026` e impostato il campo `Città = Padova`. Ho riletto la scheda per conferma.
