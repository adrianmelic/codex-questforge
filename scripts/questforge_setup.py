"""First-run setup for Codex Questforge."""

from __future__ import annotations

import argparse
import importlib.util
import json
import locale
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

try:
    from .rules_index import (
        RuleChunk,
        split_markdown_sections,
        write_index,
        write_sqlite_index,
    )
except ImportError:  # pragma: no cover - direct script execution path
    from rules_index import (
        RuleChunk,
        split_markdown_sections,
        write_index,
        write_sqlite_index,
    )

SRD_SOURCES = {
    "en": {
        "label": "English SRD v5.2.1",
        "url": "https://media.dndbeyond.com/compendium-images/srd/5.2/SRD_CC_v5.2.1.pdf",
        "filename": "SRD_CC_v5.2.1.pdf",
    },
    "es": {
        "label": "Español SRD v5.2.1",
        "url": "https://media.dndbeyond.com/compendium-images/srd/5.2/SP_SRD_CC_v5.2.1.pdf",
        "filename": "SP_SRD_CC_v5.2.1.pdf",
    },
}


@dataclass(frozen=True)
class SetupPaths:
    """Questforge local setup paths."""

    data_dir: Path
    downloads_dir: Path
    rules_dir: Path
    resources_dir: Path
    srd_resources_dir: Path
    language_resources_dir: Path
    pdf_path: Path
    markdown_path: Path
    jsonl_index_path: Path
    sqlite_index_path: Path
    manifest_path: Path


@dataclass(frozen=True)
class SetupResult:
    """Summary of a setup run."""

    language: str
    source_label: str
    source_url: str
    pdf_path: str | None
    markdown_path: str | None
    jsonl_index_path: str | None
    sqlite_index_path: str | None
    resources_index_path: str | None
    status: str
    notes: list[str]


Downloader = Callable[[str, Path], None]
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_language(value: str | None) -> str | None:
    """Return a supported language code from a locale-like value."""

    if not value:
        return None
    normalized = value.strip().lower().replace("-", "_")
    if not normalized:
        return None
    language_code = normalized.split("_", maxsplit=1)[0].split(
        ".", maxsplit=1
    )[0]
    if language_code in SRD_SOURCES:
        return language_code
    return None


def detect_language(
    environment: dict[str, str] | None = None,
    default: str = "en",
) -> str:
    """Detect the Questforge language without asking the user."""

    environment = environment if environment is not None else dict(os.environ)
    candidates = [
        environment.get("QUESTFORGE_LANGUAGE"),
        environment.get("LANGUAGE"),
        environment.get("LC_ALL"),
        environment.get("LC_MESSAGES"),
        environment.get("LANG"),
    ]

    for candidate in candidates:
        # LANGUAGE can contain a colon-delimited priority list.
        for part in (candidate or "").split(":"):
            language = normalize_language(part)
            if language:
                return language

    locale_candidates = [
        locale.getlocale()[0],
        locale.getlocale(locale.LC_CTYPE)[0],
        locale.getlocale(locale.LC_TIME)[0],
    ]
    for candidate in locale_candidates:
        language = normalize_language(candidate)
        if language:
            return language

    return default


def resolve_language(language: str | None) -> str:
    if language in (None, "auto"):
        return detect_language()
    normalized_language = normalize_language(language)
    if normalized_language is None:
        supported = ", ".join(sorted(SRD_SOURCES))
        raise ValueError(
            f"Unsupported language {language!r}; use one of: {supported}."
        )
    return normalized_language


def get_setup_paths(
    data_dir: Path,
    source_filename: str,
    language: str | None = None,
) -> SetupPaths:
    rules_stem = Path(source_filename).stem
    language_dir = language or rules_stem.lower()
    return SetupPaths(
        data_dir=data_dir,
        downloads_dir=data_dir / "downloads",
        rules_dir=data_dir / "rules",
        resources_dir=data_dir / "resources",
        srd_resources_dir=data_dir / "resources" / "srd",
        language_resources_dir=data_dir / "resources" / "srd" / language_dir,
        pdf_path=data_dir / "downloads" / source_filename,
        markdown_path=data_dir / "rules" / f"{rules_stem}.md",
        jsonl_index_path=data_dir / "rules" / f"{rules_stem}.jsonl",
        sqlite_index_path=data_dir / "rules" / f"{rules_stem}.sqlite",
        manifest_path=data_dir / "questforge-setup.json",
    )


def slugify_resource(value: str) -> str:
    normalized = value.strip().lower()
    slug = SLUG_PATTERN.sub("-", normalized).strip("-")
    return slug or "section"


def default_download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        destination.write_bytes(response.read())


