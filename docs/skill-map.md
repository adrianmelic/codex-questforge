# Skill Map

Questforge is a plugin made of several skills. Users normally invoke only
`questforge`; the other skills are specialized modes used by the orchestrator.

| Skill | Role | Trigger |
| --- | --- | --- |
| `questforge` | Main orchestrator for play. | Start, continue, prep, or play a campaign. |
| `questforge-setup` | First-run setup and SRD data. | Missing `.questforge`, language, PDF, indexes, licensing. |
| `questforge-rules` | Rules lookup and rulings. | DCs, checks, saves, advantage, disadvantage, dice, house rules. |
| `questforge-campaign` | Campaign memory. | Campaign creation, session logs, state patches, clocks, NPCs, inventory. |
| `questforge-save` | Portable and cloud saves. | Meaningful-turn autosave, exact-folder cloud sync, cross-device resume, conflicts, migration, ZIP export. |
| `questforge-puzzles` | Non-blocking deduction beats. | Clue connections, symbolic minigames, route logic, social contradictions. |
| `questforge-visuals` | Native visual generation. | Visual planning, scene images, maps, items, inventory, merchants, outfits, comic pages, 360 viewers, local gallery, visual continuity. |

## Preferred Invocation

Users should be able to say:

> I want to play @questforge.

The orchestrator should then:

1. Check setup through `questforge-setup`.
2. Create or load campaign memory through `questforge-campaign`.
3. Verify the initial local snapshot and use `questforge-save` after each meaningful state change; offer cloud storage only after play begins and only as an opt-in path.
4. Run play, using `questforge-rules`, `questforge-puzzles`, and `questforge-visuals` as needed.
5. End sessions by compacting continuity, writing state changes, and verifying the final canonical save.

## Design Rule

Keep `questforge` small and table-facing. Move operational details into the
specialized skills so Codex can stay focused while playing.
