# New User Beta Review

Date: 2026-05-17

Scenario: `La Campana del Cienagal`

Goal: test Codex Questforge as a first-time user from clean setup through a
playable scene with SRD rules, dice, visual prep, native image generation,
visual reuse, session close, and continuity handoff.

## Evidence

Ignored beta workspace:
`plugins/codex-questforge/outputs/beta-new-user-20260517-questforge/`

The run proved:

- clean setup downloaded `SP_SRD_CC_v5.2.1.pdf`, detected Spanish, extracted
  and indexed 398 pages;
- a new campaign workspace was created for `La Campana del Cienagal`;
- rules lookup found Spanish SRD references for ability checks and DCs;
- an open deterministic roll resolved the first meaningful action:
  `1d20+5 (normal): [6] + 5 = 11`;
- visual prep created four session-0 anchors: Iria, Reedwight, Sunken Bell
  Causeway, and Verdigris Bell Clapper;
- generated-image registration worked through `--asset-source`;
- `visual_reuse.py` created a scene-frame prompt from four canon anchors;
- the first inconsistent scene prompt was marked `rejected`;
- the corrected native scene image was registered as `variant`;
- session 1 was closed and session 2 recovered the next choice.

## Friction Found And Fixed

| Friction | Fix |
| --- | --- |
| `--install-pdf-extractor` printed noisy pip notices during the happy path. | `questforge_setup.py` now captures successful pip output and disables pip version checks. |
| Live scene-frame prompts could contradict a resolved roll if the action text was manually written wrong. | `visual_reuse.py` now accepts `--roll` and `--outcome`, and includes them in saved prompts. |
| Docs focused on `--asset-path`, but native image generation usually saves outside the campaign folder. | Docs and `questforge-visuals` now show `--asset-source` for copying selected generated images into `images/assets/`. |

## Native Image Review

The generated Reedwight scene succeeded as a table image: Iria, the clapper,
white reeds, marsh water, and the non-attacking raised hand are readable. It was
marked `variant`, not `canon`, because the bell tower appears more intact than
the canon "tower stump" description. This is the right workflow: useful scene
images can enrich play without becoming future reference anchors.

## Product Notes

- The core loop now feels testable by a human: setup, start, prep, play, image,
  review, close, continue.
- The visual status vocabulary is doing useful work. `canon` should remain for
  reusable anchors; `variant` is ideal for good cinematic frames with minor
  drift.
- The next human beta should focus on pacing and fun, not command correctness.
