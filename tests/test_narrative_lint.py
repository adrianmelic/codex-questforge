import json

from scripts.narrative_lint import format_markdown, lint_text, main


def test_lint_detects_metaphysical_pileup_without_banning_motifs():
    text = (
        "El pueblo entrega recuerdos a una caja consciente. Hay un contrato "
        "que nadie puede decir en voz alta, y una regla secreta gobierna cada "
        "promesa cuando el rumor se vuelve real."
    )

    result = lint_text(text)

    assert not result.ok
    assert any(issue.code == "metaphysical_pileup" for issue in result.issues)
    assert {hit.category for hit in result.hits} >= {
        "memory_trade",
        "sentient_contract",
        "secret_rules",
        "unsayable",
    }


def test_lint_accepts_grounded_fantasy_scene():
    text = (
        "The miller owes two months of rent, the bridge guard wants coin, "
        "rain has spoiled the flour, and the mayor hides a normal ledger to "
        "protect her brother from guild law."
    )

    result = lint_text(text)

    assert result.ok
    assert result.warning_count == 0


def test_lint_marks_theme_overexplicit_as_info_only():
    text = (
        "The truth of the lesson gives meaning to every moral choice, and the "
        "theme of destiny becomes the final truth of the road."
    )

    result = lint_text(text)

    assert result.ok
    assert result.warning_count == 0
    assert any(issue.code == "theme_overexplicit" for issue in result.issues)


def test_markdown_output_includes_revision_nudge():
    result = lint_text("A memory bargain with an object.")
    output = format_markdown(result)

    assert "Questforge Narrative Lint" in output
    assert "Revision Nudge" in output
    assert "mundane pressure" in output


def test_cli_json_reports_warnings(capsys):
    exit_code = main(
        [
            "--text",
            (
                "Memory is traded under a contract with a sentient object. "
                "No one can say the secret rule out loud."
            ),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["warning_count"] >= 1
