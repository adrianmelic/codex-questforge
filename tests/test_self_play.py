from datetime import date

from scripts.self_play import run_self_play


def test_self_play_creates_playable_campaign_artifacts(tmp_path):
    result = run_self_play(
        campaigns_dir=tmp_path,
        name="The Clockwork Apiary",
        session_date=date(2026, 5, 17),
    )

    assert result.visual_prompt_count == 4
    assert set(result.visual_kinds) == {"item", "location", "map", "recap"}
    assert "1d20+4" in result.roll_summary
    assert result.turn_count == 12

    campaign_root = tmp_path / "the-clockwork-apiary"
    report_path = campaign_root / "self-play-report.md"
    transcript_path = campaign_root / "self-play-transcript.md"
    campaign_state_path = campaign_root / "campaign-state.md"
    adventure_spine_path = campaign_root / "dm" / "adventure-spine.md"
    puzzle_ledger_path = campaign_root / "dm" / "puzzle-ledger.md"
    visual_index_path = campaign_root / "images" / "visual-index.md"
    session_two_path = campaign_root / "sessions" / "session-002.md"

    assert report_path.exists()
    assert transcript_path.exists()
    assert session_two_path.exists()

    report = report_path.read_text(encoding="utf-8")
    assert "self-play-transcript.md` with 12 turns" in report

    transcript = transcript_path.read_text(encoding="utf-8")
    assert transcript.count("### Turn ") == 12
    assert "Rules lookup target: ability checks." in transcript
    assert "Visual prompt saved: exploration map." in transcript
    assert "Empty Hives clock advances to 1/6" in " ".join(transcript.split())

    campaign_state = campaign_state_path.read_text(encoding="utf-8")
    assert "Self-Play State Patch" not in campaign_state
    assert "| Mara Vey | Self-play | Human | Ranger | 1 |" in campaign_state
    assert "| Empty Hives | 6 | 1 |" in campaign_state
    assert "| Brass Hive Key | Apprentice Nilo |" in campaign_state

    adventure_spine = adventure_spine_path.read_text(encoding="utf-8")
    assert (
        "A false queen scent is emptying the communal hives" in adventure_spine
    )
    assert "active" in adventure_spine

    puzzle_ledger = puzzle_ledger_path.read_text(encoding="utf-8")
    assert "Three Waggle Angles" in puzzle_ledger
    assert "shallow angle points toward the blue orchard" in puzzle_ledger

    session_two = session_two_path.read_text(encoding="utf-8")
    assert "- Characters present: Mara Vey" in session_two
    assert "Mara discovered that blue queen scent" in session_two
    assert "confront the honey factor" in session_two

    visual_index = visual_index_path.read_text(encoding="utf-8")
    assert "Brass Hive Key" in visual_index
    assert "Apiary Terrace Map" in visual_index
