# Changelog

## 1.2.0 — 2026-08-03

- Added a guided local credential wizard for Windows and macOS, with a three-step visual accordion and real Futuria CRM screenshots.
- The wizard accepts the account URL, extracts the account ID, verifies the connection read-only and stores the credential with Windows DPAPI or macOS Keychain.
- Added loopback-only session isolation, CSRF protection, no-store headers, request limits and cross-platform tests; the private key never enters chat, process arguments or wizard logs.
- Isolated Windows PowerShell module discovery so DPAPI storage remains reliable when the agent starts from PowerShell 7.
- Kept the protected PowerShell and Terminal prompts as automatic fallback when Node.js is unavailable.

## 1.1.0 — 2026-07-31

- First formally tagged public release.
- Shared Futuria CRM and list-cleaning skills for Codex and Claude Code.
- Protected PIT setup through Windows DPAPI or macOS Keychain.
- Bundled API helpers that keep the PIT out of chat and agent command arguments.
- Public installation, privacy and security documentation.
- Native Codex marketplace metadata plus the Claude Code marketplace.

## 1.0.0 — 2026-07-07

- Initial API-first, single-account and white-label release on `main`.
- Human confirmation gates for messages, publications and destructive actions.
- Contact-list cleanup with chat review, Excel fallback, dry-run and local snapshots.
- Manifest version published without a formal Git tag or GitHub Release.
