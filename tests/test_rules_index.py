import json
from pathlib import Path

import pytest

from scripts.rules_index import (
    build_index,
    main,
    read_index,
    search_setup_index,
    search_index,
    split_markdown_sections,
    write_index,
    write_sqlite_index,
)


def test_split_markdown_sections_uses_headings():
    chunks = split_markdown_sections(
        "# Ability Checks\nRoll a d20.\n\n## Advantage\nRoll twice.",
        source="sample.md",
    )

    assert [chunk.heading for chunk in chunks] == [
        "Ability Checks",
        "Advantage",
    ]
    assert chunks[0].text == "Roll a d20."


def test_build_write_read_and_query_index(tmp_path: Path):
    source_path = tmp_path / "rules.md"
    source_path.write_text(
        "# Grappling\nUse a Strength check against a resisting creature.\n"
        "\n# Resting\nA long rest restores resources.\n",
        encoding="utf-8",
    )
    index_path = tmp_path / "rules.jsonl"

    chunks = build_index([source_path])
    write_index(chunks, index_path)
    loaded_chunks = read_index(index_path)
    results = search_index(loaded_chunks, "strength creature", limit=1)

    assert index_path.exists()
    assert len(loaded_chunks) == 2
    assert results[0].chunk.heading == "Grappling"
    assert results[0].score > 0


def test_query_command_rejects_missing_index(tmp_path: Path):
    with pytest.raises(SystemExit) as raised_error:
        main(
            [
                "query",
                "--index",
                str(tmp_path / "missing.jsonl"),
                "--query",
                "grapple",
            ]
        )

    assert raised_error.value.code == 2


def test_search_setup_index_uses_manifest_sqlite_path(tmp_path: Path):
    source_path = tmp_path / "rules.md"
    source_path.write_text(
        "# Ability Checks\nRoll a d20 and add a modifier.\n",
        encoding="utf-8",
    )
    chunks = build_index([source_path])
    sqlite_index_path = tmp_path / "rules.sqlite"
    write_sqlite_index(chunks, sqlite_index_path)
    manifest_path = tmp_path / "questforge-setup.json"
    manifest_path.write_text(
        json.dumps(
            {
                "language": "en",
                "sqlite_index_path": str(sqlite_index_path),
                "jsonl_index_path": None,
                "resources_index_path": None,
            }
        ),
        encoding="utf-8",
    )

    setup_index, results = search_setup_index(
        manifest_path,
        "modifier",
        limit=1,
    )

    assert setup_index.language == "en"
    assert results[0].chunk.heading == "Ability Checks"
