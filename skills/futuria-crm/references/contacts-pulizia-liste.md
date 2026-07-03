# List cleanup & suspicious contacts

How to recognise and remove spam, fake or junk contacts from the user's Futuria CRM account. Automated by the `pulisci-liste-crm` skill (detect → review with the client in chat, or via an Excel checklist when candidates are many → delete, with a dry-run before any real deletion). Always reply in Italian and always call the platform **Futuria CRM**.

## Principle

Never delete based on a single detail of the name or email: people with stylised names or heavily dotted emails are often real contacts. Deletion is justified only by **combined, structural signals**, and every deletion still goes through human review.

## What is spam (delete-grade, v1 high precision)

- Email on a disposable or temporary domain.
- Scam/crypto text or links inside the contact fields.
- **No identity at all**: no name, no email, no phone.
- No identity (no name, no phone) + an email that looks generated (random local part, digit runs, exotic TLD).

## Context signals (never sufficient on their own)

- Many contacts created in the **same minute**: could be a spam injection, but also a **normal list imported by the owner** — on its own it authorises nothing.
- Contact arriving from **social/WhatsApp without a name**: almost always a real person who wrote without leaving their data — not spam.
- Name with stylised Unicode characters, heavily dotted email: often creators or legitimate contacts.

## What is NOT spam (do not delete)

- Real contacts that simply **never open** emails: they are not fake. If anything, exclude them from sends — do not delete them.
- **Clients, recurring customers, partners**, contacts with orders or open deals: always protected (protect-list active in the tool).

## Why it matters (email deliverability)

Lists full of dead or fake contacts hurt email delivery: the more messages land in spam, the worse the sender domain's reputation gets. Clean lists improve inbox placement.
