from datetime import date

from scripts.campaign_memory import (
    create_campaign,
    register_visual_asset,
    save_visual_prompt,
)
from scripts.preflight import format_preflight_markdown, run_preflight

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
)


def add_registered_asset(tmp_path, campaign_root, asset_name):
    prompt_path = save_visual_prompt(
        campaign_root=campaign_root,
        session_number=1,
        scene_number=1,
        kind="scene",
        label="Gorge Bridge",
        prompt="A misty bridge above a gorge.",
    )
    source_asset = tmp_path / asset_name
    source_asset.write_bytes(PNG_BYTES)
    return register_visual_asset(
        campaign_root=campaign_root,
        asset_source=source_asset,
        asset_filename=asset_name,
        prompt_path=prompt_path.relative_to(campaign_root),
        status="canon",
    )


def test_preflight_passes_fresh_campaign_with_only_continuity_warning(
    tmp_path,
):
    paths = create_campaign(
        tmp_path,
        "The Amber Gate",
        tone="heroic mystery",
        session_date=date(2026, 5, 23),
    )

    result = run_preflight(paths.root)

    assert result.ok is True
    assert result.error_count == 0
    assert result.warning_count == 1
    assert result.issues[0].code == "empty_visual_ledger"
    assert result.visual_asset_count == 0


def test_preflight_reports_missing_registered_visual_asset(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Broken Gallery",
        session_date=date(2026, 5, 23),
    )
    asset_path = add_registered_asset(tmp_path, paths.root, "bridge.png")
    asset_path.unlink()

    result = run_preflight(paths.root)

    assert result.ok is False
    assert result.error_count == 1
    assert result.missing_visual_asset_count == 1
    assert result.issues[0].code == "missing_visual_asset"


def test_preflight_can_refresh_gallery(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Gallery Ready",
        session_date=date(2026, 5, 23),
    )
    add_registered_asset(tmp_path, paths.root, "bridge.png")

    result = run_preflight(
        paths.root,
        refresh_gallery=True,
        title="Gallery Ready",
    )

    gallery_path = paths.root / "images" / "visual-gallery.html"
    assert result.ok is True
    assert gallery_path.exists()
    assert result.latest_gallery_url.endswith("visual-gallery.html#latest")
    assert result.visual_asset_count == 1


def test_preflight_can_repair_safe_missing_templates(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Older Campaign",
        session_date=date(2026, 5, 23),
    )
    paths.adventure_spine.unlink()
    paths.puzzle_ledger.unlink()
    paths.visual_ledger.unlink()
    paths.player_journal.unlink()

    result = run_preflight(paths.root, repair_missing_templates=True)

    assert result.ok is True
    assert paths.adventure_spine.exists()
    assert paths.puzzle_ledger.exists()
    assert paths.visual_ledger.exists()
    assert paths.player_journal.exists()
    assert {issue.code for issue in result.issues} == {
        "created_missing_template",
        "empty_visual_ledger",
    }


def test_preflight_markdown_is_human_readable(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Readable Report",
        session_date=date(2026, 5, 23),
    )

    result = run_preflight(paths.root)
    report = format_preflight_markdown(result)

    assert "# Questforge Preflight" in report
    assert "Status: PASS" in report
    assert "empty_visual_ledger" in report
