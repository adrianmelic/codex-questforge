# Self-Play Protocol

Codex can test Questforge by simulating both sides of a short session: one
assistant instance acts as DM, and a second persona acts as a simple player.
The goal is not to "win" but to verify that the plugin produces a playable loop.

## Roles

- DM: follows `skills/questforge/SKILL.md`, uses campaign memory, makes rulings,
  saves visual prompts, and updates state.
- Player: chooses plausible actions, asks for clarifications, and occasionally
  makes risky choices.

## Required Test Beats

Run a 10- to 15-turn mini-session with:

1. Auto-language setup or a mocked `.questforge` setup.
2. New campaign workspace.
3. Opening scene with a choice.
4. At least one rules lookup or ruling.
5. At least one visible dice roll.
6. At least one hook status in `dm/adventure-spine.md`.
7. At least one non-blocking puzzle beat in `dm/puzzle-ledger.md`.
8. At least four saved visual prompts across at least three visual kinds.
9. At least one persistent object or map visual.
10. End-of-session state update.
11. Next session log creation.

For a deterministic smoke test, run:

```powershell
python plugins\codex-questforge\scripts\self_play.py `
  --campaigns-dir campaigns `
  --name "The Amber Gate Self Play"
```

The deterministic smoke test writes `self-play-transcript.md` with 12 turns so
the beta can be reviewed for actual table feel, not only filesystem output.

For broader alpha testing, run:

```powershell
python plugins\codex-questforge\scripts\alpha_playtest.py `
  --output-dir playtests\alpha-001
```

That harness creates several scenario workspaces and a summary report. Use it
when tuning fun, pacing, visual cadence, and continuity across play styles.

## Pass Criteria

The self-play passes when:

- the player always knows what they can do next;
- the DM does not reveal hidden map or secret information early;
- saved prompts are specific enough to generate useful native images;
- visual continuity is recorded in `visual-bible.md` or `visual-index.md`;
- adventure continuity is recorded in `dm/adventure-spine.md`;
- puzzle beats have fallbacks in `dm/puzzle-ledger.md`;
- campaign state changes after choices and rolls;
- the next session can start from saved files without relying on chat memory.
