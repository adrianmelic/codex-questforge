# Questforge Sound Atlas

Questforge uses audio as a table aid, not as a soundtrack that competes with
the Dungeon Master. The goal is a pool of short, loopable ambience tracks and a
smaller set of one-shot stingers that Codex can choose by scene tags.

## Design Rules

- Keep most loops subtle enough to play under reading and conversation.
- Prefer 20 to 40 second seamless loops for ambience.
- Prefer 3 to 5 second one-shots for stingers.
- Avoid lyrics, intelligible speech, modern instruments, trailer hits, and
  strong melodies unless a campaign explicitly asks for them.
- Treat every public track as an owned, licensed asset with provenance.
- Keep rejected or unreviewed candidates out of the public audio library.

## Files

- `templates/sound-atlas-v0.1.json`: planned Suno prompts with stable IDs,
  categories, tags, intensity, volume, and license metadata.
- `templates/audio-library.json`: example campaign-local approved library.
- `assets/audio/library.json`: bundled starter pack with approved Suno-generated MP3 files.
- `<campaign-root>/audio/library.json`: live library for a campaign.
- `<campaign-root>/audio/*.mp3`: approved local audio files.
- `scripts/audio_library.py`: validation, prompt listing, and scene selection.

## Suno Workflow

Generate in batches, then curate:

1. Open Suno `Create`.
2. Use `Sounds`.
3. Use the current best model, for example `v5.5`.
4. Use `Loop` for atlas tracks whose `type` is `loop`.
5. Use `One-Shot` for atlas tracks whose `type` is `one-shot`.
6. Generate 4 to 8 prompts per batch.
7. Mark each generated candidate as `approved`, `variant`, or `rejected`.
8. Download only approved files into a local campaign or project audio folder.
9. Rename files to match the atlas ID, for example
   `tavern_warm_rain_01.mp3`.
10. Add or update the track in `audio/library.json` with `status: approved`.

Use the prompt lister to avoid copying prompts by hand from JSON:

```powershell
python plugins\questforge\scripts\audio_library.py list-prompts `
  --library plugins\questforge\templates\sound-atlas-v0.1.json `
  --limit 8
```

## Curation Rubric

Approve a track only if it passes all of these:

- It loops without an obvious restart.
- It stays below the narration instead of demanding attention.
- It has no clear words, copyrighted melody, modern production cue, or sudden
  disruptive hit unless it is a one-shot.
- It matches its tags and intensity.
- It is useful for at least two plausible scenes.
- Its license metadata is clear enough for the intended distribution.

Reject or mark as `variant` if the track is good but too specific, too loud,
too musical, too repetitive, or likely to fatigue players.

## License Notes

For public distribution, only package tracks created while the account has an
active plan that grants commercial rights for newly generated outputs. Keep
subscription and generation-date proof outside the repo if needed. If a track
requires attribution, preserve it in `credit`.

Do not include free-plan, unknown-license, borrowed, or third-party audio in a
public Questforge release.

## Selection During Play

Questforge should select audio only when it helps sustained ambience:

- tavern, campfire, village, temple, library;
- forest, coast, river, swamp, snow, storm;
- cave, crypt, cell, ruins, puzzle door;
- ritual, threat, chase, battle, fire, portal.

Use the selector against the campaign-local approved library when it exists:

```powershell
python plugins\questforge\scripts\audio_library.py select `
  --library campaigns\the-amber-gate\audio\library.json `
  --tag tavern `
  --tag rain `
  --intensity 2 `
  --format args
```

For first-run play or challenge demos, use the bundled starter pack:

```powershell
python plugins\questforge\scripts\audio_library.py select `
  --library plugins\questforge\assets\audio\library.json `
  --tag dungeon `
  --tag exploration `
  --intensity 3 `
  --format args
```

The `args` output can be appended to `panorama_viewer.py`:

```powershell
python plugins\questforge\scripts\panorama_viewer.py `
  --image campaigns\the-amber-gate\images\assets\tavern-360.png `
  --output campaigns\the-amber-gate\images\viewers\tavern-360.html `
  --title "Rainy Tavern" `
  --narration "You step inside as rain taps the shutters." `
  --initial-zoom-level 14 `
  <audio args from audio_library.py>
```

For static images shown in chat, mention the ambience briefly if useful, but do
not force audio. For 360 viewers, use the speaker toggle and let the browser
remember the player preference.

## Public Pack Strategy

For the first challenge-ready release, ship a small approved pack instead of a large uncurated dump:

- 11 approved starter tracks in `assets/audio/starter-pack/`.
- 28 additional generated candidates kept locally under ignored `outputs/` for later review.
- clear `assets/audio/library.json` metadata for every public track.
- a note that the expanded atlas is in progress.

This keeps the playable entry lightweight while leaving room to grow before the
deadline.
