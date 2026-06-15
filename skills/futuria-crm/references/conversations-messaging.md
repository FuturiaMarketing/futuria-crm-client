# Conversations & messaging

Read and send messages in the user's Futuria CRM account (the unified conversations inbox).

## Primary MCP tools

- `conversations_search-conversation` — find a conversation by contact, channel, or query.
- `conversations_get-messages` — read the message history of a conversation.
- `conversations_send-a-new-message` — send an outbound message in a conversation.

## Working rules

- **Sending is an outbound action to a real person.** Treat every `send-a-new-message` as user-facing: confirm the recipient, the channel, and the exact text with the user before sending, unless they have clearly authorised this specific send.
- **Channel matters.** A conversation can span SMS, WhatsApp, email, and more. Confirm which channel you are sending on — usage cost and tone differ (see the wallet model in `references/terminology-and-voice.md`).
- **Read before reply.** Pull recent messages so your reply has context; don't answer blind.
- **No bulk blasts here.** This tool is for individual conversation messages, not newsletters. Mass email is a marketing feature with its own usage cost.

## Drafting replies

- Match the language and tone of the incoming message.
- Keep the platform name as **Futuria CRM** if it ever comes up; never expose a vendor name to the end recipient either.

## Output example (Italian)

> Ho trovato la conversazione con **Luca Verdi** (canale WhatsApp) nel tuo account Futuria CRM. Ho preparato questa risposta — confermi l'invio?
> «Buongiorno Luca, confermo l'appuntamento di giovedì alle 15. A presto!»
