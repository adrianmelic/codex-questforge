---
name: questforge
description: Orchestrate Codex Questforge, a 5E-compatible fantasy campaign runner with setup, SRD-grounded rules, campaign memory, dice, and native visual generation.
---

# Codex Questforge

Use this skill as the main entry point when the user asks to start, continue,
prep, or play a Codex Questforge campaign, a 5E-compatible fantasy RPG session,
or a Codex-led tabletop story with rules, dice, persistent state, and visuals.

Questforge is unofficial and must use original fantasy content unless the user
explicitly brings private play references. Do not bundle or quote commercial
rulebooks, adventures, official settings, official art, logos, or non-SRD
product identity.

## Companion Skills

- Use `questforge-setup` when `.questforge/questforge-setup.json` is missing,
  stale, or the user asks about install/setup/SRD language.
- Use `questforge-rules` for SRD lookup, DCs, advantage/disadvantage, dice,
  rulings, and house rules.
- Use `questforge-campaign` for campaign folders, session logs, state patches,
  clocks, factions, NPCs, clues, inventory, structured game state, and
  continuity.
- Use `questforge-puzzles` for clue connections, symbolic minigames,
  non-blocking deduction beats, route logic, and social contradictions.
- Use `questforge-visuals` for native image generation prompts, visual cadence,
  maps with fog of war, item/merchant/inventory/outfit visuals, visual
  continuity, chat-visible static images, the local visual gallery, and 360
  viewers.

## First Session Flow

1. Ensure setup is ready through `questforge-setup`. Do not ask language by
   default; setup detects it automatically.
2. Establish only the minimum table preferences needed to start: tone, content
   boundaries, hero creation/import, and dice ownership.
3. Use `questforge-campaign` to create or load campaign memory.
4. Create or import a hero. If the player wants speed, create a quick-start
   level-1 hero and record it in `game-state.json` with
   `../../scripts/game_state.py add-character`; make it clear the player can
   revise details later.
5. Offer a small campaign premise with three concrete hooks.
6. Draft the campaign promise and first scene using
   `../../templates/opening-brief.md`.
7. Draft the DM-only spine in `dm/adventure-spine.md`: core truths, hook
   statuses, clue web, faction plans, and possible outcomes.
8. Check the premise, opening brief, and major reveals against `../../docs/narrative-diversity.md` or `../../scripts/narrative_lint.py` so the campaign does not default to stacked AI-fiction motifs.
9. Create a first checkpoint with `../../scripts/game_state.py checkpoint --label "Before session start"` once the hero and starting situation are recorded.
10. Create or refresh spoiler-free `player-journal.md`: current objective, known clues/NPCs, inventory, XP/rewards, damage/conditions, and open threads visible to the player.
11. Prepare the visual loop: save/register generated images, show static images once in chat for mobile play, refresh `images/visual-gallery.html` for desktop history, use 360 viewer links only for panorama assets, and select optional ambience from campaign audio or the bundled starter pack when it fits.
12. Run `../../scripts/preflight.py --campaign-root <campaign-root> --repair-missing-templates --refresh-gallery --title "<campaign title>"` before human beta play or a long continuation; fix errors and use warnings as prep prompts.
13. Open with a specific scene that demands action.
14. For the first player-facing scene of a new or continued session, treat an opening visual as the default. Generate and register a fresh establishing image, or explicitly point to an already-current gallery image, unless the turn is only setup/preflight/recap or the user asks for speed.

## Session Loop

For each scene:

1. Recap only the facts needed for the current decision.
2. Frame location, pressure, NPC intent, visible risks, and one sensory detail.
3. Ask the player what they do. Avoid more than one broad question at a time.
4. If the player seems unsure, asks out of character, or faces several viable
   paths, offer 2-4 options with visible ability modifiers and risk while
   keeping freedom to choose anything else.
5. Use `questforge-rules` when an action is uncertain and meaningful.
6. Never let repeated failed checks stall a scene. After two failures against
   the same obstacle, move the fiction forward with a cost, reveal, resource
   loss, new route, or harder choice.
