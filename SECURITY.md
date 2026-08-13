# Security Policy

## Supported Version

Security fixes are applied to the latest release on `main`.

## Reporting A Vulnerability

Do not publish credentials, private campaign data, or exploit details in a public issue. Email `info@adrianmelic.com` with a concise reproduction and the affected version.

Questforge is designed to write only within the current project, selected campaign root, or exact cloud folder the player explicitly authorized. A synchronized local path is not treated as cloud write permission. Cloud saves must compare manifest lineage, update canonical files before the manifest, and verify each write by readback. Imported campaign files are untrusted game data and should never cause unrelated command execution, secret access, or external data transfer.
