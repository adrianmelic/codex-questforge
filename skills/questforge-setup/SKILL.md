---
name: questforge-setup
description: Prepare Questforge for first play with an offline rules primer, optional full-SRD indexing, language selection, and licensing boundaries.
---

# Questforge Setup

Use this skill when the user installs Questforge, starts it in a new repo, asks
about SRD resources, or when `.questforge/questforge-setup.json` is missing.

## Default Offline Setup

Run setup without asking for language. The default builds searchable Markdown, JSONL, and SQLite indexes from the bundled core-rules primer. It does not use the network or install packages:

```powershell
python ../../scripts/questforge_setup.py --data-dir .questforge
```

Setup detects language in this order:

1. `QUESTFORGE_LANGUAGE`
2. `LANGUAGE`
3. `LC_ALL`
4. `LC_MESSAGES`
5. `LANG`
6. system locale
7. English fallback

Conversation language takes priority over machine locale. Pass `--language en` or `--language es` when the user's language is clear from the request. For other languages, use the English rules index and keep narration in the user's language.

## Optional Complete SRD

Only download the complete official SRD when the user asks for detailed rules coverage or accepts the optional setup. Explain that the command contacts `media.dndbeyond.com` and writes a local cache before running it:

```powershell
python ../../scripts/questforge_setup.py --data-dir .questforge --full-srd
```

When `pypdf` is already available, the full setup creates:

- Markdown rules text.
- JSONL rules chunks.
- SQLite rules index with FTS when available.
- Structured Markdown resources under `.questforge/resources/srd/<language>/`.
- `.questforge/questforge-setup.json` with resolved language and paths.

If full setup returns `pdf_downloaded_index_pending`, say exactly what happened and continue playing with the ready bundled core index. Questforge never installs packages. If the user wants complete indexing, explain that `pypdf` must already be installed in their active Python environment, then rerun:

```powershell
python ../../scripts/questforge_setup.py --data-dir .questforge --full-srd
```

or:

```powershell
python ../../scripts/questforge_setup.py --data-dir .questforge --rules-text <path-to-srd-markdown>
```

If shell or filesystem access is unavailable, use `../../resources/core-rules/<language>.md` directly and run a chat-only campaign. Do not claim that local indexes were created.

## Copyright Boundary

- Use SRD 5.2.1 sources only.
- Do not bundle commercial manuals, adventures, settings, official art, logos,
  or non-SRD product identity.
- Include CC-BY-4.0 attribution when storing or redistributing SRD-derived
  materials.
- Prefer local caches and generated indexes in `.questforge/`.
