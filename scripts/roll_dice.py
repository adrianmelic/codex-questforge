"""Small dice roller for Codex Questforge."""

from __future__ import annotations

import argparse
import random
import re
from dataclasses import dataclass
from typing import Iterable

DICE_PATTERN = re.compile(
    r"^\s*(?P<count>\d*)d(?P<sides>\d+)\s*(?P<modifier>[+-]\s*\d+)?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DiceRoll:
    """Result of a single dice expression."""

    notation: str
    total: int
    rolls: tuple[int, ...]
    modifier: int
    kept: tuple[int, ...]
    dropped: tuple[int, ...]
    mode: str

    def summary(self) -> str:
        modifier_text = ""
        if self.modifier > 0:
            modifier_text = f" + {self.modifier}"
        elif self.modifier < 0:
            modifier_text = f" - {abs(self.modifier)}"

        dropped_text = ""
        if self.dropped:
            dropped_values = ", ".join(str(value) for value in self.dropped)
            dropped_text = f"; dropped {dropped_values}"

        roll_values = ", ".join(str(value) for value in self.rolls)
        return (
            f"{self.notation} ({self.mode}): [{roll_values}]"
            f"{modifier_text} = {self.total}{dropped_text}"
        )


def parse_notation(notation: str) -> tuple[int, int, int]:
    """Parse notation such as d20, 2d6+3, or 1d8 - 1."""

    match = DICE_PATTERN.match(notation)
    if not match:
        raise ValueError(f"Unsupported dice notation: {notation!r}")

    count_text = match.group("count")
    count = int(count_text) if count_text else 1
    sides = int(match.group("sides"))
    modifier_text = match.group("modifier")
    modifier = int(modifier_text.replace(" ", "")) if modifier_text else 0

    if count < 1:
        raise ValueError("Dice count must be at least 1.")
    if sides < 2:
        raise ValueError("Dice sides must be at least 2.")
    if count > 100:
        raise ValueError("Dice count must be 100 or lower.")

    return count, sides, modifier


def roll_dice(
    notation: str,
    mode: str = "normal",
    random_generator: random.Random | None = None,
) -> DiceRoll:
    """Roll a dice expression with optional d20 advantage/disadvantage."""

    count, sides, modifier = parse_notation(notation)
    mode = mode.lower()
    generator = random_generator or random.SystemRandom()

    if mode not in {"normal", "advantage", "disadvantage"}:
        raise ValueError("Mode must be normal, advantage, or disadvantage.")

    if mode in {"advantage", "disadvantage"} and (count, sides) != (1, 20):
        raise ValueError(
            "Advantage and disadvantage apply only to 1d20 rolls."
        )

    if mode == "normal":
        rolls = tuple(generator.randint(1, sides) for _ in range(count))
        kept = rolls
        dropped: tuple[int, ...] = ()
    else:
        rolls = tuple(generator.randint(1, 20) for _ in range(2))
        kept_value = max(rolls) if mode == "advantage" else min(rolls)
        dropped_value = min(rolls) if mode == "advantage" else max(rolls)
        kept = (kept_value,)
        dropped = (dropped_value,)

    total = sum(kept) + modifier
    return DiceRoll(
        notation=normalize_notation(count, sides, modifier),
        total=total,
        rolls=rolls,
        modifier=modifier,
        kept=kept,
        dropped=dropped,
        mode=mode,
    )


def normalize_notation(count: int, sides: int, modifier: int) -> str:
    """Return a compact canonical notation string."""

    modifier_text = ""
    if modifier > 0:
        modifier_text = f"+{modifier}"
    elif modifier < 0:
        modifier_text = str(modifier)
    return f"{count}d{sides}{modifier_text}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Roll dice for Questforge.")
    parser.add_argument("notation", help="Dice notation, for example d20+4.")
    parser.add_argument(
        "--mode",
        choices=("normal", "advantage", "disadvantage"),
        default="normal",
        help="Roll mode. Advantage/disadvantage only support d20.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional deterministic seed for reproducible rolls.",
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    parser = build_parser()
    parsed_arguments = parser.parse_args(arguments)
    generator = (
        random.Random(parsed_arguments.seed)
        if parsed_arguments.seed is not None
        else None
    )
    result = roll_dice(
        parsed_arguments.notation,
        mode=parsed_arguments.mode,
        random_generator=generator,
    )
    print(result.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
