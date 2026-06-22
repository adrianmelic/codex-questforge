# Beta Preflight Checklist

Use this before a human beta session or any long continuation where continuity, visuals, and pacing matter.

## 1. Run The Audit

```powershell
python plugins\questforge\scripts\preflight.py `
  --campaign-root campaigns\<campaign-slug> `
  --repair-missing-templates `
  --refresh-gallery `
  --title "<campaign title>"
```

Continue only when errors are zero. Warnings are prep prompts, not automatic blockers.

## 2. Fill The Player Surface

Update `player-journal.md` with only spoiler-free facts:

- current objective;
- immediate risk;
- known clues and NPCs;
- inventory, money, XP, rewards, leverage, and contacts;
- damage, conditions, disguises, wounds, or visible states;
- open threads the player can act on next.

## 3. Fill The Visual Ledger

If preflight reports `empty_visual_ledger`, add active rows to `images/visual-ledger.md` before play. Keep this short and high-impact:

- player character appearance, current outfit, injuries, bandages, disguise, or carried signature gear;
- recurring NPCs or creatures that are likely to reappear;
- important objects with scale and shape, such as a 40 cm iron box with seven brass studs;
- locations whose layout must stay stable across maps, POVs, and scene frames;
- campaign style constraints, such as immersive fantasy realism and no unwanted film grain.

Do not try to document every prop. Track only details that would feel wrong if they changed.

## 4. Prepare The Visual Surfaces

Open `images/visual-gallery.html#latest` in the Codex in-app Browser when available. Keep the same gallery URL for the session as the desktop/history surface. Static generated images should still be shown once in the Codex conversation so mobile users can see them. Use the local gallery for 360 viewers, desktop review, and chronological history.

## 5. Prepare The Next Scene

Before the first live turn, decide:

- the current location and immediate pressure;
- one NPC, faction, clock, or danger that can move without player permission;
- the next meaningful choice;
- one possible reward, clue, XP moment, or useful loot;
- whether the next visual should be a scene frame, comic page, map, inventory board, or POV 360.

## 6. During Play

For each meaningful turn:

- move the fiction forward even on failed rolls;
- show relevant ability modifiers when suggesting options;
- award XP, loot, clues, or leverage for meaningful progress;
- update `player-journal.md`, `campaign-state.md`, and `images/visual-ledger.md` as states change;
- show each selected static generated image once in chat with absolute-path Markdown;
- refresh the gallery after registering a generated image.
