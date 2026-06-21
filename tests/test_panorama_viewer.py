import base64
import json

import pytest

from scripts.panorama_viewer import (
    create_panorama_viewer,
    infer_audio_mime_type,
    infer_mime_type,
    slugify,
    validate_audio_volume,
    validate_initial_zoom_level,
)

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/l27I4wAAAABJRU5ErkJggg=="
)
MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x21fake mp3 test bytes"


def test_create_panorama_viewer_embeds_image_data_uri(tmp_path):
    image_path = tmp_path / "tavern-360.png"
    image_path.write_bytes(PNG_BYTES)
    output_path = tmp_path / "viewer.html"

    result = create_panorama_viewer(
        image_path=image_path,
        output_path=output_path,
        title="Rain Door Tavern",
        narration=(
            "Entras empapado. El posadero levanta la mirada antes de que "
            "cierres la puerta."
        ),
        initial_zoom_level=14,
    )

    html = output_path.read_text(encoding="utf-8")
    assert result.viewer_path == str(output_path.resolve())
    assert result.viewer_url.startswith("file:///")
    assert result.image_path == str(image_path.resolve())
    assert result.title == "Rain Door Tavern"
    assert result.narration.startswith("Entras empapado.")
    assert result.initial_zoom_level == 14
    assert "data:image/png;base64," in html
    assert "Rain Door Tavern" in html
    assert "El posadero levanta la mirada" in html
    assert (
        json.dumps(str(image_path.resolve()), ensure_ascii=False) not in html
    )
    assert '<canvas id="viewer"' in html
    assert 'id="flat-viewer"' in html
    assert "Questforge 360 panorama fallback viewer" in html
    assert "0.5 + latitude / PI" in html
    assert "const MIN_FOV = Math.PI / 6;" in html
    assert "const MAX_FOV = Math.PI * 0.53;" in html
    assert "isBlankWebGlFrame" not in html
    assert 'activateFlatViewer("Flat panorama fallback")' not in html
    assert "state.yaw += deltaX" in html
    assert "state.pitch = clamp(state.pitch + deltaY" in html
    assert "flatState.x + deltaX" in html
    assert "flatState.y = clamp(flatState.y + deltaY" in html
    assert "const INITIAL_ZOOM_LEVEL = 14;" in html
    assert "const INITIAL_FOV = zoomLevelToFov" in html
    assert "state.fov = INITIAL_FOV" in html
    assert 'const AUDIO_DATA_URI = "";' in html
    assert "configureAmbientAudio()" in html
    assert "questforgeAmbientAudioEnabled" in html
    assert 'class="audio-toggle"' in html


def test_create_panorama_viewer_embeds_optional_audio_loop(tmp_path):
    image_path = tmp_path / "tavern-360.png"
    image_path.write_bytes(PNG_BYTES)
    audio_path = tmp_path / "Oakbeam Tavern.mp3"
    audio_path.write_bytes(MP3_BYTES)
    output_path = tmp_path / "viewer.html"

    result = create_panorama_viewer(
        image_path=image_path,
        audio_path=audio_path,
        audio_title="Oakbeam Tavern",
        audio_volume=0.24,
        output_path=output_path,
    )

    html = output_path.read_text(encoding="utf-8")
    assert result.audio_path == str(audio_path.resolve())
    assert result.audio_title == "Oakbeam Tavern"
    assert result.audio_volume == 0.24
    assert "data:audio/mpeg;base64," in html
    assert "Oakbeam Tavern" in html
    assert "const AUDIO_VOLUME = 0.24;" in html
    assert "Mute ambience" in html
    assert (
        json.dumps(str(audio_path.resolve()), ensure_ascii=False) not in html
    )


def test_create_panorama_viewer_uses_title_slug_for_default_output(tmp_path):
    image_path = tmp_path / "source.png"
    image_path.write_bytes(PNG_BYTES)

    result = create_panorama_viewer(
        image_path=image_path,
        title="POV: Rain Door Tavern",
    )

    assert result.viewer_path.endswith("pov-rain-door-tavern-360.html")


def test_infer_mime_type_rejects_unsupported_images(tmp_path):
    image_path = tmp_path / "image.bmp"
    image_path.write_bytes(b"fake")

    with pytest.raises(ValueError, match="Unsupported panorama"):
        infer_mime_type(image_path)


def test_infer_audio_mime_type_rejects_unsupported_audio(tmp_path):
    audio_path = tmp_path / "loop.flac"
    audio_path.write_bytes(b"fake")

    with pytest.raises(ValueError, match="Unsupported audio"):
        infer_audio_mime_type(audio_path)


def test_validate_initial_zoom_level_bounds():
    validate_initial_zoom_level(1)
    validate_initial_zoom_level(22)

    with pytest.raises(ValueError, match="between 1 and 22"):
        validate_initial_zoom_level(0)

    with pytest.raises(ValueError, match="between 1 and 22"):
        validate_initial_zoom_level(23)


def test_validate_audio_volume_bounds():
    validate_audio_volume(0)
    validate_audio_volume(1)
    validate_audio_volume(0.35)

    with pytest.raises(ValueError, match="between 0 and 1"):
        validate_audio_volume(-0.01)

    with pytest.raises(ValueError, match="between 0 and 1"):
        validate_audio_volume(1.01)


def test_slugify_keeps_stable_viewer_names():
    assert slugify("POV: Rain Door Tavern") == "pov-rain-door-tavern"
    assert slugify("  ") == "panorama"
