# Pulizia liste e contatti sospetti

Come riconoscere e rimuovere contatti spam, fake o spazzatura dal tuo account Futuria CRM. Automatizzato dalla skill `pulisci-liste-crm` (trova → rivedi nel browser → elimina, con prova a vuoto prima delle eliminazioni). Rispondi sempre in italiano e chiama la piattaforma sempre **Futuria CRM**.

## Principio

Mai cancellare in base a un solo dettaglio del nome o dell'email: chi usa nomi stilizzati o email con tanti punti è spesso un contatto vero. Si elimina solo su **segnali combinati e strutturali**, e ogni eliminazione passa comunque dalla revisione umana.

## Cosa è spam (eliminabile, v1 ad alta precisione)

- Email con dominio "usa e getta" o temporaneo.
- Testi scam/crypto o link nei campi del contatto.
- **Nessuna identità**: niente nome, email e telefono.
- Nessuna identità (no nome, no telefono) + email che sembra generata (locale casuale, cifre in serie, TLD esotico).

## Segnali di contesto (mai sufficienti da soli)

- Molti contatti creati nello **stesso minuto**: può essere un'iniezione spam, ma anche una **normale lista importata dal titolare** — da solo non autorizza nulla.
- Contatto arrivato da **social/WhatsApp senza nome**: quasi sempre una persona reale che ha scritto senza lasciare i dati — non è spam.
- Nome con caratteri Unicode stilizzati, email molto puntata: spesso creator o contatti legittimi.

## Cosa NON è spam (non cancellare)

- Contatti veri che però **non aprono mai** le email: non sono fake. Vanno semmai esclusi dagli invii, non eliminati.
- **Clienti, clienti ricorrenti, partner**, contatti con ordini o trattative: si proteggono sempre (protect-list attiva nello strumento).

## Perché conta (recapito email)

Liste piene di contatti morti o falsi peggiorano la consegna delle tue email: più finiscono nello spam, peggiora la reputazione del tuo dominio. Tenere le liste pulite migliora il recapito in posta in arrivo.
