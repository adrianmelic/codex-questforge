# Game State Ledger

`game-state.json` is the player-facing mechanical ledger for Codex Questforge. It complements `campaign-state.md`: Markdown keeps readable campaign memory, while the JSON ledger keeps the current playable state precise enough for inventory, equipment, shops, combat, spell resources, rests, death saves, level-ups, and rollback.

## Design Rule

Narration stays flexible. Mechanical state does not. If a choice changes HP, money, equipment, spell slots, death state, level, inventory, shop stock, combat turn order, or a checkpoint, update `game-state.json` with `scripts/game_state.py`.

## Player Status

Use status before decisions that depend on resources:

```powershell
python plugins\questforge\scripts\game_state.py status --campaign-root campaigns\the-amber-gate
```

Show a compact summary in conversation: objective, immediate risk, HP, relevant equipment, useful inventory, available spell slots/resources, conditions, and pending level-up or reward.

## Inventory And Equipment

Use inventory for meaningful objects, not every apple in every crate. Use equipment slots when visuals or rules depend on what the character is wearing or holding.

```powershell
python plugins\questforge\scripts\game_state.py add-item --campaign-root campaigns\the-amber-gate --character "Mara Vey" --name "Stormproof cloak" --value 12gp --mechanical-effect "Advantage against cold rain exposure"
python plugins\questforge\scripts\game_state.py equip --campaign-root campaigns\the-amber-gate --character "Mara Vey" --item "Stormproof cloak" --slot cloak
```

If a generated image shows the character after an equipment change, the prompt should include the equipped state from `game-state.json`.

## Shops

Merchants should be playable, not just menus. Track stock and purchases so repeated visits stay coherent.

```powershell
python plugins\questforge\scripts\game_state.py add-shop-item --campaign-root campaigns\the-amber-gate --shop-id low-door --shop-name "Low Door Outfitters" --merchant "Sella" --item-name "Iron lantern" --price 5gp --stock 1
python plugins\questforge\scripts\game_state.py buy-item --campaign-root campaigns\the-amber-gate --character "Mara Vey" --shop-id low-door --item "Iron lantern"
```

## Combat

Combat is turn-based by default. Keep the textual state authoritative: initiative, whose turn it is, HP, AC, conditions, available resources, terrain, hazards, and interactables. Visual maps can help, but they must not become the only source of truth.

```powershell
python plugins\questforge\scripts\game_state.py start-combat --campaign-root campaigns\the-amber-gate --name "Warehouse ambush" --combatant "Mara Vey:14" --combatant "Dock Cutthroat:11:6:13:enemy"
python plugins\questforge\scripts\game_state.py set-tactical-scene --campaign-root campaigns\the-amber-gate --summary "Crates form half cover around a lantern spill." --terrain "stacked crates" --hazard "oil lamp can spread fire" --interactable "rope pulley can drop sacks"
python plugins\questforge\scripts\game_state.py combat-action --campaign-root campaigns\the-amber-gate --actor "Mara Vey" --summary "Mara shoves the lamp toward the cutthroat." --target "Dock Cutthroat" --damage 3
python plugins\questforge\scripts\game_state.py end-turn --campaign-root campaigns\the-amber-gate
```

## Spells, Rests, And Conditions

Use SRD lookup for rules, then record the outcome.

```powershell
python plugins\questforge\scripts\game_state.py set-spell-slots --campaign-root campaigns\the-amber-gate --character "Mara Vey" --slot-level 1 --max 3
python plugins\questforge\scripts\game_state.py spend-spell-slot --campaign-root campaigns\the-amber-gate --character "Mara Vey" --slot-level 1
python plugins\questforge\scripts\game_state.py add-condition --campaign-root campaigns\the-amber-gate --character "Mara Vey" --name "Poisoned" --effect "Disadvantage on attack rolls and ability checks" --ends-on long_rest
python plugins\questforge\scripts\game_state.py rest --campaign-root campaigns\the-amber-gate --character "Mara Vey" --kind long
```

## Level Up

XP can unlock a pending level-up. Codex should present a guided choice, consult SRD rules for class-specific options, then record the chosen result.

```powershell
python plugins\questforge\scripts\game_state.py award-xp --campaign-root campaigns\the-amber-gate --character "Mara Vey" --amount 300 --reason "Solved the bridge ward"
python plugins\questforge\scripts\game_state.py level-up-options --campaign-root campaigns\the-amber-gate --character "Mara Vey"
python plugins\questforge\scripts\game_state.py apply-level-up --campaign-root campaigns\the-amber-gate --character "Mara Vey" --new-level 2 --hp-increase 5 --feature "Arcane recovery recorded from SRD lookup"
```

## Death And Rollback

Death mode defaults to `heroic`: 0 HP triggers death saves, but Codex should frame consequences dramatically and avoid cheap random anticlimax unless the table wants a hard mode. `narrative` mode can treat 0 HP as defeat rather than death. Hard irreversible moments should get checkpoints.

```powershell
python plugins\questforge\scripts\game_state.py checkpoint --campaign-root campaigns\the-amber-gate --label "Before opening the black door"
python plugins\questforge\scripts\game_state.py apply-damage --campaign-root campaigns\the-amber-gate --character "Mara Vey" --amount 20
python plugins\questforge\scripts\game_state.py death-save --campaign-root campaigns\the-amber-gate --character "Mara Vey" --result success
python plugins\questforge\scripts\game_state.py restore-checkpoint --campaign-root campaigns\the-amber-gate --id before-opening-the-black-door-2026-06-09T120000+0000
```

Rollback is table control, not automatically an in-world retcon. If the player says they regret a choice, offer the last checkpoint plainly.
