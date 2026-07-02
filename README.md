# Futuria CRM — assistente per agenti AI

Skill ufficiale **Futuria Marketing** che permette al tuo agente AI di operare direttamente sul tuo account **Futuria CRM**: contatti, conversazioni e messaggi, opportunità e pipeline, appuntamenti, task, tag, email, social, blog, pagamenti e pulizia delle liste contatti.

Funziona con Claude Code e con agenti compatibili (Codex). L'agente si collega al tuo account con le tue credenziali, lavora direttamente sulle API di Futuria CRM e risponde sempre in italiano.

## Cosa fa

- **Contatti & tag** — crea, aggiorna, cerca contatti; gestisce i tag; evita i duplicati.
- **Conversazioni** — legge la cronologia e prepara/invia messaggi (con la tua conferma).
- **Opportunità & pipeline** — sposta gli affari tra gli stage, aggiorna valore e stato.
- **Appuntamenti** — consulta calendari, appuntamenti e note.
- **Contenuti** — template email, post social programmati, articoli del blog.
- **Pagamenti** — consulta ordini e transazioni (sola lettura).
- **Pulizia liste** — trova contatti spam/fake, te li fa rivedere in una pagina nel browser, elimina solo quelli che confermi (prima fa sempre una prova a vuoto).

## Installazione

### 1. Aggiungi il marketplace e installa il plugin

In Claude Code:

```
/plugin marketplace add FuturiaMarketing/futuria-crm-client
/plugin install futuria-crm@futuria-crm
```

> Se hai ricevuto il plugin come cartella locale, usa il percorso della cartella al posto del repository.

### 2. Imposta le credenziali del tuo account

Il plugin si collega al tuo account Futuria CRM con **due** variabili d'ambiente:

| Variabile | Cos'è |
| --- | --- |
| `FUTURIA_CRM_TOKEN` | Il token di accesso del tuo account (inizia con `pit-`) |
| `FUTURIA_CRM_LOCATION` | L'ID del tuo account |

Entrambi i valori te li fornisce **il tuo referente Futuria Marketing** all'attivazione. Se non li hai, scrivici: te li configuriamo noi.

Impostale così, poi **riavvia l'agente**:

```powershell
# Windows (PowerShell)
setx FUTURIA_CRM_TOKEN "pit-il-tuo-token"
setx FUTURIA_CRM_LOCATION "id-del-tuo-account"
```

```bash
# macOS / Linux (aggiungi al tuo ~/.zshrc o ~/.bashrc)
export FUTURIA_CRM_TOKEN="pit-il-tuo-token"
export FUTURIA_CRM_LOCATION="id-del-tuo-account"
```

> Non sai farlo? Chiedi direttamente all'agente: «aiutami a configurare Futuria CRM» — ti guida passo passo.

### 3. Usa l'assistente

Chiedi in linguaggio naturale, ad esempio:

- «Crea un contatto per Maria Bianchi, mail maria@example.com, e mettile il tag cliente-2026.»
- «Com'è messa la pipeline Vendite questo mese?»
- «Prepara una risposta WhatsApp a Luca Verdi per confermare l'appuntamento di giovedì.»
- «Pulisci le liste contatti dallo spam.»
- «Spiegami come funzionano i crediti del mio account.»

Oppure invoca i comandi dedicati:

```
/futuria-crm  <la tua richiesta>
/pulisci-liste-crm
```

## Pulizia liste: come funziona

1. L'agente analizza i tuoi contatti e individua solo i profili **chiaramente** fasulli (domini email usa-e-getta, testi scam, profili senza alcuna identità). Clienti, partner e contatti con ordini o trattative sono sempre protetti.
2. Si apre una pagina nel tuo browser dove decidi tu, contatto per contatto: **tieni** o **elimina**.
3. L'agente fa prima una **prova a vuoto** e ti mostra l'elenco; elimina solo dopo la tua conferma, tenendo una copia di sicurezza di ogni contatto rimosso.

## Privacy & sicurezza

- Le tue credenziali restano **solo** sulla tua macchina, nelle variabili d'ambiente: non sono incluse nel plugin e non vengono condivise.
- L'assistente non stampa mai il token in chiaro.
- I dati del tuo account viaggiano solo tra la tua macchina e Futuria CRM.
- Le azioni verso l'esterno (invio messaggi, pubblicazione contenuti) vengono confermate con te prima dell'esecuzione.
- L'assistente non muove denaro: sui pagamenti lavora in sola lettura.
- Le eliminazioni di contatti passano sempre da: tua revisione nel browser → prova a vuoto → tua conferma esplicita.

## Aggiornamenti

Quando pubblichiamo una nuova versione, aggiorna il plugin dal marketplace (`/plugin` → aggiorna `futuria-crm`).

## Supporto

Per attivazione, credenziali o domande sull'account: **il tuo referente Futuria Marketing** — https://futuriamarketing.com

---

© Futuria Marketing. Futuria CRM è la piattaforma CRM, marketing e commerce di Futuria Marketing.
