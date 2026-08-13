"""Portable and conflict-aware save helpers for Questforge campaigns."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    from .campaign_memory import existing_session_numbers
    from .game_state import STATE_VERSION
except ImportError:  # pragma: no cover - direct script execution path
    from campaign_memory import existing_session_numbers
    from game_state import STATE_VERSION


SCHEMA_VERSION = 2
MANIFEST_NAME = "questforge.json"
FIXED_ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)
HISTORY_LIMIT = 100
PROFILES = {"canonical", "complete"}
REQUIRED_FILES = {
    "campaign-state.md",
    "game-state.json",
    "player-journal.md",
    "opening-brief.md",
    "dm/adventure-spine.md",
    "dm/puzzle-ledger.md",
    "visual-bible.md",
    "images/visual-index.md",
    "images/visual-ledger.md",
}
REQUIRED_DIRECTORIES = {
    "characters",
    "sessions",
    "checkpoints",
}
CANONICAL_FILES = REQUIRED_FILES | {
    "campaign-conception.json",
    "analytics/session-events.jsonl",
    "audio/library.json",
}
CANONICAL_DIRECTORIES = {
    "characters",
    "sessions",
    "checkpoints",
    "dm",
    "images/prompts",
}
MEDIA_FILES = {"images/visual-gallery.html"}
MEDIA_DIRECTORIES = {
    "images/assets",
    "images/viewers",
    "audio",
}
EXCLUDED_PARTS = {
    ".git",
    ".questforge",
    ".pytest_cache",
    "__pycache__",
    "rules",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
LEGACY_ALIASES = {
    "player-journal.md": re.compile(r"player-journal-session-\d{3}\.md$"),
    "images/visual-index.md": re.compile(
        r"(?:images/)?visual-index-session-\d{3}\.md$"
    ),
}
CANONICAL_MANIFEST = {
    "campaignState": "campaign-state.md",
    "gameState": "game-state.json",
    "playerJournal": "player-journal.md",
    "openingBrief": "opening-brief.md",
    "adventureSpine": "dm/adventure-spine.md",
    "puzzleLedger": "dm/puzzle-ledger.md",
    "visualBible": "visual-bible.md",
    "visualIndex": "images/visual-index.md",
    "visualLedger": "images/visual-ledger.md",
    "characters": "characters/",
    "sessions": "sessions/",
    "checkpoints": "checkpoints/",
    "visualPrompts": "images/prompts/",
    "manifest": MANIFEST_NAME,
}


@dataclass(frozen=True)
class SaveIssue:
    """One portable-save finding."""

    level: str
    code: str
    message: str
    path: str = ""


@dataclass(frozen=True)
class CampaignInspection:
    """Read-only campaign save inspection."""

    campaign_root: str
    ok: bool
    schema_version: int
    campaign_id: str
    current_session: int
    latest_session: int
    canonical_file_count: int
    canonical_bytes: int
    media_file_count: int
    media_bytes: int
    sync_hint: dict
    issues: list[SaveIssue]


def utc_now() -> str:
    """Return a stable UTC timestamp for manifests and receipts."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_relative(path: Path, campaign_root: Path) -> str:
    return path.relative_to(campaign_root).as_posix()


def path_is_under(relative_path: str, directory: str) -> bool:
    return relative_path == directory or relative_path.startswith(
        f"{directory}/"
    )


def classify_file(relative_path: str) -> str:
    """Classify a campaign file as canonical, media, or excluded."""

    path = Path(relative_path)
    if relative_path == MANIFEST_NAME:
        return "manifest"
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return "excluded"
    if path.name == ".DS_Store" or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return "excluded"
    if relative_path in CANONICAL_FILES or any(
        path_is_under(relative_path, directory)
        for directory in CANONICAL_DIRECTORIES
    ):
        return "canonical"
    if relative_path in MEDIA_FILES or any(
        path_is_under(relative_path, directory)
        for directory in MEDIA_DIRECTORIES
    ):
        return "media"
    return "excluded"


def campaign_files(campaign_root: Path, profile: str) -> list[Path]:
    """Return portable files for a save profile, excluding the manifest."""

    if profile not in PROFILES:
        raise ValueError(f"Unknown save profile: {profile}")
    selected: list[Path] = []
    for path in sorted(campaign_root.rglob("*")):
        relative_path = normalized_relative(path, campaign_root)
        classification = classify_file(relative_path)
        wanted = classification == "canonical" or (
            profile == "complete" and classification == "media"
        )
        if not wanted:
            continue
        try:
            if path.is_symlink() or not path.is_file():
                continue
        except OSError as error:
            raise OSError(
                f"Could not inspect campaign file {path}: {error}"
            ) from error
        selected.append(path)
    return selected


