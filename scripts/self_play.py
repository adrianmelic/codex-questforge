"""Deterministic self-play smoke test for Questforge."""

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
    name: str = "The Clockwork Apiary",
    session_date: date | None = None,
) -> SelfPlayResult:
    """Run a deterministic mini-session that exercises the Questforge loop."""

    session_date = session_date or date.today()
    paths = create_campaign(
        campaigns_dir=campaigns_dir,
        name=name,
        tone="bright rural investigation with practical stakes",
        boundaries="no graphic gore",
        session_date=session_date,
    )
    write_hero_sheet(paths.characters / "mara-vey.md")
    record_hook_status(
        paths.root,
        hook="A false queen scent is emptying the communal hives",
        origin="opening scene",
        status="active",
        current_meaning=(
            "the bees can be recovered only if the decoy route is understood"
        ),
        next_payoff="Mara can trace the scent, move the hives, or expose the buyer",
    )
    record_puzzle_beat(
        paths.root,
        title="Three Waggle Angles",
        kind="clue_connection",
        required_clues=[
            "the returning bees carry blue orchard pollen",
            "the brass hive key has three angles cut into its bow",
        ],
        ask_at_table="Which key angle matches the bees' repeated waggle turn?",
        solution="the shallow angle points toward the blue orchard terraces",
        fallback="another hive empties, but the departing swarm reveals the route",
        reward="lower the next tracking DC by 2",
        symbolic_weight="shared labor leaves a direction even when words fail",
        status="prepared",
    )

    roll = roll_dice("d20+4", random_generator=random.Random(9))
    visual_prompts = [
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=1,
            kind="location",
            label="Sunwheel Apiary",
            prompt=(
                "Original 5E-compatible fantasy location, unofficial and not "
                "using official D&D setting, logo, product art, or named "
                "copyrighted character. Subject: a sunlit hillside apiary "
                "with painted wooden hives, orchard terraces, and a decoy "
                "wagon drawing a visible stream of bees. Purpose: establish "
                "the opening location. "
                "Style: painterly fantasy realism, cinematic wide shot, "
                "readable staging. Avoid: official logos, copied product art."
            ),
        ),
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=1,
            kind="item",
            label="Brass Hive Key",
            prompt=(
                "Original 5E-compatible fantasy item, unofficial and not using "
                "official D&D product art. Subject: heavy brass hive key, "
                "three angle notches in the bow, blue pollen in the teeth, "
                "and a red cord. Purpose: persistent clue and inventory "
                "object. Style: isolated prop view on pale workbench wood."
            ),
        ),
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=2,
            kind="map",
            label="Apiary Terrace Map",
            prompt=(
                "Original fantasy player-known exploration map. Subject: "
                "known hive rows, communal press, decoy wagon track, and blue "
                "orchard edge. Hide unvisited storehouses, concealed paths, "
                "and unknown workers under blank parchment. Sparse "
                "table-useful labels only."
            ),
        ),
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=3,
            kind="recap",
            label="The Bees Choose The Decoy",
            prompt=(
                "Original 5E-compatible fantasy recap image. Subject: Mara Vey "
                "realizing a stream of bees follows blue pollen toward a "
                "painted decoy wagon while apprentice Nilo holds the brass "
                "hive key behind her. Purpose: end-of-session postcard. Mood: "
                "bright investigation with practical urgency. Avoid official "
                "setting identifiers and copied art."
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
            "Mara discovered that blue queen scent is drawing the bees toward "
            "the decoy wagon.",
            "Apprentice Nilo now trusts Mara and still holds the brass hive "
            "key.",
            "The first exploration map shows only the known hive terraces and "
            "blue orchard edge.",
        ],
        start_location="upper row of the Sunwheel Apiary",
        pressure="a second communal hive is beginning to empty",
        next_choice=(
            "trace the decoy wagon, move the remaining queens, or confront "
            "the honey factor"
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
                "- Visual anchors: russet work cloak, wrapped bow, blue pollen on boots",
                "- Current goal: protect the communal hives and find the decoy buyer",
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

- Mara arrives while the Sunwheel Apiary is losing its bees to a decoy wagon.
- Apprentice Nilo holds the only hive key while the honey factor demands entry.

## Scenes

### Scene 1

- Location: upper row of the Sunwheel Apiary.
- Pressure: another communal hive is beginning to empty.
- Player action: Mara studies flight paths, pollen, and wheel marks.
- Roll: {roll_summary}
- Outcome: success. Blue pollen links the departing bees to the decoy wagon.
- State changes: clue added; Nilo trusts Mara; Empty Hives clock 1/6.
- Visual prompts saved: location, item.

### Scene 2

- Location: apiary terraces.
- Pressure: the wagon route disappears among working orchard lanes.
- Player action: Mara sketches known terrain before advancing.
- Outcome: exploration map saved without revealing unvisited storehouses.
- State changes: map reference added to visual index.
- Visual prompts saved: map.

### Scene 3

- Location: upper row of the Sunwheel Apiary.
- Pressure: the second hive begins to empty toward the orchard.
- Player action: Mara keeps the hive key visible and prepares to follow.
- Outcome: session closes on a clear next choice.
- Visual prompts saved: recap.

## Rules Rulings

| Ruling | Reason | Keep As House Rule |
| --- | --- | --- |
| Wisdom (Survival), moderate DC | Reading mixed pollen and wagon tracks is uncertain and meaningful. | no |

## End State

- Party position: upper row of the Sunwheel Apiary.
- Immediate next choice: trace the wagon, move the queens, or confront the
  honey factor.
- Changed clocks: Empty Hives 1/6.
- Changed NPC attitudes: Apprentice Nilo trusts Mara.
- Rewards: clue connecting blue pollen to the decoy route.
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
- Tone: bright rural investigation with practical stakes
- Content boundaries: no graphic gore
- House rules:
- SRD attribution included: yes
- Last updated: {session_date.isoformat()}

## Party

| Character | Player | Ancestry | Class | Level | Notes |
| --- | --- | --- | --- | --- | --- |
| Mara Vey | Self-play | Human | Ranger | 1 | Practical protector of the apiary |

## Current Situation

- Location: upper row of the Sunwheel Apiary
- Immediate pressure: a second communal hive is beginning to empty
- Open decision: trace the wagon, move the queens, or confront the honey factor

## Fronts And Clocks

| Front Or Clock | Segments | Filled | Advances When |
| --- | --- | --- | --- |
| Empty Hives | 6 | 1 | Delay, failed tracking, or surrendering the hive key |

## Factions

| Name | Goal | Leverage | Relationship |
| --- | --- | --- | --- |
| South Orchard Factors | Control communal honey contracts | Tax seals and hired collectors | Commercial threat |

## NPCs

| Name | Role | Wants | Visual Anchor | Attitude |
| --- | --- | --- | --- | --- |
| Apprentice Nilo | Apiary key keeper | Keep the communal queens together | Blue pollen on sleeves | Trusts Mara |

## Locations

| Name | Role | Secret Or Pressure | Status |
| --- | --- | --- | --- |
| Sunwheel Apiary | Communal hillside workplace | A decoy scent redirects its bees | Active and exposed |

## Clues

| Clue | Meaning | Confirmed |
| --- | --- | --- |
| Blue pollen on returning bees | The decoy route passes the blue orchard | yes |

## Inventory And Rewards

| Item | Holder | Mechanical Notes | Story Notes |
| --- | --- | --- | --- |
| Brass Hive Key | Apprentice Nilo | Opens communal queen frames | Its angle marks encode terrace directions |

## Visual Continuity

| Subject | Type | Anchor Details | Reuse Notes |
| --- | --- | --- | --- |
| Sunwheel Apiary | location | painted hives, ochre terraces, orchard edge, bright work light | opening location and recurring workplace |
| Brass Hive Key | item | brass key, three angle notches, blue pollen, red cord | persistent clue and inventory object |
| Apiary Terrace Map | map | known hive rows and orchard edge only | reveal only explored areas |

## Open Threads

- Who bought the decoy queen scent?
- Why did Pell cut matching angles into the hive key?
- Can the communal bees be recovered before collection day?
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

Bees stream away from the Sunwheel Apiary toward a painted wagon on the lower
terrace. Apprentice Nilo holds the brass hive key and asks whether Mara wants to
trace the swarm, secure the queen frames, or question the honey factor first.

### Turn 2 - Player

Mara stays beside the upper hives and studies flight paths, pollen, and wagon
marks before anyone moves the queen frames.

### Turn 3 - DM

The action is uncertain and meaningful. Rules lookup target: ability checks.
Ruling: Wisdom (Survival), moderate DC, because Mara is reading animal movement,
mixed pollen, and traffic rather than recalling lore.

### Turn 4 - Player

Mara accepts the risk and keeps Nilo beside the closed frames while she checks
which returning bees carry pollen from outside the communal terraces.

### Turn 5 - DM

Open roll: {roll_summary}. Success. Blue pollen appears only on bees returning
from the decoy wagon. Someone painted the wagon with imported queen scent and
parked it along a deliberate route.

### Turn 6 - Player

Mara asks Nilo who cut the three angles into the brass hive key, and she asks to
see it before the honey factor takes it.

### Turn 7 - DM

Nilo admits clerk Pell recut the key after the spring inspection. The three
angles match the bees' repeated waggle turns and point toward different orchard
terraces.

### Turn 8 - Player

Mara wants a clear visual record of the key before anyone tampers with it.

### Turn 9 - DM

Visual prompt saved: item, Brass Hive Key. The prompt records the three angle
notches, blue pollen, worn teeth, and red cord so the object can remain visually
consistent later.

### Turn 10 - Player

Mara sketches only what she can verify: the hive rows, communal press, wagon
track, and blue orchard edge. She refuses to mark storehouses she has not seen.

### Turn 11 - DM

Visual prompt saved: exploration map. Unvisited storehouses, concealed routes,
and unknown workers stay covered by blank parchment. Empty Hives clock advances
to 1/6 because another queen frame begins to lose its workers.

### Turn 12 - Player

Mara ends the session holding position. Next time she will choose whether to
trace the wagon, move the remaining queens, or confront the honey factor.
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
    parser.add_argument("--name", default="The Clockwork Apiary")
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
