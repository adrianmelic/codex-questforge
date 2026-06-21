from scripts.puzzle_beats import (
    PuzzleBeat,
    classify_puzzle_kind,
    render_puzzle_beat,
    validate_puzzle_beat,
)


def test_classify_puzzle_kind_from_summary():
    assert (
        classify_puzzle_kind("choose the route from map timing clues")
        == "route_logic"
    )
    assert classify_puzzle_kind("connect two old promises") == (
        "clue_connection"
    )


def test_render_puzzle_beat_keeps_failure_forward_guardrails():
    puzzle = PuzzleBeat(
        title="The Three Unfinished Bells",
        kind="symbolic_order",
        clues=[
            "The innkeeper said one bell means sleep.",
            "The baker said the dawn bell did not finish.",
        ],
        player_ask="Which bell do you touch first?",
        solution="touch the unfinished dawn bell first",
        fallback="the wrong bell wakes a guard, but opens the side door",
        reward="enter the archive without spending the white key",
        symbolic_weight="broken promises can still open a way forward",
    )

    output = render_puzzle_beat(puzzle)

    assert "Failure-forward fallback" in output
    assert "Do not require exact wording" in output
    assert "Design Warnings\n\n- None." in output


def test_validate_puzzle_warns_on_single_clue_and_missing_symbolism():
    warnings = validate_puzzle_beat(
        PuzzleBeat(
            title="Weak Lock",
            kind="key_choice",
            clues=["The key is white."],
            player_ask="Which key?",
            solution="white key",
            fallback="noise draws a clerk but the door opens",
            reward="archive access",
        )
    )

    assert "Use at least two prior clues" in warnings[0]
    assert any("symbolic weight" in warning for warning in warnings)
