---
name: questforge-rules
description: Resolve 5E-compatible rules questions using local Questforge SRD indexes, concise citations, transparent rulings, and recorded house rules.
---

# Questforge Rules

Use this skill when a game action needs SRD lookup, a rule citation, a DC,
advantage or disadvantage, a table ruling, a house rule, or dice resolution.

## Rules Lookup

Prefer the setup manifest wrapper:

```powershell
python ../../scripts/rules_index.py query-setup --manifest .questforge/questforge-setup.json --query "<topic>"
```

It automatically uses SQLite when available, then JSONL fallback. If the setup
manifest is unavailable, query explicit paths:

```powershell
python ../../scripts/rules_index.py query-sqlite --index <sqlite_index_path> --query "<topic>"
python ../../scripts/rules_index.py query --index <jsonl_index_path> --query "<topic>"
```

Give the player a short ruling in the configured language. Do not paste long
SRD passages. Cite the returned `Reference` path and section/page when useful.

## Rulings

When the exact rule is absent or unclear:

- State the uncertainty briefly.
- Make a fair table ruling that keeps play moving.
- Record recurring rulings in the campaign state under house rules.
- Use the established ruling consistently unless the user changes it.

## Dice

Ask whether the player rolls or Codex rolls when preference is unknown.

Use:

```powershell
python ../../scripts/roll_dice.py d20+4 --mode normal
```

Supported modes: `normal`, `advantage`, `disadvantage`.

Before rolling, state:

- ability or save;
- DC band or opposing roll;
- stakes of success and failure;
- whether advantage/disadvantage applies and why.

Use 5E-style DC anchors instead of drifting to 13/14 by default:

- no roll: safe, obvious, already solved, or failure would only mean trying again;
- DC 5: very easy but uncertain under pressure;
- DC 10: easy;
- DC 15: medium;
- DC 20: hard;
- DC 25: very hard;
- DC 30: nearly impossible.

The anchors are guidance, not a requirement that every DC be exactly a
multiple of 5. For ordinary play, prefer anchor values because players can
learn them. For a specific fictional nuance, choose a nearby value such as 12,
13, 16, 17, or 18 and say why. Avoid repeated 12-15 clustering; if recent
checks all sit in that band, intentionally switch to no roll, DC 10, DC 15, DC
20, an opposed roll, or a resource tradeoff.

Use `../../scripts/dc_planner.py` before important checks or whenever recent
checks feel clustered:

```powershell
python ../../scripts/dc_planner.py --difficulty medium --position normal --approach clever --recent-dc 13 --recent-dc 14 --recent-dc 14 --recent-dc 13
```

Treat high stakes as bigger consequences, not automatically a higher DC. Raise
or lower the DC only because the fictional task is harder/easier, the position
is weak/strong, or the approach is poor/clever. Use DC 12-14 only as a
deliberate fine adjustment with an explicit reason, not as the default medium
check.

When offering suggested actions, include the relevant modifier when it helps the
player understand their character: `Sigilo +5`, `Carisma -1`, `Investigación
+3`, or similar. Use `../../scripts/action_options.py` for compact comparable
options when the user seems blocked or asks what they can do.

On failure, advance the world instead of blocking the story. If the same
obstacle has already produced two failed checks or the user says the situation
is dragging, stop asking for repeated rolls against that obstacle. Use
`../../scripts/check_resolution.py` to force a `failure_forward` result with a
cost and a new option.
