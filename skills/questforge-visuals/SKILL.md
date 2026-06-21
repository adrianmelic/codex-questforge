---
name: questforge-visuals
description: Use native Codex image generation as a Questforge table aid for scenes, objects, maps, inventory, merchants, outfits, symbols, and recap visuals with persistent visual memory.
---

# Questforge Visuals

Use this skill when a visual would clarify the shared imagination, preserve an
important object or location, help spatial decisions, or make inventory/trade
easier to understand.

## Format Choice

Before generating, plan the visual beat:

```powershell
python ../../scripts/visual_planner.py --beat "<resolved player-facing beat>"
```

Use the returned `format`, `kind`, `continuity_requirements`, and `next_steps`.
If `should_generate` is false, answer in chat and skip image generation.
If `should_generate` is true, satisfy the continuity requirements before
requesting native image generation.

The planner chooses among:

- `single_scene`: one location, one moment, one main action.
- `comic-page`: two or more places, times, or actions in one response.
- `map`: spatial decisions, routes, exits, fog of war, or tactical planning.
- `inventory`: current gear, loot, money, burden, or carried clues.
- `merchant`: buy/sell comparison boards.
- `reference_plate`: recurring character, object, outfit, creature, or place.
- `pov-360`: first-person spatial immersion.

Use `../../scripts/comic_panels.py classify --summary "<beat>"` when unsure. If
the beat contains "después", "luego", "mientras", "antes de", "vuelve",
"camino a", "paga y desayuna", "entra y sale", or several locations, do not
request a single naturalistic scene unless the user explicitly asks for it.

## Cadence

For image-rich play, generate a visual for important turns where the fiction
changes: decision consequences, dialogue turns with new posture or leverage,
reveals, movement, danger, spell effects, item discoveries, maps, and scene
transitions. Skip images for brief rules questions, quick clarifications, purely
mechanical back-and-forth, or beats already covered by a recent useful image.

At the start of a new or continued session, the first player-facing scene should have a visual by default. After setup, preflight, file loading, or recap is complete, either generate and register a fresh establishing image for the current scene or explicitly point to a still-current gallery image. Do not let the first actionable scene be text-only unless the user asks for speed, the turn is only out-of-character setup, or no in-fiction scene has started yet.

Do not set a hard image cap by default. If the user enjoys a visual-first game,
keep generating scene frames as the fiction advances. Static generated images
should appear once in the Codex conversation so mobile users can see them, and
they should also be registered in the local gallery for desktop history and
review. Do not paste duplicate thumbnails or extra file links for the same
static image. Use fewer images only when the user asks for speed, is asking
rules questions, or is clearly trying to move quickly.

Default visual style should be immersive fantasy realism: grounded materials,
clear staging, dramatic but plausible light, and no unwanted film grain. Use a
different style only when the campaign has already established one or the user
asks for it.

## Local Gallery

Use one stable local gallery per campaign as the desktop visual board and
history. After each saved and registered native image, refresh it:

```powershell
python ../../scripts/visual_gallery.py --campaign-root <campaign-root> --title "<campaign title>"
```

The script writes `<campaign-root>/images/visual-gallery.html`, prints a
`file:///` URL ending in `#latest`, and renders a chronological scroll log:
older images at the top, newer images lower down, with every image in a stable
same-size frame and one compact line such as `#35 · scene · Nela explica su
olvido`. Panorama/360 entries are embedded as interactive viewer iframes in
the gallery, not static images. If a panorama-like asset has no viewer yet, the
gallery creates a default local viewer under `images/viewers/`. Return that URL
as a Markdown link when useful. If `@Browser` is
available, open or refresh that same URL in the in-app browser so the player
can keep the gallery beside the story.
When the page is on `#latest`, it follows the latest image while visible. If
the player jumps to `#visual-<n>`, it stops following so historical review is
stable.
If the current Browser surface refuses `file:///` navigation by policy, return
the link and continue; do not spend play time on browser workarounds.

