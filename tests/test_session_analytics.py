import json

from scripts.session_analytics import analyze_session, append_event


def write_session(path):
    path.write_text(
        """# Session Log

## Session

- Campaign: Test
- Session: 1

## Scenes

### Scene 1

- Risk read: Destreza +5, CD 14, para cruzar sin ruido; Sabiduria +3, CD 13, para leer la sala.
- Roll: Destreza 1d20+5 = 18. Sabiduria 1d20+3 con ventaja = 12.

### Scene 2

- Roll: Fuerza para abrir la reja, CD 12: 1d20-1 = 10.
""",
        encoding="utf-8",
    )


def write_visual_index(path):
    path.write_text(
        """# Visual Index

| Kind | Label | Session | Scene | Prompt Path | Status | Asset Path |
| --- | --- | ---: | ---: | --- | --- | --- |
| scene | Door | 1 | 1 | images/prompts/door.md | canon | images/assets/door.png |
| map | Room Map | 1 | 2 | images/prompts/map.md | canon | images/assets/map.png |
""",
        encoding="utf-8",
    )


def test_analyze_session_extracts_dc_distribution_and_outcomes(tmp_path):
    session_log = tmp_path / "session-001.md"
    visual_index = tmp_path / "visual-index.md"
    write_session(session_log)
    write_visual_index(visual_index)

    result = analyze_session(session_log, visual_index=visual_index)

    assert result.scenes == 2
    assert result.checks == 3
    assert result.paired_checks == 3
    assert result.dc_distribution == {12: 1, 13: 1, 14: 1}
    assert result.successes == 1
    assert result.failures == 2
    assert result.advantage_count == 1
    assert result.visual_kind_distribution == {"map": 1, "scene": 1}
    assert any(
        warning.code == "dc_range_narrow" for warning in result.warnings
    )


def test_append_event_writes_structured_jsonl(tmp_path):
    events_path = append_event(
        tmp_path,
        {
            "event_type": "check",
            "session": 1,
            "scene": 2,
            "dc": 16,
            "roll_total": 12,
            "tags": ["stealth", "failure-forward"],
        },
    )

    payload = json.loads(events_path.read_text(encoding="utf-8"))

    assert payload["event_type"] == "check"
    assert payload["dc"] == 16
    assert payload["tags"] == ["stealth", "failure-forward"]
