import json

from scripts.narrative_lint import (
    format_markdown,
    lint_documents,
    lint_text,
    main,
    material_anchor_categories,
)


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
        "The baker owes two months of rent, the guild inspector wants coin, "
        "sun has cracked the flour bins, and the mayor hides a normal ledger "
        "to protect her brother from guild law."
    )

    result = lint_text(text)

    assert result.ok
    assert result.warning_count == 0


def test_material_grounding_accepts_many_domains_without_rain():
    text = (
        "Hot forge iron burns through the last charcoal while two sisters "
        "argue over wages, a council permit, and the cart needed for market."
    )

    categories = material_anchor_categories(text)

    assert categories >= {
        "livelihood",
        "institutions",
        "relationships",
        "logistics",
        "built_environment",
    }


def test_lint_warns_when_openings_repeat_an_environmental_crutch():
    documents = [
        "Rain covers the mill while rain rattles its roof.",
        "Lluvia sobre el mercado y lluvia en los toldos.",
        "A storm and rain close the northern road.",
        "Rain hides the tracks beside the old forge.",
    ]

    result = lint_documents(documents)

    assert not result.ok
    assert any(
        issue.code == "environmental_motif_repeated_across_openings"
        and "precipitation" in issue.categories
        for issue in result.issues
    )


def test_lint_accepts_environmentally_varied_openings():
    documents = [
        "Noon glare flashes across an alpine lens workshop.",
        "Actors rehearse on dew-cool boards at a spring amphitheater.",
        "A caravan crosses black salt at a copper sunset.",
        "Warm orchard dust hangs above the communal press.",
    ]

    result = lint_documents(documents)

    assert not any(
        issue.code == "environmental_motif_repeated_across_openings"
        for issue in result.issues
    )


def test_corpus_lint_does_not_stack_unrelated_motifs_across_drafts():
    documents = [
        "One family guards a memory archive beside a working forge.",
        "A living object bargains for wages in a crowded market.",
        "A monastery follows one secret rule about its food stores.",
    ]

    result = lint_documents(documents)

    assert not any(
        issue.code == "metaphysical_pileup" for issue in result.issues
    )


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
    assert "material pressure" in output


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
