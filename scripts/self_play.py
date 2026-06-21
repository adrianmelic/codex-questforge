"""Deterministic self-play smoke test for Codex Questforge."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

try:
    from .campaign_memory import (
        create_campaign,
        create_next_session,
        record_hook_status,
        record_puzzle_beat,
        save_visual_prompt,
        slugify,
    )
    from .roll_dice import roll_dice
except ImportError:  # pragma: no cover - direct script execution path
    from campaign_memory import (
        create_campaign,
        create_next_session,
        record_hook_status,
        record_puzzle_beat,
        save_visual_prompt,
        slugify,
    )
    from roll_dice import roll_dice


@dataclass(frozen=True)
class SelfPlayResult:
    """Summary of a Questforge self-play run."""

    campaign_root: str
    session_log: str
    next_session_log: str
    transcript_path: str
    report_path: str
    turn_count: int
    visual_prompt_count: int
    visual_kinds: list[str]
    roll_summary: str


def run_self_play(
    campaigns_dir: Path,
    name: str = "The Amber Gate",
    session_date: date | None = None,
) -> SelfPlayResult:
    """Run a deterministic mini-session that exercises the Questforge loop."""

    session_date = session_date or date.today()
    paths = create_campaign(
        campaigns_dir=campaigns_dir,
        name=name,
        tone="heroic mystery with eerie ruins",
        boundaries="no graphic gore",
        session_date=session_date,
    )
    write_hero_sheet(paths.characters / "mara-vey.md")
    record_hook_status(
        paths.root,
        hook="The amber lantern is out of phase",
        origin="opening scene",
        status="active",
        current_meaning=(
            "the bridge can be crossed safely only if the lantern is understood"
        ),
        next_payoff="Mara can parley with the whisper or force the lantern back",
    )
    record_puzzle_beat(
        paths.root,
        title="Three Lantern Intervals",
        kind="clue_connection",
        required_clues=[
            "rain bends around the floating amber lantern",
            "the copper tube shows the pilgrim road etched in three gaps",
        ],
        ask_at_table="Which gap in the pilgrim-road etching matches the lantern?",
        solution="the middle gap matches the bridge span",
        fallback="the lantern flares and advances the clock, but reveals the path",
        reward="lower the next bridge crossing DC by 2",
        symbolic_weight="a broken map can still teach where the light is missing",
        status="prepared",
    )

    roll = roll_dice("d20+4", random_generator=random.Random(9))
    visual_prompts = [
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=1,
            kind="location",
            label="Gorge Bridge",
            prompt=(
                "Original 5E-compatible fantasy location, unofficial and not "
                "using official D&D setting, logo, product art, or named "
                "copyrighted character. Subject: a rain-slick green stone "
                "bridge over a storm gorge, with three amber lanterns glowing "
                "across the span. Purpose: establish the opening location. "
                "Style: painterly fantasy realism, cinematic wide shot, "
                "readable staging. Avoid: official logos, copied product art."
            ),
        ),
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=1,
            kind="item",
            label="Copper Map Tube",
            prompt=(
                "Original 5E-compatible fantasy item, unofficial and not using "
                "official D&D product art. Subject: sealed copper map tube, "
                "amber wax seal, thin pilgrim-road etching, small dent near "
                "one cap, leather cord. Purpose: persistent clue and inventory "
                "object. Style: isolated prop view on wet dark stone."
            ),
        ),
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=2,
            kind="map",
            label="Gorge Bridge Fog Map",
            prompt=(
                "Original fantasy exploration map with fog of war. Subject: "
                "known west approach, visible bridge span, three lantern marks, "
                "and the first abbey silhouette. Hide unexplored abbey rooms, "
                "secret paths, enemy positions, and trap mechanisms under mist "
                "and blank parchment. Sparse table-useful labels only."
            ),
        ),
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=3,
            kind="recap",
            label="Rain Bent Around The Lantern",
            prompt=(
                "Original 5E-compatible fantasy recap image. Subject: Mara Vey "
                "realizing rain bends around a floating amber lantern while "
                "Brother Caldus clutches the copper tube behind her. Purpose: "
                "end-of-session postcard. Mood: heroic mystery, eerie but not "
                "grim. Avoid official setting identifiers and copied art."
            ),
        ),
    ]

    session_log = paths.sessions / "session-001.md"
    session_log.write_text(
        build_session_log(name, session_date, roll.summary()),
        encoding="utf-8",
        newline="\n",
    )
    write_campaign_state(paths.campaign_state, name, session_date)
    next_session = create_next_session(
        paths.root,
        session_date=session_date,
        characters_present="Mara Vey",
        recap=[
            "Mara discovered that the amber lantern exists out of phase with "
            "the bridge.",
            "Brother Caldus now trusts Mara and still holds the copper map "
            "tube.",
            "The first fog-of-war map shows only the west approach and "
            "visible bridge.",
        ],
        start_location="west side of the gorge bridge",
        pressure="the lantern waits at the edge of the overlapping ruin",
        next_choice=(
            "cross, parley with the whisper, or force the lantern back into "
            "phase"
        ),
    )
    transcript_text = build_turn_transcript(name, session_date, roll.summary())
    transcript_path = paths.root / "self-play-transcript.md"
    transcript_path.write_text(
        transcript_text,
        encoding="utf-8",
        newline="\n",
    )
    turn_count = count_transcript_turns(transcript_text)
    report_path = paths.root / "self-play-report.md"
    report_path.write_text(
        build_report(
            visual_prompts,
            roll.summary(),
            transcript_path.name,
            turn_count,
        ),
        encoding="utf-8",
        newline="\n",
    )

    visual_kinds = sorted(
        {visual_kind_from_prompt_path(path) for path in visual_prompts}
    )
    return SelfPlayResult(
        campaign_root=str(paths.root),
        session_log=str(session_log),
        next_session_log=str(next_session),
        transcript_path=str(transcript_path),
        report_path=str(report_path),
        turn_count=turn_count,
        visual_prompt_count=len(visual_prompts),
        visual_kinds=visual_kinds,
        roll_summary=roll.summary(),
    )


def visual_kind_from_prompt_path(path: Path) -> str:
    tail = path.name.split("-scene-", maxsplit=1)[1]
    return tail.split("-", maxsplit=2)[1]


def write_hero_sheet(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Mara Vey",
                "",
                "- Concept: practical human ranger",
                "- Level: 1",
                "- Visual anchors: dark travel cloak, wrapped bow, rain-worn boots",
                "- Current goal: escort Brother Caldus and understand the Amber Gate",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def build_session_log(
    campaign_name: str,
    session_date: date,
    roll_summary: str,
) -> str:
    return f"""# Session Log

