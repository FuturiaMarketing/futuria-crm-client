# Futuria CRM — skill per agenti AI

Plugin ufficiale **Futuria Marketing** per collegare Codex o Claude Code al proprio account **Futuria CRM** tramite PIT e API diretta.

La prima versione è volutamente locale e semplice:

- funziona con **Codex** e **Claude Code**;
- usa un solo account Futuria CRM;
- non installa e non richiede alcun connettore MCP;
- conserva il PIT nel portachiavi del sistema operativo, non nella chat;
- risponde sempre in italiano e chiama la piattaforma sempre **Futuria CRM**.

## Il testo da incollare al proprio agente

Copia questo testo in una chat nuova di Codex o Claude Code:

```text
Installa la release stabile della skill Futuria CRM dal repository pubblico
https://github.com/FuturiaMarketing/futuria-crm-client seguendo INSTALL.md.
Rileva autonomamente se sei Codex o Claude Code e usa il percorso previsto per
quel runtime. Non chiedermi mai di incollare il PIT in chat o in un comando:
dopo l'installazione apri una finestra Terminale separata e visibile, avvia la
configurazione protetta inclusa nella skill e lascia che inserisca lì PIT e ID
account. Poi verifica la connessione in sola lettura e comunicami soltanto il
nome dell'account collegato e l'esito.
```

L’agente seguirà la procedura dettagliata in [INSTALL.md](INSTALL.md). Non serve usare `winget` o Homebrew per installare la skill. Python è necessario soltanto per la funzione opzionale **Pulisci liste**; se manca, l’agente deve chiedere conferma prima di installarlo.

## Cosa può fare

- **Contatti, note, task e tag** — cerca, crea e aggiorna, evitando i duplicati.
- **Conversazioni** — legge la cronologia e prepara o invia messaggi dopo conferma.
- **Opportunità e pipeline** — consulta e aggiorna trattative, valore, stato e fase.
- **Appuntamenti** — consulta calendari, eventi e note.
- **Contenuti** — lavora su template email, post social e articoli del blog.
- **Pagamenti** — consulta ordini e transazioni in sola lettura.
- **Pulizia liste** — individua profili chiaramente fasulli, li sottopone alla revisione dell’utente e procede solo dopo dry-run e conferma esplicita.

## Come protegge il PIT

- **Windows:** inserimento nascosto in una finestra PowerShell; il PIT viene cifrato con la protezione dati dell’utente Windows.
- **macOS:** inserimento nascosto in Terminale; il PIT viene salvato nel Portachiavi di macOS.
- Le variabili d’ambiente restano disponibili come fallback per utenti tecnici e ambienti automatizzati, ma non sono il percorso consigliato.
- Il PIT non deve mai essere incollato nella chat, inserito in un prompt o passato come argomento di un comando.

Gli script API inclusi recuperano il PIT internamente e non lo stampano. Dettagli e limiti sono descritti in [PRIVACY.md](PRIVACY.md) e [SECURITY.md](SECURITY.md).

## Uso

Dopo l’installazione e la configurazione basta chiedere, per esempio:

- «Crea un contatto per Maria Bianchi e aggiungi il tag cliente-2026.»
- «Com’è messa la pipeline Vendite questo mese?»
- «Prepara una risposta WhatsApp a Luca per confermare l’appuntamento.»
- «Pulisci le liste contatti dallo spam.»

Codex può richiamare esplicitamente `$futuria-crm` o `$pulisci-liste-crm`. In Claude Code le skill del plugin sono disponibili anche tramite i comandi con namespace del plugin; normalmente non serve invocarli, perché l’agente riconosce le richieste dal linguaggio naturale.

## Privacy essenziale

I dati letti dal CRM vengono elaborati dall’agente AI scelto dall’utente. Possono quindi essere trattati anche dal relativo fornitore AI, secondo piano, impostazioni e contratto dell’utente. La skill non invia telemetria propria a Futuria Marketing e nella v1 non usa un server MCP Futuria.

Per attivazione, PIT, revoca o supporto: il proprio referente Futuria Marketing — <https://futuriamarketing.com>.

---

© Futuria Marketing. Tutti i diritti riservati.
