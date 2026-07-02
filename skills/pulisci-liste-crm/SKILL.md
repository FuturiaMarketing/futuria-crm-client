---
name: pulisci-liste-crm
description: Use when cleaning up your Futuria CRM contact lists - detect spam, fake or junk contacts, review them in a local browser page with keep/delete toggles, then delete the marked ones after a dry-run. Trigger on pulisci liste, pulizia contatti, clean my CRM list, rimuovi spam dai contatti, igiene contatti, /pulisci-liste-crm. Always answer in Italian and always call the platform Futuria CRM.
---

# Pulisci liste — Futuria CRM

Comando per ripulire le liste contatti del **tuo account Futuria CRM** da spam, fake e profili-spazzatura, con **review nel browser** prima di cancellare. Rispondi sempre in italiano; chiama la piattaforma sempre **Futuria CRM**, mai con altri nomi.

L'utente tipico **non è tecnico**: esegui tu ogni comando; a lui restano solo due gesti — decidere nella pagina del browser e confermare in chat.

## Quando usarla
- "pulisci le liste", "pulizia contatti", "togli gli spam", "igiene contatti", `/pulisci-liste-crm`.

Per le euristiche di riconoscimento vedi `../futuria-crm/references/contacts-pulizia-liste.md` (dalla radice del plugin: `skills/futuria-crm/references/contacts-pulizia-liste.md`).

## Prerequisiti
- Variabili d'ambiente del tuo account Futuria CRM: **`FUTURIA_CRM_TOKEN`** e **`FUTURIA_CRM_LOCATION`** (il token deve poter leggere ed eliminare contatti). Se mancano, guida l'utente col setup in `../futuria-crm/references/getting-started.md` — non fermarti.
- Python 3 (solo stdlib, nessuna dipendenza). `python3` su macOS, `python` su Windows.

## Le tre fasi
Script: `scripts/crm-list-cleanup.py`.

1. **detect** — trova i candidati sospetti:
   `python scripts/crm-list-cleanup.py detect`
   Stampa il path di `candidates.json` (lavora in `~/.futuria/crm-cleanup/`). Con **0 candidati**: riferisci che le liste risultano pulite e fermati qui.
2. **review** — apri la pagina nel browser per decidere (Tieni/Elimina):
   `python scripts/crm-list-cleanup.py review --candidates <candidates.json>`
   Va lanciato in **background**: il server locale apre il browser e attende l'invio dell'utente, poi scrive `decisions.json` e stampa il path. Spiega all'utente cosa deve fare nella pagina.
3. **delete** — **dry-run di default**:
   `python scripts/crm-list-cleanup.py delete --decisions <decisions.json>`
   Mostra all'utente l'elenco `WOULD_DELETE`. **Solo dopo conferma esplicita in chat**, rilancia con `--execute`.

Al termine riferisci in italiano: eliminati / già assenti / protetti-saltati / falliti, e dove si trova lo snapshot di sicurezza.

## Sicurezza (già nello script, non aggirarla)
- **Dry-run di default**; si cancella solo ciò che l'utente ha marcato `elimina` nella pagina e riconfermato in chat.
- **Protect-list** attiva (clienti, ricorrenti, partner, fornitori); tag extra con `--protect-tags`.
- **Snapshot** completo dei contatti in detect; in `--execute` ogni contatto viene **riletto** prima dell'eliminazione (snapshot pre-delete + skip se nel frattempo è diventato protetto).
- Eliminazioni tolleranti se un contatto è già sparito; ritmo rispettoso dei limiti API.
- v1 propone solo **fake strutturali**: i contatti veri che non aprono mai le email non vengono toccati, e un contatto WhatsApp/social senza nome non è mai un candidato.