def file_records(campaign_root: Path, profile: str) -> dict[str, dict]:
    """Hash every file in one portable snapshot."""

    records: dict[str, dict] = {}
    for path in campaign_files(campaign_root, profile):
        relative_path = normalized_relative(path, campaign_root)
        try:
            records[relative_path] = {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        except OSError as error:
            raise OSError(
                f"Could not read campaign file {path}: {error}"
            ) from error
    return records


def read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def read_manifest(campaign_root: Path) -> dict:
    manifest_path = campaign_root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing campaign manifest: {manifest_path}")
    return read_json(manifest_path)


def validate_game_state(path: Path) -> None:
    """Require a parseable mechanical ledger with the supported core shape."""

    payload = read_json(path)
    version = payload.get("version")
    if isinstance(version, bool) or version != STATE_VERSION:
        raise ValueError(
            f"game-state.json version must be {STATE_VERSION}, got {version!r}."
        )
    required_types = {
        "party": list,
        "characters": dict,
        "combat": dict,
    }
    for field, expected_type in required_types.items():
        if not isinstance(payload.get(field), expected_type):
            raise ValueError(
                f"game-state.json field {field!r} must be a "
                f"{expected_type.__name__}."
            )


def integer_value(value: object, default: int = 0) -> int:
    """Return an integer value or a conservative default."""

    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def detect_sync_hint(path: Path) -> dict:
    """Infer a sync provider from the selected path without claiming access."""

    normalized = str(path.expanduser()).replace("\\", "/").casefold()
    if "/library/cloudstorage/googledrive-" in normalized or re.match(
        r"^[a-z]:/(mi unidad|my drive)(/|$)", normalized
    ):
        return {
            "detected": True,
            "provider": "google-drive",
            "authorization": "not-verified",
        }
    if "/library/cloudstorage/onedrive-" in normalized or re.search(
        r"/(onedrive|one drive)([-/]|$)", normalized
    ):
        return {
            "detected": True,
            "provider": "onedrive",
            "authorization": "not-verified",
        }
    return {
        "detected": False,
        "provider": "none",
        "authorization": "not-applicable",
    }


def legacy_aliases(campaign_root: Path) -> dict[str, list[Path]]:
    """Find known non-canonical files left by older campaign workflows."""

    matches = {canonical: [] for canonical in LEGACY_ALIASES}
    for path in campaign_root.rglob("*.md"):
        relative_path = normalized_relative(path, campaign_root)
        for canonical, pattern in LEGACY_ALIASES.items():
            if pattern.search(relative_path):
                try:
                    if not path.is_symlink() and path.is_file():
                        matches[canonical].append(path)
                except OSError:
                    matches[canonical].append(path)
    return matches


def manifest_continuity_issues(campaign_root: Path) -> list[SaveIssue]:
    """Audit manifest/session alignment and legacy canonical-file conflicts."""

    issues: list[SaveIssue] = []
    manifest_path = campaign_root / MANIFEST_NAME
    manifest: dict = {}
    try:
        manifest_exists = manifest_path.is_file()
    except OSError as error:
        issues.append(
            SaveIssue(
                level="error",
                code="unreadable_manifest",
                message=f"Could not inspect campaign manifest: {error}",
                path=str(manifest_path),
            )
        )
        return issues
    if not manifest_exists:
        issues.append(
            SaveIssue(
                level="error",
                code="missing_manifest",
                message="The canonical questforge.json manifest is missing.",
                path=str(manifest_path),
            )
        )
    else:
        try:
            manifest = read_manifest(campaign_root)
        except (json.JSONDecodeError, OSError, ValueError) as error:
            issues.append(
                SaveIssue(
                    level="error",
                    code="invalid_manifest",
                    message=f"The campaign manifest is not valid JSON: {error}",
                    path=str(manifest_path),
                )
            )

    schema_version = manifest.get("schemaVersion", 1) if manifest else 0
    if manifest and schema_version != SCHEMA_VERSION:
        issues.append(
            SaveIssue(
                level="warning",
                code="legacy_manifest_schema",
                message=(
                    f"Manifest schema {schema_version} must be migrated to "
                    f"schema {SCHEMA_VERSION} before cloud sync."
                ),
                path=str(manifest_path),
            )
        )
    if manifest and not manifest.get("campaignId"):
        issues.append(
            SaveIssue(
                level="warning",
                code="missing_campaign_id",
                message="The campaign needs a stable campaignId before sync.",
                path=str(manifest_path),
            )
        )

    session_numbers = existing_session_numbers(campaign_root / "sessions")
    latest_session = session_numbers[-1] if session_numbers else 0
    current_session = integer_value(manifest.get("currentSession"))
    if manifest and current_session < 1:
        issues.append(
            SaveIssue(
                level="error",
                code="invalid_current_session",
                message="Manifest currentSession must be a positive integer.",
                path=str(manifest_path),
            )
        )
    if manifest and latest_session and current_session != latest_session:
        issues.append(
            SaveIssue(
                level="error",
                code="manifest_session_mismatch",
                message=(
                    f"Manifest points to session {current_session}, but the "
                    f"latest canonical session log is {latest_session}."
                ),
                path=str(manifest_path),
            )
        )

    for canonical, aliases in legacy_aliases(campaign_root).items():
        canonical_path = campaign_root / canonical
        for alias_path in sorted(aliases):
            try:
                canonical_exists = canonical_path.is_file()
            except OSError as error:
                issues.append(
                    SaveIssue(
                        level="error",
                        code="unreadable_canonical_file",
                        message=f"Could not inspect canonical file: {error}",
                        path=str(canonical_path),
                    )
                )
                continue
            if canonical_exists:
                try:
                    same_content = sha256_file(alias_path) == sha256_file(
                        canonical_path
                    )
                except OSError as error:
                    issues.append(
                        SaveIssue(
                            level="error",
                            code="unreadable_legacy_copy",
                            message=f"Could not compare legacy copy: {error}",
                            path=str(alias_path),
                        )
                    )
                    continue
                if same_content:
                    level = "warning"
                    code = "duplicate_noncanonical_copy"
                    message = (
                        "A redundant session-scoped copy exists outside the "
                        "canonical path."
                    )
                else:
                    level = "error"
                    code = "conflicting_noncanonical_copy"
                    message = (
                        "A session-scoped copy differs from the canonical "
                        "file and must be reconciled before saving."
                    )
                issues.append(
                    SaveIssue(
                        level=level,
                        code=code,
                        message=message,
                        path=str(alias_path),
                    )
                )
            else:
                issues.append(
                    SaveIssue(
                        level="warning",
                        code="recoverable_noncanonical_copy",
                        message=(
                            f"Canonical {canonical} is missing, but one "
                            "legacy copy may be migrated without deleting it."
                        ),
                        path=str(alias_path),
                    )
                )
    return issues


def inspect_campaign(
    campaign_root: Path,
    include_media_inventory: bool = True,
) -> CampaignInspection:
    """Inspect a campaign without mutating it."""

    campaign_root = campaign_root.expanduser().resolve()
    issues: list[SaveIssue] = []
    if not campaign_root.is_dir():
        issues.append(
            SaveIssue(
                level="error",
                code="missing_campaign_root",
                message="Campaign root does not exist.",
                path=str(campaign_root),
            )
        )
        return CampaignInspection(
            campaign_root=str(campaign_root),
            ok=False,
            schema_version=0,
            campaign_id="",
            current_session=0,
            latest_session=0,
            canonical_file_count=0,
            canonical_bytes=0,
            media_file_count=0,
            media_bytes=0,
            sync_hint=detect_sync_hint(campaign_root),
            issues=issues,
        )

    issues.extend(manifest_continuity_issues(campaign_root))
    for relative_path in sorted(REQUIRED_FILES):
        path = campaign_root / relative_path
        try:
            is_file = path.is_file()
        except OSError as error:
            issues.append(
                SaveIssue(
                    level="error",
                    code="unreadable_canonical_file",
                    message=f"Could not inspect canonical file: {error}",
                    path=str(path),
                )
            )
            continue
        if not is_file:
            issues.append(
                SaveIssue(
                    level="error",
                    code="missing_canonical_file",
                    message="A required canonical save file is missing.",
                    path=str(path),
                )
            )
        elif relative_path == "game-state.json":
            try:
                validate_game_state(path)
            except (OSError, ValueError) as error:
                issues.append(
                    SaveIssue(
                        level="error",
                        code="invalid_game_state",
                        message=f"Mechanical state is not usable: {error}",
                        path=str(path),
                    )
                )
    for relative_path in sorted(REQUIRED_DIRECTORIES):
        path = campaign_root / relative_path
        try:
            is_directory = path.is_dir()
        except OSError as error:
            issues.append(
                SaveIssue(
                    level="error",
                    code="unreadable_canonical_directory",
                    message=f"Could not inspect directory: {error}",
                    path=str(path),
                )
            )
            continue
        if not is_directory:
            issues.append(
                SaveIssue(
                    level="error",
                    code="missing_canonical_directory",
                    message="A required canonical save directory is missing.",
                    path=str(path),
                )
            )

    try:
        for path in campaign_root.rglob("*"):
            classification = classify_file(
                normalized_relative(path, campaign_root)
            )
            if classification != "canonical" and not (
                include_media_inventory and classification == "media"
            ):
                continue
            try:
                is_symlink = path.is_symlink()
            except OSError as error:
                issues.append(
                    SaveIssue(
                        level="warning",
                        code="path_inspection_incomplete",
                        message=f"Could not inspect path metadata: {error}",
                        path=str(path),
                    )
                )
                continue
            if is_symlink:
                issues.append(
                    SaveIssue(
                        level="error",
                        code="nonportable_symlink",
                        message="Symlinks are excluded from portable saves.",
                        path=str(path),
                    )
                )
    except OSError as error:
        issues.append(
            SaveIssue(
                level="warning",
                code="tree_inspection_incomplete",
                message=f"Could not inspect every optional path: {error}",
                path=str(campaign_root),
            )
        )

    manifest: dict = {}
    try:
        manifest = read_manifest(campaign_root)
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        pass
    try:
        canonical = campaign_files(campaign_root, "canonical")
    except OSError as error:
        canonical = []
        issues.append(
            SaveIssue(
                level="error",
                code="canonical_inventory_incomplete",
                message=str(error),
                path=str(campaign_root),
            )
        )
    complete = list(canonical)
    if include_media_inventory:
        try:
            complete = campaign_files(campaign_root, "complete")
        except OSError as error:
            issues.append(
                SaveIssue(
                    level="warning",
                    code="media_inventory_incomplete",
                    message=str(error),
                    path=str(campaign_root),
                )
            )
    canonical_set = set(canonical)
    media = [path for path in complete if path not in canonical_set]
    sessions = existing_session_numbers(campaign_root / "sessions")
    canonical_bytes = safe_total_bytes(canonical, issues, "canonical")
    media_bytes = safe_total_bytes(media, issues, "media")
    return CampaignInspection(
        campaign_root=str(campaign_root),
        ok=not any(issue.level == "error" for issue in issues),
        schema_version=(
            integer_value(manifest.get("schemaVersion", 1), default=1)
            if manifest
            else 0
        ),
        campaign_id=str(manifest.get("campaignId", "")),
        current_session=integer_value(manifest.get("currentSession")),
        latest_session=sessions[-1] if sessions else 0,
        canonical_file_count=len(canonical),
        canonical_bytes=canonical_bytes,
        media_file_count=len(media),
        media_bytes=media_bytes,
        sync_hint=detect_sync_hint(campaign_root),
        issues=issues,
    )


def safe_total_bytes(
    paths: list[Path],
    issues: list[SaveIssue],
    kind: str,
) -> int:
    """Sum available sizes and report Drive placeholders without crashing."""

    total = 0
    for path in paths:
        try:
            total += path.stat().st_size
        except OSError as error:
            issues.append(
                SaveIssue(
                    level="error" if kind == "canonical" else "warning",
                    code=f"unreadable_{kind}_file",
                    message=f"Could not read file metadata: {error}",
                    path=str(path),
                )
            )
    return total


def format_inspection_markdown(inspection: CampaignInspection) -> str:
    status = "READY" if inspection.ok else "NEEDS ATTENTION"
    lines = [
        "# Questforge Save Inspection",
        "",
        f"- Campaign: {inspection.campaign_root}",
        f"- Status: {status}",
        f"- Schema: {inspection.schema_version}",
        f"- Current session: {inspection.current_session}",
        f"- Latest session log: {inspection.latest_session}",
        (
            f"- Canonical save: {inspection.canonical_file_count} files, "
            f"{inspection.canonical_bytes} bytes"
        ),
        (
            f"- Optional media: {inspection.media_file_count} files, "
            f"{inspection.media_bytes} bytes"
        ),
        (
            "- Synced-folder hint: "
            f"{inspection.sync_hint.get('provider', 'none')} "
            "(permission not inferred)"
        ),
    ]
    if inspection.issues:
        lines.extend(["", "## Findings"])
        for issue in inspection.issues:
            lines.append(
                f"- {issue.level.upper()} {issue.code}: "
                f"{issue.message} ({issue.path})"
            )
    return "\n".join(lines) + "\n"


def default_storage() -> dict:
    return {
        "autosave": {
            "enabled": True,
            "trigger": "meaningful-turn",
            "compaction": "scene-boundary-or-three-turns",
            "media": "separate",
        },
        "snapshot": None,
        "history": [],
        "local": None,
        "cloud": None,
    }


def normalize_manifest(
    manifest: dict,
    latest_session: int,
    accept_latest_session: bool = False,
) -> dict:
    """Upgrade manifest structure while preserving campaign-specific fields."""

    normalized = json.loads(json.dumps(manifest))
    normalized["schemaVersion"] = SCHEMA_VERSION
    if not str(normalized.get("campaignId", "")).strip():
        normalized["campaignId"] = str(uuid.uuid4())
    if not isinstance(normalized.get("currentScene"), dict):
        normalized["currentScene"] = {
            "id": f"session-{latest_session:03d}:scene-001",
            "label": "current scene",
        }
    if accept_latest_session and latest_session:
        normalized["currentSession"] = latest_session
    normalized["canonicalFiles"] = dict(CANONICAL_MANIFEST)
    if not isinstance(normalized.get("storage"), dict):
        normalized["storage"] = default_storage()
    storage = normalized["storage"]
    defaults = default_storage()
    for key, value in defaults.items():
        storage.setdefault(key, value)
    if not isinstance(storage.get("autosave"), dict):
        storage["autosave"] = {}
    autosave = storage["autosave"]
    for key, value in defaults["autosave"].items():
        autosave.setdefault(key, value)
    if not isinstance(storage.get("history"), list):
        storage["history"] = []
    return normalized


def snapshot_payload(
    manifest: dict,
    records: dict[str, dict],
    profile: str,
    saved_at: str,
) -> tuple[dict, bool]:
    """Return manifest with a new snapshot, or unchanged if hashes match."""

    storage = manifest["storage"]
    previous = storage.get("snapshot") or {}
    current_session = integer_value(manifest.get("currentSession"))
    current_scene = manifest.get("currentScene")
    if (
        previous.get("files") == records
        and previous.get("profile") == profile
        and previous.get("session") == current_session
        and previous.get("scene") == current_scene
    ):
        return manifest, False

    revision = int(previous.get("revision", 0) or 0) + 1
    parent_save_id = previous.get("saveId") or None
    seed = {
        "campaignId": manifest["campaignId"],
        "parentSaveId": parent_save_id,
        "revision": revision,
        "profile": profile,
        "session": current_session,
        "scene": current_scene,
        "files": records,
    }
    save_id = sha256_bytes(
        json.dumps(
            seed,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    snapshot = {
        "saveId": save_id,
        "parentSaveId": parent_save_id,
        "revision": revision,
        "savedAt": saved_at,
        "session": current_session,
        "scene": current_scene,
        "profile": profile,
        "manifestWrittenLast": True,
        "files": records,
    }
    storage["snapshot"] = snapshot
    history = [
        entry
        for entry in storage.get("history", [])
        if isinstance(entry, dict) and entry.get("saveId") != save_id
    ]
    history.append({"revision": revision, "saveId": save_id})
    storage["history"] = history[-HISTORY_LIMIT:]
    storage["local"] = {
        "saveId": save_id,
        "verifiedAt": saved_at,
        "fileCount": len(records),
    }
    return manifest, True


def atomic_write_json(path: Path, payload: dict) -> None:
    """Replace one JSON file atomically in its existing directory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(
            descriptor, "w", encoding="utf-8", newline="\n"
        ) as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        Path(temporary_name).replace(path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def atomic_copy_file(source: Path, destination: Path) -> None:
    """Copy one legacy file without exposing a partial canonical result."""

    if destination.exists():
        raise FileExistsError(
            f"Refusing to overwrite canonical migration target: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        shutil.copyfile(source, temporary_path)
        if sha256_file(source) != sha256_file(temporary_path):
            raise OSError("Legacy migration copy failed SHA-256 verification.")
        temporary_path.replace(destination)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def ensure_ready(inspection: CampaignInspection) -> None:
    blockers = [
        issue.code for issue in inspection.issues if issue.level == "error"
    ]
    if blockers:
        raise ValueError(
            "Campaign save is blocked by: " + ", ".join(sorted(set(blockers)))
        )
    if (
        inspection.schema_version != SCHEMA_VERSION
        or not inspection.campaign_id
    ):
        raise ValueError("Run campaign_save.py migrate before saving.")


def record_local_save(
    campaign_root: Path,
    profile: str = "canonical",
    scene_id: str = "",
    scene_label: str = "",
) -> dict:
    """Record a verified local snapshot and write the manifest last."""

    campaign_root = campaign_root.expanduser().resolve()
    inspection = inspect_campaign(
        campaign_root,
        include_media_inventory=profile == "complete",
    )
    ensure_ready(inspection)
    manifest = normalize_manifest(
        read_manifest(campaign_root),
        latest_session=inspection.latest_session,
    )
    if scene_id:
        manifest["currentScene"] = {
            "id": scene_id,
            "label": scene_label or scene_id,
        }
    records = file_records(campaign_root, profile)
    saved_at = utc_now()
    manifest, changed = snapshot_payload(manifest, records, profile, saved_at)
    if changed:
        manifest["storage"]["local"]["syncHint"] = detect_sync_hint(
            campaign_root
        )
        atomic_write_json(campaign_root / MANIFEST_NAME, manifest)
    snapshot = manifest["storage"].get("snapshot") or {}
    return {
        "status": "saved" if changed else "unchanged",
        "campaignRoot": str(campaign_root),
        "saveId": snapshot.get("saveId", ""),
        "revision": snapshot.get("revision", 0),
        "profile": snapshot.get("profile", profile),
        "fileCount": len(records),
        "manifestWrittenLast": True,
    }


def cloud_plan(campaign_root: Path) -> dict:
    """Return the current local snapshot for a connector-driven cloud sync."""

    campaign_root = campaign_root.expanduser().resolve()
    manifest = read_manifest(campaign_root)
    storage = manifest.get("storage", {})
    snapshot = storage.get("snapshot") if isinstance(storage, dict) else None
    profile = snapshot.get("profile") if isinstance(snapshot, dict) else None
    inspection = inspect_campaign(
        campaign_root,
        include_media_inventory=profile == "complete",
    )
    ensure_ready(inspection)
    if not isinstance(snapshot, dict) or not snapshot.get("saveId"):
        raise ValueError("Run save-local before planning a cloud sync.")
    current_records = file_records(campaign_root, snapshot["profile"])
    if current_records != snapshot.get("files"):
        raise ValueError(
            "Campaign files changed after the last local snapshot; run "
            "save-local again before cloud sync."
        )
    return {
        "campaignId": manifest["campaignId"],
        "campaign": manifest.get("campaign", campaign_root.name),
        "saveId": snapshot["saveId"],
        "parentSaveId": snapshot.get("parentSaveId"),
        "revision": snapshot["revision"],
        "profile": snapshot["profile"],
        "session": snapshot.get("session"),
        "scene": snapshot.get("scene"),
        "files": snapshot["files"],
        "history": storage.get("history", []),
        "manifestPath": MANIFEST_NAME,
        "writeOrder": "all listed files, then questforge.json",
    }


def validate_remote_before(
    manifest: dict,
    remote_before: dict | None,
) -> None:
    """Require the remote manifest to be an ancestor of the local snapshot."""

    if remote_before is None:
        return
    if remote_before.get("campaignId") != manifest.get("campaignId"):
        raise ValueError("Remote folder belongs to a different campaignId.")
    remote_save_id = remote_before.get("saveId")
    remote_revision = int(remote_before.get("revision", 0) or 0)
    snapshot = manifest["storage"]["snapshot"]
    if remote_save_id == snapshot.get(
        "saveId"
    ) and remote_revision == snapshot.get("revision"):
        return
    history_pairs = {
        (int(entry.get("revision", 0) or 0), entry.get("saveId"))
        for entry in manifest["storage"].get("history", [])
        if isinstance(entry, dict)
    }
    if (remote_revision, remote_save_id) not in history_pairs:
        raise ValueError(
            "Remote save is not a known ancestor; stop and reconcile the "
            "conflict instead of overwriting it."
        )
    if remote_revision > int(snapshot.get("revision", 0) or 0):
        raise ValueError("Remote save is newer than the local snapshot.")


def validate_receipt_target(
    receipt: dict,
    provider: str,
    folder_ref: str,
    receipt_name: str,
) -> None:
    """Bind one verification receipt to the exact selected cloud folder."""

    if not isinstance(provider, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]*", provider
    ):
        raise ValueError("Cloud target provider is missing or invalid.")
    if not isinstance(folder_ref, str) or not folder_ref.strip():
        raise ValueError("Cloud target folderRef is missing or invalid.")
    if receipt.get("provider") != provider:
        raise ValueError(
            f"{receipt_name} provider does not match the selected provider."
        )
    if receipt.get("folderRef") != folder_ref:
        raise ValueError(
            f"{receipt_name} folderRef does not match the selected folder."
        )


def validate_cloud_receipt(
    manifest: dict,
    receipt: dict,
    provider: str,
    folder_ref: str,
) -> None:
    """Validate write authorization, ancestry, and every file readback."""

    snapshot = manifest["storage"]["snapshot"]
    validate_receipt_target(
        receipt,
        provider,
        folder_ref,
        "Data receipt",
    )
    if receipt.get("saveId") != snapshot.get("saveId"):
        raise ValueError("Receipt saveId does not match the local snapshot.")
    if receipt.get("writeAuthorized") is not True:
        raise ValueError("Cloud write authority was not verified.")
    if "remoteBefore" not in receipt:
        raise ValueError(
            "Receipt must declare remoteBefore; use null only after verifying "
            "that the selected folder has no campaign manifest."
        )
    remote_before = receipt["remoteBefore"]
    if remote_before is not None and not isinstance(remote_before, dict):
        raise ValueError("Receipt remoteBefore must be an object or null.")
    validate_remote_before(manifest, remote_before)
    receipts = receipt.get("files")
    if not isinstance(receipts, dict):
        raise ValueError("Receipt must contain per-file verification records.")
    for relative_path, record in snapshot["files"].items():
        remote_record = receipts.get(relative_path)
        if not isinstance(remote_record, dict):
            raise ValueError(f"Missing cloud receipt for {relative_path}.")
        if remote_record.get("verified") is not True:
            raise ValueError(
                f"Cloud readback was not verified for {relative_path}."
            )
        if remote_record.get("sha256") != record["sha256"]:
            raise ValueError(f"Cloud hash mismatch for {relative_path}.")


def stage_cloud_manifest(
    campaign_root: Path,
    receipt_path: Path,
    provider: str,
    folder_ref: str,
    output_path: Path,
    folder_url: str = "",
) -> dict:
    """Create the manifest that must be uploaded after all other files."""

    if not isinstance(provider, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]*", provider
    ):
        raise ValueError("Provider must use lowercase kebab-case.")
    if not isinstance(folder_ref, str) or not folder_ref.strip():
        raise ValueError("An exact provider folder reference is required.")
    campaign_root = campaign_root.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    try:
        output_path.relative_to(campaign_root)
    except ValueError:
        pass
    else:
        raise ValueError(
            "Stage the cloud manifest outside the campaign root so it cannot "
            "advance canonical state before remote verification."
        )
    plan = cloud_plan(campaign_root)
    manifest = read_manifest(campaign_root)
    receipt = read_json(receipt_path)
    validate_cloud_receipt(manifest, receipt, provider, folder_ref)
    verified_at = utc_now()
    manifest["storage"]["cloud"] = {
        "provider": provider,
        "folderRef": folder_ref,
        "folderUrl": folder_url or None,
        "saveId": plan["saveId"],
        "revision": plan["revision"],
        "verifiedAt": verified_at,
        "verification": "per-file-readback",
        "fileCount": len(plan["files"]),
    }
    atomic_write_json(output_path, manifest)
    return {
        "stagedManifest": str(output_path),
        "sha256": sha256_file(output_path),
        "saveId": plan["saveId"],
        "provider": provider,
        "folderRef": folder_ref,
        "uploadLastAs": MANIFEST_NAME,
    }


def commit_cloud_manifest(
    campaign_root: Path,
    staged_manifest_path: Path,
    manifest_receipt_path: Path,
) -> dict:
    """Commit the staged manifest locally after remote manifest readback."""

    campaign_root = campaign_root.expanduser().resolve()
    staged_manifest_path = staged_manifest_path.expanduser().resolve()
    staged = read_json(staged_manifest_path)
    current = read_manifest(campaign_root)
    staged_snapshot = staged.get("storage", {}).get("snapshot", {})
    current_snapshot = current.get("storage", {}).get("snapshot", {})
    if staged.get("campaignId") != current.get("campaignId"):
        raise ValueError("Staged manifest belongs to another campaign.")
    if staged_snapshot.get("saveId") != current_snapshot.get("saveId"):
        raise ValueError("Campaign changed after cloud manifest staging.")
    receipt = read_json(manifest_receipt_path)
    expected_hash = sha256_file(staged_manifest_path)
    if receipt.get("verified") is not True:
        raise ValueError("Remote questforge.json readback was not verified.")
    if receipt.get("sha256") != expected_hash:
        raise ValueError("Remote questforge.json hash does not match staging.")
    if receipt.get("saveId") != staged_snapshot.get("saveId"):
        raise ValueError("Remote manifest receipt has the wrong saveId.")
    staged_cloud = staged.get("storage", {}).get("cloud")
    if not isinstance(staged_cloud, dict):
        raise ValueError("Staged manifest is missing its cloud target.")
    validate_receipt_target(
        receipt,
        staged_cloud.get("provider"),
        staged_cloud.get("folderRef"),
        "Manifest receipt",
    )
    atomic_write_json(campaign_root / MANIFEST_NAME, staged)
    return {
        "status": "cloud-save-complete",
        "saveId": staged_snapshot["saveId"],
        "revision": staged_snapshot["revision"],
        "provider": staged["storage"]["cloud"]["provider"],
        "folderRef": staged["storage"]["cloud"]["folderRef"],
        "manifestWrittenLast": True,
    }


def build_portable_archive(
    campaign_root: Path,
    output_path: Path,
    include_media: bool = False,
) -> dict:
    """Build a deterministic portable campaign ZIP."""

    campaign_root = campaign_root.expanduser().resolve()
    profile = "complete" if include_media else "canonical"
    record_local_save(campaign_root, profile=profile)
    selected = campaign_files(campaign_root, profile)
    selected_directories = portable_directories(campaign_root, profile)
    manifest_path = campaign_root / MANIFEST_NAME
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for directory in selected_directories:
                relative_path = (
                    normalized_relative(
                        directory,
                        campaign_root,
                    ).rstrip("/")
                    + "/"
                )
                archive_info = zipfile.ZipInfo(
                    relative_path,
                    FIXED_ZIP_TIMESTAMP,
                )
                archive_info.external_attr = (0o40755 << 16) | 0x10
                archive.writestr(archive_info, b"")
            for path in selected:
                relative_path = normalized_relative(path, campaign_root)
                archive_info = zipfile.ZipInfo(
                    relative_path,
                    FIXED_ZIP_TIMESTAMP,
                )
                archive_info.compress_type = zipfile.ZIP_DEFLATED
                archive_info.external_attr = 0o100644 << 16
                archive.writestr(archive_info, path.read_bytes())
            archive_info = zipfile.ZipInfo(
                MANIFEST_NAME,
                FIXED_ZIP_TIMESTAMP,
            )
            archive_info.compress_type = zipfile.ZIP_DEFLATED
            archive_info.external_attr = 0o100644 << 16
            archive.writestr(archive_info, manifest_path.read_bytes())
        temporary_path.replace(output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return {
        "archive": str(output_path),
        "profile": profile,
        "fileCount": len(selected) + 1,
        "bytes": output_path.stat().st_size,
        "sha256": sha256_file(output_path),
    }


def portable_directories(campaign_root: Path, profile: str) -> list[Path]:
    """Return explicit directory entries needed to restore a SaveSet."""

    roots = set(CANONICAL_DIRECTORIES)
    if profile == "complete":
        roots.update(MEDIA_DIRECTORIES)
    directories: set[Path] = set()
    for relative_root in roots:
        root = campaign_root / relative_root
        if not root.is_dir() or root.is_symlink():
            continue
        directories.add(root)
        directories.update(
            path
            for path in root.rglob("*")
            if path.is_dir()
            and not path.is_symlink()
            and not any(part in EXCLUDED_PARTS for part in path.parts)
        )
    return sorted(directories)


def migration_plan(
    campaign_root: Path,
    accept_latest_session: bool = False,
) -> dict:
    """Build a non-destructive migration plan for an older campaign."""

    campaign_root = campaign_root.expanduser().resolve()
    actions: list[dict] = []
    blockers: list[dict] = []
    if not campaign_root.is_dir():
        blockers.append(
            {"code": "missing_campaign_root", "path": str(campaign_root)}
        )
        return {"actions": actions, "blockers": blockers}

    manifest_path = campaign_root / MANIFEST_NAME
    try:
        manifest = read_manifest(campaign_root)
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        ValueError,
    ) as error:
        blockers.append(
            {
                "code": "invalid_or_missing_manifest",
                "path": str(manifest_path),
                "message": str(error),
            }
        )
        return {"actions": actions, "blockers": blockers}

    alias_map = legacy_aliases(campaign_root)
    for canonical, aliases in alias_map.items():
        canonical_path = campaign_root / canonical
        try:
            canonical_exists = canonical_path.is_file()
        except OSError as error:
            blockers.append(
                {
                    "code": "unreadable_canonical_file",
                    "path": str(canonical_path),
                    "message": str(error),
                }
            )
            continue
        if canonical_exists:
            differing: list[Path] = []
            for alias_path in aliases:
                try:
                    if sha256_file(alias_path) != sha256_file(canonical_path):
                        differing.append(alias_path)
                except OSError as error:
                    blockers.append(
                        {
                            "code": "unreadable_legacy_copy",
                            "path": str(alias_path),
                            "canonical": canonical,
                            "message": str(error),
                        }
                    )
            if differing:
                blockers.append(
                    {
                        "code": "conflicting_noncanonical_copy",
                        "path": str(differing[-1]),
                        "canonical": canonical,
                    }
                )
            continue
        if len(aliases) == 1:
            actions.append(
                {
                    "action": "copy_legacy_canonical",
                    "source": str(aliases[0]),
                    "destination": str(canonical_path),
                }
            )
        elif len(aliases) > 1:
            blockers.append(
                {
                    "code": "ambiguous_legacy_copies",
                    "canonical": canonical,
                    "paths": [str(path) for path in aliases],
                }
            )

    planned_destinations = {
        Path(action["destination"]).resolve()
        for action in actions
        if action["action"] == "copy_legacy_canonical"
    }
    for relative_path in sorted(REQUIRED_FILES):
        path = (campaign_root / relative_path).resolve()
        try:
            is_file = path.is_file()
        except OSError as error:
            blockers.append(
                {
                    "code": "unreadable_canonical_file",
                    "path": str(path),
                    "message": str(error),
                }
            )
            continue
        if not is_file and path not in planned_destinations:
            blockers.append(
                {
                    "code": "missing_canonical_file",
                    "path": str(path),
                    "message": "Cannot reconstruct this file safely.",
                }
            )
        elif is_file and relative_path == "game-state.json":
            try:
                validate_game_state(path)
            except (OSError, ValueError) as error:
                blockers.append(
                    {
                        "code": "invalid_game_state",
                        "path": str(path),
                        "message": str(error),
                    }
                )
    for relative_path in sorted(REQUIRED_DIRECTORIES):
        path = campaign_root / relative_path
        try:
            is_directory = path.is_dir()
        except OSError as error:
            blockers.append(
                {
                    "code": "unreadable_canonical_directory",
                    "path": str(path),
                    "message": str(error),
                }
            )
            continue
        if is_directory:
            continue
        if relative_path == "checkpoints":
            actions.append(
                {"action": "create_directory", "path": str(path.resolve())}
            )
        else:
            blockers.append(
                {"code": "missing_canonical_directory", "path": str(path)}
            )

    sessions = existing_session_numbers(campaign_root / "sessions")
    latest_session = sessions[-1] if sessions else 0
    current_session = integer_value(manifest.get("currentSession"))
    if latest_session and current_session != latest_session:
        if accept_latest_session:
            actions.append(
                {
                    "action": "set_current_session",
                    "from": current_session,
                    "to": latest_session,
                }
            )
        else:
            blockers.append(
                {
                    "code": "manifest_session_mismatch",
                    "message": (
                        "Review the latest session, then rerun with "
                        "--accept-latest-session if it is canonical."
                    ),
                }
            )
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        actions.append(
            {
                "action": "upgrade_manifest_schema",
                "from": manifest.get("schemaVersion", 1),
                "to": SCHEMA_VERSION,
            }
        )
    if not manifest.get("campaignId"):
        actions.append({"action": "assign_campaign_id"})
    actions.append({"action": "write_manifest_last"})
    return {
        "campaignRoot": str(campaign_root),
        "latestSession": latest_session,
        "actions": actions,
        "blockers": blockers,
    }


def migrate_campaign(
    campaign_root: Path,
    apply: bool = False,
    accept_latest_session: bool = False,
) -> dict:
    """Migrate only safe, explicit legacy state and preserve old copies."""

    campaign_root = campaign_root.expanduser().resolve()
    plan = migration_plan(campaign_root, accept_latest_session)
    plan["applied"] = False
    if plan["blockers"] or not apply:
        return plan

    for action in plan["actions"]:
        if action["action"] == "copy_legacy_canonical":
            destination = Path(action["destination"])
            atomic_copy_file(Path(action["source"]), destination)
        elif action["action"] == "create_directory":
            Path(action["path"]).mkdir(parents=True, exist_ok=True)

    manifest = read_manifest(campaign_root)
    source_schema = manifest.get("schemaVersion", 1)
    manifest = normalize_manifest(
        manifest,
        latest_session=plan["latestSession"],
        accept_latest_session=accept_latest_session,
    )
    migrated_at = utc_now()
    manifest["migration"] = {
        "completedAt": migrated_at,
        "sourceSchemaVersion": source_schema,
        "legacyCopiesPreserved": True,
    }
    records = file_records(campaign_root, "canonical")
    manifest, _ = snapshot_payload(
        manifest,
        records,
        "canonical",
        migrated_at,
    )
    manifest["storage"]["local"]["syncHint"] = detect_sync_hint(campaign_root)
    atomic_write_json(campaign_root / MANIFEST_NAME, manifest)
    plan["applied"] = True
    plan["saveId"] = manifest["storage"]["snapshot"]["saveId"]
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect, save, sync, migrate, or export Questforge campaigns."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--campaign-root", required=True, type=Path)
    inspect_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
    )

    save_parser = subparsers.add_parser("save-local")
    save_parser.add_argument("--campaign-root", required=True, type=Path)
    save_parser.add_argument(
        "--profile",
        choices=tuple(sorted(PROFILES)),
        default="canonical",
    )
    save_parser.add_argument("--scene-id", default="")
    save_parser.add_argument("--scene-label", default="")

    plan_parser = subparsers.add_parser("plan-cloud")
    plan_parser.add_argument("--campaign-root", required=True, type=Path)

    stage_parser = subparsers.add_parser("stage-cloud")
    stage_parser.add_argument("--campaign-root", required=True, type=Path)
    stage_parser.add_argument("--receipt", required=True, type=Path)
    stage_parser.add_argument("--provider", required=True)
    stage_parser.add_argument("--folder-ref", required=True)
    stage_parser.add_argument("--folder-url", default="")
    stage_parser.add_argument("--output", required=True, type=Path)

    commit_parser = subparsers.add_parser("commit-cloud")
    commit_parser.add_argument("--campaign-root", required=True, type=Path)
    commit_parser.add_argument(
        "--staged-manifest",
        required=True,
        type=Path,
    )
    commit_parser.add_argument(
        "--manifest-receipt",
        required=True,
        type=Path,
    )

    package_parser = subparsers.add_parser("package")
    package_parser.add_argument("--campaign-root", required=True, type=Path)
    package_parser.add_argument("--output", required=True, type=Path)
    package_parser.add_argument("--include-media", action="store_true")

    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--campaign-root", required=True, type=Path)
    migrate_parser.add_argument("--apply", action="store_true")
    migrate_parser.add_argument(
        "--accept-latest-session",
        action="store_true",
    )
    return parser


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(arguments: Iterable[str] | None = None) -> int:
    parsed = build_parser().parse_args(arguments)
    try:
        if parsed.command == "inspect":
            inspection = inspect_campaign(parsed.campaign_root)
            if parsed.format == "markdown":
                print(format_inspection_markdown(inspection), end="")
            else:
                print_json(asdict(inspection))
            return 0 if inspection.ok else 1
        if parsed.command == "save-local":
            print_json(
                record_local_save(
                    parsed.campaign_root,
                    profile=parsed.profile,
                    scene_id=parsed.scene_id,
                    scene_label=parsed.scene_label,
                )
            )
            return 0
        if parsed.command == "plan-cloud":
            print_json(cloud_plan(parsed.campaign_root))
            return 0
        if parsed.command == "stage-cloud":
            print_json(
                stage_cloud_manifest(
                    parsed.campaign_root,
                    parsed.receipt,
                    parsed.provider,
                    parsed.folder_ref,
                    parsed.output,
                    folder_url=parsed.folder_url,
                )
            )
            return 0
        if parsed.command == "commit-cloud":
            print_json(
                commit_cloud_manifest(
                    parsed.campaign_root,
                    parsed.staged_manifest,
                    parsed.manifest_receipt,
                )
            )
            return 0
        if parsed.command == "package":
            print_json(
                build_portable_archive(
                    parsed.campaign_root,
                    parsed.output,
                    include_media=parsed.include_media,
                )
            )
            return 0
        if parsed.command == "migrate":
            result = migrate_campaign(
                parsed.campaign_root,
                apply=parsed.apply,
                accept_latest_session=parsed.accept_latest_session,
            )
            print_json(result)
            return 1 if result["blockers"] else 0
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        ValueError,
    ) as error:
        print_json({"status": "error", "message": str(error)})
        return 1
    raise AssertionError(f"Unhandled command: {parsed.command}")


if __name__ == "__main__":
    raise SystemExit(main())
