---
name: pulisci-liste-crm
description: Use when cleaning up your Futuria CRM contact lists - detect spam, fake or junk contacts, review them in a local browser page with keep/delete toggles, then delete the marked ones. Trigger on pulisci liste, pulizia contatti, clean my CRM list, rimuovi spam dai contatti, igiene contatti, /futuria:pulisci-liste-crm. Always answer in Italian and always call the platform Futuria CRM.
---

# Pulisci liste — Futuria CRM

Comando per ripulire le liste contatti del **tuo account Futuria CRM** da spam, fake e profili-spazzatura, con **review nel browser** prima di cancellare. Rispondi sempre in italiano; chiama la piattaforma sempre **Futuria CRM**, mai con altri nomi.

## Quando usarla
- "pulisci le liste", "pulizia contatti", "togli gli spam", "igiene contatti", `/futuria:pulisci-liste-crm`.

Per le euristiche di riconoscimento vedi `futuria-crm/references/contacts-pulizia-liste.md`.

## Prerequisiti
- Token e location del tuo account Futuria CRM disponibili allo script come `FUTURIA_CRM_TOKEN` e `FUTURIA_CRM_LOCATION` (lo stesso token del tuo account; deve poter eliminare contatti).
- Esporta `FUTURIA_ENV_LOCAL` col path del file `env.local` se non lanci dalla cartella che lo contiene.
- Python 3 (solo stdlib, nessuna dipendenza). `python3` su macOS, `python` su Windows.

## Le tre fasi (account singolo)
Script: `scripts/crm-list-cleanup.py`.

1. **detect** — trova i candidati sospetti:
   `python3 scripts/crm-list-cleanup.py detect`
   Stampa il path di `candidates.json`.
2. **review** — apri la pagina nel browser per decidere (Tieni/Elimina):
   `python3 scripts/crm-list-cleanup.py review --candidates <candidates.json>`
   Va lanciato in **background**: il server locale apre il browser e attende il tuo invio, poi scrive `decisions.json`.
3. **delete** — **dry-run di default**:
   `python3 scripts/crm-list-cleanup.py delete --decisions <decisions.json>`
   mostra cosa cancellerebbe. Solo dopo conferma esplicita, rilancia con `--execute`.

## Cancellazione
- Se il tuo account Futuria CRM espone un tool di eliminazione contatti via MCP, **preferiscilo**.
- Altrimenti la fase `delete` usa l'API diretta del tuo account.

## Sicurezza
- **Dry-run di default**; cancelli solo ciò che marchi `elimina` nella pagina.
- **Protect-list** attiva (clienti, ricorrenti, partner, contatti con ordini/trattative).
- **Snapshot** completo prima di ogni operazione; eliminazioni tolleranti se un contatto è già sparito.
- v1 propone solo **fake strutturali**: i contatti veri che non aprono mai le email non vengono toccati.
