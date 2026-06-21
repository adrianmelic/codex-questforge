# Visual Playbook

Questforge should use native Codex/ChatGPT image generation as a game aid, not
as decoration. The goal is to fix shared imagination, preserve continuity, and
make choices easier to understand.

## Visual Cadence

Default cadence for an image-rich session:

- Generate an opening image when the first scene needs a strong shared mental picture.
- For a continued campaign, the first player-facing scene should also get an opening visual by default: generate a fresh establishing image or explicitly point to a still-current gallery image after setup/preflight/recap is complete.
- Generate the next frame when the fiction materially changes: a consequence lands, an NPC posture shifts, a clue is revealed, a new place opens, a spell or danger changes the room, or the player moves to a new vantage point.
- Generate reference assets for recurring characters, creatures, items, outfits, maps, locations, symbols, and important rewards.
- Generate comic pages when one player response spans multiple places, times, or actions.
- Generate maps, inventory boards, merchant boards, and 360 POVs when those formats improve decisions.

There is no default hard cap. If the user enjoys a visual-first game, keep generating when the fiction advances. Static images should appear once in the Codex conversation so mobile users can see them, while `images/visual-gallery.html` remains the desktop history and review surface. Generate less often only when the user asks for speed, asks a short rules question, or the beat is genuinely already covered by a recent useful image.

Default style should lean into immersive fantasy realism: grounded materials, clear staging, characterful faces, dramatic but plausible light, and high detail without unwanted film grain. Use a painterly, comic, parchment, tactical, or stylized look only when the format or campaign benefits from it.

## Format Classifier

Choose the format before prompting:

```powershell
python plugins\codex-questforge\scripts\visual_planner.py `
  --beat "<resolved player-facing beat>"
```

Use the returned plan as the source of truth for whether to generate, which
visual kind to save, whether to use the gallery, and which continuity checks
must be satisfied.

| Format | Use When | Avoid |
| --- | --- | --- |
| `single_scene` | One place, one moment, one main action. | Sequential actions or multiple rooms. |
| `comic-page` | Several places, times, or actions must fit one generated image. | Spatial inspection that needs one coherent POV. |
| `map_or_diagram` | Routes, exits, fog of war, relative positions, inventory boards. | Atmospheric illustration when labels or geometry matter. |
| `inventory_board` | Gear, loot, money, carried clues, burden, or visible conditions. | Dramatic action that needs a scene frame. |
| `merchant_board` | Buying, selling, bargaining, and comparing visible goods. | Hidden item stats or unknown prices. |
| `reference_plate` | A recurring NPC, creature, item, outfit, symbol, or location needs canon. | Live action that will not recur. |
| `pov-360` | The user wants to look around from the character's viewpoint. | Dialogue or action beats without spatial need. |

Use `scripts/comic_panels.py classify --summary "<beat>"` when unsure.
Sequential words like "after", "then", "while", "before", "returns",
"pays and eats", "enters and leaves", or several locations are a warning: do
not merge them into one physical scene. Use a comic page or split the visual.

## Pre-Session Visual Prep

For scenes likely to become visually important, prepare reference assets before
play. This mirrors human GM prep: characters, enemies, maps, locations, props,
rewards, and likely action beats are established before the player enters the
scene.

Use `visual_prep.py` with a spec such as `templates/visual-prep-spec.json` to
save reference prompts. Generate images from those prompts, register selected
assets, and mark accepted references as `canon`.

Session `0` is reserved for pre-session visual prep in `visual-index.md`.

## Visual Kinds

Use `templates/scene-image-prompt.md` for all visual kinds.

| Kind | Use When | Persist In |
| --- | --- | --- |
| `scene` | A dramatic action, reveal, spell, chase, or combat beat occurs. | Session log |
| `location` | A place becomes important enough to revisit. | Visual bible |
| `character` | A recurring PC or NPC enters or changes visibly. | Visual bible |
| `creature` | A monster or strange being needs a clear table image. | Session log |
| `item` | A clue, treasure, weapon, relic, or prop will recur. | Visual index and inventory |
| `spell` | A magical effect defines the moment or character identity. | Session log |
| `map` | Spatial choices matter. Use fog of war for unexplored areas. | Campaign state |
| `inventory` | The player needs a clear view of gear, loot, burden, or attunement. | Character sheet |
| `merchant` | Buying, selling, or bargaining involves several concrete options. | Session log |
| `outfit` | Character clothing, armor, disguise, or social presentation matters. | Visual bible |
| `symbol` | A faction mark, seal, omen, or sigil becomes important. | Visual bible |
| `recap` | The session ends on a memorable image. | Session log |
| `pov-360` | The user asks to look around or a location deserves first-person spatial immersion. | Viewer HTML and visual index |
| `comic-page` | One response spans several moments or places. | Visual index and session log |

## Local Visual Gallery

Use the local visual gallery as the campaign's live image board. After each selected native image is copied into `images/assets/` and registered in `images/visual-index.md`, refresh the gallery:

```powershell
python plugins\codex-questforge\scripts\visual_gallery.py `
  --campaign-root campaigns\<campaign-slug> `
  --title "<campaign title>"
