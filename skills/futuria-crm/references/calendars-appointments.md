# Calendars & appointments

Read calendar activity and appointment notes from the user's Futuria CRM account.

## Primary MCP tools

- `calendars_get-calendar-events` — list events/appointments in a date range.
- `calendars_get-appointment-notes` — read the notes attached to a specific appointment.

## Working rules

- **Read-oriented surface.** These tools read calendar state. Creating, rescheduling, or cancelling an appointment may not be exposed via MCP — fall back to the direct API or the web interface, and confirm the change with the user first (it affects a real person's booking).
- **Date ranges:** always pass an explicit range; default windows can be misleading. Use the account's timezone.
- **Cross-reference contacts:** an appointment usually links to a contact — use the contact reference if the user wants the full picture.

## When to use direct API or interface

- To book, move, or cancel an appointment when no MCP tool covers it.
- To inspect calendar configuration (availability, team members) not returned by the event read.

## Output example (Italian)

> Nel tuo account Futuria CRM, questa settimana risultano **3 appuntamenti**: lun 10:00 con M. Bianchi, mer 15:00 con L. Verdi, ven 09:30 (slot libero). Vuoi che apra le note di uno di questi?
