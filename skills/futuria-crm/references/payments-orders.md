# Payments & orders

Read payment activity from the user's Futuria CRM account. This area is **read-mostly** — you inspect and report, you do not move money.

## Primary MCP tools

- `payments_list-transactions` — list transactions (filter by date range / status).
- `payments_get-order-by-id` — read a specific order.

## Working rules

- **Never initiate, refund, or alter a payment.** If the user wants to take a financial action, point them to the billing/payments section of their account and let them perform it. Report and summarise only.
- **Money is sensitive:** always state the currency, and don't round in a way that hides detail when reporting amounts.
- **Wallet vs orders:** account *usage credits* (wallet) are different from customer *orders/transactions*. If the user is asking about their own running costs, that is the wallet model in `references/terminology-and-voice.md`, not this area.
- For totals across periods or filters the MCP tools don't expose, use the direct API (`references/api-and-troubleshooting.md`).

## Output example (Italian)

> Nel tuo account Futuria CRM, nel periodo 1–31 maggio 2026 risultano **14 transazioni** per un totale di € 3.880 (12 riuscite, 2 fallite). Vuoi il dettaglio di una in particolare?
