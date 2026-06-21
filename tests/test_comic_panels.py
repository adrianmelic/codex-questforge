import pytest

from scripts.comic_panels import build_comic_prompt, classify_visual_format


def test_classify_two_moment_beat_as_comic_page():
    plan = classify_visual_format(
        "Iria paga al posadero en la puerta del cuarto y luego baja a "
        "desayunar en la sala común."
    )

    assert plan.kind == "comic_page_2"
    assert plan.panel_count == 2


def test_classify_spatial_request_as_map_or_diagram():
    plan = classify_visual_format(
        "Necesito entender la ruta, dónde está la salida y decidir por dónde ir."
    )

    assert plan.kind == "map_or_diagram"


def test_build_comic_prompt_requires_clear_panels():
    prompt = build_comic_prompt(
        title="Morning At The Inn",
        panels=[
            "At the room door, Iria pays the innkeeper with her good hand.",
            "Downstairs, Iria eats breakfast and watches the hooded traveler.",
        ],
        continuity="Iria keeps her left hand bandaged.",
    )

    assert "2 ordered panels" in prompt
    assert "Iria keeps her left hand bandaged" in prompt
    assert "no speech bubbles" in prompt


def test_build_comic_prompt_rejects_invalid_panel_count():
    with pytest.raises(ValueError, match="2, 4, or 6"):
        build_comic_prompt("Bad page", ["one panel"])