## Session

- Campaign: {campaign_name}
- Session: 1
- Date: {session_date.isoformat()}
- Characters present: Mara Vey

## Recap

- Mara escorts Brother Caldus to the old gorge bridge during a storm.
- Three amber lanterns burn across the span without visible holders.

## Scenes

### Scene 1

- Location: west side of the gorge bridge.
- Pressure: a whisper demands the copper map tube.
- Player action: Mara studies rain, tracks, and wind around the lanterns.
- Roll: {roll_summary}
- Outcome: success. The rain bends around the lantern instead of touching it.
- State changes: clue added; Brother Caldus trusts Mara; Abbey Gate clock 1/6.
- Visual prompts saved: location, item.

### Scene 2

- Location: bridge approach.
- Pressure: crossing may pull Mara into an overlapping ruin.
- Player action: Mara sketches known terrain before advancing.
- Outcome: fog-of-war map saved without revealing hidden abbey rooms.
- State changes: map reference added to visual index.
- Visual prompts saved: map.

### Scene 3

- Location: west side of the gorge bridge.
- Pressure: the lantern waits at the edge of the visible world.
- Player action: Mara keeps the copper tube and prepares to step forward.
- Outcome: session closes on a clear next choice.
- Visual prompts saved: recap.

## Rules Rulings

| Ruling | Reason | Keep As House Rule |
| --- | --- | --- |
| Wisdom (Survival), moderate DC | Reading storm-distorted tracks is uncertain and meaningful. | no |

## End State

- Party position: west side of the gorge bridge.
- Immediate next choice: cross, parley with the whisper, or force the lantern
  back into phase.
- Changed clocks: Abbey Gate 1/6.
- Changed NPC attitudes: Brother Caldus trusts Mara.
- Rewards: clue about overlapping ruins.
- Damage, conditions, resources: none.
"""


def write_campaign_state(
    campaign_state_path: Path,
    campaign_name: str,
    session_date: date,
) -> None:
    campaign_state_path.write_text(
        f"""# Campaign State

## Metadata

- Campaign: {campaign_name}
- System: 5E-compatible, SRD-grounded
- Tone: heroic mystery with eerie ruins
- Content boundaries: no graphic gore
- House rules:
- SRD attribution included: yes
- Last updated: {session_date.isoformat()}

## Party

| Character | Player | Ancestry | Class | Level | Notes |
| --- | --- | --- | --- | --- | --- |
| Mara Vey | Self-play | Human | Ranger | 1 | Practical escort for Brother Caldus |

## Current Situation

- Location: west side of the gorge bridge
- Immediate pressure: the lantern waits at the edge of the overlapping ruin
- Open decision: cross, parley with the whisper, or force the lantern back into phase

## Fronts And Clocks

| Front Or Clock | Segments | Filled | Advances When |
| --- | --- | --- | --- |
| Abbey Gate | 6 | 1 | Delay, failed occult investigation, or surrendering the copper tube |

## Factions

| Name | Goal | Leverage | Relationship |
| --- | --- | --- | --- |
| The Amber Gate | Overlay ruined places onto the present | Out-of-phase lanterns and whispers | Unknown threat |

## NPCs

| Name | Role | Wants | Visual Anchor | Attitude |
| --- | --- | --- | --- | --- |
| Brother Caldus | Village archivist | Keep the copper map tube safe | Clutches the tube when frightened | Trusts Mara |

## Locations

| Name | Role | Secret Or Pressure | Status |
| --- | --- | --- | --- |
| Gorge Bridge | Threshold to the abbey road | It overlaps a parallel ruin | Visible but unstable |

