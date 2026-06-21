# Skill Map

Codex Questforge is a plugin made of several skills. Users normally invoke only
`questforge`; the other skills are specialized modes used by the orchestrator.

| Skill | Role | Trigger |
| --- | --- | --- |
| `questforge` | Main orchestrator for play. | Start, continue, prep, or play a campaign. |
| `questforge-setup` | First-run setup and SRD data. | Missing `.questforge`, language, PDF, indexes, licensing. |
| `questforge-rules` | Rules lookup and rulings. | DCs, checks, saves, advantage, disadvantage, dice, house rules. |
| `questforge-campaign` | Campaign memory. | Campaign creation, session logs, state patches, clocks, NPCs, inventory. |
| `questforge-puzzles` | Non-blocking deduction beats. | Clue connections, symbolic minigames, route logic, social contradictions. |
| `questforge-visuals` | Native visual generation. | Visual planning, scene images, maps, items, inventory, merchants, outfits, comic pages, 360 viewers, local gallery, visual continuity. |

## Preferred Invocation

Users should be able to say:

> Use Codex Questforge to start a campaign.

The orchestrator should then:

1. Check setup through `questforge-setup`.
2. Create or load campaign memory through `questforge-campaign`.
3. Run play, using `questforge-rules`, `questforge-puzzles`, and
   `questforge-visuals` as needed.
4. End sessions by writing state changes to files.

## Design Rule

Keep `questforge` small and table-facing. Move operational details into the
specialized skills so Codex can stay focused while playing.