def install_pdf_extractor() -> None:
    completed_process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "--disable-pip-version-check",
            "install",
            "pypdf",
        ],
        capture_output=True,
        text=True,
    )
    if completed_process.returncode != 0:
        output = "\n".join(
            part
            for part in (
                completed_process.stdout.strip(),
                completed_process.stderr.strip(),
            )
            if part
        )
        raise RuntimeError(
            "Failed to install pypdf for SRD PDF extraction."
            + (f"\n{output}" if output else "")
        )


def has_pypdf() -> bool:
    return importlib.util.find_spec("pypdf") is not None


def extract_pdf_pages(pdf_path: Path) -> list[str]:
    """Extract PDF text by page using optional pypdf."""

    if not has_pypdf():
        raise RuntimeError("pypdf is not installed.")

    from pypdf import PdfReader  # type: ignore[import-not-found]

    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return pages


def pages_to_markdown(
    pages: Iterable[str],
    source_label: str,
    source_url: str,
) -> str:
    lines = [
        f"# {source_label}",
        "",
        f"Source: {source_url}",
        "License: Creative Commons Attribution 4.0 International.",
        "",
    ]
    for page_number, page_text in enumerate(pages, start=1):
        cleaned_text = page_text.strip()
        if not cleaned_text:
            continue
        lines.extend(
            [
                f"## Page {page_number}",
                "",
                cleaned_text,
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def chunks_from_pages(
    pages: Iterable[str],
    source_label: str,
) -> list[RuleChunk]:
    chunks: list[RuleChunk] = []
    for page_number, page_text in enumerate(pages, start=1):
        cleaned_text = page_text.strip()
        if cleaned_text:
            chunks.append(
                RuleChunk(
                    source=source_label,
                    heading=f"Page {page_number}",
                    text=cleaned_text,
                )
            )
    return chunks


def read_rules_text_source(source_path: Path) -> tuple[str, list[RuleChunk]]:
    text = source_path.read_text(encoding="utf-8-sig")
    chunks = split_markdown_sections(text, source_path.name)
    if not chunks:
        chunks = [
            RuleChunk(source=source_path.name, heading="Rules", text=text)
        ]
    return text, chunks


def write_structured_resources(
    paths: SetupPaths,
    chunks: Iterable[RuleChunk],
    source_label: str,
    source_url: str,
    language: str,
) -> list[RuleChunk]:
    """Write Markdown resources and return chunks pointing at those files."""

    chunks = list(chunks)
    if paths.language_resources_dir.exists():
        shutil.rmtree(paths.language_resources_dir)
    sections_dir = paths.language_resources_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    resource_chunks: list[RuleChunk] = []
    index_rows = [
        f"# {source_label}",
        "",
        f"- Language: `{language}`",
        f"- Source: {source_url}",
        "- License: Creative Commons Attribution 4.0 International.",
        "",
        "## Sections",
        "",
    ]

    for index, chunk in enumerate(chunks, start=1):
        filename = f"{index:04d}-{slugify_resource(chunk.heading)}.md"
        relative_path = (
            Path("resources") / "srd" / language / "sections" / filename
        )
        section_path = sections_dir / filename
        section_text = "\n".join(
            [
                "---",
                "questforge_resource: srd",
                f"language: {language}",
                f"source: {json.dumps(source_label, ensure_ascii=False)}",
                f"source_url: {json.dumps(source_url, ensure_ascii=False)}",
                "license: CC-BY-4.0",
                f"section: {json.dumps(chunk.heading, ensure_ascii=False)}",
                "---",
                "",
                f"# {chunk.heading}",
                "",
                chunk.text.strip(),
                "",
            ]
        )
        section_path.write_text(section_text, encoding="utf-8", newline="\n")
        index_rows.append(f"- [{chunk.heading}](sections/{filename})")
        resource_chunks.append(
            RuleChunk(
                source=relative_path.as_posix(),
                heading=chunk.heading,
                text=chunk.text,
            )
        )

    resource_index = paths.language_resources_dir / "00-index.md"
    resource_index.write_text(
        "\n".join(index_rows).strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_srd_manifest(paths, language, source_label, source_url, len(chunks))
    return resource_chunks


def write_srd_manifest(
    paths: SetupPaths,
    language: str,
    source_label: str,
    source_url: str,
    section_count: int,
) -> None:
    manifest_path = paths.srd_resources_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    installed_language = {
        "label": source_label,
        "sourceUrl": source_url,
        "license": "CC-BY-4.0",
        "index": f"{language}/00-index.md",
        "sectionCount": section_count,
    }
    installed_languages = {language: installed_language}
    default_language = language
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        installed_languages = existing.get("installedLanguages", {})
        installed_languages[language] = installed_language
        existing_default = existing.get("defaultLanguage")
        if existing_default in installed_languages:
            default_language = existing_default
    if "en" in installed_languages:
        default_language = "en"
    payload = {
        "defaultLanguage": default_language,
        "installedLanguages": installed_languages,
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_manifest(paths: SetupPaths, result: SetupResult) -> None:
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    paths.manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def setup_questforge(
    data_dir: Path,
    language: str | None = "auto",
    force: bool = False,
    rules_text: Path | None = None,
    downloader: Downloader = default_download,
    install_extractor: bool = False,
) -> SetupResult:
    """Prepare local Questforge data and rules indexes."""

    language = resolve_language(language)
    source = SRD_SOURCES[language]
    paths = get_setup_paths(data_dir, source["filename"], language)
    notes: list[str] = []

    paths.downloads_dir.mkdir(parents=True, exist_ok=True)
    paths.rules_dir.mkdir(parents=True, exist_ok=True)
    paths.resources_dir.mkdir(parents=True, exist_ok=True)

    if install_extractor and not has_pypdf():
        install_pdf_extractor()
        notes.append("Installed pypdf for PDF text extraction.")

    if rules_text is not None:
        markdown_text, chunks = read_rules_text_source(rules_text)
        paths.markdown_path.write_text(
            markdown_text,
            encoding="utf-8",
            newline="\n",
        )
        resource_chunks = write_structured_resources(
            paths,
            chunks,
            source["label"],
            source["url"],
            language,
        )
        write_index(resource_chunks, paths.jsonl_index_path)
        write_sqlite_index(resource_chunks, paths.sqlite_index_path)
        status = "ready"
        notes.append(f"Built rules indexes from text source: {rules_text}")
    else:
        if force or not paths.pdf_path.exists():
            downloader(source["url"], paths.pdf_path)
            notes.append(f"Downloaded {source['label']}.")
        else:
            notes.append(f"Reused existing PDF: {paths.pdf_path}")

        if has_pypdf():
            pages = extract_pdf_pages(paths.pdf_path)
            chunks = chunks_from_pages(pages, source["label"])
            markdown_text = pages_to_markdown(
                pages,
                source["label"],
                source["url"],
            )
            paths.markdown_path.write_text(
                markdown_text,
                encoding="utf-8",
                newline="\n",
            )
            resource_chunks = write_structured_resources(
                paths,
                chunks,
                source["label"],
                source["url"],
                language,
            )
            write_index(resource_chunks, paths.jsonl_index_path)
            write_sqlite_index(resource_chunks, paths.sqlite_index_path)
            status = "ready"
            notes.append(f"Extracted and indexed {len(chunks)} PDF pages.")
        else:
            status = "pdf_downloaded_index_pending"
            notes.append(
                "PDF was downloaded, but pypdf is not installed; rules indexes "
                "were not generated."
            )
            notes.append(
                "Install pypdf or rerun with --install-pdf-extractor to build "
                "the local JSONL and SQLite rules indexes."
            )

    result = SetupResult(
        language=language,
        source_label=source["label"],
        source_url=source["url"],
        pdf_path=str(paths.pdf_path) if paths.pdf_path.exists() else None,
        markdown_path=(
            str(paths.markdown_path) if paths.markdown_path.exists() else None
        ),
        jsonl_index_path=(
            str(paths.jsonl_index_path)
            if paths.jsonl_index_path.exists()
            else None
        ),
        sqlite_index_path=(
            str(paths.sqlite_index_path)
            if paths.sqlite_index_path.exists()
            else None
        ),
        resources_index_path=(
            str(paths.language_resources_dir / "00-index.md")
            if (paths.language_resources_dir / "00-index.md").exists()
            else None
        ),
        status=status,
        notes=notes,
    )
    write_manifest(paths, result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare a local Questforge rules cache and database."
    )
    parser.add_argument(
        "--data-dir",
        default=".questforge",
        type=Path,
        help="Local Questforge data directory. Defaults to .questforge.",
    )
    parser.add_argument(
        "--language",
        choices=("auto", *tuple(SRD_SOURCES)),
        default="auto",
        help=(
            "SRD language to use. Defaults to auto: QUESTFORGE_LANGUAGE, "
            "system locale, then English."
        ),
    )
    parser.add_argument(
        "--rules-text",
        type=Path,
        help="Use an existing UTF-8 rules text/Markdown file instead of PDF.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload the SRD PDF when using the official source.",
    )
    parser.add_argument(
        "--install-pdf-extractor",
        action="store_true",
        help="Install pypdf with pip before extracting the SRD PDF.",
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    parsed_arguments = parser.parse_args(arguments)
    result = setup_questforge(
        data_dir=parsed_arguments.data_dir,
        language=parsed_arguments.language,
        force=parsed_arguments.force,
        rules_text=parsed_arguments.rules_text,
        install_extractor=parsed_arguments.install_pdf_extractor,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0 if result.status == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
