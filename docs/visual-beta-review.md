# Visual Beta Review: Rootbound Vault

Date: 2026-05-17

Scenario: `Rootbound Vault Alpha`

Visual run:

- 5 native images generated as separate assets.
- Assets copied into the local ignored playtest workspace under
  `plugins/codex-questforge/outputs/visual-beta-rootbound/`.
- `images/visual-index.md` updated from `prompt-saved` to `asset-saved` for
  all five visual beats.

## Asset Review

| Asset | Table Value | Continuity Notes | Verdict |
| --- | --- | --- | --- |
| Rootbound Vault Fog Map | Strong spatial aid. Shows known entry, root door, water, moss route, blocked route, and heavy fog. | Decorative border marks are fine because they are not usable labels. It does not expose secret rooms or enemies. | Keep |
| Living Root Door | Strong location anchor. The water channel and root lattice make approach choices concrete. | Matches the map and reinforces the green-fire palette. | Keep |
| Green Fire Seed | Excellent persistent object. It clearly reads as tempting, magical, and dangerous. | Good match for root hollow and green glow. | Keep |
| Bramble Sentinel | Strong creature anchor. Clear silhouette, cracked stone mask, thorn body, and green eyes. | Good enough to reuse as the sentinel's canonical look. | Keep |
| Moss Path Chase | Best drama image. It makes the failed roll feel exciting and keeps the escape route visible. | Minor drift risk: Tamsin reads a little elf-like rather than clearly halfling, and the sentinel mask differs slightly from the creature asset. Future prompts should restate scale and prior creature anchors. | Keep with note |

## What Improved Play

- The map made the player's movement choices easier to understand.
- The door and seed gave the dungeon a memorable visual identity before danger
  appeared.
- The sentinel gave the threat a concrete silhouette without exposing rules.
- The chase image made failure feel active rather than punitive.
- Separate assets were more useful than a collage because they can be reused in
  session logs, inventory/state, and future prompts.

## What To Adjust

- Register generated PNGs in `visual-index.md` immediately after selecting them.
- When generating a later scene that includes prior assets, quote the prior
  visual anchors explicitly.
- For small ancestries or unusual character scale, state scale in relation to
  the environment or creature.
- Review composite scenes for drift before treating them as campaign canon.

## Prompt Lesson

For follow-up action scenes, use language like:

```text
Preserve the established Bramble Sentinel design: humanoid braided thorn body,
green ember eyes, cracked pale stone mask, wet root armor silhouette. Preserve
Tamsin Reed as a small halfling delver, clearly shorter than a human, in
practical dark travel gear. Keep the safe moss path visible.
```