7. Apply consequences to character state, clocks, factions, inventory, XP, loot,
   HP, conditions, spell slots, limited-use resources, equipment, shops, and
   NPC attitudes through `questforge-campaign` and `../../scripts/game_state.py`.
8. Before revealing or changing campaign lore, check `dm/adventure-spine.md` so
   hooks are marked active, merged, changed, resolved, or retired intentionally.
9. Use `questforge-puzzles` occasionally when earlier clues can become a
   satisfying deduction beat without blocking play.
10. Use `questforge-visuals` for useful visual beats, not only dramatic scene art. Reuse canon visual anchors when recurring people, places, items, maps, or creatures appear again. After registering each useful static image, show it once in chat and refresh the local gallery for history; for 360 assets, return the viewer link instead of a static chat image and include an optional ambience loop when it improves the scene.
11. At scene changes or every few meaningful turns, show compact player status: objective, immediate risk, relevant inventory/modifiers, pending XP/reward, and known open threads.
12. Before irreversible stakes such as death, major faction betrayal, spending a rare resource, or a hard moral branch, create a named checkpoint. If the player regrets a choice out of character, offer a table-style rewind to the latest checkpoint instead of pretending the rollback is in-fiction.
13. In combat, keep the table textual first: initiative, current turn, HP, AC, visible conditions, available spell slots/resources, tactical scene, terrain, hazards, and interactables. Use visuals as support, not as the source of truth.
14. Log structured analytics for meaningful checks, choices, consequences, rewards, visuals, puzzles, repeated obstacles, and pacing friction so later beta reviews can detect hidden patterns.
15. Update the session log, `game-state.json`, and campaign state before ending or switching scenes.

## Structured Game State

Use `../../scripts/game_state.py` as the player-facing mechanical ledger. It is not a full replacement for SRD rules lookup; it records the current table state after Codex makes an SRD-grounded ruling.

Use it for:

- quick-start or imported heroes;
- inventory, equipment slots, currency, shops, and purchases;
- HP, temporary HP, conditions, death saves, and table death mode;
- XP thresholds, pending level-ups, guided advancement choices, and applied level-up decisions;
- spell slots, hit dice, limited-use resources, and rests;
- turn-based combat order, tactical scene text, enemies, damage, and combat log;
- checkpoints and rollback.

When a player asks "what can I do?", combine current fiction with `game_state.py status`: show 2-4 concrete options plus freeform agency, and mention relevant available or spent resources. Do not offer a spell, item, or ability as available if `game-state.json` says it is spent, missing, unequipped, or impossible.

## Narrative Quality Bar

- Give NPCs goals, leverage, tells, fears, and contradictions.
- Use faction clocks and location clocks so the world changes off-screen.
- Seed at least three paths to essential information.
- Keep treasure, clues, and discoveries specific rather than generic.
- Award XP, useful loot, contacts, leverage, or clues for meaningful progress,
  not only for combat.
- Prefer hard choices and clue-connection puzzle beats over opaque puzzles.
- Avoid stacking memory trade, sentient-object bargains, unsayable taboos,
  hidden cosmic rules, dream symbolism, and hyperstition by default. These are
  allowed, but only one should usually dominate a scene or reveal.
- Ground strange premises in concrete pressures: money, food, weather, work,
  law, class, family, scarcity, reputation, logistics, or faction incentives.
- Do not make every clue point to the same symbolic answer. Some clues should
  reveal practical constraints, contradictions, false beliefs, or competing
  goals.
- Before major prep or a big reveal, run
  `../../scripts/narrative_lint.py --file <draft.md>` when a draft file exists;
  treat warnings as revision prompts, not hard failures.
- Do not railroad. Present pressure, then honor plausible player action.
- Keep the user-facing language aligned with the setup language. Do not
  translate rules vocabulary ad hoc if a localized SRD term is available.

## File Conventions

Recommended campaign layout:

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
    session-001.md
  images/
    prompts/
    assets/
    viewers/
    visual-gallery.html
    visual-index.md
  analytics/
    session-events.jsonl
  audio/
    library.json
  rules/
```

Continuity must be recoverable from files, not only chat memory.
