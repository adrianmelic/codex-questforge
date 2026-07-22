from datetime import date

from scripts.campaign_memory import (
    create_campaign,
    register_visual_asset,
    save_visual_prompt,
    set_visual_status,
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
    assert result.warning_count == 2
    assert {issue.code for issue in result.issues} == {
        "empty_visual_ledger",
        "no_generated_visuals",
    }
    assert result.visual_asset_count == 0
    assert result.pending_visual_count == 0


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


def test_preflight_reports_visual_prompts_without_assets(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Prompt Only",
        session_date=date(2026, 5, 23),
    )
    save_visual_prompt(
        campaign_root=paths.root,
        session_number=1,
        scene_number=1,
        kind="scene",
        label="Unfinished Harbor",
        prompt="A storm over a harbor.",
    )

    result = run_preflight(paths.root)

    assert result.visual_asset_count == 0
    assert result.pending_visual_count == 1
    assert any(
        issue.code == "pending_visual_generation" for issue in result.issues
    )


def test_preflight_distinguishes_unavailable_visual_from_pending(tmp_path):
    paths = create_campaign(
        tmp_path,
        "No Native Image Surface",
        session_date=date(2026, 5, 23),
    )
    prompt_path = save_visual_prompt(
        campaign_root=paths.root,
        session_number=1,
        scene_number=1,
        kind="scene",
        label="Sunlit Terrace",
        prompt="A sunlit terrace above a crowded market.",
    )
    set_visual_status(
        campaign_root=paths.root,
        prompt_path=prompt_path.relative_to(paths.root),
        status="unavailable",
    )

    result = run_preflight(paths.root)

    assert result.pending_visual_count == 0
    assert result.unavailable_visual_count == 1
    assert all(
        issue.code != "pending_visual_generation" for issue in result.issues
    )


def test_release_preflight_blocks_prompt_only_opening(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Prompt Only Release",
        session_date=date(2026, 5, 23),
    )
    save_visual_prompt(
        campaign_root=paths.root,
        session_number=1,
        scene_number=1,
        kind="scene",
        label="Opening",
        prompt="An original opening scene.",
    )

    result = run_preflight(
        paths.root,
        require_generated_visuals=True,
        require_opening_visual=True,
    )

    assert result.ok is False
    assert {issue.code for issue in result.issues} >= {
        "pending_visual_generation",
        "missing_opening_visual",
    }


def test_release_preflight_accepts_registered_opening_visual(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Visual Release",
        session_date=date(2026, 5, 23),
    )
    add_registered_asset(tmp_path, paths.root, "opening.png")

    result = run_preflight(
        paths.root,
        require_generated_visuals=True,
        require_opening_visual=True,
    )

    assert result.ok is True
    assert result.visual_asset_count == 1
    assert all(
        issue.code != "missing_opening_visual" for issue in result.issues
    )


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
        "no_generated_visuals",
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
    assert "0 unavailable" in report
