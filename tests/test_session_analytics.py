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


def test_structured_events_make_analysis_language_independent(tmp_path):
    session_log = tmp_path / "session-001.md"
    session_log.write_text(
        """# Registro de sesión

## Escenas

### Escena 1

- Tirada: Destreza +4 contra CD 10; total 8, fallo.

### Escena 2

- Tirada: Carisma +5 contra CD 15; total 18, éxito.
""",
        encoding="utf-8",
    )
    events_path = tmp_path / "session-events.jsonl"
    events_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_type": "check",
                        "session": 1,
                        "scene": 1,
                        "dc": 10,
                        "modifier": "4",
                        "roll_total": 8,
                        "advantage_state": "normal",
                        "outcome": "failure",
                    }
                ),
                json.dumps(
                    {
                        "event_type": "check",
                        "session": 1,
                        "scene": 2,
                        "dc": 15,
                        "modifier": "5",
                        "roll_total": 18,
                        "advantage_state": "advantage",
                        "outcome": "success",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = analyze_session(session_log, events_path=events_path)

    assert result.scenes == 2
    assert result.checks == 2
    assert result.dc_distribution == {10: 1, 15: 1}
    assert result.successes == 1
    assert result.failures == 1
    assert result.advantage_count == 1
    assert result.modifier_distribution == {"+4": 1, "+5": 1}


def test_analysis_distinguishes_prompts_from_generated_visuals(tmp_path):
    session_log = tmp_path / "session-001.md"
    session_log.write_text("# Session Log\n", encoding="utf-8")
    visual_index = tmp_path / "visual-index.md"
    visual_index.write_text(
        """# Visual Index

| Kind | Label | Session | Scene | Prompt Path | Status | Asset Path |
| --- | --- | ---: | ---: | --- | --- | --- |
| scene | Harbor | 1 | 1 | images/prompts/harbor.md | prompt-saved | - |
""",
        encoding="utf-8",
    )

    result = analyze_session(session_log, visual_index=visual_index)

    assert result.visual_count == 1
    assert result.generated_visual_count == 0
    assert result.pending_visual_count == 1
    assert any(
        warning.code == "visuals_not_generated" for warning in result.warnings
    )


def test_analysis_warns_when_one_dc_dominates(tmp_path):
    session_log = tmp_path / "session-001.md"
    session_log.write_text("# Session Log\n", encoding="utf-8")
    events_path = tmp_path / "session-events.jsonl"
    events = [
        {
            "event_type": "check",
            "session": 1,
            "scene": 1,
            "dc": dc,
            "modifier": 3,
            "roll_total": 12,
            "outcome": "success",
        }
        for dc in [10, 10, 10, 10, 15]
    ]
    events_path.write_text(
        "\n".join(json.dumps(event) for event in events) + "\n",
        encoding="utf-8",
    )

    result = analyze_session(session_log, events_path=events_path)

    assert any(
        warning.code == "dc_value_dominant" for warning in result.warnings
    )
