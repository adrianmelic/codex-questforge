# Visual Prep Workflow

Questforge should prepare important visuals before play the same way a human GM
prepares maps, NPCs, enemies, props, and scene references.

The goal is to create canon visual anchors first, then use those anchors during
live play to generate scene frames that feel consistent with the campaign.

## When To Prep

Use pre-session visual prep when a scene is likely to include:

- a recurring player character, NPC, or enemy;
- a location that the player will revisit;
- a map where spatial decisions matter;
- a persistent object, reward, symbol, outfit, or inventory state;
- action scenes that should reuse established designs.

Skip prep when the session is mostly conversation, travel, or quick rules
resolution.

## Prep Flow

1. Write or adapt a visual prep spec.
2. Run `visual_prep.py` to save reference prompts.
3. Generate native images from those prompts.
4. Register selected PNGs with `register-visual-asset`.
5. Mark accepted references as `canon`.
6. During play, list canon anchors and create scene-frame prompts with
   `visual_reuse.py`.
7. Mark useful alternatives as `variant` and broken images as `rejected`.

Example:

```powershell
python plugins\codex-questforge\scripts\visual_prep.py `
  --campaign-root campaigns\rootbound-vault `
  --spec plugins\codex-questforge\templates\visual-prep-spec.json
```

After image generation:

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py register-visual-asset `
  --campaign-root campaigns\rootbound-vault `
  --asset-source <generated-image.png> `
  --asset-filename bramble-sentinel-reference.png `
  --kind creature `
  --label "Bramble Sentinel Reference Sheet" `
  --session 0 `
  --scene 2 `
  --status canon
```

If the asset was already registered and later reviewed:

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py set-visual-status `
  --campaign-root campaigns\rootbound-vault `
  --kind creature `
  --label "Bramble Sentinel Reference Sheet" `
  --session 0 `
  --scene 2 `
  --status canon
```

Before a live visual beat, list the reusable library:

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py list-visual-assets `
  --campaign-root campaigns\rootbound-vault `
  --status canon `
  --format markdown
```

Then build a scene-frame prompt from specific anchors:

```powershell
python plugins\codex-questforge\scripts\visual_reuse.py `
  --campaign-root campaigns\rootbound-vault `
  --session 1 `
  --scene 4 `
  --label "Tamsin Marks The Safe Moss Path" `
  --action "Tamsin marks the safe moss path with chalk while the Bramble Sentinel pushes through the root door." `
  --roll "Dexterity check DC 15: 17" `
  --outcome "success with a noisy complication" `
  --anchor-label "Tamsin Reed Reference Sheet" `
  --anchor-label "Bramble Sentinel Reference Sheet" `
  --require-asset
```

## Recommended Prep Assets

| Asset | Use |
| --- | --- |
| `character-reference-sheet` | Front, back, three-quarter, expression, and typical action for a PC or recurring NPC. |
| `creature-reference-sheet` | Full silhouette, face/mask, attack or movement pose, scale cue. |
| `location-plate` | Establishing view, approach route, lighting, and one key detail. |
| `prop-sheet` | Persistent item, reward, key, clue, letter, weapon, or symbol. |
| `map-fog-of-war` | Known layout only, with secrets hidden until discovered. |
| `scene-frame` | A live-play moment generated from canon anchors. |

## Scene Frame Prompt Pattern

When generating a live action frame, include the relevant canon anchors:

```text
Preserve the established Bramble Sentinel canon: humanoid braided thorn body,
green ember eyes, cracked pale stone mask, wet root armor silhouette.
Preserve Tamsin Reed canon: small halfling delver, practical dark travel gear,
chalk pouch, careful posture, clearly shorter than a human.
Scene: Tamsin marks a safe moss path while the sentinel pushes through roots.
Keep the safe route visible and do not reveal unexplored rooms.
```

Prefer generating this pattern with `visual_reuse.py` once the anchors are in
`images/visual-index.md`. The script reads the original prompt summaries,
includes registered asset paths, and saves the new scene prompt back into the
campaign index for review after native image generation.

## Canon Statuses

Use these statuses in `images/visual-index.md`:

- `prompt-saved`: prompt exists, no selected image yet.
- `asset-saved`: a PNG exists and is registered.
- `canon`: accepted as a reference for future prompts.
- `variant`: useful alternate, not the main reference.
- `rejected`: do not use; breaks continuity or quality bar.

Do not treat a generated image as canon until it has been reviewed for
continuity, usefulness, and spoiler safety.
