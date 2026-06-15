# Contacts, tags & tasks

Operate on people in the user's Futuria CRM account: contacts, their tags, and contact tasks.

## Primary MCP tools

- `contacts_get-contacts` — list/search contacts (use a small `limit` first).
- `contacts_get-contact` — read one contact by id.
- `contacts_create-contact` — create a new contact.
- `contacts_update-contact` — update an existing contact by id.
- `contacts_upsert-contact` — create-or-update by a unique key (email/phone). Prefer this over blind create when a duplicate might exist.
- `contacts_add-tags` / `contacts_remove-tags` — manage tags on a contact.
- `contacts_get-all-tasks` — read tasks attached to contacts.
- `locations_get-custom-fields` — discover the account's custom fields before writing to them (field ids and types).

## Working rules

- **Avoid duplicates.** Before creating, search by email or phone; if a match exists, use `upsert-contact` or `update-contact` instead of `create-contact`.
- **Custom fields:** never assume a field exists because you saw it in an old export or template. Read `locations_get-custom-fields` and use the real field id.
- **Tags:** create the tag implicitly by adding it; keep tag names consistent with what already exists in the account (read current tags first if unsure).
- **Write safety:** read the contact → apply the smallest change → re-read to confirm → report the changed fields and the contact id, in Italian.

## When to use direct API

- Bulk reads with precise pagination, or custom-field folder management (see `references/api-and-troubleshooting.md`).
- When you need exact control of the request body that the MCP tool doesn't expose.

## Output example (Italian)

> Ho aggiornato il contatto **Maria Bianchi** (id `…`) nel tuo account Futuria CRM: aggiunto il tag `cliente-2026` e impostato il campo `Città = Padova`. Ho riletto la scheda per conferma.
