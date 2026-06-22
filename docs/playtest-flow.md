# Questforge Playtest Flow

Use this flow to test whether Codex Questforge can run a rich session instead
of only storing notes.

## 1. Create The Campaign Workspace

First, prepare local rules data:

```powershell
python plugins\questforge\scripts\questforge_setup.py `
  --data-dir .questforge `
  --install-pdf-extractor
```

If testing the no-install path, omit `--install-pdf-extractor`. Setup should
then either reuse an existing extractor or report `pdf_downloaded_index_pending`
with a clear instruction to rerun with `--install-pdf-extractor` or provide a
converted SRD Markdown file with `--rules-text`.

Setup auto-detects language from `QUESTFORGE_LANGUAGE`, the system locale, then
English. Use `--language es` or `--language en` only to override detection.
Setup should create structured Markdown resources in
`.questforge/resources/srd/<language>/` when extraction succeeds or `--rules-text`
is provided.

```powershell
python plugins\questforge\scripts\campaign_memory.py new `
  --campaigns-dir campaigns `
  --name "The Amber Gate" `
  --tone "heroic mystery with eerie ruins" `
  --boundaries "no graphic gore"
```

Expected result:

```text
campaigns/the-amber-gate/
  campaign-state.md
  game-state.json
  checkpoints/
  player-journal.md
  dm/adventure-spine.md
  dm/puzzle-ledger.md
  visual-bible.md
  opening-brief.md
  questforge.json
  characters/
  sessions/session-001.md
  images/prompts/
  images/assets/
  images/viewers/
  images/visual-index.md
  rules/
```

Before handing the campaign to a human beta tester or resuming a long run, audit the workspace:

```powershell
python plugins\questforge\scripts\preflight.py `
  --campaign-root campaigns\the-amber-gate `
  --repair-missing-templates `
  --refresh-gallery `
  --title "The Amber Gate"
```

The preflight should have zero errors. Warnings are not automatic blockers, but they should shape the next prep pass; an empty visual ledger means recurring visible states are likely to drift. The repair flag only backfills safe empty notebooks for older campaigns and does not overwrite existing files.

## 2. Establish The Table

Codex should ask for only the minimum needed to begin:

- desired tone;
- content boundaries;
- whether the user wants to create a hero or use a quick-start hero;
- whether Codex or the user rolls dice.

Then Codex should offer three hooks and ask the user to choose one.

## 3. Open In Scene

The first scene should contain:

- a specific place;
- a visible pressure;
- an NPC or force with intent;
- one sensory detail;
- a decision that can change the state of the world.

Avoid lore dumps. Put the player under interesting pressure within the first
message.

## 4. Resolve A Meaningful Roll

When the user attempts something uncertain:

```powershell
python plugins\questforge\scripts\roll_dice.py d20+4 --mode normal
```

Codex should state the ability, DC band, stakes, roll, result, and consequence.
Before important checks, use DC anchors or the planner instead of defaulting to
13/14:

```powershell
python plugins\questforge\scripts\dc_planner.py `
  --difficulty medium `
  --position normal `
  --approach ordinary
```

Use no roll for obvious progress, DC 10 for easy uncertainty, DC 15 for medium,
DC 20 for hard, or an opposed roll when an active NPC resists.
When the player seems unsure, show 2-4 options with modifiers and risk:

```powershell
python plugins\questforge\scripts\action_options.py `
  --option "Force the hatch|Dexterity (Thieves' Tools)|+5|DC 14|noise from below|the hatch opens|the patrol hears you, but a new route opens"
```

On failure, the scene must still move forward. After two failed checks against
the same obstacle, use `check_resolution.py` or make the ruling directly: add a
cost, reveal, resource loss, or new route, then stop rolling against that same
blocker.
For rules lookup, prefer:

```powershell
python plugins\questforge\scripts\rules_index.py query-setup `
  --manifest .questforge\questforge-setup.json `
  --query "ability checks"
```

## 4.5. Keep The Mechanical Ledger Current

Use `game-state.json` for the pencil-and-paper side of play. The transcript can be rich and freeform, but inventory, equipment, money, HP, conditions, spell slots, rests, level-ups, combat turn order, tactical scene notes, and rollback checkpoints should survive in files.

Create or import the hero before the first real scene:

```powershell
python plugins\questforge\scripts\game_state.py add-character `
  --campaign-root campaigns\the-amber-gate `
  --name "Mara Vey" `
  --class-name "Wizard" `
  --ancestry "Human" `
  --max-hp 8 `
  --armor-class 12
```

