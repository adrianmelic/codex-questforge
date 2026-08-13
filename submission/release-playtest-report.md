# Questforge Release Playtest Report

Playtests: 2026-07-10

Release audit: 2026-07-16

Installed-plugin acceptance: 2026-07-22

Platform 1.2.0 publication verified: 2026-07-25

Questforge 1.3.0 save and installed-plugin acceptance: 2026-08-12

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

## Platform Publication

On 2026-07-25, the public ChatGPT Plugins directory rendered Questforge version 1.2.0 with Adrián Melic as developer, all six public skills, the book-and-anvil icon, and the expected public description and capabilities. The local 1.2.0 archive used to synchronize the functional public source was `29,942,163` bytes with SHA-256 `08f1bcccee519c8c3774a933f295f47b6ef78b8c9f49b30927a23af80a1951a5`.

After synchronizing GitHub and correcting the canonical website, policy links, and public documentation, `scripts/package_plugin.py` deterministically builds a source-equivalent 1.2.0 archive of `29,942,289` bytes with SHA-256 `b273b486dc948b33474ba72cb49e3181a3997bac5356421d0906070a16496acd`. The hash differs from the Platform artifact only because of those public metadata and documentation corrections.

The 1.1.0 installed-plugin acceptance above remains the detailed conversational evidence for the opening-image contract. Future releases must repeat that acceptance rather than inferring product-surface behavior from local tests alone.

## 1.3.0 Acceptance Completed

The 1.3.0 candidate adds a seventh `questforge-save` skill, schema-2 manifests, deterministic snapshot lineage, local autosave verification, conflict-aware cloud staging, conservative legacy migration, and portable ZIP export. Its local test suite uses synthetic campaigns only; no private campaign is included in the repository or archive.

On 2026-08-12, the full repository suite passed 142 tests. All seven skills and the plugin manifest passed their structural validators. The packaged archive contained 89 allowlisted entries, including the save skill, helper, and public design document, with no private workspace paths, high-confidence secrets, or forbidden campaign/playtest trees detected.

The final acceptance used only disposable synthetic campaigns outside the public repository:

- **Clean installed-plugin opening:** a new task activated the exact 1.3.0 candidate, created a fresh synthetic campaign, invoked native image generation once, displayed the result once, registered the PNG as `canon`, refreshed a one-item gallery, and passed strict preflight with `0` errors and `0` warnings.
- **Google Drive creation and readback:** one exact disposable folder was selected and authorized. Questforge proved write access, reproduced the canonical folder structure, uploaded 15 gameplay-critical files, verified each by readback, and wrote and verified `questforge.json` last.
- **Cross-task resume:** a new task read the remote manifest first, verified all 15 canonical files and their hashes, resumed at the recorded scene, resolved one meaningful player action, and advanced the campaign from revision 2 to revision 3.
- **Verified next revision:** five changed files were updated in place with their provider file identities preserved. Every change passed readback, the manifest was again written and verified last, and a final independent audit matched 15 of 15 canonical files.
- **Safe failure behavior:** synthetic conflict cases for unverified permission, a different campaign ID, a newer remote revision, divergent same-revision lineage, and failed readback stopped without overwrite or false success.
- **Media isolation and fallback:** a deliberately unavailable optional-media file did not invalidate the canonical SaveSet. The canonical ZIP fallback passed integrity checks and stored `questforge.json` as its final file entry.

No real campaign, provider credential, personal folder reference, connector receipt, or generated acceptance asset is included in the repository or submission archive. Each future release must repeat the clean installed-plugin opening and any provider-specific connector acceptance it claims to support.

## 1.3.1 Integrity Hotfix Prepared

After the 1.3.0 pull request was merged, automated Codex review identified three executable validation gaps: a data receipt could omit `remoteBefore`, receipts were not bound to the exact provider folder, and migration did not parse `game-state.json` before accepting it as canonical. Review of the follow-up hotfix found ten more gaps: incomplete nested character/combat records; incomplete shop/item/checkpoint records; inconsistent character-name normalization; malformed limited-use resources; contradictory shop prices; checkpoint IDs that were not portable to Windows; invalid or duplicate combatant names that could partially replace combat state; checkpoint IDs that could collide after moving to a case-insensitive filesystem; numeric shop prices that could overflow floating-point conversion; and a newer-Python-only integrality method in the first exact-price implementation. Each could accept data that later failed during normal play, status rendering, purchase resolution, or cross-device restore. Disposable synthetic reproductions confirmed all thirteen findings; no real campaign or provider folder was involved.

The 1.3.1 hotfix requires explicit remote-manifest state, binds both data and final-manifest receipts to the same exact provider and opaque folder reference, normalizes stored character names, parses shop prices exactly before verifying their canonical copper value, and uses one shared mechanical-state validator to block malformed or incomplete character, combat, resource, shop, item, and checkpoint data during loading, persistence, inspection, and migration. Purchase logic checks exact-price integrality through the fraction denominator, avoiding a newer-Python-only method. Combat setup validates the complete replacement before mutating campaign state. Checkpoint identifiers are constrained to a Windows-safe, cross-filesystem filename component before any checkpoint path is read or written, and their normalized case-insensitive identities must remain unique. On 2026-08-13, all 165 Python tests passed, all seven skills and the plugin manifest passed structural validation, and two independent builds produced the same 89-entry archive: `29,972,893` bytes with SHA-256 `15b462d9d030490912498d47f2c3cf497f4e54dab1d7dbe17bbfb99bc2cf57ce`. Focused final staged-diff and tracked-tree scans found no high-confidence credential, private campaign path, personal machine path, connector/app identifier, or task identifier. A new clean installed-plugin and Google Drive acceptance, GitHub release publication, tagging, and Platform publication remain separate pending gates.
