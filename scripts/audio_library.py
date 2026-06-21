"""Select and validate Questforge ambience tracks."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

APPROVED_STATUSES = {"approved", "canon", "published", "ready"}


@dataclass(frozen=True)
class AudioTrack:
    """One local or planned ambience asset."""

    id: str
    title: str
    type: str
    category: str
    tags: tuple[str, ...]
    intensity: int | None
    default_volume: float
    duration_seconds: int | None
    status: str
    license: str
    credit: str
    path: str
    prompt: str


@dataclass(frozen=True)
class AudioSelection:
    """Best matching ambience track for a scene."""

    track: AudioTrack
    resolved_path: str
    score: int
    matched_tags: tuple[str, ...]
    command_arguments: str


@dataclass(frozen=True)
class AudioValidation:
    """Validation result for one audio library."""

    library_path: str
    track_count: int
    approved_count: int
    usable_count: int
    missing_files: tuple[str, ...]
    duplicate_ids: tuple[str, ...]


def load_tracks(library_path: Path) -> list[AudioTrack]:
    """Load tracks from an audio library or sound atlas JSON file."""

    payload = json.loads(library_path.read_text(encoding="utf-8"))
    raw_tracks = payload.get("tracks", payload.get("entries", []))
    if not isinstance(raw_tracks, list):
        raise ValueError(
            "Audio library must contain a tracks or entries list."
        )
    return [normalize_track(item) for item in raw_tracks]


def normalize_track(raw_track: object) -> AudioTrack:
    if not isinstance(raw_track, dict):
        raise ValueError("Each audio track must be an object.")
    track_id = str(raw_track.get("id") or raw_track.get("label") or "").strip()
    if not track_id:
        raise ValueError("Each audio track needs an id or label.")
    tags = tuple(
        sorted(
            {
                normalize_token(tag)
                for tag in raw_track.get("tags", [])
                + raw_track.get("moods", [])
                if str(tag).strip()
            }
        )
    )
    return AudioTrack(
        id=track_id,
        title=str(raw_track.get("title") or track_id).strip(),
        type=normalize_token(raw_track.get("type") or "loop"),
        category=normalize_token(raw_track.get("category") or ""),
        tags=tags,
        intensity=optional_int(raw_track.get("intensity")),
        default_volume=optional_float(
            raw_track.get("default_volume", raw_track.get("volume", 0.28))
        ),
        duration_seconds=optional_int(
            raw_track.get("duration_seconds", raw_track.get("duration"))
        ),
        status=normalize_token(raw_track.get("status") or "draft"),
        license=str(raw_track.get("license") or "").strip(),
        credit=str(raw_track.get("credit") or "").strip(),
        path=str(raw_track.get("path") or "").strip(),
        prompt=str(raw_track.get("prompt") or "").strip(),
    )


def optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def optional_float(value: object) -> float:
    if value in (None, ""):
        return 0.28
    return float(value)


def normalize_token(value: object) -> str:
    return str(value).strip().casefold().replace("_", "-")


def resolve_track_path(library_path: Path, track: AudioTrack) -> Path | None:
    if not track.path:
        return None
    track_path = Path(track.path)
    if not track_path.is_absolute():
        track_path = library_path.parent / track_path
    return track_path.expanduser().resolve()


def validate_audio_library(
    library_path: Path,
    require_existing_files: bool = True,
) -> AudioValidation:
    tracks = load_tracks(library_path)
    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    missing_files: list[str] = []
    usable_count = 0
    approved_count = 0

    for track in tracks:
        if track.id in seen_ids:
            duplicate_ids.append(track.id)
        seen_ids.add(track.id)
        if track.status in APPROVED_STATUSES:
            approved_count += 1
        resolved_path = resolve_track_path(library_path, track)
        is_usable = track.status in APPROVED_STATUSES and resolved_path
        if is_usable and resolved_path and resolved_path.exists():
            usable_count += 1
        elif (
            require_existing_files
            and track.status in APPROVED_STATUSES
            and resolved_path
        ):
            missing_files.append(str(resolved_path))

    return AudioValidation(
        library_path=str(library_path.resolve()),
        track_count=len(tracks),
        approved_count=approved_count,
        usable_count=usable_count,
        missing_files=tuple(missing_files),
        duplicate_ids=tuple(sorted(set(duplicate_ids))),
    )


def select_audio_track(
    library_path: Path,
    tags: Iterable[str],
    category: str = "",
    kind: str = "loop",
    intensity: int | None = None,
    require_existing_file: bool = True,
) -> AudioSelection:
    """Return the best approved track for a scene."""

    normalized_tags = tuple(normalize_token(tag) for tag in tags if tag)
    normalized_category = normalize_token(category)
    normalized_kind = normalize_token(kind)
    candidates: list[AudioSelection] = []

    for track in load_tracks(library_path):
        if track.status not in APPROVED_STATUSES:
            continue
        resolved_path = resolve_track_path(library_path, track)
        if require_existing_file and (
            resolved_path is None or not resolved_path.exists()
        ):
            continue
        if normalized_kind and track.type != normalized_kind:
            continue
        score, matched_tags = score_track(
            track=track,
            query_tags=normalized_tags,
            category=normalized_category,
            intensity=intensity,
        )
        if score <= 0:
            continue
        if resolved_path is None:
            resolved_path = Path(track.path or track.id)
        candidates.append(
            AudioSelection(
                track=track,
                resolved_path=str(resolved_path),
                score=score,
                matched_tags=matched_tags,
                command_arguments=build_panorama_arguments(
                    resolved_path=resolved_path,
                    track=track,
                ),
            )
        )

    if not candidates:
        raise ValueError("No approved audio track matched the scene.")
    return sorted(
        candidates,
        key=lambda item: (
            item.score,
            -(item.track.intensity or 0),
            item.track.title,
        ),
        reverse=True,
    )[0]


def score_track(
    track: AudioTrack,
    query_tags: tuple[str, ...],
    category: str = "",
    intensity: int | None = None,
) -> tuple[int, tuple[str, ...]]:
    matched_tags = tuple(tag for tag in query_tags if tag in track.tags)
    score = len(matched_tags) * 10
    if category and category == track.category:
        score += 12
    elif category and category in track.tags:
        score += 6
    if intensity is not None and track.intensity is not None:
        score += max(0, 8 - abs(intensity - track.intensity) * 2)
    elif not query_tags and not category:
        score += 1
    if "generic" in track.tags:
        score -= 1
    return score, matched_tags


def build_panorama_arguments(resolved_path: Path, track: AudioTrack) -> str:
    return " ".join(
        [
            "--audio",
            shlex.quote(str(resolved_path)),
            "--audio-title",
            shlex.quote(track.title),
            "--audio-volume",
            str(track.default_volume),
        ]
    )


def render_prompt_list(
    library_path: Path,
    status: str = "prompt-ready",
    limit: int | None = None,
) -> str:
    status = normalize_token(status)
    tracks = [
        track
        for track in load_tracks(library_path)
        if not status or track.status == status
    ]
    if limit is not None:
        tracks = tracks[:limit]
    lines: list[str] = []
    for index, track in enumerate(tracks, start=1):
        lines.extend(
            [
                f"## {index}. {track.id}",
                "",
                f"- Title: {track.title}",
                f"- Type: {track.type}",
                f"- Category: {track.category}",
                f"- Tags: {', '.join(track.tags)}",
                f"- Intensity: {track.intensity}",
                "",
                "```text",
                track.prompt,
                "```",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select and validate Questforge ambience tracks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--library", required=True, type=Path)
    validate_parser.add_argument(
        "--allow-missing-files",
        action="store_true",
        help="Do not report missing approved audio files.",
    )

    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("--library", required=True, type=Path)
    select_parser.add_argument("--tag", action="append", default=[])
    select_parser.add_argument("--category", default="")
    select_parser.add_argument("--kind", default="loop")
    select_parser.add_argument("--intensity", type=int)
    select_parser.add_argument(
        "--allow-missing-file",
        action="store_true",
        help="Allow selecting a track whose audio file is not present.",
    )
    select_parser.add_argument(
        "--format",
        choices=("json", "args", "markdown"),
        default="json",
    )

    prompts_parser = subparsers.add_parser("list-prompts")
    prompts_parser.add_argument("--library", required=True, type=Path)
    prompts_parser.add_argument("--status", default="prompt-ready")
    prompts_parser.add_argument("--limit", type=int)
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    if parsed_arguments.command == "validate":
        result = validate_audio_library(
            parsed_arguments.library,
            require_existing_files=not parsed_arguments.allow_missing_files,
        )
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return 1 if result.missing_files or result.duplicate_ids else 0
    if parsed_arguments.command == "select":
        result = select_audio_track(
            library_path=parsed_arguments.library,
            tags=parsed_arguments.tag,
            category=parsed_arguments.category,
            kind=parsed_arguments.kind,
            intensity=parsed_arguments.intensity,
            require_existing_file=not parsed_arguments.allow_missing_file,
        )
        if parsed_arguments.format == "args":
            print(result.command_arguments)
        elif parsed_arguments.format == "markdown":
            print(render_selection_markdown(result))
        else:
            print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return 0
    if parsed_arguments.command == "list-prompts":
        print(
            render_prompt_list(
                library_path=parsed_arguments.library,
                status=parsed_arguments.status,
                limit=parsed_arguments.limit,
            ),
            end="",
        )
        return 0
    raise AssertionError(f"Unhandled command: {parsed_arguments.command}")


def render_selection_markdown(selection: AudioSelection) -> str:
    track = selection.track
    return "\n".join(
        [
            f"### {track.title}",
            "",
            f"- ID: `{track.id}`",
            f"- Path: `{selection.resolved_path}`",
            f"- Matched tags: `{', '.join(selection.matched_tags)}`",
            f"- Score: `{selection.score}`",
            f"- Volume: `{track.default_volume}`",
            "",
            "```powershell",
            selection.command_arguments,
            "```",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
