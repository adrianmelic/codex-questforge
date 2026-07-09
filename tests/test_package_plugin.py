import json
import zipfile
from pathlib import Path

from scripts.package_plugin import (
    build_archive,
    release_files,
    validate_submission_test_count,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_release_file_set_contains_runtime_and_excludes_private_artifacts():
    paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in release_files(REPO_ROOT)
    }

    assert ".codex-plugin/plugin.json" in paths
    assert "skills/questforge/SKILL.md" in paths
    assert "scripts/game_state.py" in paths
    assert "resources/core-rules/en.md" in paths
    assert "templates/game-state.json" in paths
    assert "PRIVACY.md" in paths
    assert "assets/screenshot-questforge-cover.png" not in paths
    assert "scripts/alpha_playtest.py" not in paths
    assert "scripts/self_play.py" not in paths
    assert not any(path.startswith("tests/") for path in paths)
    assert not any("__pycache__" in path for path in paths)


def test_archive_is_portal_ready(tmp_path: Path):
    archive_path = build_archive(REPO_ROOT, tmp_path)

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        manifest = json.loads(
            archive.read(".codex-plugin/plugin.json").decode("utf-8")
        )

    assert archive_path.name == (
        f"questforge-skills-{manifest['version']}.zip"
    )
    assert manifest["name"] == "questforge"
    assert "skills/questforge/SKILL.md" in names
    assert "assets/audio/library.json" in names
    assert not any(name.startswith(".git/") for name in names)


def test_submission_has_exact_required_test_count():
    validate_submission_test_count(REPO_ROOT)
