from datetime import date

from scripts.campaign_memory import (
    create_campaign,
    register_visual_asset,
    save_visual_prompt,
)
from scripts.visual_gallery import create_visual_gallery

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
)


def add_registered_asset(
    tmp_path,
    campaign_root,
    session_number,
    scene_number,
    kind,
    label,
    asset_name,
    status="asset-saved",
):
    prompt_path = save_visual_prompt(
        campaign_root=campaign_root,
        session_number=session_number,
        scene_number=scene_number,
        kind=kind,
        label=label,
        prompt=f"Prompt for {label}.",
    )
    source_asset = tmp_path / asset_name
    source_asset.write_bytes(PNG_BYTES)
    register_visual_asset(
        campaign_root=campaign_root,
        asset_source=source_asset,
        asset_filename=asset_name,
        prompt_path=prompt_path.relative_to(campaign_root),
        status=status,
    )


def test_create_visual_gallery_writes_chronological_log_and_links_assets(
    tmp_path,
):
    paths = create_campaign(
        tmp_path,
        "La Campana Negra",
        tone="dark mystery",
        session_date=date(2026, 5, 23),
    )
    add_registered_asset(
        tmp_path,
        paths.root,
        session_number=1,
        scene_number=1,
        kind="scene",
        label="Room Door Payment",
        asset_name="room-door-payment.png",
    )
    add_registered_asset(
        tmp_path,
        paths.root,
        session_number=1,
        scene_number=2,
        kind="location",
        label="Rain Door Tavern 360 POV",
        asset_name="rain-door-tavern.png",
    )
    viewer_path = (
        paths.root / "images" / "viewers" / "rain-door-tavern-360.html"
    )
    viewer_path.parent.mkdir(parents=True, exist_ok=True)
    viewer_path.write_text(
        "<!doctype html><title>360</title>", encoding="utf-8"
    )
    add_registered_asset(
        tmp_path,
        paths.root,
        session_number=1,
        scene_number=3,
        kind="scene",
        label="Rejected Drift",
        asset_name="rejected-drift.png",
        status="rejected",
    )

    result = create_visual_gallery(paths.root, title="La Campana Negra")

    gallery_path = paths.root / "images" / "visual-gallery.html"
    html = gallery_path.read_text(encoding="utf-8")
    assert result.gallery_path == str(gallery_path.resolve())
    assert result.gallery_url.startswith("file:///")
    assert result.gallery_url.endswith("visual-gallery.html#latest")
    assert result.item_count == 2
    assert result.skipped_missing_assets == 0
    assert "La Campana Negra" in html
    assert 'id="timeline"' in html
    assert 'href="#visual-1"' in html
    assert 'href="#latest"' in html
    assert "scrollToHash" in html
    assert "GALLERY_VERSION" in html
    assert "AUTO_REFRESH_MS" in html
    assert "checkForGalleryUpdate" in html
    assert "window.setInterval" in html
    assert "entry-frame" in html
    assert 'frame.classList.add("panorama")' in html
    assert "caption-main" in html
    assert "iframe" in html
    assert "Open 360" in html
    assert 'id="image-link"' not in html
    assert 'id="prompt-link"' not in html
    assert "createAction" not in html
    assert "Room Door Payment" in html
    assert "Rain Door Tavern 360 POV" in html
    assert "Rejected Drift" not in html
    assert "assets/room-door-payment.png" in html
    assert "assets/rain-door-tavern.png" in html
    assert "viewers/rain-door-tavern-360.html" in html


def test_visual_gallery_can_include_rejected_assets(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Rootbound Vault",
        session_date=date(2026, 5, 23),
    )
    add_registered_asset(
        tmp_path,
        paths.root,
        session_number=1,
        scene_number=1,
        kind="scene",
        label="Rejected Composite",
        asset_name="rejected-composite.png",
        status="rejected",
    )

    result = create_visual_gallery(paths.root, include_rejected=True)

    html = (paths.root / "images" / "visual-gallery.html").read_text(
        encoding="utf-8"
    )
    assert result.item_count == 1
    assert "Rejected Composite" in html


def test_visual_gallery_can_scan_extra_viewer_roots(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Old Viewer Campaign",
        session_date=date(2026, 5, 23),
    )
    add_registered_asset(
        tmp_path,
        paths.root,
        session_number=1,
        scene_number=1,
        kind="location",
        label="Archive Hall 360 POV",
        asset_name="archive-hall.png",
    )
    external_viewer_dir = tmp_path / "old-viewers"
    external_viewer_dir.mkdir()
    external_viewer_dir.joinpath("archive-hall-360.html").write_text(
        "<!doctype html><title>Archive Hall 360</title>",
        encoding="utf-8",
    )

    create_visual_gallery(paths.root, viewer_roots=[external_viewer_dir])

    html = (paths.root / "images" / "visual-gallery.html").read_text(
        encoding="utf-8"
    )
    assert "old-viewers/archive-hall-360.html" in html


def test_visual_gallery_links_matching_viewer_without_panorama_label(
    tmp_path,
):
    paths = create_campaign(
        tmp_path,
        "Implicit Viewer Campaign",
        session_date=date(2026, 5, 23),
    )
    add_registered_asset(
        tmp_path,
        paths.root,
        session_number=1,
        scene_number=1,
        kind="location",
        label="POV junto al fuego en la posada",
        asset_name="pov-fuego-posada.png",
    )
    viewer_path = (
        paths.root / "images" / "viewers" / "pov-fuego-posada-360.html"
    )
    viewer_path.write_text(
        "<!doctype html><title>Fuego 360</title>",
        encoding="utf-8",
    )

    create_visual_gallery(paths.root)

    html = (paths.root / "images" / "visual-gallery.html").read_text(
        encoding="utf-8"
    )
    assert "viewers/pov-fuego-posada-360.html" in html
    assert 'frame.classList.add("panorama")' in html


def test_visual_gallery_creates_default_viewer_for_panorama_asset(tmp_path):
    paths = create_campaign(
        tmp_path,
        "Auto Viewer Campaign",
        session_date=date(2026, 5, 23),
    )
    add_registered_asset(
        tmp_path,
        paths.root,
        session_number=1,
        scene_number=1,
        kind="location",
        label="POV panoramico interior de la posada",
        asset_name="pov-panoramico-posada-interior.png",
    )

    create_visual_gallery(paths.root)

    generated_viewer = (
        paths.root
        / "images"
        / "viewers"
        / "pov-panoramico-interior-de-la-posada-360.html"
    )
    html = (paths.root / "images" / "visual-gallery.html").read_text(
        encoding="utf-8"
    )
    assert generated_viewer.exists()
    assert "viewers/pov-panoramico-interior-de-la-posada-360.html" in html
    assert "POV panoramico interior de la posada" in (
        generated_viewer.read_text(encoding="utf-8")
    )