For `pov-360` assets, create the panorama viewer first under
`<campaign-root>/images/viewers/`, then refresh the gallery. Matching 360
viewers are linked from the selected gallery item. Older entries that were
saved as `location` still link when their label or asset name clearly contains
`360`, `panorama`, or `panoramico`; the gallery also links existing matching
viewer filenames such as `<asset-stem>-360.html`. Use `--viewer-root` for
legacy viewer folders outside the campaign.

## Chat Image Surface

For every useful static generated image (`scene`, `location`, `character`,
`creature`, `item`, `spell`, `map`, `inventory`, `merchant`, `outfit`,
`symbol`, `recap`, and `comic-page`), show the selected image once in the
conversation after it has been saved or copied into `images/assets/`. Use
standard Markdown with an absolute filesystem path:

```markdown
![Nela explains her lost memory](C:/path/to/campaign/images/assets/nela-memory.png)
```

Keep the nearby text short: narrate the scene normally, then show the image, or
show the image after the consequence paragraph. Do not also return a separate
`Image` button, prompt link, local file path, or gallery-only instruction for
that same static image unless the user asks for debugging details. Continue to
refresh the local gallery in the background for history and desktop play.

For `pov-360`, return the local viewer link and optionally open it with
`@Browser`; do not treat the raw panorama as the main chat image unless the
user explicitly asks for a flat preview.

## Pre-Session Prep

For important scenes, prepare visuals before live play. Use this for recurring
characters, NPCs, enemies, maps, locations, persistent items, rewards, symbols,
outfits, and likely action beats.

Create reference prompts from a spec:

```powershell
python ../../scripts/visual_prep.py --campaign-root <campaign-root> --spec ../../templates/visual-prep-spec.json
```

Then generate native images from the saved prompts, register selected PNGs, and
mark accepted references as `canon`. Use session `0` for pre-session reference
assets. See `../../docs/visual-prep-workflow.md`.

## Live Reuse

Before generating a scene with recurring visual elements, list usable canon
anchors:

```powershell
python ../../scripts/campaign_memory.py list-visual-assets --campaign-root <campaign-root> --status canon --format markdown
```

Create live scene-frame prompts from the relevant anchors instead of rewriting
continuity by hand:

```powershell
python ../../scripts/visual_reuse.py --campaign-root <campaign-root> --session <n> --scene <n> --label "<scene label>" --action "<player-facing action>" --roll "<actual roll or check>" --outcome "<resolved table outcome>" --anchor-label "<canon label>" --require-asset
```

Use repeated `--anchor-label` values for multiple anchors. If a reviewed image
is useful but not canonical, use `--anchor-status variant` intentionally and
state why in the prompt or session log. When a visual follows a roll, include
the actual roll and outcome so the image prompt cannot contradict the table.

Also check `images/visual-ledger.md` and preserve active visible states such as
bandaged hands, disguises, carried objects, object scale, faction marks, and
stable room layouts. Do not regress a visible state unless the fiction changes
it.

For visual-first play, every generated prompt must either use `visual_reuse.py`
with relevant anchors or explicitly include the active visual ledger and explain
why no existing canon anchor applies.

## POV 360

When the user asks to look around, inspect a scene from the character's point of
view, enter an important location, or would benefit from spatial immersion,
request a native equirectangular 360 panorama. After generation, create a local
viewer:

```powershell
python ../../scripts/panorama_viewer.py --image <generated-360.png> --output <campaign-root>/images/viewers/<label>-360.html --title "<scene title>" --narration "<short in-scene narration>" --initial-zoom-level 14
```

Return the `viewer_url` as a Markdown link. If `@Browser` is available, open
that `file:///` URL there. The viewer is standalone and does not require a local
server. Use narration text from the current scene instead of technical labels or
file paths.

For sustained ambience, add one licensed or user-provided loop. Prefer a campaign-local approved library at `<campaign-root>/audio/library.json`; if it does not exist, use the bundled starter pack at `../../assets/audio/library.json`. Select by scene tags before creating the viewer:

```powershell
python ../../scripts/audio_library.py select --library <campaign-root>/audio/library.json --tag tavern --tag rain --intensity 2 --format args
```

Fallback example:

