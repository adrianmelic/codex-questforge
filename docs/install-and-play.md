# Install And Play

This is the external-user happy path for Codex Questforge.

## 1. Install Or Enable The Plugin

Enable `codex-questforge` from the plugin marketplace entry or place the plugin
folder under the expected Codex plugin directory.

The user-facing entry point is:

> Use Codex Questforge to start a campaign.

## 2. Run First-Time Setup

From the repo or project where the user wants campaign files, use the full
playable setup:

```powershell
python plugins\codex-questforge\scripts\questforge_setup.py --data-dir .questforge --install-pdf-extractor
```

The command detects language automatically. To force English or Spanish:

```powershell
python plugins\codex-questforge\scripts\questforge_setup.py --data-dir .questforge --install-pdf-extractor --language en
python plugins\codex-questforge\scripts\questforge_setup.py --data-dir .questforge --install-pdf-extractor --language es
```

If the user does not want setup to install `pypdf`, omit
`--install-pdf-extractor`. Setup can then return
`pdf_downloaded_index_pending`, which means the PDF cache exists but rules
search is not ready. To finish indexing later:

```powershell
python plugins\codex-questforge\scripts\questforge_setup.py --data-dir .questforge --install-pdf-extractor
```

Setup creates local, non-committed data under `.questforge/`:

```text
.questforge/
  downloads/
  rules/
    <srd>.md
    <srd>.jsonl
    <srd>.sqlite
  resources/
    srd/
      manifest.json
      <language>/
        00-index.md
        sections/
  questforge-setup.json
```

## 3. Start A Campaign

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py new `
  --campaigns-dir campaigns `
  --name "The Amber Gate" `
  --tone "heroic mystery" `
  --boundaries "no graphic gore"
```

Then say:

> Use Codex Questforge with `.questforge` rules. Start `The Amber Gate`.

Before a human beta session or a long continuation, Codex can run:

```powershell
python plugins\codex-questforge\scripts\preflight.py `
  --campaign-root campaigns\the-amber-gate `
  --repair-missing-templates `
  --refresh-gallery `
  --title "The Amber Gate"
```

Treat errors as blockers. Treat warnings as prep notes, especially a missing or empty player-facing continuity surface such as `player-journal.md` or an empty visual ledger.

Campaign creation also creates `game-state.json` and `checkpoints/`. This is the mechanical source of truth for the player-facing side of play: inventory, equipment, money, shops, HP, death saves, spell slots, rests, level-up choices, turn order, tactical scene notes, and rollback checkpoints.

## 4. During Play

Codex should:

- use the configured language from `.questforge/questforge-setup.json`;
- query rules with:

```powershell
python plugins\codex-questforge\scripts\rules_index.py query-setup `
  --manifest .questforge\questforge-setup.json `
  --query "<topic>"
```

- roll dice openly with `roll_dice.py`;
- keep mechanical state current with `game_state.py`;
- update campaign state and session logs;
- keep `player-journal.md` spoiler-free and current for the player;
- save typed visual prompts with `save-visual-prompt`;
- register generated images with `register-visual-asset`; prefer
  `--asset-source` when the native image was generated outside the campaign
  folder;
- show each selected static generated image once in the Codex conversation
  with absolute-path Markdown so mobile play can see it;
- refresh `images/visual-gallery.html` with `visual_gallery.py` after useful
  images are registered, then open the stable `file:///` gallery URL in
  `@Browser` when available for desktop history and 360 viewers;
- select optional ambience with `audio_library.py` from a campaign-local `audio/library.json` when present, otherwise from `plugins/codex-questforge/assets/audio/library.json`;
- reuse canon visual anchors with `list-visual-assets` and `visual_reuse.py`
  when recurring characters, creatures, items, maps, or locations appear again;
- create local `pov-360` viewers with `panorama_viewer.py` when native image
  generation produces an equirectangular 360 panorama;
- request native Codex/ChatGPT image generation when visuals help play.

Useful mechanical commands during play:

```powershell
python plugins\codex-questforge\scripts\game_state.py status --campaign-root campaigns\the-amber-gate
python plugins\codex-questforge\scripts\game_state.py add-character --campaign-root campaigns\the-amber-gate --name "Mara Vey" --class-name "Wizard" --ancestry "Human" --max-hp 8 --armor-class 12
python plugins\codex-questforge\scripts\game_state.py equip --campaign-root campaigns\the-amber-gate --character "Mara Vey" --item "Stormproof cloak" --slot cloak
python plugins\codex-questforge\scripts\game_state.py spend-spell-slot --campaign-root campaigns\the-amber-gate --character "Mara Vey" --slot-level 1
python plugins\codex-questforge\scripts\game_state.py rest --campaign-root campaigns\the-amber-gate --character "Mara Vey" --kind long
python plugins\codex-questforge\scripts\game_state.py checkpoint --campaign-root campaigns\the-amber-gate --label "Before the dangerous bargain"
```

## 5. Test The Plugin

Run deterministic self-play:

```powershell
python plugins\codex-questforge\scripts\self_play.py `
  --campaigns-dir campaigns `
  --name "The Amber Gate Self Play"
```

The self-play should create:

- `self-play-report.md`;
- `self-play-transcript.md`;
- `sessions/session-001.md`;
- `sessions/session-002.md`;
- four typed visual prompts;
- `images/visual-index.md`;
- `images/visual-gallery.html` after at least one generated image is
  registered;
- state changes recoverable from campaign files.

For broader alpha testing across play styles:

```powershell
python plugins\codex-questforge\scripts\alpha_playtest.py `
  --output-dir playtests\alpha-001
```

For human beta sessions, copy `templates/beta-feedback.md` into the campaign
folder after play and score the session with `docs/beta-fun-rubric.md`.
