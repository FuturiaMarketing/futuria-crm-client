# Opportunities & pipelines

Track deals through the sales pipelines of the user's Futuria CRM account.

## Primary MCP tools

- `opportunities_get-pipelines` — list pipelines and their stages (read this first to get stage ids and names).
- `opportunities_search-opportunity` — find opportunities by contact, pipeline, stage, status, or query.
- `opportunities_get-opportunity` — read one opportunity by id.
- `opportunities_update-opportunity` — update an opportunity (stage, status, monetary value, assigned owner, etc.).

## Working rules

- **Resolve the pipeline first.** Stage ids only make sense within a pipeline — always `get-pipelines` before moving an opportunity, so you use the correct stage id.
- **Status vs stage.** "Stage" is the position in the pipeline; "status" is open / won / lost / abandoned. Be explicit about which you are changing.
- **Money fields:** confirm the currency and amount with the user before changing a value.
- **Write safety:** read the opportunity → apply the smallest change → re-read → report the new stage/status and the opportunity id, in Italian.

## When to use direct API

- Reporting across many opportunities, or filters the MCP search doesn't expose.

## Output example (Italian)

> Nella pipeline **Vendite 2026** del tuo account Futuria CRM ho spostato l'opportunità **Preventivo Rossi** (id `…`) dallo stage *Contatto iniziale* a *Proposta inviata* e impostato il valore a € 2.400. Ho riletto l'opportunità per conferma.
