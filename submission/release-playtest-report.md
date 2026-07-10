# Questforge Release Playtest Report

Date: 2026-07-10

## Method

Two independent conversational campaigns were run against the repository skills. The test driver acted only as the player, read every Game Master response, and chose the next message naturally. The Game Master agents were not given a scripted turn sequence and did not simulate player decisions.

The Spanish campaign used quick character creation. The English campaign used assisted creation for a spellcaster. A short Spanish regression followed after the first fixes.

## Session Metrics

| Language | Player Turns | Scenes | Checks | Success / Failure | Structured Events | Generated / Pending Visuals | Event Window |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Spanish | 19 | 4 | 13 | 10 / 3 | 30 | 0 / 0 | 61.5 min |
| English | 24 | 7 | 7 | 4 / 3 | 63 | 0 / 3 | 68.5 min |

The event windows exclude some work before the first event, so 3.24 and 2.85 minutes per player turn are lower bounds. Complex state-heavy turns sometimes exceeded six minutes.

## Coverage

- Quick and assisted character creation.
- English and Spanish conversation and campaign files.
- Open checks, contests, advantage, failure forward, initiative, damage, and an object-targeting combat action.
- Cantrips, spell slots, Innate Sorcery, Bardic Inspiration, illegal self-targeting, and exact SRD-backed level-up choices.
- Inventory review, equipment changes, currency, merchant stock, and purchases.
- Puzzles, clue connections, NPC cooperation, faction clocks, moral choices, and split-party tasks.
- Short rests, XP, guided level-ups, checkpoints, and rollback without losing resolved story state.
- Offline core rules and consent-gated full SRD download/indexing without package installation.
- Narrative diversity lint on openings, DM spines, and session logs.

## What Worked

- Both original campaigns remained coherent across long sessions and avoided the repetitive memory/contract/secret-rule motif stack the narrative lint is designed to detect.
- Failures usually changed the situation instead of repeating the same obstacle.
- Mechanical state preserved HP, XP, currency, inventory, shops, spell slots, limited-use resources, rests, checkpoints, level-up choices, and rollback.
- The English assisted flow asked three short character decisions before play.
- Creative magic was adjudicated without granting nonexistent spells, and an ancestry/class cantrip audit correctly resolved an apparent over-allocation.
- Full SRD access was requested explicitly, remained inside the selected workspace, installed no packages, and produced page citations for advancement.

## Release Findings And Fixes

### Fixed

- A Spanish opening check was rolled and persisted but omitted from the player-facing response. The turn contract now forbids any hidden player-affecting roll and requires the check block before consequence narration.
- Session analytics parsed English Markdown headings and reported zero scenes/checks for the Spanish campaign. Structured JSONL checks are now the language-independent primary source.
- Analytics counted saved visual prompts as visuals. It now reports generated and pending counts separately and warns on missing or ungenerated visuals.
- The English session used DC 10 for six of seven checks. Analytics now warns when one DC dominates at least 70 percent of a session, and the rules skill directs the Game Master to vary no-roll, advantage, consequences, contests, resource tradeoffs, and the full DC ladder.
- The Spanish Game Master invented a candle that was not in state. The runtime contract now requires a `game-state.json` check before relying on equipment and forbids inferring specific objects from a generic pack.
- An instrument could be marked with an equipped slot while remaining in the backpack. Equipment now supports `instrument` and `focus`, and any item created with a slot becomes consistently equipped.
- First-session setup required many independent writes. `quick_start.py` now creates the campaign, hero, equipment, state, checkpoint, minimum spine, opening, journal, session, analytics event, continuity rows, and visual prompt atomically from one spec. The local transaction completes in about 0.4 seconds.
- Preflight now detects both sessions with no visuals and prompt-only visual queues.

### Still Requires Product-Surface Verification

- The delegated playtest runtime did not expose a usable native image-generation call. Even when the image-generation skill was attached, it saved a prompt without producing an asset. The plugin now requires an explicit generated asset or a visible `visual_unavailable` outcome before returning a selected visual beat. Final review still needs one installed-plugin run on a surface where native image generation is available.
- The quick-start regression reduced the observed opening from roughly six-to-eight minutes to about four-and-a-half minutes, but model planning and visual work still dominate latency. The local persistence portion is no longer the bottleneck.

## Release Gate

The rules, state, multilingual analytics, and campaign continuity paths are ready for packaging. Before submitting to the public directory, run one installed-plugin opening on the final OpenAI product surface and confirm that the first generated image appears in chat and is registered in the campaign gallery. Treat a silent `prompt-saved` row as a failed test.
