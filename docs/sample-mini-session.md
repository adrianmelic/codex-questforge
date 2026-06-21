# Sample Mini-Session

This is a compact target experience for Codex Questforge. It is not official
D&D content and does not use an official setting, official characters, official
art, or commercial rulebook text.

## Setup

Campaign: The Amber Gate  
Tone: heroic mystery with eerie ruins  
Boundary: no graphic gore  
Hero: Mara Vey, human ranger, level 1  
Rolling: Codex rolls in the open

## Opening

The rain has turned the old pilgrim road into black glass. Ahead, a bridge of
greenish stone crosses a gorge where stormwater boils far below. Three lanterns
burn on the far side even though no one is holding them.

Brother Caldus, the village archivist, clutches a sealed copper tube against
his chest. "The gate under the abbey opened at moonrise. Something inside it is
answering prayers it should not understand."

Before Mara can reply, one lantern lifts from its hook and swings toward the
gorge, as if carried by an invisible hand. A child's voice whispers from the
rain: "Bring me the map, and I will give back the bell-ringer."

Immediate choice: secure the archivist, pursue the lantern, inspect the bridge,
or answer the voice.

## Meaningful Roll

Mara wants to read tracks and wind patterns to learn whether the lantern is a
creature, a spell, or a trick.

Codex ruling:

- Check: Wisdom (Survival)
- DC band: moderate, because the storm is actively erasing evidence.
- Stakes: success reveals what moved the lantern; failure reveals the truth
  late enough that the threat advances.

Example roll:

```powershell
python plugins\codex-questforge\scripts\roll_dice.py d20+4 --seed 9
```

Example result:

```text
1d20+4 (normal): [15] + 4 = 19
```

Outcome: Mara sees that the lantern did not move through the rain. The rain
bent around it. That means the carrier is not invisible; it is out of phase
with the road, walking a parallel ruin that overlaps this bridge.

State changes:

- Clue added: "The Amber Gate overlays ruined places onto the present."
- Clock advanced: Abbey Gate 1/6, because the whisper has noticed Mara.
- NPC attitude changed: Brother Caldus trusts Mara's judgment.

## Native Visual Prompts

Save this location prompt before requesting native image generation:

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py save-visual-prompt `
  --campaign-root campaigns\the-amber-gate `
  --session 1 `
  --scene 1 `
  --kind location `
  --label "Gorge Bridge" `
  --prompt "Original 5E-compatible fantasy campaign scene, unofficial and not using any official D&D setting, logo, product art, or named copyrighted character. Scene: a ranger and an anxious archivist stand on a rain-slick green stone bridge as three amber lanterns glow across a storm gorge. Location: abandoned pilgrim road, midnight rain, ruined abbey silhouettes in the distance. Characters: Mara Vey, practical human ranger in a dark travel cloak with a bow wrapped against the rain; Brother Caldus, elderly archivist clutching a copper map tube. Action: one lantern floats sideways toward the gorge while rain bends around an unseen overlapping ruin. Mood: heroic mystery, eerie but not grim. Style: painterly fantasy realism, cinematic wide shot, readable staging, cool storm palette with warm amber lights. Avoid: official logos, official setting identifiers, copied product art, gore, modern objects."
```

Also save a persistent item prompt:

```powershell
python plugins\codex-questforge\scripts\campaign_memory.py save-visual-prompt `
  --campaign-root campaigns\the-amber-gate `
  --session 1 `
  --scene 1 `
  --kind item `
  --label "Copper Map Tube" `
  --prompt "Original 5E-compatible fantasy campaign item, unofficial and not using official D&D product art. Subject: a sealed copper map tube clutched by Brother Caldus. Object continuity: aged copper cylinder, amber wax seal, thin pilgrim-road etching, small dent near one cap, leather cord. Purpose: persistent clue and inventory object. Style: painterly fantasy realism, isolated prop view on dark wet stone, readable details. Avoid: official logos, copied product art, modern objects."
```

Then Codex should request native image generation from the integrated product
surface if available. It should not call image API scripts.

## Session Close

End state to write into the session log:

- Party position: west side of the gorge bridge.
- Immediate next choice: cross, parley with the whisper, or force the lantern
  back into phase.
- Changed clock: Abbey Gate 1/6.
- Changed NPC attitudes: Brother Caldus now trusts Mara.
- Rewards: clue about overlapping ruins.
- Resources: no damage, no spent ammunition.

The next session can start with Mara deciding whether to step into the parallel
ruin or keep one foot in the rain-soaked present.
