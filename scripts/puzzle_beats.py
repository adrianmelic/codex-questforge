"""Draft non-blocking Questforge deduction beats and minigames."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

PUZZLE_KINDS = {
    "clue_connection",
    "symbolic_order",
    "contradiction",
    "route_logic",
    "key_choice",
    "ritual_sequence",
    "social_read",
}

KIND_PATTERNS = {
    "symbolic_order": ["order", "sequence", "first", "second", "last"],
    "contradiction": ["lie", "contradiction", "inconsistent", "alibi"],
    "route_logic": ["route", "map", "path", "door", "exit", "timing"],
    "key_choice": ["key", "seal", "phrase", "tune", "lock"],
    "ritual_sequence": ["ritual", "ingredient", "bell", "oath", "circle"],
    "social_read": ["trust", "pressure", "witness", "confess"],
}


@dataclass(frozen=True)
class PuzzleBeat:
    """One small player-facing reasoning beat."""

    title: str
    kind: str
    clues: list[str]
    player_ask: str
    solution: str
    fallback: str
    reward: str
    symbolic_weight: str = ""


def classify_puzzle_kind(summary: str) -> str:
    """Choose a likely puzzle kind from a short description."""

    text = summary.casefold()
    for kind, patterns in KIND_PATTERNS.items():
        if any(re.search(rf"\b{pattern}\b", text) for pattern in patterns):
            return kind
    return "clue_connection"


def validate_puzzle_beat(puzzle: PuzzleBeat) -> list[str]:
    """Return design warnings for puzzle beats that may feel weak."""

    warnings = []
    if puzzle.kind not in PUZZLE_KINDS:
        warnings.append(f"Unknown kind `{puzzle.kind}`.")
    if len([clue for clue in puzzle.clues if clue.strip()]) < 2:
        warnings.append(
            "Use at least two prior clues for satisfying deduction."
        )
    if len(puzzle.player_ask.split()) > 32:
        warnings.append("Keep the player-facing ask short and concrete.")
    if not puzzle.fallback.strip():
        warnings.append("Add a failure-forward fallback so play cannot block.")
    if not puzzle.reward.strip():
        warnings.append("Add a meaningful reward or changed situation.")
    if not puzzle.symbolic_weight.strip():
        warnings.append(
            "Add symbolic weight if this beat touches a core theme."
        )
    return warnings


def render_puzzle_beat(puzzle: PuzzleBeat) -> str:
    """Render a puzzle beat as a DM-ready Markdown note."""

    clue_lines = "\n".join(f"- {clue.strip()}" for clue in puzzle.clues)
    warnings = validate_puzzle_beat(puzzle)
    warning_lines = "\n".join(f"- {warning}" for warning in warnings)
    if not warning_lines:
        warning_lines = "- None."
    return f"""# Puzzle Beat: {puzzle.title.strip()}

- Kind: `{puzzle.kind}`
- Player-facing ask: {sentence(puzzle.player_ask)}
- Solution: {sentence(puzzle.solution)}
- Failure-forward fallback: {sentence(puzzle.fallback)}
- Reward: {sentence(puzzle.reward)}
- Symbolic weight: {sentence(puzzle.symbolic_weight or "optional")}

## Prior Clues

{clue_lines}

## Guardrails

- Do not require exact wording.
- Accept partial reasoning with progress plus complication.
- After two wrong attempts or a hint request, point back to one clue.
- If still blocked, apply the fallback and keep play moving.

## Design Warnings

{warning_lines}
"""


def sentence(value: str) -> str:
    stripped_value = value.strip()
    if stripped_value.endswith((".", "!", "?")):
        return stripped_value
    return stripped_value + "."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Draft Questforge puzzle beats that cannot block play."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify_parser = subparsers.add_parser("classify")
    classify_parser.add_argument("--summary", required=True)

    draft_parser = subparsers.add_parser("draft")
    draft_parser.add_argument("--title", required=True)
    draft_parser.add_argument("--kind", default="")
    draft_parser.add_argument("--summary", default="")
    draft_parser.add_argument("--clue", action="append", required=True)
    draft_parser.add_argument("--ask", required=True)
    draft_parser.add_argument("--solution", required=True)
    draft_parser.add_argument("--fallback", required=True)
    draft_parser.add_argument("--reward", required=True)
    draft_parser.add_argument("--symbolic-weight", default="")
    draft_parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)

    if parsed_arguments.command == "classify":
        print(classify_puzzle_kind(parsed_arguments.summary))
        return 0

    kind = parsed_arguments.kind or classify_puzzle_kind(
        parsed_arguments.summary or parsed_arguments.title
    )
    puzzle = PuzzleBeat(
        title=parsed_arguments.title,
        kind=kind,
        clues=parsed_arguments.clue,
        player_ask=parsed_arguments.ask,
        solution=parsed_arguments.solution,
        fallback=parsed_arguments.fallback,
        reward=parsed_arguments.reward,
        symbolic_weight=parsed_arguments.symbolic_weight,
    )
    if parsed_arguments.format == "json":
        payload = asdict(puzzle)
        payload["warnings"] = validate_puzzle_beat(puzzle)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_puzzle_beat(puzzle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
