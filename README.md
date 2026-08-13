# Questforge

![A Questforge adventure begins in a sunlit cliffside city](assets/screenshots/questforge-scene-v2.png)

## Say anything. The world keeps up.

**Questforge is an open-ended, 5E-compatible fantasy RPG played inside Codex.** Codex becomes the Game Master, rules referee, campaign memory, and visual table. You speak naturally; Questforge prepares an original campaign, resolves meaningful uncertainty in the open, and remembers what your choices changed in a portable save.

This is not a browser game that happens to use Codex. **The conversation is the game.**

[Explore Questforge](https://adrianmelic.com/questforge) | [Install it in ChatGPT](https://chatgpt.com/plugins/plugins_6a611d2ff7b88191b75a5290bceb0e87) | [Read the installation guide](docs/install-and-play.md)

## Recent Update: Portable Campaigns

**Questforge 1.3.0 lets a campaign continue beyond one conversation or computer.**

Play still starts immediately: there is no Questforge account or storage setup before the opening scene. After play begins, Questforge can offer one optional invitation to make the campaign portable. If you accept, enable a storage connector you already use, select one exact folder, and explicitly authorize Questforge to write there. Google Drive is the first end-to-end tested beta target.

From then on, meaningful actions create verified snapshots of the hero, world, clues, sessions, checkpoints, Game Master continuity, and next decision. To continue on another supported device or in a new task, enable Questforge and the same storage connector, select that campaign folder, and ask to resume. The connector may request authorization again in the new task.

Questforge checks the campaign identity and save history before continuing. If it finds a newer or divergent copy, it stops instead of silently overwriting it. Generated images, 360 viewers, and ambience synchronize separately, so a media problem does not invalidate the playable campaign. When direct cloud synchronization is unavailable, Questforge can create a portable ZIP instead.

[Read how portable and cloud saves work](docs/cloud-saves.md)

## Start Playing

Install or enable Questforge, start a new task so the skills are loaded, and say:

```text
I want to play @questforge. Create a quick hero and begin.
```

Or ask for an assisted hero:

```text
I am new to tabletop RPGs. Guide me through creating a hero, then begin.
```

Questforge follows the language of the conversation. English and Spanish have bundled rules primers; other languages use the English rules index when a localized SRD term is unavailable.

## What Play Feels Like

1. **You act freely.** Investigate, bargain, cast, fight, flee, improvise, ask out of character, or attempt something the Game Master did not anticipate.
2. **The table resolves uncertainty.** Meaningful checks show the ability or attack, modifier, DC or opposing result, advantage state, natural roll, total, and outcome.
3. **The world changes.** HP, XP, inventory, equipment, spell slots, clues, NPC attitudes, faction pressure, clocks, rewards, and consequences become durable state.
4. **The next beat becomes visible.** When native image generation is available, useful scene images appear once in the same conversation and are also registered in the local campaign gallery.

Failures move the fiction forward with costs or harder choices. Repeated bad rolls do not trap the player at the same obstacle. Combat, shops, rests, level-ups, death saves, checkpoints, and table-style rewinds are supported without turning the campaign into a fixed dialogue tree.

## Where You See And Hear The Game

Questforge has a portable conversation layer and an enhanced local desktop layer.

| Surface | Player experience |
| --- | --- |
| **Conversation** | Narration, dialogue, visible dice, rulings, compact state, inventory and spell status, choices, and freeform actions. Static generated scenes are shown here when native image generation is available, including on mobile-capable conversation surfaces. |
| **Local Codex workspace** | Persistent campaign files, journals, clues, NPCs, factions, mechanical state, checkpoints, analytics, and a live visual table that can stay open beside the story and follow new assets. |
| **Selected cloud folder** | Optional cross-device canonical saves through a writable storage connector the player already installed and explicitly authorizes. Questforge compares save lineage, verifies every write by readback, and writes the manifest last. Google Drive is the first 1.3 beta target. |
| **Local 360 viewer** | Important spatial moments can open as standalone `file:///` photospheres with natural drag direction, inertial movement, smooth zoom, and keyboard controls; no local server is required. |
| **Optional soundtrack** | A scene-appropriate approved track can be attached when the viewer is first created. Audio never starts for a new player by default; the speaker toggle is voluntary and its preference is remembered by later viewers when the browser permits it. |

If a surface has no writable filesystem, Questforge can use an explicitly selected writable storage connector for the canonical SaveSet. Without either storage path, it keeps a compact campaign ledger in the conversation and does not pretend that durable files or checkpoints were created. Galleries, 360 viewers, and ambience remain optional local enhancements.

## Why Campaigns Do Not Start From The Same Template

Every new campaign begins with a private creative conception pass. Questforge considers several materially different possibilities, then establishes:

- environment, biome, climate, season, time, surface, and physical scale;
- community, social scale, livelihoods, and relationships between important NPCs;
- a material conflict, an active threat, faction pressure, and a concrete reason to act;
- tone, aesthetics, sensory palette, and the campaign's long-term promise;
- a minimum coherent Game Master spine with exactly three different clue routes and multiple plausible outcomes.

The bundled quick-start spec is deliberately neutral. It does not default to a port, rain, water, fog, darkness, or any other recurring environmental device, and it does not ban those elements when a specific campaign earns them. A local repetition audit compares recent campaign conceptions so a rename is not mistaken for an original premise.

## Core Capabilities

- quick, assisted, or imported/custom level-1 heroes;
- original 5E-compatible fantasy campaigns with transparent dice and rulings;
- offline English and Spanish rules indexes, with optional full SRD 5.2.1 indexing;
- persistent `game-state.json` for HP, AC, XP, inventory, equipment, shops, rests, spell slots, combat, conditions, death saves, and checkpoints;
- campaign memory for clues, NPCs, factions, locations, session logs, a player journal, and a Game Master-only adventure spine;
- meaningful-turn local autosaves, conflict-aware opt-in cloud synchronization, cross-device resume, legacy-save migration, and portable ZIP export;
- failure-forward adjudication, varied difficulty classes, rewards beyond combat, and anti-stall pacing;
- generated scenes, tactical maps, items, reference plates, comic beats, inventories, merchants, outfits, recaps, and 360 POV panoramas;
- visual continuity for recurring characters, injuries, equipment, objects, locations, and maps;
- an optional original ambience pack licensed for redistribution by its creator;
- local analytics that distinguish generated visuals from pending prompts and surface repetitive DC or pacing patterns.

## Install From Source

Add this repository as a marketplace:

```text
codex plugin marketplace add adrianmelic/codex-questforge
```

Then open **Plugins** in the ChatGPT desktop app, or `/plugins` in a current Codex CLI, install Questforge, and start a new task. The repository includes `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, and the complete skills bundle.

You can also ask Codex:

```text
Install the Questforge plugin from https://github.com/adrianmelic/codex-questforge, then start a new task so I can play it.
```

Official references: [Build plugins](https://learn.chatgpt.com/docs/build-plugins) and [Submit plugins](https://learn.chatgpt.com/docs/submit-plugins).

## First Run And Rules

The default setup is offline and installs no packages. During normal play, Questforge handles setup and campaign bootstrap. For manual review, run this from the project where campaign files should live:

```powershell
python scripts\questforge_setup.py --data-dir .questforge
```

It detects English or Spanish and builds local Markdown, JSONL, and SQLite indexes from the bundled core-rules primer. The game can begin immediately.

With the player's explicit consent, detailed rules lookup can optionally download and index the official SRD 5.2.1 PDF:

```powershell
python scripts\questforge_setup.py --data-dir .questforge --full-srd
```

Questforge never installs packages. If `pypdf` is unavailable, it continues with the offline core index and explains how complete extraction can be retried in an environment where the user has prepared that dependency. The `.questforge/` directory is local runtime data and should not be committed.

## Development

Run the full test suite without leaving Python cache artifacts in the repository:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m pytest tests -p no:cacheprovider
```

Validate the plugin and all seven skills with the current `plugin-creator` and `skill-creator` validators. Build the deterministic OpenAI Platform archive with:

```powershell
python scripts\package_plugin.py
```

The archive is written to `dist/`, which is intentionally ignored by Git.

Developers and reviewers can reproduce a complete local campaign scaffold from a completed creative brief. Copy `templates/quick-start-spec.json`, invent every empty value, then audit and run it:

```powershell
python scripts/campaign_conception.py --spec <completed-spec.json> --campaigns-dir <play-workspace>/campaigns
python scripts/quick_start.py --workspace-root <play-workspace> --spec <completed-spec.json>
```

These scripts create the conception record, campaign memory, hero state, equipment, checkpoint, minimum Game Master spine, opening brief, player journal, first session, analytics event, visual continuity, and opening visual prompt. Native image generation remains a product-surface action and is never performed through a bundled API key.

Inspect, migrate, save, or export one synthetic/local campaign through the portable SaveSet helper:

```powershell
python scripts/campaign_save.py inspect --campaign-root <campaign-root> --format markdown
python scripts/campaign_save.py save-local --campaign-root <campaign-root>
python scripts/campaign_save.py package --campaign-root <campaign-root> --output <questforge-save.zip>
```

See [Portable and cloud saves](docs/cloud-saves.md) for consent, conflict, verification, cross-device resume, and cloud-only behavior.

## Repository Map

- `.codex-plugin/plugin.json` - plugin manifest and public install-surface metadata.
- `.agents/plugins/marketplace.json` - source marketplace for repository installation.
- `skills/` - runtime orchestration, setup, rules, campaign, portable saves, puzzles, and visuals.
- `scripts/` - setup, rules search, dice, state, memory, portable saves, migration, visuals, audio, analytics, preflight, and packaging.
- `resources/core-rules/` - offline English and Spanish rules primers derived from SRD 5.2.1.
- `templates/` - neutral campaign, journal, state, visual, audio, and puzzle structures.
- `assets/audio/starter-pack/` - curated Suno-generated ambience tracks.
- `submission/` - OpenAI Platform listing copy, prompts, test cases, release notes, and publication evidence.
- `docs/` - GitHub Pages compatibility routes, installation guidance, design notes, and sanitized playtest evidence.

## Current Public Release

Questforge 1.3.0 is published in the ChatGPT Plugins directory. It adds the seventh `questforge-save` skill, schema-2 campaign manifests with stable IDs and save lineage, meaningful-turn autosave, verified local snapshots, opt-in cloud synchronization through a user-selected writable connector, conservative migration of older campaigns, cross-device resume, and canonical or media-inclusive ZIP export. Google Drive is the first end-to-end tested beta target; the provider-neutral contract does not add a Questforge server or publisher access to campaign data.

Acceptance on 2026-08-12 used disposable synthetic campaigns only. A clean task resumed a verified Google Drive save, advanced it through a meaningful turn, updated the next revision without replacing file identities, and read back all 15 canonical files plus the final manifest. A separate clean activation generated one native opening image, registered it as `canon`, refreshed the gallery, and passed strict preflight with zero errors and zero warnings. Conflict, permission, optional-media failure, and ZIP fallback paths were also exercised without touching a real campaign. Version 1.3.0 was published on 2026-08-13.

[Install Questforge](https://chatgpt.com/plugins/plugins_6a611d2ff7b88191b75a5290bceb0e87) or see [the release playtest report](submission/release-playtest-report.md) for the underlying evidence.

## Prepared Next Release

Questforge 1.3.1 is a focused integrity hotfix prepared in response to automated review of the merged 1.3.0 pull request and its follow-up hotfix. Data and final-manifest receipts must now identify the exact provider and folder they verify, a data receipt cannot omit its prior remote-manifest state, and malformed or structurally unusable `game-state.json` files—including incomplete nested character, combat, resource, shop, item, or checkpoint records—block loading, persistence, inspection, and migration instead of becoming canonical snapshots. Stored character names are normalized consistently, shop prices must match their canonical copper value, and checkpoint IDs must be portable across macOS, Windows, and common synchronized filesystems. Combat setup validates the complete replacement before changing campaign state, while normalized case-insensitive checkpoint identity prevents rollback files from colliding after a save moves between filesystems.

The local suite passes 163 tests, including regressions for all eleven review findings, and the updated save skill passes structural validation. GitHub release publication and a final clean Platform acceptance for 1.3.1 remain separate pending gates.

Version 1.3.1 is not yet released on GitHub or published on OpenAI Platform.

## Roadmap

- Evaluate a larger curated original ambience pack in a later release. The first public version keeps the soundtrack intentionally small so additional music does not delay publication.
- Run an end-to-end OneDrive connector acceptance before describing OneDrive as tested rather than contract-compatible.
- Evaluate optional large-media background synchronization separately from the small canonical autosave path.

## Privacy, Terms, And Support

- [Privacy policy](https://adrianmelic.com/privacy-policy)
- [Terms of use](https://adrianmelic.com/terms-of-service)
- [Support](https://adrianmelic.com/en/#contact)
- [Security policy](SECURITY.md)

Questforge does not operate a publisher-controlled server or transmit campaign data to the publisher. Optional cloud saves go directly to the exact third-party folder the player selects through their installed connector. Campaigns can contain information the player entered; review them before sharing, exporting, or committing them.

## License And Notices

Original code and plugin materials are MIT licensed. See `LICENSE`.

Questforge is unofficial and is not affiliated with, endorsed, sponsored, or approved by OpenAI or Wizards of the Coast LLC. Rules references are grounded in SRD material released under Creative Commons Attribution 4.0 International. See `NOTICE.md` and [SRD sources](docs/srd-sources.md).

The starter audio pack contains curated tracks generated by Adrián Melic with Suno v5.5 while using a paid plan intended to grant commercial rights for newly generated outputs. See [audio licensing and provenance](assets/audio/README.md).