## Clues

| Clue | Meaning | Confirmed |
| --- | --- | --- |
| Rain bends around the lantern | The lantern is out of phase, not invisible | yes |

## Inventory And Rewards

| Item | Holder | Mechanical Notes | Story Notes |
| --- | --- | --- | --- |
| Copper Map Tube | Brother Caldus | none known | Key object demanded by the whisper |

## Visual Continuity

| Subject | Type | Anchor Details | Reuse Notes |
| --- | --- | --- | --- |
| Gorge Bridge | location | rain-slick green stone, storm gorge, three amber lanterns | opening location and recurring threshold |
| Copper Map Tube | item | copper cylinder, amber wax, pilgrim-road etching, leather cord | persistent clue and inventory object |
| Gorge Bridge Fog Map | map | west approach visible, abbey hidden by mist | reveal only explored areas |

## Open Threads

- What happens if Mara crosses into the overlapping ruin?
- Who is the whisper claiming to speak for?
- Why does the Amber Gate want the copper map tube?
""",
        encoding="utf-8",
        newline="\n",
    )


def build_turn_transcript(
    campaign_name: str,
    session_date: date,
    roll_summary: str,
) -> str:
    return f"""# Questforge Self-Play Transcript

## Session

- Campaign: {campaign_name}
- Date: {session_date.isoformat()}
- Player persona: cautious but curious ranger
- DM persona: consequence-forward Questforge runner

### Turn 1 - DM

Rain lashes the gorge bridge. Three amber lanterns glow across the span, but no
hands hold them. Brother Caldus keeps the copper map tube under his cloak and
asks whether Mara wants to cross, study the bridge, or question him first.

### Turn 2 - Player

Mara stays on the west side and studies the rain, the lantern light, and the
stonework before stepping onto the bridge.

### Turn 3 - DM

The action is uncertain and meaningful. Rules lookup target: ability checks.
Ruling: Wisdom (Survival), moderate DC, because Mara is reading weather,
tracks, and unnatural movement rather than recalling lore.

### Turn 4 - Player

Mara accepts the risk and keeps Brother Caldus behind the parapet while she
checks where the storm refuses to fall.

### Turn 5 - DM

Open roll: {roll_summary}. Success. The rain bends around the nearest lantern
instead of striking it. The lantern is not invisible; it is out of phase with
the bridge.

### Turn 6 - Player

Mara asks Brother Caldus why the whisper wants the copper tube, and she asks to
see the seal without breaking it.

### Turn 7 - DM

Caldus admits the tube came from the abbey road. He has never opened it. The
amber wax seal carries a pilgrim-road mark that matches the road on the old
map fragments.

### Turn 8 - Player

Mara wants a clear visual record of the tube before anyone tampers with it.

### Turn 9 - DM

Visual prompt saved: item, Copper Map Tube. The prompt records the copper
cylinder, amber seal, pilgrim-road etching, dented cap, and leather cord so the
object can remain visually consistent later.

### Turn 10 - Player

Mara sketches only what she can verify: the west approach, the bridge, the
three lantern positions, and the abbey silhouette. She refuses to mark rooms
she has not seen.

### Turn 11 - DM

Visual prompt saved: fog-of-war map. Hidden abbey rooms, traps, and enemy
positions stay covered by mist and blank parchment. Abbey Gate clock advances
to 1/6 because the lantern has noticed the copper tube.

### Turn 12 - Player

Mara ends the session holding position. Next time she will choose whether to
cross, parley with the whisper, or force the lantern back into phase.
"""


def count_transcript_turns(transcript_text: str) -> int:
    return sum(
        1
        for line in transcript_text.splitlines()
        if line.startswith("### Turn ")
    )


def build_report(
    visual_prompts: list[Path],
    roll_summary: str,
    transcript_name: str,
    turn_count: int,
) -> str:
    prompt_lines = "\n".join(f"- `{path.name}`" for path in visual_prompts)
    return f"""# Questforge Self-Play Report

## Result

Pass.

## Evidence

- Transparent roll: `{roll_summary}`
- Transcript: `{transcript_name}` with {turn_count} turns
- Visual prompt count: {len(visual_prompts)}
- Visual prompts:
{prompt_lines}
- Campaign state consolidated with clue, clock, NPC attitude, persistent item,
  persistent map, visual anchors, and open threads.
- DM adventure spine and non-blocking puzzle ledger created.
- Next session log created.

## Notes

This self-play does not call native image generation. It validates the campaign
loop and persistent prompts that a live Codex session would hand to native image
generation.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Questforge self-play.")
    parser.add_argument("--campaigns-dir", required=True, type=Path)
    parser.add_argument("--name", default="The Amber Gate")
    parser.add_argument("--date", dest="date_text")
    return parser


def parse_date(date_text: str | None) -> date | None:
    if date_text is None:
        return None
    return date.fromisoformat(date_text)


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = run_self_play(
        campaigns_dir=parsed_arguments.campaigns_dir,
        name=parsed_arguments.name,
        session_date=parse_date(parsed_arguments.date_text),
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
