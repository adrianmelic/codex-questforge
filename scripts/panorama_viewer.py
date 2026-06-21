"""Generate standalone Questforge 360 panorama viewer HTML files."""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PLUGIN_ROOT / "templates" / "panorama-viewer.html"
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
SUPPORTED_AUDIO_MIME_TYPES = {
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".mpeg": "audio/mpeg",
    ".oga": "audio/ogg",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
}


@dataclass(frozen=True)
class PanoramaViewerResult:
    """Created 360 viewer artifact."""

    viewer_path: str
    viewer_url: str
    image_path: str
    title: str
    narration: str
    initial_zoom_level: int
    audio_path: str | None
    audio_title: str
    audio_volume: float
    html_bytes: int


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    slug = SLUG_PATTERN.sub("-", normalized).strip("-")
    return slug or "panorama"


def infer_mime_type(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    raise ValueError(
        "Unsupported panorama image type. Use PNG, JPEG, or WebP."
    )


def infer_audio_mime_type(audio_path: Path) -> str:
    suffix = audio_path.suffix.lower()
    try:
        return SUPPORTED_AUDIO_MIME_TYPES[suffix]
    except KeyError as error:
        raise ValueError(
            "Unsupported audio type. Use MP3, M4A, AAC, OGG, WAV, or WebM."
        ) from error


def create_panorama_viewer(
    image_path: Path,
    output_path: Path | None = None,
    title: str = "",
    narration: str = "",
    initial_zoom_level: int = 14,
    audio_path: Path | None = None,
    audio_title: str = "",
    audio_volume: float = 0.28,
) -> PanoramaViewerResult:
    """Create a local HTML viewer with the panorama embedded as a data URI."""

    image_path = image_path.expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Missing panorama image: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"Panorama path is not a file: {image_path}")

    viewer_title = title.strip() or image_path.stem
    viewer_narration = narration.strip() or viewer_title
    validate_initial_zoom_level(initial_zoom_level)
    validate_audio_volume(audio_volume)
    if output_path is None:
        output_path = image_path.with_name(f"{slugify(viewer_title)}-360.html")
    output_path = output_path.expanduser().resolve()

    image_data_uri = encode_data_uri(image_path, infer_mime_type(image_path))
    viewer_audio_path = resolve_optional_file(audio_path, "audio")
    if viewer_audio_path is None:
        audio_data_uri = ""
        viewer_audio_title = ""
    else:
        audio_data_uri = encode_data_uri(
            viewer_audio_path,
            infer_audio_mime_type(viewer_audio_path),
        )
        viewer_audio_title = audio_title.strip() or viewer_audio_path.stem

    html = render_template(
        title=viewer_title,
        narration=viewer_narration,
        initial_zoom_level=initial_zoom_level,
        image_data_uri=image_data_uri,
        audio_data_uri=audio_data_uri,
        audio_title=viewer_audio_title,
        audio_volume=audio_volume,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8", newline="\n")

    return PanoramaViewerResult(
        viewer_path=str(output_path),
        viewer_url=output_path.as_uri(),
        image_path=str(image_path),
        title=viewer_title,
        narration=viewer_narration,
        initial_zoom_level=initial_zoom_level,
        audio_path=str(viewer_audio_path) if viewer_audio_path else None,
        audio_title=viewer_audio_title,
        audio_volume=audio_volume,
        html_bytes=output_path.stat().st_size,
    )


def validate_initial_zoom_level(level: int) -> None:
    if level < 1 or level > 22:
        raise ValueError("Initial zoom level must be between 1 and 22.")


def validate_audio_volume(volume: float) -> None:
    if volume < 0 or volume > 1:
        raise ValueError("Audio volume must be between 0 and 1.")


def resolve_optional_file(path: Path | None, label: str) -> Path | None:
    if path is None:
        return None
    resolved_path = path.expanduser().resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Missing {label} file: {resolved_path}")
    if not resolved_path.is_file():
        raise ValueError(
            f"{label.title()} path is not a file: {resolved_path}"
        )
    return resolved_path


def encode_data_uri(path: Path, mime_type: str) -> str:
    return f"data:{mime_type};base64," + base64.b64encode(
        path.read_bytes()
    ).decode("ascii")


def render_template(
    title: str,
    narration: str,
    initial_zoom_level: int,
    image_data_uri: str,
    audio_data_uri: str,
    audio_title: str,
    audio_volume: float,
) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        template.replace("__TITLE_TEXT__", escape_html_text(title))
        .replace("__TITLE_JSON__", json.dumps(title, ensure_ascii=False))
        .replace(
            "__NARRATION_JSON__",
            json.dumps(narration, ensure_ascii=False),
        )
        .replace(
            "__INITIAL_ZOOM_LEVEL_JSON__",
            json.dumps(initial_zoom_level),
        )
        .replace(
            "__IMAGE_DATA_URI_JSON__",
            json.dumps(image_data_uri, ensure_ascii=False),
        )
        .replace(
            "__AUDIO_DATA_URI_JSON__",
            json.dumps(audio_data_uri, ensure_ascii=False),
        )
        .replace("__AUDIO_TITLE_JSON__", json.dumps(audio_title))
        .replace("__AUDIO_VOLUME_JSON__", json.dumps(audio_volume))
    )


def escape_html_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a standalone Questforge 360 panorama viewer."
    )
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--title", default="")
    parser.add_argument("--narration", default="")
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--audio-title", default="")
    parser.add_argument(
        "--audio-volume",
        type=float,
        default=0.28,
        help="Ambient loop volume from 0 to 1. Defaults to 0.28.",
    )
    parser.add_argument(
        "--initial-zoom-level",
        type=int,
        default=14,
        help=(
            "Initial zoom level from 1 to 22. Higher values start wider. "
            "Defaults to 14."
        ),
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = create_panorama_viewer(
        image_path=parsed_arguments.image,
        output_path=parsed_arguments.output,
        title=parsed_arguments.title,
        narration=parsed_arguments.narration,
        initial_zoom_level=parsed_arguments.initial_zoom_level,
        audio_path=parsed_arguments.audio,
        audio_title=parsed_arguments.audio_title,
        audio_volume=parsed_arguments.audio_volume,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
