"""Build and query a small local text index for SRD-style rules notes."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

HEADING_PATTERN = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
TERM_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


@dataclass(frozen=True)
class RuleChunk:
    """A searchable chunk of rules text."""

    source: str
    heading: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    """A scored rules search result."""

    score: int
    chunk: RuleChunk


@dataclass(frozen=True)
class SetupIndex:
    """Resolved index paths from questforge-setup.json."""

    language: str
    sqlite_index_path: Path | None
    jsonl_index_path: Path | None
    resources_index_path: Path | None


def normalize_terms(text: str) -> set[str]:
    return {term.lower() for term in TERM_PATTERN.findall(text)}


def split_markdown_sections(text: str, source: str) -> list[RuleChunk]:
    """Split Markdown-ish text into chunks by heading."""

    chunks: list[RuleChunk] = []
    current_heading = "Untitled"
    current_lines: list[str] = []

    for line in text.splitlines():
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            append_chunk(chunks, source, current_heading, current_lines)
            current_heading = heading_match.group("title").strip()
            current_lines = []
            continue
        current_lines.append(line)

    append_chunk(chunks, source, current_heading, current_lines)
    return chunks


def append_chunk(
    chunks: list[RuleChunk],
    source: str,
    heading: str,
    lines: list[str],
) -> None:
    text = "\n".join(lines).strip()
    if text:
        chunks.append(RuleChunk(source=source, heading=heading, text=text))


def build_index(source_paths: Iterable[Path]) -> list[RuleChunk]:
    chunks: list[RuleChunk] = []
    for source_path in source_paths:
        text = source_path.read_text(encoding="utf-8-sig")
        chunks.extend(split_markdown_sections(text, source_path.name))
    return chunks


def write_index(chunks: Iterable[RuleChunk], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as output_file:
        for chunk in chunks:
            output_file.write(json.dumps(asdict(chunk), ensure_ascii=False))
            output_file.write("\n")


def write_sqlite_index(chunks: Iterable[RuleChunk], output_path: Path) -> None:
    """Write chunks to a small SQLite database with optional FTS5 search."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(output_path) as connection:
        connection.execute("DROP TABLE IF EXISTS rules_chunks")
        connection.execute("DROP TABLE IF EXISTS questforge_metadata")
        connection.execute("DROP TABLE IF EXISTS rules_fts")
        connection.execute("""
            CREATE TABLE rules_chunks (
                id INTEGER PRIMARY KEY,
                source TEXT NOT NULL,
                heading TEXT NOT NULL,
                text TEXT NOT NULL
            )
            """)
        connection.execute("""
            CREATE TABLE questforge_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)
        chunk_rows = [
            (chunk.source, chunk.heading, chunk.text) for chunk in chunks
        ]
        connection.executemany(
            """
            INSERT INTO rules_chunks (source, heading, text)
            VALUES (?, ?, ?)
            """,
            chunk_rows,
        )
        fts_enabled = create_fts_index(connection, chunk_rows)
        connection.executemany(
            """
            INSERT INTO questforge_metadata (key, value)
            VALUES (?, ?)
            """,
            [
                ("schema", "questforge-rules-index-v1"),
                ("fts_enabled", "yes" if fts_enabled else "no"),
            ],
        )


def create_fts_index(
    connection: sqlite3.Connection,
    chunk_rows: list[tuple[str, str, str]],
) -> bool:
    """Create an FTS5 table when the local SQLite build supports it."""

    try:
        connection.execute("""
            CREATE VIRTUAL TABLE rules_fts
            USING fts5(source UNINDEXED, heading, text)
            """)
    except sqlite3.OperationalError:
        return False

    connection.executemany(
        """
        INSERT INTO rules_fts (source, heading, text)
        VALUES (?, ?, ?)
        """,
        chunk_rows,
    )
    return True


def read_index(index_path: Path) -> list[RuleChunk]:
    chunks: list[RuleChunk] = []
    with index_path.open("r", encoding="utf-8") as index_file:
        for line in index_file:
            if not line.strip():
                continue
            payload = json.loads(line)
            chunks.append(
                RuleChunk(
                    source=payload["source"],
                    heading=payload["heading"],
                    text=payload["text"],
                )
            )
    return chunks


def sqlite_has_fts(connection: sqlite3.Connection) -> bool:
    cursor = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'rules_fts'
        """)
    return cursor.fetchone() is not None


