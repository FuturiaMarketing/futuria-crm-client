---
name: pulisci-liste-crm
description: Use when cleaning up your Futuria CRM contact lists - detect spam, fake or junk contacts, review them with the client directly in chat (or via an Excel checklist when there are many), then delete only the confirmed ones after a dry-run. Trigger on pulisci liste, pulizia contatti, clean my CRM list, rimuovi spam dai contatti, igiene contatti, /pulisci-liste-crm. Always answer in Italian and always call the platform Futuria CRM.
---

# Pulisci liste — Futuria CRM

Clean the contact lists of the client's **Futuria CRM** account from spam, fake and junk profiles. The review happens **directly in chat**: no local server, no browser page, no background process. Always reply in Italian; always call the platform **Futuria CRM**, never any other name.

The typical client is **non-technical**: you run every command; the client only decides and confirms in chat (or fills in one Excel file when candidates are many).

## When to use
- "pulisci le liste", "pulizia contatti", "togli gli spam", "igiene contatti", `/pulisci-liste-crm`.

Detection heuristics: `../futuria-crm/references/contacts-pulizia-liste.md` (from the plugin root: `skills/futuria-crm/references/contacts-pulizia-liste.md`).

## Prerequisites
- Protected credentials configured by the main Futuria CRM skill on Windows or macOS; environment variables remain a technical fallback. The PIT must be able to read and delete contacts. If missing, guide the client through `../futuria-crm/references/getting-started.md` — never ask for the PIT in chat.
- Python 3 (stdlib only, no dependencies — the Excel checklist included). `python3` on macOS, `python` on Windows.

## The flow
Script: `scripts/crm-list-cleanup.py`. Every phase prints the path of the file it produced — pass it to the next phase.

1. **detect** — find delete-grade candidates:
   `python scripts/crm-list-cleanup.py detect`
   Prints the path of `candidates.json` (works in `~/.futuria/crm-cleanup/`). With **0 candidates**: report in Italian that the lists look clean and stop here.
2. **review in chat** (default, up to ~50 candidates) — show the client EVERY candidate, numbered, in Italian: name, email, phone, source, creation date and the detection signals. Never hide or summarize away a candidate. Let the client answer in their own words ("elimina 1 e 3, tieni il resto"); silence or ambiguity is never consent — ask again. Then map the client's choices to contact IDs from `candidates.json` and record them deterministically:
   `python scripts/crm-list-cleanup.py decide --candidates <candidates.json> --delete <id1,id2,...>`
   (or `--keep-all` / `--delete-all`). The script accepts only IDs present among the candidates and writes `decisions.json`.
3. **review via Excel checklist** (fallback: more than ~50 candidates, or the client prefers a file):
   `python scripts/crm-list-cleanup.py checklist --candidates <candidates.json>`
   generates `pulizia-liste-checklist.xlsx`: one row per candidate with the signals, a dropdown **Elimina/Tieni** per row pre-set to Elimina. Tell the client to open it, set **Tieni** on the contacts to keep, save the file and come back to chat. Then:
   `python scripts/crm-list-cleanup.py decide --candidates <candidates.json> --from-checklist <path.xlsx>`
   Rows left blank, removed, or with anything other than Elimina count as **Tieni**.
4. **delete** — **dry-run by default**:
   `python scripts/crm-list-cleanup.py delete --decisions <decisions.json>`
   Show the client the `WOULD_DELETE` list. **Only after an explicit confirmation in chat**, rerun with `--execute`.

At the end report in Italian: deleted / already gone / protected-skipped / failed, and where the safety snapshot lives.

## Safety (built into the script — do not bypass it)
- **Dry-run by default**; a contact is deleted only if the client marked it Elimina AND re-confirmed in chat on the dry-run list.
- `decide` is the only writer of `decisions.json` and validates every ID against the detected candidates — never hand-craft or edit that file.
- **Protect-list** always on (clients, recurring customers, partners, suppliers); extra tags with `--protect-tags`.
- Full contact **snapshot** at detect; with `--execute` every contact is **re-read** first (pre-delete snapshot + skip if it became protected in the meantime).
- Deletions tolerate contacts already gone; API rate limits respected.
- v1 flags only **structural fakes**: real contacts that never open emails are untouched, and a WhatsApp/social contact without a name is never a candidate.
