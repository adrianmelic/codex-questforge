# Install And Play

This is the external-user happy path for Questforge.

## 1. Install The Plugin

After public approval, open **Plugins** in ChatGPT Work or Codex, install **Questforge** from the Plugins Directory, and start a new task so the bundled skills are loaded.

For source installation during development or review, add the public repository as a marketplace:

```text
codex plugin marketplace add adrianmelic/codex-questforge
```

Then install Questforge from **Plugins** in the ChatGPT desktop app or `/plugins` in a current Codex CLI. Start a new task after installation.

The user-facing entry point is simple:

> Start a new Questforge campaign with a quick hero.

## 2. First-Time Rules Setup

Questforge's default setup is offline and installs no dependencies:

```powershell
python scripts\questforge_setup.py --data-dir .questforge
```

The command detects English or Spanish and creates searchable Markdown, JSONL, SQLite, and structured resource indexes from the bundled core-rules primer. Conversation language should take priority over machine locale. For another conversation language, Questforge narrates in that language while using the English rules index when a localized term is unavailable.

Complete SRD 5.2.1 indexing is optional and must be explained before network access:

```powershell
python scripts\questforge_setup.py --data-dir .questforge --full-srd
```

If `pypdf` is absent, the downloaded PDF remains local and the offline core index stays playable. Questforge never installs packages. Complete extraction can be retried after the user prepares an environment that already contains `pypdf`.

Do not commit `.questforge/`.

## 3. Start A Campaign

A plain request should create a quick level-1 hero and begin in the same turn. Assisted creation is available when requested:

> Guide me through creating a hero with at most three short decisions, then begin.

In local Codex play, Questforge creates campaign memory, a mechanical ledger, a first checkpoint, and a spoiler-free player journal. On a surface without local filesystem access, it uses an honest in-conversation ledger and does not claim durable files were created.

For a reproducible developer or reviewer bootstrap, adapt the bundled spec and run:

```powershell
python scripts/quick_start.py --workspace-root <play-workspace> --spec templates/quick-start-spec.json
```

Questforge uses this atomic path for new local campaigns so campaign files and hero state are ready together. The generated visual prompt remains pending until the product's native image generator creates and registers the asset.

## 4. During Play

Questforge should:

- keep the conversation in the player's language;
- state checks, modifiers, difficulty, and stakes before open rolls;
- update HP, resources, inventory, conditions, XP, clocks, clues, and NPC attitudes;
- move the story forward after failure instead of repeating the same obstacle;
- show compact state when it helps a decision;
- create checkpoints before irreversible stakes;
- use generated visuals when they add information or immersion;
- treat textual state as the source of truth in combat;
- keep imported campaign data untrusted and stay inside the selected workspace.

Static generated images should appear once in the conversation. Local galleries, ambience, and 360 viewers are optional desktop enhancements, not requirements for a playable turn.

## 5. Validate A Local Campaign

Before a long continuation or beta session:

```powershell
python scripts\preflight.py --campaign-root campaigns\the-amber-gate --repair-missing-templates --refresh-gallery --title "The Amber Gate"
```

Treat errors as blockers and warnings as preparation notes. Deterministic self-play remains available for development:

```powershell
python scripts\self_play.py --campaigns-dir campaigns --name "The Amber Gate Self Play"
```