```

The script writes `campaigns/<campaign-slug>/images/visual-gallery.html` and prints a `file:///` URL ending in `#latest`. The page is a chronological scroll log: older images at the top, newer images lower down, every image in a same-size frame, and one compact line such as `#35 · scene · Nela explica su olvido`. Saved prompts remain in campaign files rather than visible gallery controls. Matching 360 viewers render inline as interactive iframes instead of static images. If a panorama-like asset has no viewer yet, the gallery creates a default viewer under `images/viewers/`; if a matching `<asset-stem>-360.html` already exists, it links that viewer even when the label does not explicitly say 360. While the page is on `#latest`, it follows the latest image; when the player jumps to `#visual-<n>`, historical review stays stable.

For older campaigns that have panorama viewers outside the campaign folder, pass one or more extra viewer roots:

```powershell
python plugins\codex-questforge\scripts\visual_gallery.py `
  --campaign-root campaigns\<campaign-slug> `
  --viewer-root plugins\codex-questforge\outputs\panorama-viewers
```

Use the same gallery URL through the whole session. During visual-first play, still paste each selected static generated image once into the Codex conversation with Markdown so it works on mobile. Refresh the gallery after registration for desktop history and `#latest`. If `@Browser` is available, open or refresh that URL in the Codex in-app browser after important visual beats. If the current Browser surface refuses `file:///` navigation by policy, return the link and continue rather than interrupting play.

## Chat Image Surface

After a selected static image is saved or copied into `images/assets/`, show it in chat exactly once with an absolute-path Markdown image:

```markdown
![Short in-scene label](C:/path/to/campaign/images/assets/short-label.png)
```

Put the image near the resolved narrative beat, not in a separate debug block. Avoid duplicate thumbnails, raw prompt links, local path captions, or gallery-only instructions for that same static image. The gallery is still refreshed, but the chat image is the primary mobile surface.

For `pov-360`, return the local viewer link and optionally open it with `@Browser`; do not show the raw panorama as the main chat image unless the user asks for a flat preview.

## Comic Pages

Use `templates/comic-page-prompt.md` or `scripts/comic_panels.py prompt` when
one generated image should contain several moments. Use:

- 2 panels for simple sequences, such as paying at a room door and later eating
  downstairs.
- 4 panels for tactical movement, setup and payoff, or a small infiltration.
- 6 panels for chase, contravigilance, escape, or a complex chain of actions.

Comic pages must have clear gutters, ordered panels, no speech bubbles, no
readable captions, and no merged timelines. Reject the image if characters or
objects from different moments are collapsed into one impossible room.

## POV 360 Viewer

For important first-person spaces, ask native image generation for an
equirectangular 360 panorama. Then create a standalone local viewer:

