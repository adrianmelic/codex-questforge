import pytest

from scripts.check_resolution import resolve_check


def test_resolve_check_success():
    result = resolve_check(
        total=18,
        dc=14,
        action="Open the hatch",
        success="the hatch opens silently",
        failure_cost="the patrol hears the chain",
        new_option="enter through the flour chute",
    )

    assert result.outcome == "success"
    assert result.margin == 4
    assert not result.must_move_scene


def test_resolve_check_failure_forward_after_repeated_failures():
    result = resolve_check(
        total=8,
        dc=14,
        action="Open the hatch",
        success="the hatch opens silently",
        failure_cost="the patrol reaches the wall",
        new_option="force entry now or drop into the canal",
        failure_count=2,
    )

    assert result.outcome == "failure_forward"
    assert result.must_move_scene
    assert "Do not ask for another roll" in result.summary


def test_resolve_check_requires_failure_forward_material():
    with pytest.raises(ValueError, match="failure_cost and new_option"):
        resolve_check(
            total=8,
            dc=14,
            action="Open the hatch",
            success="the hatch opens",
            failure_cost="",
            new_option="",
        )
