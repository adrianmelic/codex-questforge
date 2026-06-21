"""Plan varied Questforge DCs from fictional position and stakes."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Iterable

DC_STEPS = [
    ("very_easy", 5),
    ("easy", 10),
    ("medium", 15),
    ("hard", 20),
    ("very_hard", 25),
    ("nearly_impossible", 30),
]
STEP_INDEX = {name: index for index, (name, _) in enumerate(DC_STEPS)}


@dataclass(frozen=True)
class DCPlan:
    roll_required: bool
    dc: int | None
    difficulty: str
    mode: str
    reason: str
    warnings: list[str]
    alternatives: list[str]


def plan_dc(
    difficulty: str = "medium",
    position: str = "normal",
    approach: str = "ordinary",
    stakes: str = "normal",
    repeat_failures: int = 0,
    recent_dcs: list[int] | None = None,
) -> DCPlan:
    """Return a 5E-style DC plan with anti-clustering warnings."""

    recent_dcs = recent_dcs or []
    warnings = build_recent_dc_warnings(recent_dcs)
    alternatives = [
        "Use no roll when the action is safe, obvious, or only costs time.",
        "Use an opposed roll when an active NPC resists directly.",
        "Use a resource tradeoff when failure would only mean trying again.",
    ]

    if repeat_failures >= 2:
        return DCPlan(
            roll_required=False,
            dc=None,
            difficulty="failure_forward",
            mode="no_roll",
            reason=(
                "The obstacle has already produced two failed checks; move "
                "the scene forward with a cost or new route."
            ),
            warnings=warnings,
            alternatives=alternatives,
        )

    if difficulty == "auto":
        return DCPlan(
            roll_required=False,
            dc=None,
            difficulty="auto",
            mode="no_roll",
            reason="The fiction does not need a roll; grant progress.",
            warnings=warnings,
            alternatives=alternatives,
        )

    if difficulty == "contest":
        return DCPlan(
            roll_required=True,
            dc=None,
            difficulty="contest",
            mode="opposed_roll",
            reason="An active opponent is resisting; roll against them.",
            warnings=warnings,
            alternatives=alternatives,
        )

    rank = STEP_INDEX[difficulty]
    rank += rank_adjustment(position, approach, stakes)
    rank = max(0, min(rank, len(DC_STEPS) - 1))
    planned_difficulty, dc = DC_STEPS[rank]

    if dc in {13, 14}:
        warnings.append(
            "Avoid defaulting to DC 13/14; use clear 5E anchors unless the "
            "fiction demands a fine adjustment."
        )

    return DCPlan(
        roll_required=True,
        dc=dc,
        difficulty=planned_difficulty,
        mode="fixed_dc",
        reason=build_reason(
            planned_difficulty, dc, difficulty, position, approach, stakes
        ),
        warnings=warnings,
        alternatives=alternatives,
    )


def rank_adjustment(position: str, approach: str, stakes: str) -> int:
    adjustment = 0
    if position == "strong":
        adjustment -= 1
    elif position == "weak":
        adjustment += 1

    if approach == "clever":
        adjustment -= 1
    elif approach == "poor":
        adjustment += 1

    return adjustment


def build_recent_dc_warnings(recent_dcs: list[int]) -> list[str]:
    if len(recent_dcs) < 4:
        return []
    if min(recent_dcs) >= 12 and max(recent_dcs) <= 15:
        return [
            (
                "Recent DCs are clustered between 12 and 15. Consider no "
                "roll, DC 10, DC 15, DC 20, an opposed roll, or a resource "
                "tradeoff based on the fiction."
            )
        ]
    return []


def build_reason(
    planned_difficulty: str,
    dc: int,
    requested_difficulty: str,
    position: str,
    approach: str,
    stakes: str,
) -> str:
    parts = [
        f"Use DC {dc} ({planned_difficulty.replace('_', ' ')})",
        f"from requested {requested_difficulty.replace('_', ' ')} difficulty",
    ]
    adjustments = []
    if position != "normal":
        adjustments.append(f"{position} position")
    if approach != "ordinary":
        adjustments.append(f"{approach} approach")
    if stakes != "normal":
        adjustments.append(f"{stakes} stakes")
    if adjustments:
        parts.append("adjusted by " + ", ".join(adjustments))
    return "; ".join(parts) + "."


def format_markdown(plan: DCPlan) -> str:
    lines = [
        "# Questforge DC Plan",
        "",
        f"- Mode: `{plan.mode}`",
        f"- Roll required: `{str(plan.roll_required).lower()}`",
        f"- Difficulty: `{plan.difficulty}`",
        f"- DC: `{plan.dc if plan.dc is not None else 'none'}`",
        f"- Reason: {plan.reason}",
        "",
        "## Alternatives",
        "",
    ]
    for alternative in plan.alternatives:
        lines.append(f"- {alternative}")
    lines.extend(["", "## Warnings", ""])
    if plan.warnings:
        for warning in plan.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan varied Questforge check DCs."
    )
    parser.add_argument(
        "--difficulty",
        choices=(
            "auto",
            "very_easy",
            "easy",
            "medium",
            "hard",
            "very_hard",
            "nearly_impossible",
            "contest",
        ),
        default="medium",
    )
    parser.add_argument(
        "--position", choices=("strong", "normal", "weak"), default="normal"
    )
    parser.add_argument(
        "--approach",
        choices=("clever", "ordinary", "poor"),
        default="ordinary",
    )
    parser.add_argument(
        "--stakes", choices=("low", "normal", "high"), default="normal"
    )
    parser.add_argument("--repeat-failures", type=int, default=0)
    parser.add_argument("--recent-dc", action="append", type=int, default=[])
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    parsed_arguments = build_parser().parse_args(arguments)
    plan = plan_dc(
        difficulty=parsed_arguments.difficulty,
        position=parsed_arguments.position,
        approach=parsed_arguments.approach,
        stakes=parsed_arguments.stakes,
        repeat_failures=parsed_arguments.repeat_failures,
        recent_dcs=parsed_arguments.recent_dc,
    )
    if parsed_arguments.format == "json":
        print(json.dumps(asdict(plan), indent=2, ensure_ascii=False))
    else:
        print(format_markdown(plan), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