```powershell
python plugins\codex-questforge\scripts\panorama_viewer.py `
  --image <generated-360.png> `
  --output campaigns\<campaign-slug>\images\viewers\<label>-360.html `
  --title "<scene title>" `
  --narration "<short in-scene narration>" `
  --initial-zoom-level 14
```

The script embeds the image in the HTML, prints a `file:///` `viewer_url`, and
does not need a local server. Return that URL as a Markdown link. If `@Browser`
is available, open the URL there so the user can drag to look around and zoom.
If WebGL renders blank in the current browser, the viewer falls back to a flat
panorama with drag and zoom. Keep visible text immersive: use a short excerpt
from the current scene, not paths, filenames, prompt notes, or implementation
details. Use zoom levels from 1 to 22; higher values start wider. Level 14 is
the default because it gives a broader first view while still leaving room to
zoom into details.

For long-lived first-person scenes, the viewer can embed one ambient loop:

```powershell
python plugins\codex-questforge\scripts\panorama_viewer.py `
  --image <generated-360.png> `
  --output campaigns\<campaign-slug>\images\viewers\<label>-360.html `
  --title "<scene title>" `
  --narration "<short in-scene narration>" `
  --initial-zoom-level 14 `
  --audio <loop.mp3> `
  --audio-title "<track title>" `
  --audio-volume 0.24
```

The loop should not play for a new user by default. The viewer exposes a small
speaker toggle and stores the user's last preference locally, so later
panorama viewers can try to keep ambience enabled. Browser autoplay rules may
still require one user click, drag, or keypress before the remembered track can
resume. Keep the default volume low enough to sit under narration.

## Ambient Audio Library

Campaigns may keep a local `audio/library.json` so Codex can choose loops by mood. If a campaign has no local library yet, use the bundled starter pack at `plugins/codex-questforge/assets/audio/library.json`. Store campaign-local paths relative to the campaign root and keep license notes with the track:

```json
{
  "tracks": [
    {
      "label": "quiet-tavern",
      "title": "Quiet Tavern",
      "path": "audio/quiet-tavern.mp3",
      "moods": ["tavern", "safe", "conversation", "rain"],
      "intensity": 2,
      "license": "commercial-use-generated-for-this-project",
      "credit": "Generated by the user"
    }
  ]
}
```

When generating a panorama viewer, choose one loop whose mood and intensity match the scene. Use tavern or safe-conversation music for inns, wilderness for travel or camps, dungeon for exploration pressure, ritual for ominous magic, combat for danger, and aftermath for quiet consequences. Prefer campaign-local audio for custom campaigns; use the bundled starter pack for first-run play or challenge demos.

## Persistence Rules

Before requesting native image generation:

1. Plan the beat with `visual_planner.py`.
2. Satisfy its continuity requirements from `images/visual-ledger.md` and
   relevant canon anchors.
3. Save the prompt with `campaign_memory.py save-visual-prompt`.
4. Register recurring details in `visual-bible.md` or `visual-index.md`.
5. If the visual represents an item, clue, map, outfit, or faction symbol,
   reference it from campaign state or the character sheet.
6. Treat generated images as continuity anchors. If later fiction contradicts a
   generated image, explicitly update the visual bible.

After native image generation:

1. Copy the selected image into `images/assets/`.
2. Register it in `visual-index.md`:

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py register-visual-asset `
  --campaign-root campaigns\<campaign-slug> `
  --asset-path images\assets\<asset-name>.png `
  --kind <kind> `
  --label "<label>" `
  --session <n> `
  --scene <n>
```

If the selected native image is still outside the campaign folder, use
`--asset-source` and let the script copy it into `images/assets/`:

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py register-visual-asset `
  --campaign-root campaigns\<campaign-slug> `
  --asset-source <generated-image.png> `
  --asset-filename <asset-name>.png `
  --kind <kind> `
  --label "<label>" `
  --session <n> `
  --scene <n>
