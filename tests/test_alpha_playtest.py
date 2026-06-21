from datetime import date
from pathlib import Path

from scripts.alpha_playtest import run_alpha_playtests


def test_alpha_playtests_cover_multiple_fun_modes(tmp_path):
    result = run_alpha_playtests(
        output_dir=tmp_path / "alpha",
        session_date=date(2026, 5, 17),
    )

    assert result.passed is True
    assert result.scenario_count == 3
    assert result.total_turn_count >= 60
    assert result.total_visual_prompt_count >= 15
    assert result.minimum_fun_score >= 85

    modes = {scenario.mode for scenario in result.scenarios}
    assert modes == {
        "dungeon pressure",
        "mystery exploration",
        "social commerce",
    }

    for scenario in result.scenarios:
        assert scenario.turn_count >= 20
        assert scenario.meaningful_choice_count >= 4
        assert scenario.rules_query_count >= 2
        assert scenario.roll_count >= 2
        assert scenario.visual_prompt_count >= 5
        assert len(scenario.visual_kinds) >= 4
        assert scenario.continuity_anchor_count >= 4
        assert scenario.fun_score >= 85


def test_alpha_playtests_write_reviewable_artifacts(tmp_path):
    result = run_alpha_playtests(
        output_dir=tmp_path / "alpha",
        session_date=date(2026, 5, 17),
    )

    summary_path = tmp_path / "alpha" / "alpha-playtest-summary.md"
    assert summary_path.exists()
    summary = summary_path.read_text(encoding="utf-8")
    assert "Questforge Alpha Playtest Summary" in summary
    assert "The Amber Gate Alpha" in summary
    assert "Saltglass Market Alpha" in summary
    assert "Rootbound Vault Alpha" in summary

    first = result.scenarios[0]
    campaign_root = Path(first.campaign_root)
    transcript = first.transcript_path
    report = first.report_path
    next_session = first.next_session_path
    visual_index = campaign_root / "images" / "visual-index.md"

    assert "alpha-playtest-transcript.md" in transcript
    assert "alpha-playtest-report.md" in report
    assert "session-002.md" in next_session
    assert visual_index.exists()

    transcript_text = (
        campaign_root / "alpha-playtest-transcript.md"
    ).read_text(encoding="utf-8")
    assert transcript_text.count("### Turn ") >= 20
    assert "Open roll:" in transcript_text

    visual_index_text = visual_index.read_text(encoding="utf-8")
    assert "prompt-saved" in visual_index_text
    assert "Gorge Bridge Fog Map" in visual_index_text

    rootbound = next(
        scenario
        for scenario in result.scenarios
        if scenario.slug == "rootbound-vault"
    )
    rootbound_transcript = Path(rootbound.transcript_path).read_text(
        encoding="utf-8"
    )
    assert "1d20+6 (normal): [18] + 6 = 24. Success." in (rootbound_transcript)
    assert "1d20+4 (normal): [5] + 4 = 9. Failure." in rootbound_transcript
