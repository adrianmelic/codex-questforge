# Discord Challenge Submission Draft

Historical note: this was the submission framing for the OpenAI Discord challenge. The public page now works better as a guided sample session; the real game is the installed Codex plugin.

**Public GitHub repo:** https://github.com/adrianmelic/codex-questforge

**Guided sample session:** https://adrianmelic.github.io/codex-questforge/

**Short description:**

What if we did not just use Codex to build a game, but used Codex as the game itself?

**Codex Questforge is a fantasy RPG played inside Codex.** Codex becomes your Dungeon Master: it prepares the adventure, creates your character, reacts to whatever you decide, rolls dice openly, tracks local campaign state, remembers clues and consequences, generates scene images and 360 POV moments, and can choose ambient soundtrack loops for the current situation.

The browser link is a guided Codex-style sample session. Click a player prompt, see the simulated DM response, dice result, state update, generated scene image, tactical map, 360 viewer, and optional ambience. The installed plugin is open-ended: in Codex, you can say anything and the DM continues the story.

**What I made:**

- A local Codex plugin with six skills: main DM loop, setup, rules, campaign memory, puzzles, and visuals.
- Scripts for SRD setup, dice, rules search, game state, campaign memory, visual galleries, 360 panorama viewers, audio selection, preflight checks, and deterministic self-play.
- A starter ambience pack and a static GitHub Pages guided sample.

**How Codex helped:**

Codex helped design the plugin architecture, implement the scripts and templates, run self-play tests, analyze a long human beta campaign, fix visual/gallery/360 issues, and smoke-test the installed plugin in English and Spanish with persistent campaign files.

**How to play / controls:**

Install the plugin, open a new Codex thread, and type:

```text
I want to play @questforge.
```

Controls are natural language: say what your character does, ask what you can do, inspect inventory, request a rollback, ask for rules, or continue the story freely. It has been tested in English and Spanish, and players are encouraged to try their own language. On first campaign setup, Questforge can download and index the public 5E SRD 5.2.1 PDF locally, so the first start can take a little longer.

**Alpha note:**

It is playable today, but still alpha. Combat, level-up, shops, and long-term campaign systems are already scaffolded and will keep improving after the deadline.
