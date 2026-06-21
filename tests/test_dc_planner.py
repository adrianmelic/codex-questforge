from scripts.dc_planner import plan_dc


def test_dc_planner_uses_5e_anchor_dcs():
    plan = plan_dc(difficulty="medium")

    assert plan.roll_required is True
    assert plan.dc == 15
    assert plan.difficulty == "medium"


def test_dc_planner_moves_easy_when_position_and_approach_are_good():
    plan = plan_dc(
        difficulty="medium",
        position="strong",
        approach="clever",
        stakes="normal",
    )

    assert plan.dc == 5
    assert plan.difficulty == "very_easy"


def test_dc_planner_moves_hard_when_position_and_stakes_are_bad():
    plan = plan_dc(
        difficulty="medium",
        position="weak",
        approach="poor",
        stakes="high",
    )

    assert plan.dc == 25
    assert plan.difficulty == "very_hard"


def test_dc_planner_stops_repeated_failure_rolls():
    plan = plan_dc(repeat_failures=2)

    assert plan.roll_required is False
    assert plan.mode == "no_roll"
    assert plan.difficulty == "failure_forward"


def test_dc_planner_warns_on_recent_narrow_dc_cluster():
    plan = plan_dc(recent_dcs=[13, 14, 14, 13])

    assert any("12 and 15" in warning for warning in plan.warnings)
