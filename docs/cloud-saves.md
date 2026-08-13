# Portable And Cloud Saves

Questforge 1.3.0 introduces a portable SaveSet and an opt-in cloud synchronization workflow. The design keeps Questforge skills-only: there is no Questforge account, publisher database, or Adrián-operated campaign server. When cloud saving is enabled, the OpenAI surface uses a storage connector already installed and authorized by the player.

## Player Experience

1. **Start playing normally.** Questforge creates the hero and opening scene without requiring an account, connector, or cloud folder.
2. **Opt in after play begins.** Questforge offers one short invitation to make the campaign portable. Declining does not interrupt the game.
3. **Choose the destination.** Enable a supported storage connector, select or create one exact campaign folder, and explicitly authorize writes inside it. Questforge never scans the rest of the drive or asks for provider credentials.
4. **Keep playing.** Actions that change the fiction or mechanics create verified autosaves. Rules questions and clarifications do not create unnecessary revisions.
5. **Resume elsewhere.** In a new task or on another supported device, enable Questforge and the same connector, select the campaign folder, and ask to continue. Questforge verifies every canonical file before advancing the story. The connector may ask for folder authorization again because permission is not assumed to persist across tasks.
6. **Recover safely when needed.** A newer or divergent copy stops synchronization instead of being overwritten. If direct synchronization is unavailable, Questforge offers a portable ZIP.

Optional images, 360 viewers, gallery HTML, and ambience are transferred separately from the small gameplay-critical SaveSet. A media failure therefore cannot turn a verified playable save into a failed campaign save.

## What This Solves

A campaign should not exist only in one long conversation or on one computer. The portable format lets a player:

- recover the current hero, world, clues, clocks, and next decision from files;
- move a campaign between local Codex workspaces;
- resume from a selected Google Drive folder on another supported device;
- use an equivalent writable provider in the future without changing the campaign format;
- download a small ZIP when direct connector synchronization is unavailable.

Google Drive is the first 1.3 beta target. OneDrive and other providers use the same contract only when the current product surface exposes equivalent folder selection, raw file create/update, metadata, and readback tools and an end-to-end acceptance has passed.

## Storage Layers

Questforge separates three concerns:

| Layer | Contents | Save cadence |
| --- | --- | --- |
| Canonical SaveSet | Mechanical state, current and prior sessions, summaries, journals, characters, checkpoints, Game Master continuity, visual indexes/prompts, manifest | Every meaningful turn; compact again at scene boundaries |
| Optional media | Generated images, 360 viewers, gallery HTML, ambience files | Separately, when useful and supported |
| Reproducible cache | Rules indexes, downloaded SRD, temporary analytics output, Python/browser caches | Never required for portability |

Media can be large or slow to transfer. A media failure therefore does not invalidate a verified canonical save.

## Canonical Files

The canonical profile contains these paths when present:

```text
campaigns/<campaign-slug>/
  questforge.json
  campaign-conception.json
  campaign-state.md
  game-state.json
  player-journal.md
  opening-brief.md
  visual-bible.md
  dm/
    adventure-spine.md
    puzzle-ledger.md
  characters/
  sessions/
  checkpoints/
  images/
    prompts/
    visual-index.md
    visual-ledger.md
  analytics/
    session-events.jsonl
  audio/
    library.json
```

`game-state.json` remains the mechanical source of truth. `campaign-state.md` summarizes the world, NPCs, clues, factions, clocks, position, and next choice. The current session preserves decisions, visible rolls, and consequences. `player-journal.md` is spoiler-free. Game Master files are saved but never exposed in player-facing sync reports.

## Save Identity And Lineage

Schema 2 gives every campaign a stable `campaignId`. Every content-changing snapshot has:

- a monotonically increasing revision;
- a SHA-256 `saveId` derived from the campaign ID, parent, revision, profile, and sorted file hashes;
- a `parentSaveId`;
- session and scene coordinates;
- a bounded history of revision/save-ID pairs.

