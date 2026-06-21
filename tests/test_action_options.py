import pytest

from scripts.action_options import format_option_table, parse_option


def test_parse_option_and_format_table():
    option = parse_option(
        "Force the hatch|Dexterity (Thieves' Tools)|+5|DC 14|Noise from below|"
        "the hatch opens|the patrol hears you, but a new entry opens"
    )

    table = format_option_table([option])

    assert option.modifier == "+5"
    assert "| Force the hatch | Dexterity (Thieves' Tools) | +5 |" in table
    assert "You can also describe a different action." in table
    assert "Failure still moves play" in table


def test_parse_option_rejects_missing_fields():
    with pytest.raises(ValueError, match="7 pipe-separated"):
        parse_option("Hide|Dexterity")
