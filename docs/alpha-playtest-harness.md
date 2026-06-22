# Alpha Playtest Harness

Use the alpha harness when the question is no longer "does Questforge write the
right files?" and becomes "would a player want to keep going?"

The deterministic smoke test in `self_play.py` stays small and CI-friendly. The
alpha harness runs broader table-feel probes across several play modes:

- mystery exploration;
- social commerce;
- dungeon pressure.

## Run

```powershell
python plugins\questforge\scripts\alpha_playtest.py `
  --output-dir playtests\alpha-001
```

The command creates one campaign workspace per scenario and a root summary:

```text
playtests/alpha-001/
  alpha-playtest-summary.md
  campaigns/
    the-amber-gate-alpha/
      alpha-playtest-transcript.md
      alpha-playtest-report.md
      campaign-state.md
      dm/adventure-spine.md
      dm/puzzle-ledger.md
      sessions/session-001.md
      sessions/session-002.md
      images/visual-index.md
      images/prompts/
    saltglass-market-alpha/
    rootbound-vault-alpha/
```

## What To Review

Open `alpha-playtest-summary.md` first, then inspect each scenario report and
transcript.

Review for these questions:

- Does the first DM turn create immediate pressure?
- Does the player always know what they can do next?
- Are failed rolls still interesting, or do they just block progress?
- Do hooks stay coherent in the adventure spine instead of silently remixing?
- Do puzzle beats reward deduction without blocking the scene?
- Do visual prompts help decisions, memory, inventory, maps, or NPC identity?
- Is fog of war respected?
- Can `sessions/session-002.md` restart the game without chat memory?
- Would a human player ask to continue?

## Score Meaning

The `fun_score` is an automated readiness heuristic, not a substitute for human
playtest judgment. It rewards:

- enough turns to expose pacing;
- multiple meaningful choices;
- rules pressure and open rolls;
- visual cadence across several visual kinds;
- adventure-spine continuity and non-blocking puzzle beats;
- continuity anchors that survive session resume;
- a concrete next choice.

A passing score means the artifact is worth human beta testing. It does not
prove that the adventure is already fun for every table.

## Good Failure

If a scenario fails, keep the generated transcript. It is useful evidence. The
right fix is usually one of:

- clarify the next choice;
- add a consequence that changes state;
- turn a menu into a scene with pressure;
- add a clue route or puzzle beat with a fallback;
- save a visual prompt for a persistent object, NPC, map, or inventory board;
- remove spoilers from a map prompt;
- make failure produce a cost and a new option instead of a dead end.