```powershell
python ../../scripts/audio_library.py select --library ../../assets/audio/library.json --tag dungeon --tag exploration --intensity 3 --format args
```

Append the returned arguments to the panorama viewer command:

```powershell
python ../../scripts/panorama_viewer.py --image <generated-360.png> --output <campaign-root>/images/viewers/<label>-360.html --title "<scene title>" --narration "<short in-scene narration>" --initial-zoom-level 14 --audio <loop.mp3> --audio-title "<track title>" --audio-volume 0.24
```

Choose audio only for scenes where ambience helps: tavern, wilderness, dungeon, ritual, chase, combat, dream, travel, or aftermath. Prefer campaign-specific loops when present, otherwise use the bundled starter pack. The viewer embeds the selected loop and exposes a small speaker toggle. Do not start music for a new user by default. If the user enabled audio in a prior viewer, the next viewer should remember that preference and resume when the browser allows playback.

## Visual Kinds

Use these kinds with `save-visual-prompt`:

- `scene`
- `location`
- `character`
- `creature`
- `item`
- `spell`
- `map`
- `inventory`
- `merchant`
- `outfit`
- `symbol`
- `recap`
- `pov-360`
- `comic-page`

Build prompts from `../../templates/scene-image-prompt.md` and guidance in
`../../docs/visual-playbook.md`. For `comic-page`, use
`../../templates/comic-page-prompt.md`.

## Persistence

Before requesting native image generation, save the prompt:

```powershell
python ../../scripts/campaign_memory.py save-visual-prompt --campaign-root <campaign-root> --session <n> --scene <n> --kind <kind> --label "<label>" --prompt "<prompt>"
```

Then request native Codex/ChatGPT image generation if available. Do not call
image API scripts or use `OPENAI_API_KEY` unless the user explicitly asks to use
the API.

After generation, copy the selected image into `images/assets/` and register it:

```powershell
python ../../scripts/campaign_memory.py register-visual-asset --campaign-root <campaign-root> --asset-path images/assets/<asset-name>.png --kind <kind> --label "<label>" --session <n> --scene <n>
```

Refresh the gallery after registration:

```powershell
python ../../scripts/visual_gallery.py --campaign-root <campaign-root>
```

If native image generation saved the PNG outside the campaign workspace, let
Questforge copy it:

```powershell
python ../../scripts/campaign_memory.py register-visual-asset --campaign-root <campaign-root> --asset-source <generated-image.png> --asset-filename <asset-name>.png --kind <kind> --label "<label>" --session <n> --scene <n>
```

To mark a reviewed reference as canonical:

```powershell
python ../../scripts/campaign_memory.py set-visual-status --campaign-root <campaign-root> --kind <kind> --label "<label>" --session <n> --scene <n> --status canon
```

Persist recurring details:

- characters, outfits, locations, symbols in `visual-bible.md`;
- item, map, merchant, inventory, and recap prompts in `images/visual-index.md`;
- object or clue references in `campaign-state.md` or character sheets.

Review generated images before treating them as canon. Composite action scenes
drift most easily, so explicitly reuse prior anchors for characters, creatures,
items, maps, and locations, then compare the result with earlier assets.
Use `visual_reuse.py` for those composite scenes when canon anchors already
exist.

Valid statuses are `prompt-saved`, `asset-saved`, `canon`, `variant`, and
`rejected`.

## Fog Of War

For maps:

- show only explored or known areas;
- hide secret rooms, hidden doors, enemy counts, trap mechanisms, and unexplored
  paths;
- use parchment shadow, mist, blank space, or unlabeled boundaries for unknown
  areas;
- keep labels sparse and table-useful.

## Copyright Boundary

Prompt only for original fantasy imagery. Do not request official D&D style,
official logos, named settings, named characters, commercial adventure maps, or
copied product art.

Use only audio loops that the user owns, generated for the project, or whose
license permits the intended local or redistributed use. Do not commit or
package music without clear license notes and required attribution.
For Suno-generated project audio, only package tracks generated while the
account has an active commercial-rights plan. Keep unreviewed candidates out of
the public audio library. See `../../docs/sound-atlas.md`.
