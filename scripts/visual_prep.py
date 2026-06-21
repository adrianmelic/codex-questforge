"""Pre-session visual preparation for Codex Questforge."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    from .campaign_memory import (
        get_campaign_paths,
        save_visual_prompt,
        slugify,
    )
except ImportError:  # pragma: no cover - direct script execution path
    from campaign_memory import get_campaign_paths, save_visual_prompt, slugify


@dataclass(frozen=True)
class VisualPrepSubject:
    """One subject to prepare before play."""

    kind: str
    label: str
    anchor: str
    purpose: str
    sheet: str
    action: str = ""
    avoid: str = ""


@dataclass(frozen=True)
class VisualPrepResult:
    """Artifacts created by visual prep."""

    campaign_root: str
    plan_path: str
    prompt_paths: list[str]
    subject_count: int


DEFAULT_STYLE = (
    "immersive fantasy realism, coherent tabletop campaign reference art, "
    "grounded materials, clear silhouettes, no unwanted film grain, "
    "no readable text"
)


def prepare_visuals(
    campaign_root: Path,
    spec_path: Path,
) -> VisualPrepResult:
    """Create pre-session visual prep prompts from a JSON spec."""

    paths = get_campaign_paths(campaign_root)
    if not paths.root.exists():
        raise FileNotFoundError(f"Missing campaign root: {campaign_root}")

    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    title = str(payload.get("title", "Questforge Visual Prep"))
    style = str(payload.get("style", DEFAULT_STYLE))
    session_number = int(payload.get("session", 0))
    subjects = [
        parse_subject(subject_payload)
        for subject_payload in payload.get("subjects", [])
    ]
    if not subjects:
        raise ValueError("Visual prep spec must include at least one subject.")

    prompt_paths: list[Path] = []
    for scene_number, subject in enumerate(subjects, start=1):
        prompt = build_reference_prompt(subject, style)
        prompt_paths.append(
            save_visual_prompt(
                paths.root,
                session_number=session_number,
                scene_number=scene_number,
                kind=subject.kind,
                label=subject.label,
                prompt=prompt,
            )
        )

    plan_path = paths.root / "visual-prep-plan.md"
    plan_path.write_text(
        build_plan(title, style, subjects, prompt_paths, paths.root),
        encoding="utf-8",
        newline="\n",
    )
    return VisualPrepResult(
        campaign_root=str(paths.root),
        plan_path=str(plan_path),
        prompt_paths=[str(path) for path in prompt_paths],
        subject_count=len(subjects),
    )


def parse_subject(payload: object) -> VisualPrepSubject:
    if not isinstance(payload, dict):
        raise ValueError("Each visual prep subject must be an object.")
    return VisualPrepSubject(
        kind=required_text(payload, "kind"),
        label=required_text(payload, "label"),
        anchor=required_text(payload, "anchor"),
        purpose=required_text(payload, "purpose"),
        sheet=required_text(payload, "sheet"),
        action=str(payload.get("action", "")),
        avoid=str(payload.get("avoid", "")),
    )


def required_text(payload: dict[str, object], key: str) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"Visual prep subject is missing required key: {key}")
    return value


def build_reference_prompt(subject: VisualPrepSubject, style: str) -> str:
    action_line = (
        f"Typical action: {subject.action}. " if subject.action else ""
    )
    avoid_line = (
        f"Additional avoid: {subject.avoid}. " if subject.avoid else ""
    )
    return (
        "Original 5E-compatible fantasy reference asset, unofficial and not "
        "using official D&D settings, logos, product art, named copyrighted "
        f"characters, or commercial adventure identity. Subject: {subject.anchor}. "
        f"Purpose: {subject.purpose}. Reference sheet: {subject.sheet}. "
        f"{action_line}Style: {style}. Constraints: no readable text, no "
        f"watermark, no official logos, no copied product art. {avoid_line}"
        "Make this useful as a canon visual anchor for later scene frames."
    )


def build_plan(
    title: str,
    style: str,
    subjects: list[VisualPrepSubject],
    prompt_paths: list[Path],
    campaign_root: Path,
) -> str:
    rows = []
    for subject, prompt_path in zip(subjects, prompt_paths, strict=True):
        rows.append(
            (
                f"| {subject.kind} | {subject.label} | {subject.purpose} | "
                f"{prompt_path.relative_to(campaign_root).as_posix()} | "
                "prompt-saved |"
            )
        )
    row_text = "\n".join(rows)
    return f"""# {title}

## Style

{style}

## Prep Assets

| Kind | Label | Purpose | Prompt Path | Status |
| --- | --- | --- | --- | --- |
{row_text}

## Canonization Steps

1. Generate native images from the saved prompts.
2. Register selected PNGs with `campaign_memory.py register-visual-asset`.
3. Mark accepted reference sheets with `set-visual-status --status canon`.
4. Mark useful non-canon alternatives as `variant`.
5. Mark continuity-breaking images as `rejected`.
6. Use canon anchors explicitly in later scene-frame prompts.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare Questforge visual reference prompts before play."
    )
    parser.add_argument("--campaign-root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = prepare_visuals(
        campaign_root=parsed_arguments.campaign_root,
        spec_path=parsed_arguments.spec,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