Show compact state when choices depend on resources:

```powershell
python plugins\questforge\scripts\game_state.py status `
  --campaign-root campaigns\the-amber-gate
```

For shops and equipment, record the transaction and the equipped state rather than only narrating it:

```powershell
python plugins\questforge\scripts\game_state.py add-shop-item `
  --campaign-root campaigns\the-amber-gate `
  --shop-id low-door `
  --shop-name "Low Door Outfitters" `
  --merchant "Sella" `
  --item-name "Stormproof cloak" `
  --price 12gp `
  --stock 1

python plugins\questforge\scripts\game_state.py buy-item `
  --campaign-root campaigns\the-amber-gate `
  --character "Mara Vey" `
  --shop-id low-door `
  --item "Stormproof cloak"

python plugins\questforge\scripts\game_state.py equip `
  --campaign-root campaigns\the-amber-gate `
  --character "Mara Vey" `
  --item "Stormproof cloak" `
  --slot cloak
```

For combat, start turn order and keep a textual tactical scene:

```powershell
python plugins\questforge\scripts\game_state.py start-combat `
  --campaign-root campaigns\the-amber-gate `
  --name "Warehouse ambush" `
  --combatant "Mara Vey:14" `
  --combatant "Dock Cutthroat:11:6:13:enemy"

python plugins\questforge\scripts\game_state.py set-tactical-scene `
  --campaign-root campaigns\the-amber-gate `
  --summary "Crates form half cover around a lantern spill." `
  --terrain "stacked crates" `
  --hazard "oil lamp can spread fire" `
  --interactable "rope pulley can drop sacks"
```

Before irreversible or high-regret decisions, create a checkpoint:

```powershell
python plugins\questforge\scripts\game_state.py checkpoint `
  --campaign-root campaigns\the-amber-gate `
  --label "Before opening the black door"
```

## 5. Offer A Puzzle Beat

When earlier clues can pay off, draft a small non-blocking deduction beat:

```powershell
python plugins\questforge\scripts\puzzle_beats.py draft `
  --title "Three Bell Marks" `
  --kind symbolic_order `
  --summary "choose the ritual bell mark from prior bell clues" `
  --clue "The innkeeper said one bell means sleep." `
  --clue "The baker said the dawn bell did not finish." `
  --ask "Which bell mark do you touch first?" `
  --solution "touch the unfinished dawn mark" `
  --fallback "a clerk wakes, but the side archive opens" `
  --reward "archive access without spending the white key" `
  --symbolic-weight "unfinished promises can still point the way"
```

Then record the beat:

```powershell
python plugins\questforge\scripts\campaign_memory.py record-puzzle-beat `
  --campaign-root campaigns\the-amber-gate `
  --title "Three Bell Marks" `
  --kind symbolic_order `
  --required-clue "The innkeeper said one bell means sleep." `
  --required-clue "The baker said the dawn bell did not finish." `
  --ask-at-table "Which bell mark do you touch first?" `
  --solution "touch the unfinished dawn mark" `
  --fallback "a clerk wakes, but the side archive opens" `
  --reward "archive access without spending the white key" `
  --symbolic-weight "unfinished promises can still point the way"
```

The puzzle passes only if a wrong answer still changes the situation and keeps
play moving.

## 6. Save Native Visual Prompts

When a useful visual beat occurs, build the prompt from
`templates/scene-image-prompt.md`. First plan the format and continuity work:

```powershell
python plugins\questforge\scripts\visual_planner.py `
  --beat "Iria pays the innkeeper, then goes downstairs for breakfast."
```

If `should_generate` is true, satisfy the returned continuity requirements and
save the prompt with the planned visual kind:

```powershell
python plugins\questforge\scripts\campaign_memory.py save-visual-prompt `
  --campaign-root campaigns\the-amber-gate `
  --session 1 `
  --scene 1 `
  --kind location `
  --label "Gorge Bridge" `
  --prompt "<final native image generation prompt>"
```

Then Codex should use the integrated native image generation capability when it
is available in the current product surface. The plugin must not call image API
scripts or use `OPENAI_API_KEY` for this.

Over a normal mini-session, save at least four useful visual prompts across at
least three kinds, such as `location`, `item`, `map`, and `recap`. In an
image-rich test, generate the next frame whenever the fiction materially
changes. Static images should appear once in the Codex conversation so mobile
players can see them, and the gallery should keep the desktop/history view.