def read_sqlite_index(index_path: Path) -> list[RuleChunk]:
    with sqlite3.connect(index_path) as connection:
        cursor = connection.execute("""
            SELECT source, heading, text
            FROM rules_chunks
            ORDER BY id
            """)
        return [
            RuleChunk(source=row[0], heading=row[1], text=row[2])
            for row in cursor.fetchall()
        ]


def search_index(
    chunks: Iterable[RuleChunk],
    query: str,
    limit: int = 5,
) -> list[SearchResult]:
    query_terms = normalize_terms(query)
    if not query_terms:
        return []

    results: list[SearchResult] = []
    for chunk in chunks:
        heading_terms = normalize_terms(chunk.heading)
        text_terms = normalize_terms(chunk.text)
        score = len(query_terms & text_terms) + (
            2 * len(query_terms & heading_terms)
        )
        if score:
            results.append(SearchResult(score=score, chunk=chunk))

    return sorted(
        results,
        key=lambda result: (
            -result.score,
            result.chunk.source,
            result.chunk.heading,
        ),
    )[:limit]


def build_fts_query(query: str) -> str:
    terms = sorted(normalize_terms(query))
    return " OR ".join(terms)


def search_sqlite_index(
    index_path: Path,
    query: str,
    limit: int = 5,
) -> list[SearchResult]:
    fts_query = build_fts_query(query)
    if not fts_query:
        return []

    with sqlite3.connect(index_path) as connection:
        if sqlite_has_fts(connection):
            cursor = connection.execute(
                """
                SELECT source, heading, text, rank
                FROM rules_fts
                WHERE rules_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, limit),
            )
            return [
                SearchResult(
                    score=max(1, int(abs(row[3]) * 1_000_000)),
                    chunk=RuleChunk(
                        source=row[0],
                        heading=row[1],
                        text=row[2],
                    ),
                )
                for row in cursor.fetchall()
            ]

    return search_index(read_sqlite_index(index_path), query, limit)


def read_setup_index(manifest_path: Path) -> SetupIndex:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return SetupIndex(
        language=str(payload.get("language", "")),
        sqlite_index_path=optional_path(payload.get("sqlite_index_path")),
        jsonl_index_path=optional_path(payload.get("jsonl_index_path")),
        resources_index_path=optional_path(
            payload.get("resources_index_path")
        ),
    )


def optional_path(value: object) -> Path | None:
    if not value:
        return None
    return Path(str(value))


def search_setup_index(
    manifest_path: Path,
    query: str,
    limit: int = 5,
) -> tuple[SetupIndex, list[SearchResult]]:
    setup_index = read_setup_index(manifest_path)
    if (
        setup_index.sqlite_index_path
        and setup_index.sqlite_index_path.exists()
    ):
        return setup_index, search_sqlite_index(
            setup_index.sqlite_index_path,
            query,
            limit,
        )
    if setup_index.jsonl_index_path and setup_index.jsonl_index_path.exists():
        return setup_index, search_index(
            read_index(setup_index.jsonl_index_path),
            query,
            limit,
        )
    raise FileNotFoundError(
        "No usable rules index found in setup manifest. "
        "Rerun questforge_setup.py."
    )


def result_to_dict(result: SearchResult) -> dict[str, object]:
    return {
        "score": result.score,
        "source": result.chunk.source,
        "heading": result.chunk.heading,
        "text": result.chunk.text,
    }


def print_results(
    results: Iterable[SearchResult],
    output_format: str = "text",
    max_chars: int = 600,
) -> None:
    results = list(results)
    if output_format == "json":
        print(
            json.dumps(
                [result_to_dict(result) for result in results],
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    for result in results:
        print(f"Reference: {result.chunk.source} :: {result.chunk.heading}")
        print(f"Score: {result.score}")
        print(result.chunk.text[:max_chars].strip())
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or query a rules index."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build a JSONL index.")
    build_parser.add_argument(
        "--source",
        action="append",
        required=True,
        type=Path,
        help="UTF-8 Markdown or text source. Repeat for multiple files.",
    )
    build_parser.add_argument("--output", required=True, type=Path)
    build_parser.add_argument(
        "--sqlite-output",
        type=Path,
        help="Optional SQLite index output with FTS5 when available.",
    )

    query_parser = subparsers.add_parser("query", help="Query a JSONL index.")
    query_parser.add_argument("--index", required=True, type=Path)
    query_parser.add_argument("--query", required=True)
    query_parser.add_argument("--limit", type=int, default=5)
    query_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    query_parser.add_argument("--max-chars", type=int, default=600)

    sqlite_query_parser = subparsers.add_parser(
        "query-sqlite",
        help="Query a SQLite rules index.",
    )
    sqlite_query_parser.add_argument("--index", required=True, type=Path)
    sqlite_query_parser.add_argument("--query", required=True)
    sqlite_query_parser.add_argument("--limit", type=int, default=5)
    sqlite_query_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    sqlite_query_parser.add_argument("--max-chars", type=int, default=600)

    setup_query_parser = subparsers.add_parser(
        "query-setup",
        help="Query rules through questforge-setup.json.",
    )
    setup_query_parser.add_argument(
        "--manifest",
        default=".questforge/questforge-setup.json",
        type=Path,
    )
    setup_query_parser.add_argument("--query", required=True)
    setup_query_parser.add_argument("--limit", type=int, default=5)
    setup_query_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    setup_query_parser.add_argument("--max-chars", type=int, default=600)

    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    parsed_arguments = parser.parse_args(arguments)

    if parsed_arguments.command == "build":
        missing_sources = [
            source_path
            for source_path in parsed_arguments.source
            if not source_path.exists()
        ]
        if missing_sources:
            missing_text = ", ".join(str(path) for path in missing_sources)
            parser.error(f"Missing source file(s): {missing_text}")
        chunks = build_index(parsed_arguments.source)
        write_index(chunks, parsed_arguments.output)
        if parsed_arguments.sqlite_output:
            write_sqlite_index(chunks, parsed_arguments.sqlite_output)
        print(f"Wrote {len(chunks)} chunks to {parsed_arguments.output}")
        if parsed_arguments.sqlite_output:
            print(f"Wrote SQLite index to {parsed_arguments.sqlite_output}")
        return 0

    if parsed_arguments.command == "query-setup":
        if not parsed_arguments.manifest.exists():
            parser.error(
                f"Missing setup manifest: {parsed_arguments.manifest}"
            )
        try:
            _, results = search_setup_index(
                parsed_arguments.manifest,
                parsed_arguments.query,
                parsed_arguments.limit,
            )
        except FileNotFoundError as error:
            parser.error(str(error))
        print_results(
            results,
            parsed_arguments.format,
            parsed_arguments.max_chars,
        )
        return 0

    if not parsed_arguments.index.exists():
        parser.error(f"Missing index file: {parsed_arguments.index}")

    if parsed_arguments.command == "query-sqlite":
        results = search_sqlite_index(
            parsed_arguments.index,
            parsed_arguments.query,
            parsed_arguments.limit,
        )
    else:
        chunks = read_index(parsed_arguments.index)
        results = search_index(
            chunks,
            parsed_arguments.query,
            parsed_arguments.limit,
        )

    print_results(results, parsed_arguments.format, parsed_arguments.max_chars)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
