---
name: questforge-setup
description: Prepare Codex Questforge for first play with auto-language SRD setup, local rules indexes, licensing boundaries, and troubleshooting.
---

# Questforge Setup

Use this skill when the user installs Questforge, starts it in a new repo, asks
about SRD resources, or when `.questforge/questforge-setup.json` is missing.

## Default Playable Setup

Run setup without asking for language. Use the extractor flag so a clean
machine gets searchable local rules, not only a downloaded PDF:

```powershell
python ../../scripts/questforge_setup.py --data-dir .questforge --install-pdf-extractor
```

Setup detects language in this order:

1. `QUESTFORGE_LANGUAGE`
2. `LANGUAGE`
3. `LC_ALL`
4. `LC_MESSAGES`
5. `LANG`
6. system locale
7. English fallback

Use `--language en` or `--language es` only when the user explicitly wants an
override.

## PDF And Indexes

The setup command downloads the matching official SRD 5.2.1 PDF into the local
`.questforge/downloads/` cache. Do not commit that cache.

When `pypdf` is available, setup creates:

- Markdown rules text.
- JSONL rules chunks.
- SQLite rules index with FTS when available.
- Structured Markdown resources under `.questforge/resources/srd/<language>/`.
- `.questforge/questforge-setup.json` with resolved language and paths.

If the user declines extractor installation, rerun setup without
`--install-pdf-extractor`. If setup returns `pdf_downloaded_index_pending`, say
exactly what happened and offer one of these:

```powershell
python ../../scripts/questforge_setup.py --data-dir .questforge --install-pdf-extractor
```

or:

```powershell
python ../../scripts/questforge_setup.py --data-dir .questforge --rules-text <path-to-srd-markdown>
```

## Copyright Boundary

- Use SRD 5.2.1 sources only.
- Do not bundle commercial manuals, adventures, settings, official art, logos,
  or non-SRD product identity.
- Include CC-BY-4.0 attribution when storing or redistributing SRD-derived
  materials.
- Prefer local caches and generated indexes in `.questforge/`.
