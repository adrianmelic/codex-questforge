"""Build a deterministic Questforge archive for plugin submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable

INCLUDED_FILES = {
    ".codex-plugin/plugin.json",
    "LICENSE",
    "NOTICE.md",
    "PRIVACY.md",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "TERMS.md",
}
INCLUDED_TREES = (
    "assets",
    "resources",
    "skills",
    "templates",
)
INCLUDED_RUNTIME_DOCS = {
    "docs/beta-preflight-checklist.md",
    "docs/game-state.md",
    "docs/narrative-diversity.md",
    "docs/sound-atlas.md",
    "docs/visual-playbook.md",
    "docs/visual-prep-workflow.md",
}
EXCLUDED_NAMES = {"__pycache__", ".pytest_cache", ".DS_Store"}
EXCLUDED_RELATIVE_FILES = {"assets/screenshot-questforge-cover.png"}
EXCLUDED_RUNTIME_SCRIPTS = {"alpha_playtest.py", "self_play.py"}
SCRIPT_REFERENCE_PATTERN = re.compile(r"\.\./\.\./(?P<path>[^\s`\"')]+)")
FIXED_TIMESTAMP = (2020, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {".html", ".json", ".md", ".py", ".svg", ".yaml", ".yml"}
FORBIDDEN_RELEASE_PHRASES = {"Adrian and Codex", "Codex Questforge"}


def release_files(repo_root: Path) -> list[Path]:
    """Return the reviewed file set included in the public archive."""

    relative_paths = set(INCLUDED_FILES) | set(INCLUDED_RUNTIME_DOCS)
    for tree in INCLUDED_TREES:
        tree_root = repo_root / tree
        relative_paths.update(
            path.relative_to(repo_root).as_posix()
            for path in tree_root.rglob("*")
            if path.is_file()
            and not any(part in EXCLUDED_NAMES for part in path.parts)
        )

    scripts_root = repo_root / "scripts"
    relative_paths.update(
        path.relative_to(repo_root).as_posix()
        for path in scripts_root.glob("*.py")
        if path.name != Path(__file__).name
        and path.name not in EXCLUDED_RUNTIME_SCRIPTS
    )

    files = [repo_root / path for path in sorted(relative_paths)]
    files = [
        path
        for path in files
        if path.relative_to(repo_root).as_posix()
        not in EXCLUDED_RELATIVE_FILES
    ]
    missing = [path for path in files if not path.is_file()]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Release files are missing: {missing_text}")
    return files


def referenced_skill_files(repo_root: Path) -> set[Path]:
    """Resolve concrete plugin-root references used by bundled skills."""

    references: set[Path] = set()
    for skill_path in (repo_root / "skills").glob("*/SKILL.md"):
        text = skill_path.read_text(encoding="utf-8")
        for match in SCRIPT_REFERENCE_PATTERN.finditer(text):
            value = match.group("path").rstrip(".,;:")
            if "<" in value or "{" in value:
                continue
            resolved = (skill_path.parent / "../.." / value).resolve()
            try:
                resolved.relative_to(repo_root.resolve())
            except ValueError as error:
                raise ValueError(
                    f"Skill reference escapes the plugin root: {value}"
                ) from error
            if resolved.exists():
                references.add(resolved)
    return references


def validate_release_files(repo_root: Path, files: Iterable[Path]) -> None:
    """Reject missing references and common private or generated artifacts."""

    files = list(files)
    included = {path.resolve() for path in files}
    missing_references = referenced_skill_files(repo_root) - included
    if missing_references:
        missing_text = ", ".join(
            str(path.relative_to(repo_root))
            for path in sorted(missing_references)
        )
        raise ValueError(
            f"Skill references omitted from release: {missing_text}"
        )

    forbidden_parts = {
        ".env",
        ".git",
        ".questforge",
        "campaigns",
        "generated_images",
        "outputs",
        "playtests",
        "tests",
    }
    for path in files:
        relative = path.relative_to(repo_root)
        if any(part in forbidden_parts for part in relative.parts):
            raise ValueError(f"Private artifact in release: {relative}")
        if path.suffix.lower() in {".pyc", ".pyo"}:
            raise ValueError(f"Python cache in release: {relative}")
        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            for phrase in FORBIDDEN_RELEASE_PHRASES:
                if phrase in text:
                    raise ValueError(
                        f"Legacy public identity {phrase!r} in {relative}"
                    )

    validate_submission_test_count(repo_root)


def validate_submission_test_count(repo_root: Path) -> None:
    """Enforce the exact reviewer test count required by the portal."""

    test_cases_path = repo_root / "submission" / "test-cases.md"
    text = test_cases_path.read_text(encoding="utf-8")
    positive_count = len(
        re.findall(r"^## Positive \d+:", text, flags=re.MULTILINE)
    )
    negative_count = len(
        re.findall(r"^## Negative \d+:", text, flags=re.MULTILINE)
    )
    if (positive_count, negative_count) != (5, 3):
        raise ValueError(
            "Submission must contain exactly five positive and three "
            f"negative cases; found {positive_count} and {negative_count}."
        )


def build_archive(repo_root: Path, output_dir: Path) -> Path:
    """Create and return the deterministic release ZIP."""

    repo_root = repo_root.resolve()
    manifest = json.loads(
        (repo_root / ".codex-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )
    )
    files = release_files(repo_root)
    validate_release_files(repo_root, files)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (
        f"{manifest['name']}-skills-{manifest['version']}.zip"
    )
    with zipfile.ZipFile(
        output_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            relative_path = path.relative_to(repo_root).as_posix()
            archive_info = zipfile.ZipInfo(relative_path, FIXED_TIMESTAMP)
            archive_info.compress_type = zipfile.ZIP_DEFLATED
            archive_info.external_attr = 0o100644 << 16
            archive.writestr(archive_info, path.read_bytes())
    return output_path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the Questforge skills-only submission archive."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    parsed_arguments = build_parser().parse_args(arguments)
    output_path = build_archive(
        parsed_arguments.repo_root,
        parsed_arguments.output_dir,
    )
    print(
        json.dumps(
            {
                "archive": str(output_path.resolve()),
                "bytes": output_path.stat().st_size,
                "sha256": sha256(output_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
