# Campaign Conception

Use this process before filling `templates/quick-start-spec.json`. The template is a neutral contract, not an adventure sample. Do not run it unchanged and do not borrow a setting from showcase pages, test transcripts, or prior campaigns unless the player explicitly asks to return there.

## Creative Pass

1. Read the player's language, boundaries, hero preference, and any explicit genre request.
2. Inspect only `campaigns/*/campaign-conception.json` in the selected workspace. Note combinations already used; do not copy their prose into the new draft.
3. Privately sketch at least three materially different possibilities. Change the physical and social foundations, not only names or lore. Do not show a premise menu unless the player requested assisted selection.
4. Choose the possibility with the clearest immediate action, strongest NPC relationship tension, most concrete conflict, and best promise for consequences beyond the opening.
5. Complete every field in the neutral quick-start spec. Run the conception audit before creating campaign files. If it reports a repeated combination, reconceive at least two foundations instead of renaming them.
6. Create the minimum DM spine: core truth, active hooks, exactly three clue routes, faction intent, and plausible outcomes. Keep the opening actionable and prepare its establishing visual.

This is a design process, not a random table. The values remain free-form so Codex can invent a setting appropriate to the player and language.

## Foundations To Decide

- **Environment:** biome, climate, season, time of day, physical surface, social scale, and relevance of water. Water may be central, incidental, absent, or anything else the fiction earns; no value is preferred.
- **Community:** who lives or works here, what holds them together, and what they stand to lose.
- **Material conflict:** a concrete pressure involving resources, labor, safety, territory, logistics, law, status, care, or another legible need.
- **Threat:** the force that will worsen the situation if nobody acts. It may be mundane, fantastic, mixed, visible, or initially misunderstood.
- **NPC relationships:** at least two people with individual wants and a relationship that creates leverage, loyalty, friction, or obligation.
- **Tone and aesthetic:** the emotional contract and visual language of this campaign, selected for this premise rather than inherited from examples.
- **Sensory palette:** at least three channels among sight, sound, smell or taste, and touch or temperature.
- **Campaign promise:** what kinds of choices, consequences, discoveries, and growth the player can expect over more than one scene.

Do not use any environmental feature as automatic atmosphere. Rain, ports, rivers, fog, darkness, bright sun, dust, snow, forests, ruins, and caves are all valid when they arise from the selected conception and affect play. Repetition, not presence, is the problem.

## Audit

After writing a completed spec:

```powershell
python scripts/campaign_conception.py --spec <completed-spec.json> --campaigns-dir <workspace>/campaigns
```

The audit validates the creative brief and compares its seven free-form environmental dimensions plus narrative foundations with prior local campaigns. A repeated combination must be reconceived before `quick_start.py` writes state.

Then create the campaign atomically:

```powershell
python scripts/quick_start.py --workspace-root <workspace> --spec <completed-spec.json>
```

The campaign stores the selected brief and its signature in `campaign-conception.json`. This file is DM preparation and originality evidence, not a player-facing lore dump.