After the native image is saved locally and registered in `images/visual-index.md`, refresh the campaign gallery:

```powershell
python plugins\questforge\scripts\visual_gallery.py `
  --campaign-root campaigns\the-amber-gate `
  --title "The Amber Gate"
```

Open the printed `file:///` URL in the Codex in-app Browser when available. The
printed URL ends in `#latest` for live play, while the page itself is ordered
chronologically so scrolling down moves from earlier images to newer images.
For each selected static image, also embed the saved asset once in chat with an
absolute-path Markdown image. Do not duplicate it with extra prompt links or
debug path captions unless the tester asks for those details.

## 6.5. Record Analytics Events

For every meaningful check, hard choice, consequence, reward, visual beat,
puzzle beat, repeated obstacle, or moment where the player asks how to proceed,
append a structured event:

```powershell
python plugins\questforge\scripts\session_analytics.py log-event `
  --campaign-root campaigns\the-amber-gate `
  --event-type check `
  --session 1 `
  --scene 4 `
  --challenge-type stealth `
  --ability Dexterity `
  --skill Stealth `
  --dc 16 `
  --modifier +5 `
  --roll-total 12 `
  --outcome failure `
  --failure-forward "patrol hears noise but a new route opens" `
  --tag repeated-obstacle
```

The goal is not bureaucracy during play. Keep the event short and useful, then analyze it after the session:

```powershell
python plugins\questforge\scripts\session_analytics.py analyze `
  --session-log campaigns\the-amber-gate\sessions\session-001.md `
  --visual-index campaigns\the-amber-gate\images\visual-index.md `
  --events campaigns\the-amber-gate\analytics\session-events.jsonl
```

When a later visual includes a recurring element, list canon anchors:

```powershell
python plugins\questforge\scripts\campaign_memory.py list-visual-assets `
  --campaign-root campaigns\the-amber-gate `
  --status canon `
  --format markdown
```

Then create a live scene-frame prompt from those anchors:

```powershell
python plugins\questforge\scripts\visual_reuse.py `
  --campaign-root campaigns\the-amber-gate `
  --session 1 `
  --scene 4 `
  --label "Lantern Chase At The Gorge" `
  --action "Mara runs across the bridge while the amber lantern flares behind her." `
  --roll "Dexterity check DC 15: 11" `
  --outcome "failure that wakes the lantern without blocking movement" `
  --anchor-label "Mara Vey Reference Sheet" `
  --require-asset
```

When a location deserves first-person inspection, generate or select a 360
panorama and build a local viewer:

```powershell
python plugins\questforge\scripts\panorama_viewer.py `
  --image <generated-360.png> `
  --output campaigns\the-amber-gate\images\viewers\gorge-bridge-360.html `
  --title "Gorge Bridge POV" `
  --narration "Rain hits the rope bridge as the amber lantern turns toward you." `
  --initial-zoom-level 14 `
  --audio campaigns\the-amber-gate\audio\quiet-rain.mp3 `
  --audio-title "Quiet Rain" `
  --audio-volume 0.24
```

Audio is optional. If present, verify that it starts only after the player uses
the speaker control, and that later viewers remember the player's last audio
choice when the browser allows playback.

## 7. Close The Session

At the end:

- update the session log;
- update campaign clocks, factions, NPC attitudes, clues, and inventory;
- update hook statuses in `dm/adventure-spine.md` when a hook changes;
- record puzzle beats in `dm/puzzle-ledger.md` when they are prepared or used;
- record meaningful XP, loot, leverage, or contacts;
- record any table rulings;
- create the next session log when continuing:

```powershell
python plugins\questforge\scripts\campaign_memory.py next-session `
  --campaign-root campaigns\the-amber-gate
```

## Pass Criteria

The playtest passes when the user can:

- start from an empty campaign folder;
- prepare or detect local SRD rules data;
- make at least one consequential choice;
- resolve at least one transparent roll;
- resolve or bypass at least one non-blocking deduction beat;
- see campaign state change in the files;
- save several typed visual prompts in `images/visual-index.md`;
- write structured analytics events for meaningful checks and pacing notes;
- refresh and open `images/visual-gallery.html` as the live image board;
- run `preflight.py` with zero errors before a human beta handoff;
- reuse at least one canon visual anchor in a later scene-frame prompt;
- create and open at least one local 360 viewer when testing `pov-360`;
- toggle an ambient loop in a 360 viewer without autoplaying for a new user;
- continue into the next session without losing continuity.
