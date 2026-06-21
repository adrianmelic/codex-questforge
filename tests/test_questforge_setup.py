import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import scripts.questforge_setup as questforge_setup
from scripts.questforge_setup import (
    SRD_SOURCES,
    detect_language,
    get_setup_paths,
    normalize_language,
    pages_to_markdown,
    setup_questforge,
)
from scripts.rules_index import search_sqlite_index


def test_pages_to_markdown_keeps_page_anchors():
    markdown = pages_to_markdown(
        ["Ability checks use a d20.", "", "Resting restores resources."],
        "Test SRD",
        "https://example.invalid/srd.pdf",
    )

    assert "# Test SRD" in markdown
    assert "## Page 1" in markdown
    assert "## Page 3" in markdown
    assert "## Page 2" not in markdown


def test_normalize_language_accepts_locale_forms():
    assert normalize_language("es_ES.UTF-8") == "es"
    assert normalize_language("en-US") == "en"
    assert normalize_language("fr_FR") is None


def test_detect_language_prefers_explicit_environment():
    assert detect_language({"QUESTFORGE_LANGUAGE": "es"}) == "es"
    assert detect_language({"LANGUAGE": "fr:es:en"}) == "es"
    assert detect_language({"LANG": "en_US.UTF-8"}) == "en"


def test_install_pdf_extractor_suppresses_success_output(monkeypatch):
    calls = []

    def fake_run(command, capture_output, text):
        calls.append(
            {
                "command": command,
                "capture_output": capture_output,
                "text": text,
            }
        )
        return SimpleNamespace(returncode=0, stdout="installed", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    questforge_setup.install_pdf_extractor()

    assert calls[0]["capture_output"] is True
    assert calls[0]["text"] is True
    assert "--disable-pip-version-check" in calls[0]["command"]


def test_setup_from_rules_text_builds_local_indexes(tmp_path: Path):
    rules_text = tmp_path / "rules.md"
    rules_text.write_text(
        "# Ability Checks\nRoll a d20 and add a modifier.\n",
        encoding="utf-8",
    )
    data_dir = tmp_path / "questforge-data"

    result = setup_questforge(
        data_dir=data_dir,
        language="es",
        rules_text=rules_text,
    )
    paths = get_setup_paths(data_dir, SRD_SOURCES["es"]["filename"], "es")

    assert result.status == "ready"
    assert result.pdf_path is None
    assert paths.markdown_path.exists()
    assert paths.jsonl_index_path.exists()
    assert paths.sqlite_index_path.exists()
    assert paths.manifest_path.exists()
    assert result.resources_index_path is not None
    assert paths.language_resources_dir.name == "es"
    assert (paths.language_resources_dir / "00-index.md").exists()
    assert (
        paths.language_resources_dir / "sections" / "0001-ability-checks.md"
    ).exists()
    srd_manifest = paths.srd_resources_dir / "manifest.json"
    manifest_payload = json.loads(srd_manifest.read_text(encoding="utf-8"))
    assert manifest_payload["defaultLanguage"] == "es"
    assert manifest_payload["installedLanguages"]["es"]["label"] == (
        "Español SRD v5.2.1"
    )

    results = search_sqlite_index(paths.sqlite_index_path, "modifier", limit=1)
    assert results[0].chunk.heading == "Ability Checks"
    assert results[0].chunk.source.endswith("0001-ability-checks.md")


def test_srd_manifest_prefers_english_when_installed_after_spanish(
    tmp_path: Path,
):
    rules_text = tmp_path / "rules.md"
    rules_text.write_text(
        "# Ability Checks\nRoll a d20 and add a modifier.\n",
        encoding="utf-8",
    )
    data_dir = tmp_path / "questforge-data"

    setup_questforge(data_dir=data_dir, language="es", rules_text=rules_text)
    setup_questforge(data_dir=data_dir, language="en", rules_text=rules_text)

    manifest_path = data_dir / "resources" / "srd" / "manifest.json"
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_payload["defaultLanguage"] == "en"
    assert set(manifest_payload["installedLanguages"]) == {"en", "es"}


def test_setup_without_extractor_downloads_pdf_and_marks_index_pending(
    tmp_path: Path,
    monkeypatch,
):
    def fake_download(url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"%PDF-1.7 fake")

    monkeypatch.setattr(questforge_setup, "has_pypdf", lambda: False)

    result = setup_questforge(
        data_dir=tmp_path / "questforge-data",
        downloader=fake_download,
    )

    assert result.status == "pdf_downloaded_index_pending"
    assert result.pdf_path.endswith("SP_SRD_CC_v5.2.1.pdf")
    assert result.jsonl_index_path is None
    assert result.sqlite_index_path is None
