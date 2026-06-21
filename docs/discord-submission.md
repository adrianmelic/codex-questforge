# Discord Challenge Submission Draft

**Public GitHub repo:** https://github.com/adrianmelic/codex-questforge

**Playable game link:** https://adrianmelic.github.io/codex-questforge/

**Short description:**

Codex Questforge is a Codex-powered fantasy RPG runner. It turns a Codex thread into a persistent 5E-compatible campaign with quick character creation, open dice rolls, local campaign memory, a mechanical game-state ledger, checkpoints/rollback, optional generated scene images, 360 viewers, and ambience support.

The browser link includes a small playable scene demo, but the real game runs inside Codex after installing the plugin.

**What I made:**

- A local Codex plugin with six skills: main DM loop, setup, rules, campaign memory, puzzles, and visuals.
- Scripts for SRD setup, dice, rules search, game state, campaign memory, visual galleries, 360 panorama viewers, audio selection, preflight checks, and deterministic self-play.
- A starter ambience pack and a static GitHub Pages demo.

**How Codex helped:**

Codex helped design the plugin architecture, implement the scripts and templates, run self-play tests, analyze a long human beta campaign, fix visual/gallery/360 issues, and smoke-test the installed plugin in English and Spanish with persistent campaign files.

**How to play / controls:**

Install the plugin, open a new Codex thread, and type:

```text
Use Codex Questforge. I want to play in English. Create a quick character and start.
```

Controls are natural language: say what your character does, ask what you can do, inspect inventory, request a rollback, ask for rules, or continue the story freely.

**Alpha note:**

It is playable today, but still alpha. Combat, level-up, shops, and long-term campaign systems are already scaffolded and will keep improving after the deadline.
