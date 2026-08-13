---
name: questforge-save
description: Save, resume, migrate, export, or synchronize a Questforge campaign across local folders and user-authorized cloud storage without overwriting a newer copy. Use when play changes durable state, when the player asks for autosave, backup, Google Drive, OneDrive, cross-device play, ZIP export, campaign import, or recovery from an older/non-canonical save.
---

# Questforge Save

Keep campaign continuity recoverable outside the conversation. Use the smallest available storage path: local files first, an already installed writable cloud connector when the player opts in, and a portable ZIP fallback when direct sync is unavailable.

Read `references/save-contract.md` before configuring cloud sync, resolving a conflict, or migrating an existing campaign.

## Non-Negotiable Boundaries

- Treat a detected Google Drive, OneDrive, Dropbox, iCloud, or other synced path only as a hint. Detection never proves cloud availability, connector authorization, or write access.
- Work only inside the exact campaign root and exact cloud folder selected by the player. Do not scan their home directory, entire drive, or unrelated provider folders for campaigns.
- Obtain explicit permission before the first external write. Reuse that permission only for the same campaign, provider, and folder during the current task unless the product exposes a durable grant.
- Reading a folder or file does not prove write authority. Verify an editable capability from trusted metadata or perform a bounded non-secret canary write plus readback in the selected folder before claiming sync is ready.
- Read and compare the remote `questforge.json` before overwriting any existing campaign files. Stop on an unknown campaign ID, a newer remote revision, or divergent save lineage.
- Upload or update every changed snapshot file first. Write `questforge.json` last and verify it by readback. Never report a complete save when any critical file or the final manifest is unverified.
- Keep Game Master files private from player-facing chat. They may be stored in the selected private campaign folder, but do not quote hidden truths, clocks, or puzzle solutions in the sync report.
- Do not ask for passwords, provider tokens, API keys, or recovery codes. Use the product's connector and consent surfaces.
- Do not delete legacy copies, remote versions, checkpoints, or media during migration or conflict handling.

## Choose The Available Path

1. **Writable local campaign root:** use the bundled save helper and keep local state canonical. A folder already synchronized by a desktop provider is useful, but still describe cloud status as unverified until provider readback succeeds.
2. **No local filesystem, writable storage connector available:** use the selected provider folder as the campaign root. Read the manifest first, load only the canonical files needed for the turn, then perform the same conflict-aware write transaction through connector tools.
3. **No writable storage path:** maintain the compact in-conversation ledger, state that durable sync is unavailable, and offer a downloadable canonical SaveSet or ZIP when the surface can create one. Never imply that chat memory is a complete external save.

Google Drive is the first 1.3 beta target. Use OneDrive or another provider only when the current surface exposes equivalent folder selection, raw file create/update, metadata, and readback capabilities. Keep the contract provider-neutral and do not describe a provider as tested until its acceptance run passes.

## Start Or Attach Storage

Do not delay a new player's first actionable scene with storage setup. After the opening has been created and saved locally, offer one short, optional invitation to keep the campaign portable.

When the player accepts:

1. Identify the exact local campaign root, if available. Run:

   ```powershell
   python ../../scripts/campaign_save.py inspect --campaign-root <campaign-root> --format markdown
   ```

2. If the campaign uses an older schema, run a dry migration first:

   ```powershell
   python ../../scripts/campaign_save.py migrate --campaign-root <campaign-root>
   ```

   Show blockers. Apply only after the player confirms which session is canonical when the manifest and session logs disagree. The safe apply path is:

   ```powershell
   python ../../scripts/campaign_save.py migrate --campaign-root <campaign-root> --apply --accept-latest-session
   ```

3. Ask the player to select or create one exact provider folder for this campaign. If an existing campaign folder is selected, inspect it before any write.
4. Verify actual write authority. Prefer provider metadata equivalent to `canEdit` plus app authorization. If unavailable, create or update a tiny non-secret sync probe, read it back exactly, and retain or remove it only through a supported, scoped action.
5. Record only the provider name, opaque folder reference, optional folder URL, and verification receipts in the campaign manifest. Do not record provider credentials or unrelated local paths.

## Autosave Policy

Use two speeds:

- **Canonical autosave:** after every player action that changes fiction or mechanics, update the current session log and immediate mechanical state, refresh any affected canonical summaries, and create a new canonical snapshot. A clarification, rules question, or unchanged narration does not need a save.
- **Compaction save:** at a scene boundary, after roughly three meaningful turns, on session close, or before switching devices, compact `campaign-state.md`, `player-journal.md`, Game Master notes, clues, clocks, and the next decision, then save again.
- **Irreversible choice:** create a named checkpoint before death risk, permanent rare-resource spend, major betrayal, or hard campaign branch; then include the checkpoint in the save before resolving the choice.
- **Media:** synchronize generated images, viewers, gallery HTML, and ambience separately. Media failure must not block or downgrade a verified canonical save. Mention pending media explicitly.

