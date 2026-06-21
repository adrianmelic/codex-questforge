---
name: questforge-campaign
description: Manage Codex Questforge campaign memory, sessions, clocks, NPCs, factions, inventory, clues, state patches, and continuity between sessions.
---

# Questforge Campaign

Use this skill when starting, continuing, closing, or auditing a campaign.

## Campaign Workspace

Create campaign memory with:

```powershell
python ../../scripts/campaign_memory.py new --campaigns-dir campaigns --name "<name>"
```

Recommended layout:

```text
campaigns/<campaign-slug>/
  campaign-state.md
  game-state.json
  checkpoints/
  player-journal.md
  dm/
    adventure-spine.md
    puzzle-ledger.md
  visual-bible.md
  opening-brief.md
  questforge.json
  characters/
  sessions/
  images/
    prompts/
    assets/
    viewers/
    visual-gallery.html
    visual-index.md
  rules/
```

## Session Loop

For each scene:

1. Recap only what the current decision needs.
2. Frame location, pressure, NPC intent, visible risks, and one sensory detail.
3. Ask one clear action question.
4. Use `questforge-rules` for uncertain meaningful actions.
5. Apply consequences to character state, clocks, factions, inventory, clues,
   NPC attitudes, and the structured mechanical ledger in `game-state.json`.
6. Award XP, useful loot, leverage, or contacts when the player solves a
   meaningful problem. Avoid filling play with trivial junk loot.
7. Update `dm/adventure-spine.md` when a hook is merged, changed, resolved, or
   retired. Never let opening hooks silently drift.
8. Use `questforge-puzzles` when a clue web can become a non-blocking deduction
   beat or symbolic minigame.
9. Use `questforge-visuals` for useful visual beats and refresh the local
   gallery when a generated image is registered.
10. Update `player-journal.md` with spoiler-free current objective, known clues/NPCs, inventory, XP/rewards, damage/conditions, and open threads.
11. Append a compact analytics event for meaningful checks, choices, consequences, rewards, visuals, puzzles, repeated obstacles, and pacing notes with `../../scripts/session_analytics.py log-event`.
12. Update session log and campaign state.

## State Patch

After meaningful scenes, track:

- party location;
- immediate next choice;
- clocks advanced or reduced;
- NPC attitude changes;
- faction moves;
- clues discovered;
- hook status changes in the DM-only adventure spine;
- puzzle beats offered, solved, hinted, or bypassed;
- inventory and rewards in `campaign-state.md`, plus mechanical inventory,
  equipment, currency, and shops in `game-state.json`;
- XP and advancement notes;
- notable loot and currency changes;
- HP, temporary HP, death saves, damage, conditions, rests, spell slots, hit
  dice, limited-use resources, and level-up choices through
  `../../scripts/game_state.py`;
- persistent visible states, such as bandaged hands, disguises, carried clues,
  or damaged gear;
- visual gallery refreshes and 360 viewer paths shown to the player;
- analytics events for checks, choices, consequences, rewards, visuals,
  repeated obstacles, pacing friction, and player confusion;
- spoiler-free player journal changes;
- table rulings.

Use `../../scripts/campaign_memory.py add-inventory-item`, `award-loot`,
`award-xp`, `record-hook-status`, `record-puzzle-beat`, and `list-inventory`
for campaign-facing summaries.

Use `../../scripts/game_state.py` for the player-facing mechanical source of truth:

```powershell
python ../../scripts/game_state.py status --campaign-root <campaign-root>
python ../../scripts/game_state.py add-character --campaign-root <campaign-root> --name "<hero>" --class-name "<class>" --ancestry "<ancestry>" --max-hp 10 --armor-class 13
python ../../scripts/game_state.py add-item --campaign-root <campaign-root> --character "<hero>" --name "Stormproof cloak" --value 12gp
python ../../scripts/game_state.py equip --campaign-root <campaign-root> --character "<hero>" --item "Stormproof cloak" --slot cloak
python ../../scripts/game_state.py start-combat --campaign-root <campaign-root> --name "Warehouse ambush" --combatant "<hero>:14" --combatant "Cutthroat:11:6:13:enemy"
python ../../scripts/game_state.py set-tactical-scene --campaign-root <campaign-root> --summary "Crates, oil lamp, north door, rain-slick balcony." --terrain "crates grant half cover" --hazard "oil lamp can spread fire" --interactable "rope pulley can drop sacks"
python ../../scripts/game_state.py spend-spell-slot --campaign-root <campaign-root> --character "<hero>" --slot-level 1
python ../../scripts/game_state.py apply-damage --campaign-root <campaign-root> --character "<hero>" --amount 5
python ../../scripts/game_state.py rest --campaign-root <campaign-root> --character "<hero>" --kind long
python ../../scripts/game_state.py checkpoint --campaign-root <campaign-root> --label "Before opening the black door"
```

Before a choice that could kill the hero, permanently spend rare resources, or radically branch the campaign, create a checkpoint. If the player regrets a decision out of character, use `restore-checkpoint` and explain the rollback as table control, not as an in-world retcon unless the table wants that.

Use `../../scripts/session_analytics.py analyze --session-log <session.md> --visual-index <campaign-root>/images/visual-index.md --events <campaign-root>/analytics/session-events.jsonl` after beta play to detect hidden patterns such as narrow DC ranges, repeated modifiers, missing disadvantage, thin visual variety, repeated obstacle stalls, or pacing friction. If DCs cluster, use `../../scripts/dc_planner.py` during the next session to choose no-roll, DC 10, DC 15, DC 20, contests, or resource tradeoffs intentionally.

Before human beta play or a long continuation, run:

```powershell
python ../../scripts/preflight.py --campaign-root <campaign-root> --repair-missing-templates --refresh-gallery --title "<campaign title>"
```

Fix preflight errors before play. Treat warnings as prep notes, especially empty visual-ledger continuity and missing player-facing recovery notes. For a manual readiness pass, use `../../docs/beta-preflight-checklist.md`.

Create the next session log with:

```powershell
python ../../scripts/campaign_memory.py next-session --campaign-root <campaign-root>
```

## Player Journal

Keep `player-journal.md` spoiler-free and useful as the player's memory between sessions. Include only what the character or player already knows: current objective, immediate risk, known clues and NPCs, inventory, XP/rewards, damage or conditions, and open threads. Do not copy DM-only truths, hidden clocks, or unrevealed faction plans from `dm/adventure-spine.md`.

Continuity must be recoverable from files, not only chat memory.