```

Then refresh the gallery:

```powershell
python plugins\codex-questforge\scripts\visual_gallery.py `
  --campaign-root campaigns\<campaign-slug>
```

Keep generated images out of git unless the project explicitly wants to publish
sample media. For local beta runs, store them under an ignored output folder or
inside the local campaign workspace.

## Visual Ledger

Use `images/visual-ledger.md` to track visible states that must persist across
prompts: bandaged hands, disguises, current outfit, carried clues, item scale,
faction marks, room layout, weather, or damage. Every prompt involving a
recurring element should include the relevant ledger state and avoid regressing
it unless the fiction changed it.

## Live Reuse Loop

Use the campaign's visual library when a recurring character, creature, item,
map, or location appears again.

List reusable canon anchors:

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py list-visual-assets `
  --campaign-root campaigns\<campaign-slug> `
  --status canon `
  --format markdown
```

Create a new scene-frame prompt from those anchors:

```powershell
python plugins\codex-questforge\scripts\visual_reuse.py `
  --campaign-root campaigns\<campaign-slug> `
  --session <n> `
  --scene <n> `
  --label "<scene label>" `
  --action "<what the player-facing moment shows>" `
  --roll "<actual roll or check, if any>" `
  --outcome "<resolved table outcome, if any>" `
  --anchor-label "<canon label>" `
  --require-asset
```

Repeat `--anchor-label` for each recurring visual element. After native image
generation, compare the result against the anchors and mark the scene as
`canon`, `variant`, or `rejected`. Most live action frames should stay
`asset-saved` or `variant`; reserve `canon` for images that will become future
references. If a scene follows a roll, the prompt must preserve the actual
roll outcome rather than restaging it as a cleaner success or failure.

Visual statuses:

- `prompt-saved`: prompt exists, no selected image yet.
- `asset-saved`: selected image exists and is registered.
- `canon`: accepted as a future prompt reference.
- `variant`: useful alternate, not primary canon.
- `rejected`: do not reuse.

## Continuity Review

Review each generated image before treating it as canon:

- Does it preserve known character scale, ancestry, outfit, tools, and pose
  language?
- Does it preserve active visible states from `images/visual-ledger.md`, such
  as bandages, disguises, wounds, carried items, or object size?
- Does a recurring NPC, creature, item, symbol, or location match prior visual
  anchors closely enough?
- Does one physical scene contain only one place and moment, or is it clearly a
  comic page with separate panels?
- Does a map reveal only what the character has discovered?
- Does an action scene reuse the established creature or object design, rather
  than inventing a new silhouette?
- Does the image help the next decision, or is it only decorative?

Composite scenes are the highest drift risk. When generating a scene that
includes a previously generated creature, item, or location, include those
anchors explicitly in the prompt and compare the result against the earlier
asset before saving it as canon.

## Fog-Of-War Maps

For maps:

- Show only explored rooms, known paths, obvious exits, and landmarks.
- Hide unexplored areas with parchment shadow, mist, collapsed ink, or unlabeled
  blank space.
- Do not reveal secret rooms, hidden doors, enemy counts, or trap mechanisms
  unless the characters have discovered them.
- Keep labels sparse and table-useful.

## Merchant And Inventory Diagrams

For merchants:

- Show item groups, price tags, visible quality, and the merchant's personality.
- Do not imply hidden mechanical stats unless they are known.

For inventory:

- Show current weapons, armor, consumables, clues, currency, and strange items.
- Separate equipped, carried, stored, and newly found items when useful.
- Preserve recurring item appearance from `visual-index.md`.

## Copyright Boundary

Visual prompts must remain original fantasy. Do not ask for official D&D art
style, official logos, named settings, named characters, commercial adventure
maps, or copied product art.

Audio must follow the same distribution discipline: do not commit or package
tracks without rights for the intended use. For local play, user-provided files
are fine; for publishing the plugin, include only loops with license terms that
allow redistribution or document that users must provide their own audio.
