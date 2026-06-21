from datetime import date

from scripts.self_play import run_self_play


def test_self_play_creates_playable_campaign_artifacts(tmp_path):
    result = run_self_play(
        campaigns_dir=tmp_path,
        name="The Amber Gate",
        session_date=date(2026, 5, 17),
    )

    assert result.visual_prompt_count == 4
    assert set(result.visual_kinds) == {"item", "location", "map", "recap"}
    assert "1d20+4" in result.roll_summary
    assert result.turn_count == 12

    report_path = tmp_path / "the-amber-gate" / "self-play-report.md"
    transcript_path = tmp_path / "the-amber-gate" / "self-play-transcript.md"
    campaign_state_path = tmp_path / "the-amber-gate" / "campaign-state.md"
    adventure_spine_path = (
        tmp_path / "the-amber-gate" / "dm" / "adventure-spine.md"
    )
    puzzle_ledger_path = (
        tmp_path / "the-amber-gate" / "dm" / "puzzle-ledger.md"
    )
    visual_index_path = (
        tmp_path / "the-amber-gate" / "images" / "visual-index.md"
    )
    session_two_path = (
        tmp_path / "the-amber-gate" / "sessions" / "session-002.md"
    )

    assert report_path.exists()
    assert transcript_path.exists()
    assert session_two_path.exists()

    report = report_path.read_text(encoding="utf-8")
    assert "self-play-transcript.md` with 12 turns" in report

    transcript = transcript_path.read_text(encoding="utf-8")
    assert transcript.count("### Turn ") == 12
    assert "Rules lookup target: ability checks." in transcript
    assert "Visual prompt saved: fog-of-war map." in transcript
    assert "Abbey Gate clock advances to 1/6" in " ".join(transcript.split())

    campaign_state = campaign_state_path.read_text(encoding="utf-8")
    assert "Self-Play State Patch" not in campaign_state
    assert "| Mara Vey | Self-play | Human | Ranger | 1 |" in campaign_state
    assert "| Abbey Gate | 6 | 1 |" in campaign_state
    assert "| Copper Map Tube | Brother Caldus |" in campaign_state

    adventure_spine = adventure_spine_path.read_text(encoding="utf-8")
    assert "The amber lantern is out of phase" in adventure_spine
    assert "active" in adventure_spine

    puzzle_ledger = puzzle_ledger_path.read_text(encoding="utf-8")
    assert "Three Lantern Intervals" in puzzle_ledger
    assert "middle gap matches the bridge span" in puzzle_ledger

    session_two = session_two_path.read_text(encoding="utf-8")
    assert "- Characters present: Mara Vey" in session_two
    assert "Mara discovered that the amber lantern exists out of phase" in (
        session_two
    )
    assert "force the lantern back into phase" in session_two

    visual_index = visual_index_path.read_text(encoding="utf-8")
    assert "Copper Map Tube" in visual_index
    assert "Gorge Bridge Fog Map" in visual_index
