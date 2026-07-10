"""Analyze Questforge session logs and append structured play events."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Iterable

ROLL_PATTERN = re.compile(
    r"1d20\s*(?P<modifier>[+-]\s*\d+)?"
    r"(?P<advantage>\s+con ventaja|\s+con desventaja|"
    r"\s+with advantage|\s+with disadvantage)?\s*=\s*(?P<result>-?\d+)",
    re.IGNORECASE,
)
DC_PATTERN = re.compile(r"\b(?:CD|DC)\s*(\d{1,2})", re.IGNORECASE)


@dataclass(frozen=True)
class CheckRecord:
    session: int
    scene: int
    dc: int
    result: int | None = None
    modifier: str = ""
    advantage_state: str = "normal"
    source: str = "markdown"
    outcome: str = ""


@dataclass(frozen=True)
class AnalyticsWarning:
    code: str
    message: str


@dataclass(frozen=True)
class SessionAnalytics:
    session_log: str
    scenes: int
    checks: int
    paired_checks: int
    dc_distribution: dict[int, int]
    min_dc: int | None
    max_dc: int | None
    mean_dc: float | None
    median_dc: float | None
    successes: int
    failures: int
    exact_successes: int
    advantage_count: int
    disadvantage_count: int
    modifier_distribution: dict[str, int]
    visual_count: int = 0
    generated_visual_count: int = 0
    pending_visual_count: int = 0
    visual_kind_distribution: dict[str, int] = field(default_factory=dict)
    visual_status_distribution: dict[str, int] = field(default_factory=dict)
    analytics_event_count: int = 0
    event_type_distribution: dict[str, int] = field(default_factory=dict)
    warnings: list[AnalyticsWarning] = field(default_factory=list)


def analyze_session(
    session_log: Path,
    visual_index: Path | None = None,
    events_path: Path | None = None,
) -> SessionAnalytics:
    text = session_log.read_text(encoding="utf-8")
    scene_texts = extract_scene_blocks(text)
    markdown_checks = []
    for scene_number, scene_text in scene_texts:
        markdown_checks.extend(parse_scene_checks(scene_number, scene_text))

    visual_rows = (
        read_visual_rows(visual_index, infer_session_number(session_log))
        if visual_index
        else []
    )
    events = read_events(events_path) if events_path else []
    event_checks = parse_event_checks(events)
    checks = event_checks or markdown_checks
    event_scene_numbers = {
        int(event["scene"])
        for event in events
        if isinstance(event.get("scene"), int) and int(event["scene"]) > 0
    }
    scene_count = max(
        len(scene_texts),
        max(event_scene_numbers, default=0),
    )
    warnings = build_warnings(checks, visual_rows, events)
    paired = [check for check in checks if check.result is not None]
    dcs = [check.dc for check in checks]
    generated_visual_statuses = {"asset-saved", "canon", "variant"}
    generated_visual_count = sum(
        1 for row in visual_rows if row["status"] in generated_visual_statuses
    )
    return SessionAnalytics(
        session_log=str(session_log),
        scenes=scene_count,
        checks=len(checks),
        paired_checks=len(paired),
        dc_distribution=dict(sorted(Counter(dcs).items())),
        min_dc=min(dcs) if dcs else None,
        max_dc=max(dcs) if dcs else None,
        mean_dc=round(sum(dcs) / len(dcs), 2) if dcs else None,
        median_dc=median(dcs) if dcs else None,
        successes=sum(1 for check in paired if check_succeeded(check)),
        failures=sum(1 for check in paired if check_failed(check)),
        exact_successes=sum(
            1
            for check in paired
            if check.result is not None and check.result == check.dc
        ),
        advantage_count=sum(
            1 for check in paired if check.advantage_state == "advantage"
        ),
        disadvantage_count=sum(
            1 for check in paired if check.advantage_state == "disadvantage"
        ),
        modifier_distribution=dict(
            sorted(Counter(check.modifier or "+0" for check in paired).items())
        ),
        visual_count=len(visual_rows),
        generated_visual_count=generated_visual_count,
        pending_visual_count=len(visual_rows) - generated_visual_count,
        visual_kind_distribution=dict(
            sorted(Counter(row["kind"] for row in visual_rows).items())
        ),
        visual_status_distribution=dict(
            sorted(Counter(row["status"] for row in visual_rows).items())
        ),
        analytics_event_count=len(events),
        event_type_distribution=dict(
            sorted(
                Counter(
                    event.get("event_type", "") for event in events
                ).items()
            )
        ),
        warnings=warnings,
    )


def extract_scene_blocks(text: str) -> list[tuple[int, str]]:
    matches = list(re.finditer(r"^### Scene\s+(\d+)\b", text, re.MULTILINE))
    scene_blocks = []
    for index, match in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )
        scene_blocks.append((int(match.group(1)), text[match.start() : end]))
    return scene_blocks


def parse_scene_checks(
    scene_number: int, scene_text: str
) -> list[CheckRecord]:
    session_number = infer_session_from_text(scene_text)
    risk_text = " ".join(extract_label_blocks(scene_text, "Risk read"))
    roll_text = " ".join(extract_label_blocks(scene_text, "Roll"))
    combined_for_dc = risk_text or roll_text
    dcs = [
        int(match.group(1)) for match in DC_PATTERN.finditer(combined_for_dc)
    ]
    rolls = [
        parse_roll_match(match) for match in ROLL_PATTERN.finditer(roll_text)
    ]
    return [
        CheckRecord(
            session=session_number,
            scene=scene_number,
            dc=dc,
            result=rolls[index]["result"] if index < len(rolls) else None,
            modifier=rolls[index]["modifier"] if index < len(rolls) else "",
            advantage_state=(
                rolls[index]["advantage_state"]
                if index < len(rolls)
                else "normal"
            ),
        )
        for index, dc in enumerate(dcs)
    ]


def parse_event_checks(events: list[dict[str, object]]) -> list[CheckRecord]:
    checks = []
    for event in events:
        if event.get("event_type") != "check":
            continue
        dc = event.get("dc")
        if not isinstance(dc, int):
            continue
        result = event.get("roll_total")
        checks.append(
            CheckRecord(
                session=integer_or_zero(event.get("session")),
                scene=integer_or_zero(event.get("scene")),
                dc=dc,
                result=result if isinstance(result, int) else None,
                modifier=normalize_modifier(event.get("modifier")),
                advantage_state=normalize_advantage_state(
                    event.get("advantage_state")
                ),
                source="event",
                outcome=str(event.get("outcome", "")).casefold(),
            )
        )
    return checks


def integer_or_zero(value: object) -> int:
    return value if isinstance(value, int) else 0


def normalize_modifier(value: object) -> str:
    text = str(value or "+0").replace(" ", "")
    if text.startswith(("+", "-")):
        return text
    return f"+{text}"


def normalize_advantage_state(value: object) -> str:
    normalized = str(value or "normal").casefold()
    if normalized in {"advantage", "disadvantage"}:
        return normalized
    return "normal"


def check_succeeded(check: CheckRecord) -> bool:
    if check.outcome == "success":
        return True
    if check.outcome == "failure":
        return False
    return check.result is not None and check.result >= check.dc


def check_failed(check: CheckRecord) -> bool:
    if check.outcome == "failure":
        return True
    if check.outcome == "success":
        return False
    return check.result is not None and check.result < check.dc


def extract_label_blocks(text: str, label: str) -> list[str]:
    lines = text.splitlines()
    blocks = []
    current: list[str] = []
    active = False
    prefix = f"- {label}:"
    for line in lines:
        if line.startswith(prefix):
            if current:
                blocks.append(" ".join(current))
            current = [line]
            active = True
            continue
        if active and line.startswith("  "):
            current.append(line)
            continue
        if active:
            blocks.append(" ".join(current))
            current = []
            active = False
    if current:
        blocks.append(" ".join(current))
    return blocks


def parse_roll_match(match: re.Match[str]) -> dict[str, object]:
    advantage_text = (match.group("advantage") or "").casefold()
    advantage_state = "normal"
    if "desventaja" in advantage_text or "disadvantage" in advantage_text:
        advantage_state = "disadvantage"
    elif "ventaja" in advantage_text or "advantage" in advantage_text:
        advantage_state = "advantage"
    return {
        "result": int(match.group("result")),
        "modifier": (match.group("modifier") or "+0").replace(" ", ""),
        "advantage_state": advantage_state,
    }


def infer_session_from_text(scene_text: str) -> int:
    match = re.search(r"^- Session:\s*(\d+)", scene_text, re.MULTILINE)
    return int(match.group(1)) if match else 0


def infer_session_number(session_log: Path) -> int | None:
    match = re.search(r"session-(\d{3})\.md$", session_log.name)
    return int(match.group(1)) if match else None


def read_visual_rows(
    visual_index: Path | None, session_number: int | None
) -> list[dict[str, str]]:
    if not visual_index or not visual_index.exists():
        return []
    rows = []
    for line in visual_index.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 7 or cells[0] == "Kind":
            continue
        if (
            session_number is not None
            and optional_int(cells[2]) != session_number
        ):
            continue
        rows.append(
            {
                "kind": cells[0],
                "label": cells[1],
                "session": cells[2],
                "scene": cells[3],
                "status": cells[5],
                "asset": cells[6],
            }
        )
    return rows


def read_events(events_path: Path | None) -> list[dict[str, object]]:
    if not events_path or not events_path.exists():
        return []
    events = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def build_warnings(
    checks: list[CheckRecord],
    visual_rows: list[dict[str, str]],
    events: list[dict[str, object]],
) -> list[AnalyticsWarning]:
    warnings = []
    dcs = [check.dc for check in checks]
    if len(dcs) >= 5 and len(set(dcs)) == 1:
        warnings.append(
            AnalyticsWarning(
                code="dc_single_value",
                message=f"All {len(dcs)} recorded checks use DC {dcs[0]}.",
            )
        )
    if len(dcs) >= 5:
        dominant_dc, dominant_count = Counter(dcs).most_common(1)[0]
        if dominant_count / len(dcs) >= 0.7 and len(set(dcs)) > 1:
            warnings.append(
                AnalyticsWarning(
                    code="dc_value_dominant",
                    message=(
                        f"DC {dominant_dc} appears in {dominant_count} of "
                        f"{len(dcs)} recorded checks."
                    ),
                )
            )
    if dcs and min(dcs) >= 12 and max(dcs) <= 15:
        warnings.append(
            AnalyticsWarning(
                code="dc_range_narrow",
                message="All recorded DCs are between 12 and 15.",
            )
        )
    if dcs:
        common_count = sum(1 for dc in dcs if dc in {13, 14})
        if common_count / len(dcs) >= 0.7:
            warnings.append(
                AnalyticsWarning(
                    code="dc_13_14_dominant",
                    message="DC 13 and 14 dominate the check distribution.",
                )
            )
    paired = [check for check in checks if check.result is not None]
    if paired and any(
        check.advantage_state == "advantage" for check in paired
    ):
        if not any(
            check.advantage_state == "disadvantage" for check in paired
        ):
            warnings.append(
                AnalyticsWarning(
                    code="no_disadvantage_recorded",
                    message="Advantage appears, but no disadvantage is recorded.",
                )
            )
    if visual_rows and len({row["kind"] for row in visual_rows}) <= 2:
        warnings.append(
            AnalyticsWarning(
                code="visual_kind_low_variety",
                message="Visuals use only one or two kinds in this session.",
            )
        )
    generated_visual_statuses = {"asset-saved", "canon", "variant"}
    if visual_rows and not any(
        row["status"] in generated_visual_statuses for row in visual_rows
    ):
        warnings.append(
            AnalyticsWarning(
                code="visuals_not_generated",
                message=(
                    "Visual prompts were saved, but no generated visual asset "
                    "was registered."
                ),
            )
        )
    if (
        not visual_rows
        and events
        and any(
            event.get("event_type") in {"scene_start", "session_start"}
            for event in events
        )
    ):
        warnings.append(
            AnalyticsWarning(
                code="visuals_missing",
                message="The played session contains no recorded visual beat.",
            )
        )
    if not events:
        warnings.append(
            AnalyticsWarning(
                code="structured_events_missing",
                message="No structured analytics JSONL events were found.",
            )
        )
    return warnings


def optional_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def append_event(campaign_root: Path, payload: dict[str, object]) -> Path:
    events_path = campaign_root / "analytics" / "session-events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **{
            key: value
            for key, value in payload.items()
            if value not in ("", None)
        },
    }
    with events_path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(
            json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
        )
    return events_path


def format_markdown(result: SessionAnalytics) -> str:
    lines = [
        "# Questforge Session Analytics",
        "",
        f"- Session log: {result.session_log}",
        f"- Scenes: {result.scenes}",
        f"- Checks: {result.checks} ({result.paired_checks} with results)",
        (
            f"- DC range: {result.min_dc}-{result.max_dc}, "
            f"mean {result.mean_dc}, median {result.median_dc}"
        ),
        f"- Outcomes: {result.successes} successes, {result.failures} failures, {result.exact_successes} exact",
        f"- Advantage/disadvantage: {result.advantage_count}/{result.disadvantage_count}",
        f"- Visuals: {result.visual_count}",
        (
            f"- Generated/pending visuals: "
            f"{result.generated_visual_count}/{result.pending_visual_count}"
        ),
        f"- Structured events: {result.analytics_event_count}",
        "",
        "## DC Distribution",
        "",
    ]
    if result.dc_distribution:
        for dc, count in result.dc_distribution.items():
            lines.append(f"- DC {dc}: {count}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Modifiers", ""])
    if result.modifier_distribution:
        for modifier, count in result.modifier_distribution.items():
            lines.append(f"- {modifier}: {count}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Visual Kinds", ""])
    if result.visual_kind_distribution:
        for kind, count in result.visual_kind_distribution.items():
            lines.append(f"- {kind}: {count}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Warnings", ""])
    if result.warnings:
        for warning in result.warnings:
            lines.append(f"- `{warning.code}`: {warning.message}")
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze Questforge session logs and event streams."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--session-log", required=True, type=Path)
    analyze_parser.add_argument("--visual-index", type=Path)
    analyze_parser.add_argument("--events", type=Path)
    analyze_parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )

    event_parser = subparsers.add_parser("log-event")
    event_parser.add_argument("--campaign-root", required=True, type=Path)
    event_parser.add_argument("--event-type", required=True)
    event_parser.add_argument("--session", type=int)
    event_parser.add_argument("--scene", type=int)
    event_parser.add_argument("--summary", default="")
    event_parser.add_argument("--challenge-type", default="")
    event_parser.add_argument("--ability", default="")
    event_parser.add_argument("--skill", default="")
    event_parser.add_argument("--dc", type=int)
    event_parser.add_argument("--modifier", default="")
    event_parser.add_argument("--roll-total", type=int)
    event_parser.add_argument("--advantage-state", default="")
    event_parser.add_argument("--outcome", default="")
    event_parser.add_argument("--failure-forward", default="")
    event_parser.add_argument("--image-kind", default="")
    event_parser.add_argument("--image-label", default="")
    event_parser.add_argument("--xp", type=int)
    event_parser.add_argument("--loot", default="")
    event_parser.add_argument("--tag", action="append", default=[])
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    parsed_arguments = build_parser().parse_args(arguments)
    if parsed_arguments.command == "analyze":
        result = analyze_session(
            session_log=parsed_arguments.session_log,
            visual_index=parsed_arguments.visual_index,
            events_path=parsed_arguments.events,
        )
        if parsed_arguments.format == "json":
            print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        else:
            print(format_markdown(result), end="")
        return 0

    payload = {
        "event_type": parsed_arguments.event_type,
        "session": parsed_arguments.session,
        "scene": parsed_arguments.scene,
        "summary": parsed_arguments.summary,
        "challenge_type": parsed_arguments.challenge_type,
        "ability": parsed_arguments.ability,
        "skill": parsed_arguments.skill,
        "dc": parsed_arguments.dc,
        "modifier": parsed_arguments.modifier,
        "roll_total": parsed_arguments.roll_total,
        "advantage_state": parsed_arguments.advantage_state,
        "outcome": parsed_arguments.outcome,
        "failure_forward": parsed_arguments.failure_forward,
        "image_kind": parsed_arguments.image_kind,
        "image_label": parsed_arguments.image_label,
        "xp": parsed_arguments.xp,
        "loot": parsed_arguments.loot,
        "tags": parsed_arguments.tag,
    }
    events_path = append_event(parsed_arguments.campaign_root, payload)
    print(f"Logged event: {events_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
