# Questforge Release Playtest Report

Playtests: 2026-07-10

Release audit: 2026-07-16

Installed-plugin acceptance: 2026-07-22

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

### Product-Surface Verification Completed

- A clean task installed the final `questforge-skills-1.1.0.zip` through an isolated local marketplace and started with the public quick-start prompt. The first actionable scene invoked built-in native image generation, displayed the generated static image in the conversation, saved a 1536 x 1024 PNG inside the isolated campaign, registered the opening row as `canon`, and refreshed a one-item chronological gallery. No opening visual remained pending.
- The strict release preflight passed with `0` errors and `0` warnings: `1` registered visual, `0` pending, `0` unavailable, and `0` missing. The acceptance campaign was an original synthetic playtest kept outside the public repository; none of its files are part of the submission archive.
- The quick-start regression reduced the observed opening from roughly six-to-eight minutes to about four-and-a-half minutes, but model planning and visual work still dominate latency. The local persistence portion is no longer the bottleneck.

## Release Gate

The rules, state, multilingual analytics, campaign continuity, creative conception, deterministic packaging, and installed-plugin opening paths are ready. The 2026-07-22 acceptance confirmed that the first generated image appeared in chat, was registered in the campaign gallery, and passed strict preflight. A silent `prompt-saved` opening remains a regression and must fail future release tests.

For future release acceptance runs, execute:

```powershell
python scripts\preflight.py `
  --campaign-root campaigns\<campaign-slug> `
  --require-player-journal `
  --require-generated-visuals `
  --require-opening-visual `
  --refresh-gallery
```

The strict command checks the generated asset and local gallery inputs. A human reviewer must still confirm that the same static image appeared once in the conversation, because a local filesystem audit cannot observe the rendered chat surface.

## Publication Audit

The 2026-07-16 publication pass removed the rushed branching demo and replaced it with a product page that explains the real play surface: the conversation carries narration, rolls, state, and static generated scenes; a writable local Codex workspace adds campaign artifacts, the chronological gallery, interactive 360 viewers, and optional soundtrack playback. The public page uses one coherent original scenario rather than presenting invented choices as a playable campaign.

The README, Platform listing copy, manifest descriptions, hero image, tactical-map example, and 360 example now use the same release positioning. The public materials contain no contest or challenge framing.

Verification completed:

- `127` Python tests passed on Python 3.14.6 on macOS without forcing a language environment variable.
- All six skills passed the current `skill-creator` validator.
- The plugin passed the current `plugin-creator` validator.
- Desktop and 390 px mobile browser checks found no horizontal overflow or console warnings.
- The WebGL photosphere rendered nonblank pixels; a pointer drag changed 98.2 percent of the captured canvas and revealed another coherent direction of the same scene.
- The soundtrack remained off for a new viewer, played after a voluntary click, and preserved the preference for later viewers. When browser autoplay policy blocks restoration, the control offers an explicit resume action without discarding that preference.
- The submission archive was rebuilt at `29,713,642` bytes with SHA-256 `3c9f5ad9051ca0e5b5ef9a3ab1fc46440b1a28117391826d34c22fbdd167afac`.

One external check remains intentionally open:

1. Confirm that the Platform upload form accepts the `29.7 MB` archive and submit it for review. No archive had been uploaded when this report was committed.