For local play, after updating canonical state run:

```powershell
python ../../scripts/campaign_save.py save-local --campaign-root <campaign-root> --profile canonical --scene-id "session-003:scene-004" --scene-label "The bell chamber"
```

This hashes the canonical SaveSet, advances its lineage only when content changed, verifies the local copy, and writes `questforge.json` last.

## Cloud Save Transaction

With a writable local campaign and an authorized connector:

1. Run `save-local` after updating state.
2. Generate a read-only plan:

   ```powershell
   python ../../scripts/campaign_save.py plan-cloud --campaign-root <campaign-root>
   ```

3. Read the remote manifest if present. Compare `campaignId`, `storage.snapshot.revision`, `saveId`, and the local `history`:
   - missing remote manifest: treat as a new target only if the folder is otherwise appropriate;
   - same save ID and revision: verify rather than rewrite unchanged files;
   - known older ancestor: fast-forward by uploading changed files;
   - newer or unknown lineage: stop and reconcile; never choose a winner silently.
4. Reproduce canonical relative paths as provider subfolders below the selected campaign folder; for example, store `dm/adventure-spine.md` inside a `dm` child, not as a filename containing `/` and not flattened into the root. Create only missing subfolders required by the plan. Do not treat a truncated folder listing as proof that a file is absent; paginate or search within the exact parent when the connector supports it.
5. Upload or update only changed non-manifest files from the plan. Preserve existing provider file IDs when updating files in place.
6. Read every written file back. Build a temporary receipt containing the plan `saveId`, `writeAuthorized: true`, the exact `provider` and opaque `folderRef`, the mandatory remote-before identity (`null` only for a verified new target), and a verified SHA-256 entry for each planned file. Do not place secrets or campaign prose in the receipt.
7. Stage the final manifest:

   ```powershell
   python ../../scripts/campaign_save.py stage-cloud --campaign-root <campaign-root> --receipt <receipt.json> --provider google-drive --folder-ref <opaque-folder-id> --folder-url <folder-url> --output <temporary-questforge.json>
   ```

8. Upload the staged file as `questforge.json` last. Read it back and create a manifest receipt with its SHA-256, `saveId`, `verified: true`, and the same exact `provider` and `folderRef`.
9. Commit the verified staged manifest locally:

   ```powershell
   python ../../scripts/campaign_save.py commit-cloud --campaign-root <campaign-root> --staged-manifest <temporary-questforge.json> --manifest-receipt <manifest-receipt.json>
   ```

On a cloud-only surface, perform the equivalent transaction directly through connector tools. The remote `questforge.json` remains the last write and source of the verified result.

## Resume On Another Device

1. Ask the player to activate Questforge and their storage connector, then select the exact campaign folder.
2. Read `questforge.json` first. Validate schema, campaign ID, latest verified snapshot, session, scene, and file list.
3. Read back all canonical files in that snapshot before resuming. Treat missing or hash-mismatched files as a partial save and stop before advancing the fiction.
4. If a local copy also exists, compare lineage. Pull a known newer remote snapshot only after preserving the local copy or producing a portable archive. Stop on divergence.
5. Resume from the manifest's session and scene, using `game-state.json` as mechanical truth and the canonical summaries for continuity.
6. Re-enable meaningful-turn autosave for the remainder of the task. Do not assume authorization persists across a new task unless the connector confirms it.

## Migration Rules

- Run migration against one named campaign only. Dry-run by default.
- Assign a stable `campaignId`, schema version, canonical path map, autosave policy, lineage, and first local snapshot.
- Copy a single unambiguous legacy journal or visual index into its canonical path only when the canonical file is absent. Preserve the legacy source.
- If canonical and session-scoped copies differ, stop for review. Do not select the newest file merely by timestamp.
- Do not invent missing `game-state.json`, character mechanics, session decisions, or Game Master truth. Report the exact missing files.
- A session mismatch requires explicit acceptance of the latest canonical session log.

## Portable ZIP Fallback

Create a small canonical archive by default:

```powershell
python ../../scripts/campaign_save.py package --campaign-root <campaign-root> --output <questforge-save.zip>
```

Add `--include-media` only when the player wants a larger archive and the current surface can carry it. Rules indexes and caches are reproducible and stay out of the archive.

## Completion Report

Return a compact report with:

- status: complete, partial, conflict, or failed;
- exact local campaign root or selected provider folder;
- campaign ID, save ID, revision, session, and scene;
- canonical file count and verification method;
- media status: synced, skipped, or pending;
- any missing permission, missing file, or conflict;
- provider folder link or ZIP link when available.

Say “complete” only after the manifest was written last and verified. If cloud sync fails after local save, say that the local save is complete but cloud synchronization is pending, then offer the ZIP fallback.
