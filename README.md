# Futuria CRM — assistente per agenti AI

Skill ufficiale **Futuria Marketing** che permette al tuo agente AI di operare direttamente sul tuo account **Futuria CRM**: contatti, conversazioni e messaggi, opportunità e pipeline, appuntamenti, task, tag, email, social, blog e pagamenti.

Funziona con Claude Code e con agenti compatibili (Codex). L'agente si collega al tuo account, lavora in modo capability-first (MCP → API → interfaccia) e risponde sempre in italiano.

## Cosa fa

- **Contatti & tag** — crea, aggiorna, cerca contatti; gestisci i tag; evita i duplicati.
- **Conversazioni** — leggi la cronologia e prepara/invia messaggi (con la tua conferma).
- **Opportunità & pipeline** — sposta gli affari tra gli stage, aggiorna valore e stato.
- **Appuntamenti** — consulta calendario e note degli appuntamenti.
- **Contenuti** — template email, post social programmati, articoli del blog.
- **Pagamenti** — consulta ordini e transazioni (sola lettura).

## Installazione

### 1. Aggiungi il marketplace e installa il plugin

In Claude Code:

```
/plugin marketplace add FuturiaMarketing/futuria-crm-client
/plugin install futuria-crm@futuria-crm
```

> Se hai ricevuto il plugin come cartella locale, usa il percorso della cartella al posto del repository.

### 2. Imposta il token del tuo account

Il plugin si collega al tuo account Futuria CRM tramite la variabile d'ambiente **`FUTURIA_CRM_TOKEN`**.

- Il valore è il **Private Integration Token** del tuo account (inizia con `pit-`).
- Lo trovi nelle impostazioni del tuo account Futuria CRM, nella sezione delle integrazioni private. Se non lo trovi o non sei sicuro dei permessi, **scrivi al tuo referente Futuria**: te lo configuriamo noi.

Imposta la variabile (esempio):

```powershell
# Windows (PowerShell)
setx FUTURIA_CRM_TOKEN "pit-il-tuo-token"
```

```bash
# macOS / Linux
export FUTURIA_CRM_TOKEN="pit-il-tuo-token"
```

Riavvia l'agente dopo averla impostata.

### 3. Usa l'assistente

Chiedi in linguaggio naturale, ad esempio:

- «Crea un contatto per Maria Bianchi, mail maria@example.com, e mettile il tag cliente-2026.»
- «Com'è messa la pipeline Vendite questo mese?»
- «Prepara una risposta WhatsApp a Luca Verdi per confermare l'appuntamento di giovedì.»
- «Spiegami come funzionano i crediti del mio account.»

Oppure invoca il comando dedicato:

```
/futuria-crm  <la tua richiesta>
```

## Privacy & sicurezza

- Il tuo token resta **solo** sulla tua macchina, nella variabile d'ambiente: non è incluso nel plugin e non viene condiviso.
- L'assistente non stampa mai il token in chiaro.
- Le azioni verso l'esterno (invio messaggi, pubblicazione contenuti) vengono confermate con te prima dell'esecuzione.
- L'assistente non muove denaro: sui pagamenti lavora in sola lettura.

## Supporto

Per attivazione, permessi del token o domande sull'account: **il tuo referente Futuria Marketing** — https://futuriamarketing.com

---

© Futuria Marketing. Futuria CRM è la piattaforma CRM, marketing e commerce di Futuria Marketing.
