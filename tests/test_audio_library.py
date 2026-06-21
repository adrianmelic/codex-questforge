import json
from pathlib import Path

import pytest

from scripts.audio_library import (
    render_prompt_list,
    select_audio_track,
    validate_audio_library,
)

MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x21fake mp3 test bytes"


def write_library(tmp_path, tracks):
    library_path = tmp_path / "library.json"
    library_path.write_text(
        json.dumps({"version": 1, "tracks": tracks}),
        encoding="utf-8",
    )
    return library_path


def test_select_audio_track_matches_tags_and_intensity(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "tavern.mp3").write_bytes(MP3_BYTES)
    (audio_dir / "forest.mp3").write_bytes(MP3_BYTES)
    library_path = write_library(
        tmp_path,
        [
            {
                "id": "forest_day_01",
                "title": "Forest Day",
                "type": "loop",
                "category": "wilderness",
                "tags": ["forest", "day", "birds"],
                "intensity": 1,
                "default_volume": 0.23,
                "status": "approved",
                "path": "audio/forest.mp3",
            },
            {
                "id": "tavern_rain_01",
                "title": "Tavern Rain",
                "type": "loop",
                "category": "safe-place",
                "tags": ["tavern", "rain", "warm"],
                "intensity": 2,
                "default_volume": 0.24,
                "status": "approved",
                "path": "audio/tavern.mp3",
            },
        ],
    )

    selection = select_audio_track(
        library_path,
        tags=["tavern", "rain"],
        category="safe-place",
        intensity=2,
    )

    assert selection.track.id == "tavern_rain_01"
    assert selection.matched_tags == ("tavern", "rain")
    assert selection.resolved_path.endswith("tavern.mp3")
    assert "--audio-title 'Tavern Rain'" in selection.command_arguments
    assert "--audio-volume 0.24" in selection.command_arguments


def test_select_audio_track_ignores_unapproved_and_missing_files(tmp_path):
    library_path = write_library(
        tmp_path,
        [
            {
                "id": "prompt_only",
                "title": "Prompt Only",
                "type": "loop",
                "category": "safe-place",
                "tags": ["tavern"],
                "status": "prompt-ready",
                "path": "audio/prompt-only.mp3",
            },
            {
                "id": "missing_approved",
                "title": "Missing Approved",
                "type": "loop",
                "category": "safe-place",
                "tags": ["tavern"],
                "status": "approved",
                "path": "audio/missing.mp3",
            },
        ],
    )

    with pytest.raises(ValueError, match="No approved audio track"):
        select_audio_track(library_path, tags=["tavern"])


def test_validate_audio_library_reports_missing_and_duplicates(tmp_path):
    library_path = write_library(
        tmp_path,
        [
            {
                "id": "duplicate",
                "title": "One",
                "status": "approved",
                "path": "audio/one.mp3",
            },
            {
                "id": "duplicate",
                "title": "Two",
                "status": "draft",
                "path": "audio/two.mp3",
            },
        ],
    )

    validation = validate_audio_library(library_path)

    assert validation.track_count == 2
    assert validation.approved_count == 1
    assert validation.usable_count == 0
    assert validation.duplicate_ids == ("duplicate",)
    assert len(validation.missing_files) == 1


def test_render_prompt_list_filters_by_status(tmp_path):
    library_path = write_library(
        tmp_path,
        [
            {
                "id": "ready_prompt",
                "title": "Ready Prompt",
                "status": "prompt-ready",
                "tags": ["cave"],
                "prompt": "Seamless cave loop.",
            },
            {
                "id": "draft_prompt",
                "title": "Draft Prompt",
                "status": "draft",
                "prompt": "Draft.",
            },
        ],
    )

    rendered = render_prompt_list(library_path)

    assert "ready_prompt" in rendered
    assert "Seamless cave loop." in rendered
    assert "draft_prompt" not in rendered


def test_bundled_starter_pack_validates_and_selects():
    plugin_root = Path(__file__).resolve().parents[1]
    library_path = plugin_root / "assets" / "audio" / "library.json"

    validation = validate_audio_library(library_path)
    selection = select_audio_track(
        library_path,
        tags=["dungeon", "combat"],
        category="action",
        intensity=5,
    )

    assert validation.track_count == 11
    assert validation.approved_count == 11
    assert validation.usable_count == 11
    assert validation.missing_files == ()
    assert selection.track.id in {
        "qf_027_battle_under_stone_afd01b01",
        "qf_042_shieldwall_pulse_0d25f695",
    }
    assert "--audio " in selection.command_arguments
