"""Pre-beta audit for a local Questforge campaign workspace."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    from .campaign_memory import (
        existing_session_numbers,
        get_campaign_paths,
        read_template,
        read_visual_index,
    )
    from .visual_gallery import create_visual_gallery
except ImportError:  # pragma: no cover - direct script execution path
    from campaign_memory import (
        existing_session_numbers,
        get_campaign_paths,
        read_template,
        read_visual_index,
    )
    from visual_gallery import create_visual_gallery


@dataclass(frozen=True)
class PreflightIssue:
    """One actionable campaign readiness issue."""

    level: str
    code: str
    message: str
    path: str = ""


@dataclass(frozen=True)
class PreflightResult:
    """Structured result for a campaign preflight audit."""

    campaign_root: str
    ok: bool
    issue_count: int
    error_count: int
    warning_count: int
    visual_asset_count: int
    missing_visual_asset_count: int
    latest_gallery_url: str
    issues: list[PreflightIssue]


def run_preflight(
    campaign_root: Path,
    require_player_journal: bool = False,
    refresh_gallery: bool = False,
    repair_missing_templates: bool = False,
    title: str = "",
    viewer_roots: list[Path] | None = None,
) -> PreflightResult:
    """Audit campaign files, visual assets, and gallery readiness."""

    campaign_root = campaign_root.expanduser().resolve()
    paths = get_campaign_paths(campaign_root)
    issues: list[PreflightIssue] = []
    visual_asset_count = 0
    missing_visual_asset_count = 0
    latest_gallery_url = ""

    if not paths.root.exists():
        issues.append(
            PreflightIssue(
                level="error",
                code="missing_campaign_root",
                message="Campaign root does not exist.",
                path=str(paths.root),
            )
        )
        return build_result(
            paths.root,
            issues,
            visual_asset_count,
            missing_visual_asset_count,
            latest_gallery_url,
        )

    if repair_missing_templates:
        repair_safe_missing_templates(paths, issues)

    for required_file in required_files(paths):
        if not required_file.exists():
            issues.append(
                PreflightIssue(
                    level="error",
                    code="missing_required_file",
                    message="Required campaign file is missing.",
                    path=str(required_file),
                )
            )

    for required_directory in required_directories(paths):
        if not required_directory.is_dir():
            issues.append(
                PreflightIssue(
                    level="error",
                    code="missing_required_directory",
                    message="Required campaign directory is missing.",
                    path=str(required_directory),
                )
            )

    if not paths.player_journal.exists():
        issues.append(
            PreflightIssue(
                level="error" if require_player_journal else "warning",
                code="missing_player_journal",
                message=(
                    "Missing spoiler-free player journal for beta recovery."
                ),
                path=str(paths.player_journal),
            )
        )

    if not existing_session_numbers(paths.sessions):
        issues.append(
            PreflightIssue(
                level="warning",
                code="missing_session_logs",
                message="No session logs found.",
                path=str(paths.sessions),
            )
        )

    if paths.visual_index.exists():
        visual_asset_count, missing_visual_asset_count = audit_visual_assets(
            paths.root,
            paths.visual_index,
            issues,
        )
    if paths.visual_ledger.exists() and not has_table_data_rows(
        paths.visual_ledger
    ):
        issues.append(
            PreflightIssue(
                level="warning",
                code="empty_visual_ledger",
                message=(
                    "Visual ledger has no active continuity rows; recurring "
                    "states may drift in generated images."
                ),
                path=str(paths.visual_ledger),
            )
        )

    gallery_path = paths.root / "images" / "visual-gallery.html"
    if refresh_gallery and paths.visual_index.exists():
        try:
            gallery_result = create_visual_gallery(
                paths.root,
                title=title,
                viewer_roots=viewer_roots,
            )
            latest_gallery_url = gallery_result.gallery_url
        except (FileNotFoundError, OSError, ValueError) as error:
            issues.append(
                PreflightIssue(
                    level="error",
                    code="gallery_refresh_failed",
                    message=f"Could not refresh visual gallery: {error}",
                    path=str(gallery_path),
                )
            )
    elif gallery_path.exists():
        latest_gallery_url = f"{gallery_path.resolve().as_uri()}#latest"
    elif visual_asset_count:
        issues.append(
            PreflightIssue(
                level="warning",
                code="missing_visual_gallery",
                message=(
                    "Registered visual assets exist, but the local gallery "
                    "has not been generated."
                ),
                path=str(gallery_path),
            )
        )

    return build_result(
        paths.root,
        issues,
        visual_asset_count,
        missing_visual_asset_count,
        latest_gallery_url,
    )


def required_files(paths) -> tuple[Path, ...]:
    return (
        paths.manifest,
        paths.campaign_state,
        paths.game_state,
        paths.opening_brief,
        paths.adventure_spine,
        paths.puzzle_ledger,
        paths.visual_bible,
        paths.visual_index,
        paths.visual_ledger,
    )


def required_directories(paths) -> tuple[Path, ...]:
    return (
        paths.characters,
        paths.sessions,
        paths.checkpoints,
        paths.image_prompts,
        paths.image_assets,
        paths.image_viewers,
        paths.rules,
    )


def repair_safe_missing_templates(paths, issues: list[PreflightIssue]) -> None:
    """Create safe empty campaign notebooks for older campaign workspaces."""

    for directory in required_directories(paths):
        if directory.exists():
            continue
        directory.mkdir(parents=True, exist_ok=True)
        issues.append(
            PreflightIssue(
                level="info",
                code="created_missing_directory",
                message="Created missing campaign directory.",
                path=str(directory),
            )
        )

    for path, template_name in repairable_template_files(paths):
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            read_template(template_name),
            encoding="utf-8",
            newline="\n",
        )
        issues.append(
            PreflightIssue(
                level="info",
                code="created_missing_template",
                message="Created missing campaign notebook from template.",
                path=str(path),
            )
        )


def repairable_template_files(paths) -> tuple[tuple[Path, str], ...]:
    return (
        (paths.adventure_spine, "adventure-spine.md"),
        (paths.puzzle_ledger, "puzzle-ledger.md"),
        (paths.game_state, "game-state.json"),
        (paths.visual_ledger, "visual-ledger.md"),
        (paths.player_journal, "player-journal.md"),
    )


def audit_visual_assets(
    campaign_root: Path,
    visual_index_path: Path,
    issues: list[PreflightIssue],
) -> tuple[int, int]:
    visual_asset_count = 0
    missing_visual_asset_count = 0
    for entry in read_visual_index(visual_index_path):
        if not entry.asset_path:
            continue
        visual_asset_count += 1
        asset_path = resolve_index_path(campaign_root, entry.asset_path)
        if not asset_path.is_file():
            missing_visual_asset_count += 1
            issues.append(
                PreflightIssue(
                    level="error",
                    code="missing_visual_asset",
                    message=(
                        f"Visual index entry '{entry.label}' points to a "
                        "missing asset."
                    ),
                    path=str(asset_path),
                )
            )
    return visual_asset_count, missing_visual_asset_count


def resolve_index_path(campaign_root: Path, index_path: str) -> Path:
    candidate = Path(index_path)
    if candidate.is_absolute():
        return candidate.resolve()
    return (campaign_root / candidate).resolve()


def has_table_data_rows(path: Path) -> bool:
    header_first_cells = {
        "Entity",
        "Object",
        "Location",
        "Format",
        "---",
    }
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "## Style Notes":
            break
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        first_cell = stripped.strip("|").split("|", maxsplit=1)[0].strip()
        if first_cell and first_cell not in header_first_cells:
            return True
    return False


def build_result(
    campaign_root: Path,
    issues: list[PreflightIssue],
    visual_asset_count: int,
    missing_visual_asset_count: int,
    latest_gallery_url: str,
) -> PreflightResult:
    error_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    return PreflightResult(
        campaign_root=str(campaign_root),
        ok=error_count == 0,
        issue_count=len(issues),
        error_count=error_count,
        warning_count=warning_count,
        visual_asset_count=visual_asset_count,
        missing_visual_asset_count=missing_visual_asset_count,
        latest_gallery_url=latest_gallery_url,
        issues=issues,
    )


def format_preflight_markdown(result: PreflightResult) -> str:
    status = "PASS" if result.ok else "NEEDS ATTENTION"
    lines = [
        "# Questforge Preflight",
        "",
        f"- Campaign: {result.campaign_root}",
        f"- Status: {status}",
        f"- Issues: {result.error_count} errors, "
        f"{result.warning_count} warnings",
        f"- Visual assets: {result.visual_asset_count} registered, "
        f"{result.missing_visual_asset_count} missing",
    ]
    if result.latest_gallery_url:
        lines.append(f"- Gallery: {result.latest_gallery_url}")
    if result.issues:
        lines.extend(["", "## Findings"])
        for issue in result.issues:
            path_suffix = f" ({issue.path})" if issue.path else ""
            lines.append(
                f"- {issue.level.upper()} {issue.code}: "
                f"{issue.message}{path_suffix}"
            )
    else:
        lines.extend(["", "No blocking campaign readiness issues found."])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit a Questforge campaign before human beta play."
    )
    parser.add_argument("--campaign-root", required=True, type=Path)
    parser.add_argument("--require-player-journal", action="store_true")
    parser.add_argument("--refresh-gallery", action="store_true")
    parser.add_argument(
        "--repair-missing-templates",
        action="store_true",
        help=(
            "Create safe empty notebooks missing from older campaigns, "
            "without overwriting existing files."
        ),
    )
    parser.add_argument("--title", default="")
    parser.add_argument(
        "--viewer-root",
        action="append",
        default=[],
        type=Path,
        help="Extra folder to scan for matching 360 viewer HTML files.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = run_preflight(
        campaign_root=parsed_arguments.campaign_root,
        require_player_journal=parsed_arguments.require_player_journal,
        refresh_gallery=parsed_arguments.refresh_gallery,
        repair_missing_templates=parsed_arguments.repair_missing_templates,
        title=parsed_arguments.title,
        viewer_roots=parsed_arguments.viewer_root,
    )
    if parsed_arguments.format == "json":
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(format_preflight_markdown(result), end="")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
