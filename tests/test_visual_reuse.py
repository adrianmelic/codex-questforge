from datetime import date

import pytest

from scripts.campaign_memory import (
    create_campaign,
    register_visual_asset,
    save_visual_prompt,
)
from scripts.visual_reuse import create_scene_frame_prompt, read_prompt_excerpt


def add_canon_anchor(
    tmp_path,
    campaign_root,
    session_number,
    scene_number,
    kind,
    label,
    prompt,
    asset_name,
):
    prompt_path = save_visual_prompt(
        campaign_root,
        session_number=session_number,
        scene_number=scene_number,
        kind=kind,
        label=label,
        prompt=prompt,
    )
    source_asset = tmp_path / asset_name
    source_asset.write_bytes(b"fake-png")
    register_visual_asset(
        campaign_root,
        asset_source=source_asset,
        asset_filename=asset_name,
        prompt_path=prompt_path.relative_to(campaign_root),
        status="canon",
    )
    return prompt_path


def test_create_scene_frame_prompt_reuses_canon_anchors(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Rootbound Vault",
        tone="tense exploration",
        session_date=date(2026, 5, 17),
    )
    add_canon_anchor(
        tmp_path,
        paths.root,
        session_number=0,
        scene_number=1,
        kind="character",
        label="Tamsin Reed Reference Sheet",
        prompt=(
            "Small halfling delver in dark travel gear with a chalk pouch, "
            "careful posture, front and three-quarter views."
        ),
        asset_name="tamsin-reed-reference.png",
    )
    add_canon_anchor(
        tmp_path,
        paths.root,
        session_number=0,
        scene_number=2,
        kind="creature",
        label="Bramble Sentinel Reference Sheet",
        prompt=(
            "Braided root guardian with green ember eyes, cracked pale stone "
            "mask, wet root armor silhouette."
        ),
        asset_name="bramble-sentinel-reference.png",
    )

    result = create_scene_frame_prompt(
        paths.root,
        session_number=1,
        scene_number=4,
        label="Tamsin Marks The Safe Moss Path",
        action=(
            "Tamsin marks the safe moss path with chalk while the Bramble "
            "Sentinel pushes through the root door."
        ),
        purpose="show the consequence of the player's movement choice",
        context="inside the Rootbound Vault entry chamber",
        roll_summary="Dexterity check DC 15: 17",
        outcome="success with a noisy complication",
        anchor_labels=[
            "Tamsin Reed Reference Sheet",
            "Bramble Sentinel Reference Sheet",
        ],
        require_asset=True,
    )

    prompt_path = paths.root / result.prompt_path
    prompt_text = prompt_path.read_text(encoding="utf-8")

    assert result.anchor_count == 2
    assert "Tamsin Reed Reference Sheet" in prompt_text
    assert "Bramble Sentinel Reference Sheet" in prompt_text
    assert "images/assets/tamsin-reed-reference.png" in prompt_text
    assert "images/assets/bramble-sentinel-reference.png" in prompt_text
    assert (
        "reuse the listed anchors instead of redesigning them" in prompt_text
    )
    assert "Tamsin marks the safe moss path with chalk" in prompt_text
    assert "Roll: Dexterity check DC 15: 17." in prompt_text
    assert "Resolved outcome: success with a noisy complication." in (
        prompt_text
    )
    assert "root door.." not in prompt_text

    visual_index = paths.visual_index.read_text(encoding="utf-8")
    assert (
        "| scene | Tamsin Marks The Safe Moss Path | 1 | 4 |" in visual_index
    )


def test_create_scene_frame_prompt_reports_missing_anchor(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Rootbound Vault",
        tone="tense exploration",
        session_date=date(2026, 5, 17),
    )

    with pytest.raises(ValueError, match="Missing requested"):
        create_scene_frame_prompt(
            paths.root,
            session_number=1,
            scene_number=4,
            label="Missing Anchor Scene",
            action="Tamsin opens the root door.",
            anchor_labels=["Bramble Sentinel Reference Sheet"],
        )


def test_read_prompt_excerpt_removes_frontmatter(tmp_path):
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text(
        "---\nkind: item\nlabel: Green Fire Seed\n---\n\nGlowing seed.",
        encoding="utf-8",
    )

    assert read_prompt_excerpt(tmp_path, "prompt.md") == "Glowing seed."
