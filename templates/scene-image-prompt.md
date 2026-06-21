# Visual Prompt

Use this structure when asking for native Codex/ChatGPT image generation.

```text
Original 5E-compatible fantasy campaign visual, unofficial and not using any
official D&D setting, logo, product art, or named copyrighted character.

Kind: <scene | location | character | creature | item | spell | map | inventory | merchant | outfit | recap | symbol | pov-360 | comic-page>.
Purpose: <why this visual helps play right now>.
Subject: <what must be shown clearly>.
Context: <location, time, weather, social situation, or encounter state>.
Characters: <names, visual continuity details, poses, visible emotions, if any>.
Object continuity: <important shape, material, markings, damage, owner, if any>.
Map/diagram constraints: <known areas, hidden areas, labels, fog of war, if any>.
Action: <the moment of decision or consequence, if any>.
Mood: <tone from the campaign visual bible>.
Style: <medium/rendering/camera from the visual bible>.
Composition: <foreground, midground, background, focal point>.
Continuity constraints: <recurring colors, gear, scars, symbols, landmarks>.
Avoid: official logos, official setting identifiers, copied product art,
modern anachronisms unless established by the campaign.
```

For `pov-360`, ask for an equirectangular 360 panorama from the character's eye
level with no text, no UI, and no embedded labels. Save the generated PNG, then
build a viewer with `scripts/panorama_viewer.py`.

For `comic-page`, use `templates/comic-page-prompt.md`. Use it when one answer
covers several places, times, or actions that should not be merged into a
single physical scene.
