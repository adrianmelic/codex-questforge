import json
from datetime import date

from scripts.campaign_memory import create_campaign, set_visual_status
from scripts.visual_prep import prepare_visuals


def test_prepare_visuals_creates_reference_prompts_and_plan(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Rootbound Vault",
        tone="tense exploration",
        session_date=date(2026, 5, 17),
    )
    spec_path = tmp_path / "visual-prep.json"
    spec_path.write_text(
        json.dumps(
            {
                "title": "Rootbound Vault Visual Prep",
                "style": "painterly fantasy realism",
                "subjects": [
                    {
                        "kind": "character",
                        "label": "Tamsin Reed Reference Sheet",
                        "anchor": "small halfling delver in dark travel gear",
                        "purpose": "canon player-character visual anchor",
                        "sheet": "front, back, three-quarter, cautious crouch",
                        "action": "marking a safe moss path with chalk",
                    },
                    {
                        "kind": "creature",
                        "label": "Bramble Sentinel Reference Sheet",
                        "anchor": (
                            "braided root guardian with green ember eyes and "
                            "cracked pale stone mask"
                        ),
                        "purpose": "canon creature visual anchor",
                        "sheet": "front, side, silhouette, reaching pose",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = prepare_visuals(paths.root, spec_path)

    assert result.subject_count == 2
    assert len(result.prompt_paths) == 2
    assert paths.root.joinpath("visual-prep-plan.md").exists()

    visual_index = paths.visual_index.read_text(encoding="utf-8")
    assert "Tamsin Reed Reference Sheet" in visual_index
    assert "Bramble Sentinel Reference Sheet" in visual_index
    assert (
        "| character | Tamsin Reed Reference Sheet | 0 | 1 |" in visual_index
    )
    assert (
        "| creature | Bramble Sentinel Reference Sheet | 0 | 2 |"
        in visual_index
    )

    first_prompt = paths.image_prompts.joinpath(
        "session-000-scene-001-character-tamsin-reed-reference-sheet.md"
    ).read_text(encoding="utf-8")
    assert "front, back, three-quarter, cautious crouch" in first_prompt
    assert "marking a safe moss path with chalk" in first_prompt
    assert "canon visual anchor" in first_prompt

    plan = paths.root.joinpath("visual-prep-plan.md").read_text(
        encoding="utf-8"
    )
    assert "Canonization Steps" in plan
    assert "set-visual-status --status canon" in plan


def test_visual_prep_prompts_can_be_canonized(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Rootbound Vault",
        tone="tense exploration",
        session_date=date(2026, 5, 17),
    )
    spec_path = tmp_path / "visual-prep.json"
    spec_path.write_text(
        json.dumps(
            {
                "subjects": [
                    {
                        "kind": "creature",
                        "label": "Bramble Sentinel Reference Sheet",
                        "anchor": "braided root guardian",
                        "purpose": "canon creature visual anchor",
                        "sheet": "front, side, attack pose",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    prepare_visuals(paths.root, spec_path)

    set_visual_status(
        paths.root,
        status="canon",
        kind="creature",
        label="Bramble Sentinel Reference Sheet",
        session_number=0,
        scene_number=1,
    )

    visual_index = paths.visual_index.read_text(encoding="utf-8")
    assert "| creature | Bramble Sentinel Reference Sheet | 0 | 1 |" in (
        visual_index
    )
    assert "canon |" in visual_index
