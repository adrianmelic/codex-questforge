# AGENTS.md

Purpose: public Questforge plugin source, tests, distributable assets, and publication documentation.

## Public Boundary

- Keep this repository limited to files intended for public distribution or public engineering evidence.
- Never commit real campaign state, private play logs, unpublished generated media, local workspace paths, Codex task identifiers, source-workspace URLs, credentials, environment files, or account exports.
- Synthetic examples and playtest reports must be sanitized before publication. Use professional public contact information only where attribution, support, licensing, or repository metadata requires it.
- Treat `campaigns/`, `playtests/`, `.questforge/`, generated images, local exports, and secret-scan reports as private or reproducible runtime material unless a specific sanitized artifact is intentionally approved for this repository.

## Release Synchronization

- The public Platform version, `.codex-plugin/plugin.json`, README release status, packaged archive, Git tag, and GitHub release should describe the same version.
- When a release is prepared in another workspace, port only the distributable source files required by the package. Compare the packaged archive with this repository instead of copying an entire workspace.
- Preserve repository-only development files such as tests, packaging scripts, contribution metadata, and public documentation when syncing a skills-only archive.
- Before publishing, run the tests, package validation, a full-history secret scan, and a focused search for private paths, task identifiers, workspace URLs, and credentials.
- Use `https://adrianmelic.com/questforge` as the canonical product page. Keep the GitHub Pages compatibility URLs working while any published Platform version still references them.

## Engineering

- Keep comments and technical documentation in English unless a document is intentionally localized.
- Do not add hardcoded personal machine paths.
- For Python changes, run `black -l 79` on the touched scope and `pytest -p no:cacheprovider`.
- Build distributable archives through `scripts/package_plugin.py`; do not commit `dist/` or generated ZIP files.
