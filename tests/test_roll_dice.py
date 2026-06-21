import random

import pytest

from scripts.roll_dice import parse_notation, roll_dice


def test_parse_notation_accepts_common_forms():
    assert parse_notation("d20") == (1, 20, 0)
    assert parse_notation("2d6+3") == (2, 6, 3)
    assert parse_notation("1d8 - 1") == (1, 8, -1)


def test_seeded_normal_roll_is_reproducible():
    result = roll_dice("2d6+3", random_generator=random.Random(7))

    assert result.rolls == (3, 2)
    assert result.kept == (3, 2)
    assert result.total == 8
    assert result.summary() == "2d6+3 (normal): [3, 2] + 3 = 8"


def test_advantage_keeps_highest_d20():
    result = roll_dice(
        "d20+2",
        mode="advantage",
        random_generator=random.Random(1),
    )

    assert result.rolls == (5, 19)
    assert result.kept == (19,)
    assert result.dropped == (5,)
    assert result.total == 21


def test_disadvantage_keeps_lowest_d20():
    result = roll_dice(
        "d20-1",
        mode="disadvantage",
        random_generator=random.Random(1),
    )

    assert result.rolls == (5, 19)
    assert result.kept == (5,)
    assert result.dropped == (19,)
    assert result.total == 4


def test_advantage_rejects_non_d20_expression():
    with pytest.raises(ValueError, match="only to 1d20"):
        roll_dice("2d6", mode="advantage")


def test_rejects_invalid_notation():
    with pytest.raises(ValueError, match="Unsupported"):
        parse_notation("fireball")