This lineage distinguishes a safe older ancestor from a divergent copy. Modification time alone never decides which version wins.

## Autosave

Questforge autosaves after a player action changes fiction or mechanics. Immediate state such as HP, resources, inventory, conditions, currency, XP, combat, and checkpoints is written before the reply finishes. The current session and affected canonical summaries are included in the snapshot.

At a scene boundary, after roughly three meaningful turns, at session close, or before switching devices, Questforge performs a compaction save: it refreshes campaign and player summaries, Game Master continuity, clues, clocks, and the next decision before producing another snapshot.

A rules question, clarification, or unchanged narration does not create a pointless revision. Before an irreversible choice, Questforge creates and saves a named checkpoint first.

## Consent And Folder Selection

Questforge may recognize that a local path sits below a Google Drive or OneDrive synchronization root. That is only a convenience hint. It does not prove:

- that the provider finished uploading;
- that the current ChatGPT/Codex surface has the provider connector;
- that the connector can edit the folder;
- that a read-only file can be updated;
- that the player authorized the same target for this task.

The player must select one exact campaign folder and explicitly authorize writes. Questforge never asks for provider passwords or tokens and never scans the rest of the drive for campaigns.

## Verified Cloud Transaction

For each cloud save, Questforge follows this order:

1. Update canonical local or in-memory campaign state.
2. Create or verify the local snapshot.
3. Read the remote `questforge.json` before any overwrite.
4. Confirm the same campaign ID and a safe lineage relationship.
5. Upload or update changed non-manifest files.
6. Read each written file back and compare its SHA-256 or exact content.
7. Bind both verification receipts to that exact provider and folder, then build the final manifest.
8. Write `questforge.json` last.
9. Read the manifest back and verify it.
10. Report complete, partial, conflict, or failed status accurately.

If any critical file fails, the manifest is not advanced and the save is partial. If the local save succeeded but cloud synchronization failed, Questforge says exactly that and offers a ZIP fallback.

## Conflict Rules

Questforge fast-forwards a remote campaign only when its revision/save-ID pair is the current local snapshot or appears in local lineage. It stops when:

- the remote campaign ID differs;
- the remote revision is newer;
- the same revision has a different save ID;
- the remote save is not a known ancestor;
- campaign-like files exist without a valid manifest;
- write permission or readback cannot be verified.

The player can then preserve both copies, choose a canonical session after inspection, or export one copy before reconciliation. Questforge never merges mechanical JSON or hidden Game Master truth heuristically.

## Existing Campaigns

Migration is dry-run by default:

```powershell
python scripts/campaign_save.py migrate --campaign-root <campaign-root>
```

The migration helper can safely assign a campaign ID, upgrade the manifest schema, initialize lineage, create a missing checkpoints directory, and copy one unambiguous legacy journal or visual index into its canonical path. It preserves the source file.

It stops when a critical file such as `game-state.json` is missing, when multiple possible canonical copies exist, when two copies differ, or when the manifest session disagrees with session logs. After reviewing which session is canonical, apply explicitly:

```powershell
python scripts/campaign_save.py migrate --campaign-root <campaign-root> --apply --accept-latest-session
```

Migration never invents lost mechanics, character state, session decisions, or Game Master truth.

## Local Commands

Inspect one campaign without writing:

```powershell
python scripts/campaign_save.py inspect --campaign-root <campaign-root> --format markdown
```

Record a canonical local snapshot:

```powershell
python scripts/campaign_save.py save-local --campaign-root <campaign-root> --profile canonical --scene-id "session-003:scene-004" --scene-label "The bell chamber"
```

Create a portable ZIP without large media:

```powershell
python scripts/campaign_save.py package --campaign-root <campaign-root> --output <questforge-save.zip>
```

Add `--include-media` only when the larger archive is wanted.

The connector-driven staging commands and receipt schema are documented inside the `questforge-save` skill. They keep the final manifest as the last verified write without embedding provider credentials in the campaign.
