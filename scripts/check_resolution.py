"""Resolve Questforge checks without letting failed rolls stall play."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class CheckResolution:
    """Structured result for one uncertain action."""

    total: int
    dc: int
    outcome: str
    margin: int
    must_move_scene: bool
    summary: str


def resolve_check(
    total: int,
    dc: int,
    action: str,
    success: str,
    failure_cost: str,
    new_option: str,
    failure_count: int = 0,
) -> CheckResolution:
    """Classify a check and require a failure-forward consequence."""

    if dc <= 0:
        raise ValueError("DC must be positive.")
    if not action.strip():
        raise ValueError("Action is required.")
    if not success.strip():
        raise ValueError("Success result is required.")
    if not failure_cost.strip() or not new_option.strip():
        raise ValueError("Failure requires both failure_cost and new_option.")
    if failure_count < 0:
        raise ValueError("Failure count cannot be negative.")

    margin = total - dc
    must_move_scene = failure_count >= 2
    if total >= dc:
        outcome = "success"
        summary = f"{action}: success. {sentence(success)}"
    elif total >= dc - 3:
        outcome = "success_with_cost"
        summary = (
            f"{action}: partial success. {sentence(success)} "
            f"Cost: {sentence(failure_cost)}"
        )
    else:
        outcome = "failure_forward"
        summary = (
            f"{action}: failure, but play moves. "
            f"Cost: {sentence(failure_cost)} "
            f"New option: {sentence(new_option)}"
        )
    if must_move_scene and outcome == "failure_forward":
        summary += " Do not ask for another roll against the same obstacle."
    return CheckResolution(
        total=total,
        dc=dc,
        outcome=outcome,
        margin=margin,
        must_move_scene=must_move_scene,
        summary=summary,
    )


def sentence(value: str) -> str:
    stripped_value = value.strip()
    if stripped_value.endswith((".", "!", "?")):
        return stripped_value
    return stripped_value + "."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve a Questforge check with failure-forward output."
    )
    parser.add_argument("--total", required=True, type=int)
    parser.add_argument("--dc", required=True, type=int)
    parser.add_argument("--action", required=True)
    parser.add_argument("--success", required=True)
    parser.add_argument("--failure-cost", required=True)
    parser.add_argument("--new-option", required=True)
    parser.add_argument("--failure-count", type=int, default=0)
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    resolution = resolve_check(
        total=parsed_arguments.total,
        dc=parsed_arguments.dc,
        action=parsed_arguments.action,
        success=parsed_arguments.success,
        failure_cost=parsed_arguments.failure_cost,
        new_option=parsed_arguments.new_option,
        failure_count=parsed_arguments.failure_count,
    )
    if parsed_arguments.format == "json":
        print(json.dumps(asdict(resolution), indent=2, ensure_ascii=False))
    else:
        print(f"- Outcome: `{resolution.outcome}`")
        print(f"- Margin: `{resolution.margin}`")
        print(
            f"- Must move scene: `{str(resolution.must_move_scene).lower()}`"
        )
        print(f"- Summary: {resolution.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
