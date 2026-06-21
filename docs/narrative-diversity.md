# Narrative Diversity Guardrails

Questforge should avoid drifting into the same AI-fiction gravity wells every campaign. This is a soft quality check, not a ban list. Memory magic, sentient objects, strange contracts, taboos, prophecy, dreams, and secret rules can all work in fantasy when they earn their place and pay off cleanly.

Use these guardrails when drafting a campaign premise, opening brief, DM spine, major reveal, recap, or post-session revision. They are inspired by beta feedback and by narrative-feature work such as StoryScope, which argues that AI fiction can be distinguished by discourse-level choices such as over-explicit theme, tidy single-track plots, reduced moral ambiguity, and lower temporal complexity.

## Soft Motif Budget

- Let one metaphysical motif dominate a scene or reveal. Avoid stacking memory trade, sentient-object bargain, unsayable taboo, hidden cosmic rule, dream symbolism, and hyperstition unless the pileup is the whole premise and has a planned payoff.
- Reuse a motif only when it changes the player's available choices, not merely when it makes the lore sound deeper.
- If a motif appears in two consecutive major beats, make the next beat material, social, tactical, or logistical.

## Grounding Alternatives

Before adding another metaphysical rule, try one ordinary pressure:

- money, rent, debt, wages, taxes, scarcity;
- food, illness, weather, shelter, travel time, fatigue;
- family, loyalty, jealousy, shame, grief, pride;
- class, guild rules, local law, land rights, inheritance;
- faction incentives, reputation, leverage, blackmail, logistics.

These pressures make fantasy stranger, not smaller, because they give NPCs reasons to act that are legible before the supernatural explanation arrives.

## Reveal Discipline

- Keep secrets owned by characters, institutions, families, cults, guilds, or factions by default. Escalate to cosmic rules only when the campaign spine needs it.
- Avoid making every clue point to the same symbolic answer. Some clues should expose practical constraints, contradictions, false beliefs, or competing goals.
- Let the player discover meaning through consequences. Do not explain the lesson if action and fallout already show it.
- Preserve at least one hard choice where both sides have a defensible motive.

## Lint Command

Run the local lint before major prep or after a session recap:

```powershell
python plugins\codex-questforge\scripts\narrative_lint.py `
  --file campaigns\the-amber-gate\opening-brief.md
```

Use `--strict` only in tests or release audits. During play, warnings are prompts for revision, not failures.
