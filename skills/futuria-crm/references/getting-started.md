# Getting started — connect and verify

How to get the agent operating on the user's Futuria CRM account. Read this once per environment, then move to the area reference for the actual task.

## 1. The Futuria CRM MCP (primary channel)

- The plugin ships an MCP server named **`futuria-crm`** (see the plugin's `.mcp.json`). Its tools are named `…futuria-crm_<area>_<action>`, e.g.:
  - `contacts_create-contact`, `contacts_get-contacts`, `contacts_add-tags`
  - `conversations_search-conversation`, `conversations_send-a-new-message`
  - `opportunities_search-opportunity`, `opportunities_get-pipelines`
  - `calendars_get-calendar-events`
  - `emails_fetch-template`, `social-media-posting_create-post`, `blogs_create-blog-post`
  - `payments_list-transactions`, `locations_get-custom-fields`
- The tool names already say `futuria-crm` — safe to reason about out loud. They never expose a vendor brand.

## 2. Authentication

- The MCP server authenticates with the user's account token, supplied via the environment variable **`FUTURIA_CRM_TOKEN`**.
- That token is a **Private Integration Token** (it looks like `pit-...`). It is **not** an account id.
- **`locationId`** is a separate identifier that some direct-API endpoints require. Keep the two distinct — confusing them is the most common cause of errors.
- Never print the token in clear text. When diagnosing, show only a masked prefix (first few characters).
- The user provides their own token; there are no shared or agency credentials in this skill.

## 3. Capability-first order

For any task, pick the most specific working capability:

1. **Futuria CRM MCP** — use it when a tool covers the exact resource and returns relevant data.
2. **Direct API** — when MCP lacks the resource, is ambiguous, or you need exact control / deterministic verification. See `references/api-and-troubleshooting.md`.
3. **Web interface** — only as a last fallback, or to visually confirm something the API can't show.

State, briefly and in Italian, which path you used when it isn't obvious.

## 4. First sanity check

Before a session's first write, confirm the account is reachable:

1. Run one low-risk **read** — e.g. `contacts_get-contacts` with a small limit, or `opportunities_get-pipelines`.
2. If it returns data, the token and account are working; proceed.
3. If it fails, classify the failure before changing anything — see the error matrix in `references/api-and-troubleshooting.md`. Do not assume an object is missing until you have confirmed the token is valid.

## 5. Reporting

- Always reply in **Italian**, calling the platform **Futuria CRM**.
- After a write, report the exact fields changed and the object's identifier, and confirm you re-read the result.
- If wording about the platform, the account, or costs comes up, follow `references/terminology-and-voice.md`.
