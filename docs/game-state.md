# Game State Ledger

`game-state.json` is the player-facing mechanical ledger for Questforge. It complements `campaign-state.md`: Markdown keeps readable campaign memory, while the JSON ledger keeps the current playable state precise enough for inventory, equipment, shops, combat, spell resources, rests, death saves, level-ups, and rollback.

## Design Rule

Narration stays flexible. Mechanical state does not. If a choice changes HP, money, equipment, spell slots, death state, level, inventory, shop stock, combat turn order, or a checkpoint, update `game-state.json` with `scripts/game_state.py`.

## Player Status

Use status before decisions that depend on resources:

```powershell
python plugins\questforge\scripts\game_state.py status --campaign-root campaigns\example-campaign
```

Show a compact summary in conversation: objective, immediate risk, HP, relevant equipment, useful inventory, available spell slots/resources, conditions, and pending level-up or reward.

## Inventory And Equipment

Use inventory for meaningful objects, not every apple in every crate. Use equipment slots when visuals or rules depend on what the character is wearing or holding.

```powershell
python plugins\questforge\scripts\game_state.py add-item --campaign-root campaigns\example-campaign --character "Mara Vey" --name "Reinforced gloves" --value 12gp --mechanical-effect "Advantage when gripping hot or rough mechanisms"
python plugins\questforge\scripts\game_state.py equip --campaign-root campaigns\example-campaign --character "Mara Vey" --item "Reinforced gloves" --slot gloves
```

If a generated image shows the character after an equipment change, the prompt should include the equipped state from `game-state.json`.

## Shops

Merchants should be playable, not just menus. Track stock and purchases so repeated visits stay coherent.

```powershell
python plugins\questforge\scripts\game_state.py add-shop-item --campaign-root campaigns\example-campaign --shop-id tool-stall --shop-name "Tool Stall" --merchant "Sella" --item-name "Iron pry bar" --price 5gp --stock 1
python plugins\questforge\scripts\game_state.py buy-item --campaign-root campaigns\example-campaign --character "Mara Vey" --shop-id tool-stall --item "Iron pry bar"
```

## Combat

Combat is turn-based by default. Keep the textual state authoritative: initiative, whose turn it is, HP, AC, conditions, available resources, terrain, hazards, and interactables. Visual maps can help, but they must not become the only source of truth.

```powershell
python plugins\questforge\scripts\game_state.py start-combat --campaign-root campaigns\example-campaign --name "Workshop skirmish" --combatant "Mara Vey:14" --combatant "Saboteur:11:6:13:enemy"
python plugins\questforge\scripts\game_state.py set-tactical-scene --campaign-root campaigns\example-campaign --summary "Worktables form half cover around a brazier." --terrain "worktables grant half cover" --hazard "brazier can spread fire" --interactable "rope pulley can drop sacks"
python plugins\questforge\scripts\game_state.py combat-action --campaign-root campaigns\example-campaign --actor "Mara Vey" --summary "Mara shoves the brazier toward the saboteur." --target "Saboteur" --damage 3
python plugins\questforge\scripts\game_state.py end-turn --campaign-root campaigns\example-campaign
```

## Spells, Rests, And Conditions

Use SRD lookup for rules, then record the outcome.

```powershell
python plugins\questforge\scripts\game_state.py set-spell-slots --campaign-root campaigns\example-campaign --character "Mara Vey" --slot-level 1 --max 3
python plugins\questforge\scripts\game_state.py spend-spell-slot --campaign-root campaigns\example-campaign --character "Mara Vey" --slot-level 1
python plugins\questforge\scripts\game_state.py add-condition --campaign-root campaigns\example-campaign --character "Mara Vey" --name "Poisoned" --effect "Disadvantage on attack rolls and ability checks" --ends-on long_rest
python plugins\questforge\scripts\game_state.py rest --campaign-root campaigns\example-campaign --character "Mara Vey" --kind long
```

## Level Up

XP can unlock a pending level-up. Codex should present a guided choice, consult SRD rules for class-specific options, then record the chosen result.

```powershell
python plugins\questforge\scripts\game_state.py award-xp --campaign-root campaigns\example-campaign --character "Mara Vey" --amount 300 --reason "Solved the sabotage"
python plugins\questforge\scripts\game_state.py level-up-options --campaign-root campaigns\example-campaign --character "Mara Vey"
python plugins\questforge\scripts\game_state.py apply-level-up --campaign-root campaigns\example-campaign --character "Mara Vey" --new-level 2 --hp-increase 5 --feature "Arcane recovery recorded from SRD lookup"
```

## Death And Rollback

Death mode defaults to `heroic`: 0 HP triggers death saves, but Codex should frame consequences dramatically and avoid cheap random anticlimax unless the table wants a hard mode. `narrative` mode can treat 0 HP as defeat rather than death. Hard irreversible moments should get checkpoints.

```powershell
python plugins\questforge\scripts\game_state.py checkpoint --campaign-root campaigns\example-campaign --label "Before entering the sealed workshop"
python plugins\questforge\scripts\game_state.py apply-damage --campaign-root campaigns\example-campaign --character "Mara Vey" --amount 20
python plugins\questforge\scripts\game_state.py death-save --campaign-root campaigns\example-campaign --character "Mara Vey" --result success
python plugins\questforge\scripts\game_state.py restore-checkpoint --campaign-root campaigns\example-campaign --id before-entering-the-sealed-workshop-2026-06-09T120000+0000
```

Rollback is table control, not automatically an in-world retcon. If the player says they regret a choice, offer the last checkpoint plainly.
