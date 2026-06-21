# Beta Fun Rubric

Questforge should not merely run a rules-compatible story. It should make the
player want one more scene.

Use this rubric after human or self-play beta sessions.

## Core Signals

Score each from 1 to 5.

| Signal | 1 Means | 5 Means |
| --- | --- | --- |
| Agency | The player waits for narration. | The player keeps proposing actions. |
| Clarity | The player asks what is possible. | The player sees several clear options. |
| Stakes | Outcomes feel cosmetic. | Choices change clocks, NPCs, maps, or resources. |
| Pace | Rules, images, or exposition interrupt play. | Rules and visuals appear when they help. |
| Wonder | The scene feels generic. | The player remembers a concrete image or detail. |
| Continuity | Resuming needs chat memory. | Files alone recover the next scene. |
| Fairness | Failure feels arbitrary. | Failure costs something and creates a new option. |
| Visual Value | Images are decorative. | Images clarify identity, space, inventory, or memory. |
| Narrative Diversity | Mysteries reuse the same AI-prone motifs. | Weirdness, mundane pressure, secrets, and consequences vary by scene. |

## Pass Bar

A beta session is promising when:

- agency, clarity, and continuity are at least 4;
- no category is below 3;
- the player can name their next intended action;
- at least one visual becomes a remembered anchor;
- at least one failure or complication makes the story more interesting;
- the player would continue for another 20 minutes.

## Red Flags

Fix before inviting more testers when:

- the player does not know what they can do next;
- images arrive so often that they break momentum;
- a map reveals secrets before the character earns them;
- the GM voice explains lore instead of framing pressure;
- rules lookup becomes a lecture;
- failed rolls stop the scene;
- NPCs lack wants, leverage, or tells;
- memory loss, sentient-object bargains, unsayable taboos, hidden rules,
  dreams, and prophecy pile up without concrete reasons or planned payoff;
- every clue points to the same symbolic answer instead of mixing motives,
  logistics, social pressure, and conflicting goals;
- most checks cluster in the same narrow DC band or reuse the same two
  modifiers without table-facing reason;
- campaign files cannot restart the next session cleanly.

## Analytics Review

After beta play, run:

```powershell
python plugins\codex-questforge\scripts\session_analytics.py analyze `
  --session-log campaigns\the-amber-gate\sessions\session-001.md `
  --visual-index campaigns\the-amber-gate\images\visual-index.md `
  --events campaigns\the-amber-gate\analytics\session-events.jsonl
```

Treat warnings as design prompts. A narrow DC range is not automatically wrong,
but repeated 12-15 checks can make play feel samey unless some scenes use easy
automatic progress, genuinely hard risks, escalating clocks, contests,
resource tradeoffs, or non-roll choices.

For the next session after a narrow-DC warning, use:

```powershell
python plugins\codex-questforge\scripts\dc_planner.py `
  --difficulty medium `
  --position normal `
  --approach clever `
  --recent-dc 13 `
  --recent-dc 14 `
  --recent-dc 14 `
  --recent-dc 13
```

Prefer clear anchors (`no roll`, `DC 10`, `DC 15`, `DC 20`, opposed roll) over
unexplained `DC 13` or `DC 14`.

## Narrative Diversity Review

Before a long beta session, run:

```powershell
python plugins\codex-questforge\scripts\narrative_lint.py `
  --file campaigns\the-amber-gate\opening-brief.md
```

Use warnings as prompts to revise, not as automatic failures. The goal is not
to ban memory magic, strange bargains, taboos, dreams, or secret rules. The
goal is to avoid letting them become the default answer to every mystery.

## Image Cadence Review

For an image-rich session, expect 4 to 6 generated visuals:

- opening location or recap;
- player character or important NPC;
- persistent item or clue;
- map, inventory, merchant board, or outfit when choices depend on layout;
- dramatic scene or spell beat;
- end-of-session postcard.

Generate fewer if the player is in fast dialogue or wants quick rulings. Generate
more only when the visuals become part of play: maps, items, outfits, merchants,
recaps, clue boards, or recurring NPC identity.

## Session Debrief

Ask the player:

- What was the best moment?
- What was the least clear moment?
- Which image helped most?
- Which image was unnecessary?
- What did you want to do next?
- Did any rule or roll feel unfair?
- Would you play another session?

Record the answers in `beta-feedback.md` inside the campaign folder.
