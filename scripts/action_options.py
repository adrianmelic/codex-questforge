"""Format player-facing Questforge action options with modifiers and risk."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class ActionOption:
    """One suggested action the player may choose or ignore."""

    action: str
    check: str
    modifier: str
    difficulty: str
    risk: str
    success: str
    failure_forward: str


def parse_option(value: str) -> ActionOption:
    parts = [part.strip() for part in value.split("|")]
    if len(parts) != 7:
        raise ValueError(
            "Options must use 7 pipe-separated fields: action|check|modifier|"
            "difficulty|risk|success|failure_forward."
        )
    return ActionOption(*parts)


def format_option_table(options: list[ActionOption]) -> str:
    if not options:
        raise ValueError("At least one action option is required.")
    rows = [
        "| Option | Check | Mod | Difficulty | Visible Risk |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for option in options:
        rows.append(
            (
                f"| {cell(option.action)} | {cell(option.check)} | "
                f"{cell(option.modifier)} | {cell(option.difficulty)} | "
                f"{cell(option.risk)} |"
            )
        )
    rows.extend(
        [
            "",
            "You can also describe a different action.",
            "",
            "Resolution notes:",
        ]
    )
    for option in options:
        rows.append(
            (
                f"- **{option.action}**: success means "
                f"{sentence(option.success)} Failure still moves play: "
                f"{sentence(option.failure_forward)}"
            )
        )
    return "\n".join(rows)


def cell(value: str) -> str:
    return " ".join(value.split()).replace("|", "\\|")


def sentence(value: str) -> str:
    stripped_value = value.strip()
    if stripped_value.endswith((".", "!", "?")):
        return stripped_value
    return stripped_value + "."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render Questforge action options with modifiers."
    )
    parser.add_argument(
        "--option",
        action="append",
        required=True,
        help=(
            "Pipe-separated action option: action|check|modifier|difficulty|"
            "risk|success|failure_forward"
        ),
    )
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    options = [parse_option(value) for value in parsed_arguments.option]
    if parsed_arguments.format == "json":
        print(
            json.dumps(
                [asdict(option) for option in options],
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(format_option_table(options))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
