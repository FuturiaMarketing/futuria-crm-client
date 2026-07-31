# Futuria CRM client plugin

Public dual-runtime plugin for Codex and Claude Code. The initial release uses a customer-owned PIT and direct Futuria CRM API calls; MCP is intentionally out of scope.

## Rules

- Keep shared skill instructions runtime-neutral. Codex-specific metadata belongs only in `agents/openai.yaml` and `.codex-plugin/`.
- Never add customer data, PIT values, local credential files or realistic secret examples.
- Customer-facing text always calls the platform `Futuria CRM`.
- Use the bundled secure API helpers; never teach an agent to print or pass the PIT in a command.
- Changes to distributed files require aligned Claude, Codex and marketplace versions.
- Run `python scripts/validate-plugin.py` and the tests before release.
