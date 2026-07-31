# Installazione — istruzioni per l’agente

Questa procedura è destinata all’agente AI che riceve il link del repository. L’utente non deve scegliere manualmente il runtime né incollare credenziali nella chat.

## Obiettivo

1. Identificare se il runtime corrente è **Codex** o **Claude Code**.
2. Installare la release stabile del plugin/skill Futuria CRM.
3. Aprire un terminale separato e visibile per l’inserimento protetto di PIT e ID account.
4. Eseguire una verifica in sola lettura senza mostrare il PIT.

La v1 usa **PIT + API diretta**. Non installare né configurare MCP.

## Regole di sicurezza

- Non chiedere mai all’utente di scrivere il PIT nella chat.
- Non inserire mai il PIT in un comando, un argomento CLI, un file del progetto o un log.
- Non eseguire una configurazione credenziali in un terminale catturato nella conversazione: aprire una finestra interattiva separata.
- Non stampare il PIT, neppure parzialmente.
- Prima della prima scrittura, verificare il nome dell’account con una lettura.

## Release stabile

Release stabile: `v1.1.0`.

Repository: `https://github.com/FuturiaMarketing/futuria-crm-client`.

## Claude Code

Per l’installazione eseguita direttamente dall’agente, usare il percorso personale ufficiale delle skill di Claude Code:

1. Destinazione: `~/.claude/skills/futuria-crm-client`.
2. Se la cartella non esiste, clonare `https://github.com/FuturiaMarketing/futuria-crm-client.git` alla release `v1.1.0` con cronologia ridotta.
3. Se esiste già, verificare prima che sia la copia di questo repository e che non contenga modifiche locali; solo in quel caso aggiornare al tag `v1.1.0`. Non cancellare o sovrascrivere una cartella ambigua.
4. Se Git non è disponibile, scaricare l’archivio GitHub del tag `v1.1.0` ed estrarlo atomicamente nella stessa destinazione.
5. Eseguire `claude plugin details futuria-crm@skills-dir` quando disponibile, quindi `/reload-plugins` oppure aprire una nuova sessione.

Claude Code riconosce come plugin personale ogni cartella sotto `~/.claude/skills/` che contiene `.claude-plugin/plugin.json`; non serve registrare un marketplace per questo percorso.

Il marketplace resta disponibile per l’installazione manuale da una sessione Claude Code:

```text
/plugin marketplace add https://github.com/FuturiaMarketing/futuria-crm-client.git#v1.1.0
/plugin install futuria-crm@futuria-crm
```

Non aggiornare Claude Code o installare software di sistema senza aver informato l’utente.

## Codex

Usare la skill di sistema `$skill-installer` per installare entrambe le cartelle dalla release congelata:

```text
Installa con $skill-installer dal repository FuturiaMarketing/futuria-crm-client,
ref v1.1.0, le cartelle skills/futuria-crm e skills/pulisci-liste-crm.
```

Se `$skill-installer` non è disponibile, scaricare la release `v1.1.0` e copiare le due cartelle sotto la directory personale delle skill di Codex, senza sovrascrivere directory ambigue. Aprire una nuova chat se le skill non vengono rilevate subito.

Il repository include anche il manifest `.codex-plugin/plugin.json` e il marketplace `.agents/plugins/marketplace.json`. `codex plugin marketplace add FuturiaMarketing/futuria-crm-client@v1.1.0` registra il catalogo nei client che lo supportano, ma non va confuso con l’installazione delle skill.

## Configurazione protetta delle credenziali

Individuare la cartella installata della skill `futuria-crm`, quindi eseguire il launcher adatto al sistema operativo. Il launcher apre una seconda finestra: il PIT viene inserito soltanto lì.

### Windows

Dal terminale dell’agente eseguire:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<skill-futuria-crm>\scripts\launch-credential-setup.ps1"
```

Si apre una nuova finestra PowerShell visibile. Lo script usa `Read-Host -AsSecureString` e salva il PIT cifrato per l’utente Windows corrente. L’ID account viene salvato nella configurazione locale e non è un segreto.

### macOS

Dal terminale dell’agente eseguire:

```bash
bash "<skill-futuria-crm>/scripts/launch-credential-setup.sh"
```

Si apre una nuova finestra Terminale visibile. Il comando nativo del Portachiavi legge il PIT con un prompt senza eco e lo salva nel Portachiavi di macOS, senza inserirlo negli argomenti di processo o nel profilo shell.

### Linux

Nella v1 il percorso protetto automatizzato è previsto per Windows e macOS. Su Linux usare variabili d’ambiente impostate personalmente dall’utente in un terminale separato; non far transitare i valori nella chat.

## Verifica finale in sola lettura

Windows:

```powershell
& "<skill-futuria-crm>\scripts\crm-api.ps1" -Method GET -Path "/locations/{location}"
```

macOS:

```bash
bash "<skill-futuria-crm>/scripts/crm-api.sh" GET "/locations/{location}"
```

Confermare all’utente soltanto:

- runtime installato;
- versione della skill;
- nome dell’account collegato;
- esito della verifica.

Se la lettura fallisce per permessi, usare la sanity read contatti documentata in `skills/futuria-crm/references/getting-started.md`. Non modificare il PIT senza aver classificato l’errore.

## Python e pulizia liste

La skill principale non richiede Python. `pulisci-liste-crm` lo richiede perché esegue uno script locale deterministico.

- Windows: se Python manca, proporre `winget install Python.Python.3.12` e attendere l’autorizzazione dell’utente.
- macOS: se Python 3 manca, proporre l’installazione tramite Homebrew e attendere l’autorizzazione dell’utente.

Non installare dipendenze di sistema senza consenso.
