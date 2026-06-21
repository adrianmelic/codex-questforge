"""Build live scene-frame prompts from reusable Questforge visual anchors."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    from .campaign_memory import (
        VisualIndexEntry,
        get_campaign_paths,
        list_visual_assets,
        save_visual_prompt,
        slugify,
    )
except ImportError:  # pragma: no cover - direct script execution path
    from campaign_memory import (
        VisualIndexEntry,
        get_campaign_paths,
        list_visual_assets,
        save_visual_prompt,
        slugify,
    )


DEFAULT_ANCHOR_STATUS = ["canon"]
DEFAULT_STYLE = (
    "immersive fantasy realism, grounded materials, clear silhouettes, "
    "table-readable staging, dramatic plausible light, no unwanted film grain, "
    "no readable text"
)


@dataclass(frozen=True)
class AnchorSummary:
    """A compact canon anchor summary for scene prompt construction."""

    kind: str
    label: str
    status: str
    asset_path: str
    prompt_path: str
    prompt_excerpt: str


@dataclass(frozen=True)
class SceneFramePromptResult:
    """Artifacts created for a live scene frame."""

    campaign_root: str
    prompt_path: str
    anchor_count: int
    anchors: list[AnchorSummary]


def create_scene_frame_prompt(
    campaign_root: Path,
    session_number: int,
    scene_number: int,
    label: str,
    action: str,
    purpose: str = "",
    context: str = "",
    roll_summary: str = "",
    outcome: str = "",
    style: str = DEFAULT_STYLE,
    composition: str = "",
    anchor_statuses: list[str] | None = None,
    anchor_kinds: list[str] | None = None,
    anchor_labels: list[str] | None = None,
    require_asset: bool = False,
) -> SceneFramePromptResult:
    """Save a scene-frame prompt that explicitly reuses visual anchors."""

    paths = get_campaign_paths(campaign_root)
    if not paths.root.exists():
        raise FileNotFoundError(f"Missing campaign root: {campaign_root}")
    if not action.strip():
        raise ValueError("Scene action cannot be empty.")

    anchors = select_anchors(
        paths.root,
        statuses=anchor_statuses or DEFAULT_ANCHOR_STATUS,
        kinds=anchor_kinds,
        labels=anchor_labels,
        require_asset=require_asset,
    )
    if not anchors:
        raise ValueError(
            "No reusable visual anchors matched. Mark references as canon or "
            "pass a different --anchor-status."
        )

    summaries = [summarize_anchor(paths.root, anchor) for anchor in anchors]
    prompt = build_scene_prompt(
        action=action,
        purpose=purpose,
        context=context,
        roll_summary=roll_summary,
        outcome=outcome,
        style=style,
        composition=composition,
        anchors=summaries,
        visual_ledger=read_visual_ledger_excerpt(paths.root),
    )
    prompt_path = save_visual_prompt(
        paths.root,
        session_number=session_number,
        scene_number=scene_number,
        kind="scene",
        label=label,
        prompt=prompt,
    )
    return SceneFramePromptResult(
        campaign_root=str(paths.root),
        prompt_path=str(prompt_path),
        anchor_count=len(summaries),
        anchors=summaries,
    )


def select_anchors(
    campaign_root: Path,
    statuses: list[str],
    kinds: list[str] | None = None,
    labels: list[str] | None = None,
    require_asset: bool = False,
) -> list[VisualIndexEntry]:
    """Select reusable anchors, preserving visual-index order."""

    entries = list_visual_assets(
        campaign_root,
        statuses=statuses,
        kinds=kinds,
        require_asset=require_asset,
    )
    if not labels:
        return entries

    labels_by_slug = {slugify(label): label for label in labels}
    selected = [
        entry for entry in entries if slugify(entry.label) in labels_by_slug
    ]
    found_slugs = {slugify(entry.label) for entry in selected}
    missing_labels = [
        label
        for slug, label in labels_by_slug.items()
        if slug not in found_slugs
    ]
    if missing_labels:
        raise ValueError(
            "Missing requested reusable visual anchors: "
            + ", ".join(missing_labels)
        )
    return selected


def summarize_anchor(
    campaign_root: Path,
    entry: VisualIndexEntry,
) -> AnchorSummary:
    return AnchorSummary(
        kind=entry.kind,
        label=entry.label,
        status=entry.status,
        asset_path=entry.asset_path,
        prompt_path=entry.prompt_path,
        prompt_excerpt=read_prompt_excerpt(campaign_root, entry.prompt_path),
    )


def read_prompt_excerpt(
    campaign_root: Path,
    prompt_path: str,
    max_characters: int = 520,
) -> str:
    path = campaign_root / prompt_path
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    normalized = " ".join(
        line.strip() for line in text.splitlines() if line.strip()
    )
    if len(normalized) <= max_characters:
        return normalized
    return normalized[: max_characters - 1].rsplit(" ", 1)[0] + "..."


def build_scene_prompt(
    action: str,
    anchors: list[AnchorSummary],
    purpose: str = "",
    context: str = "",
    roll_summary: str = "",
    outcome: str = "",
    style: str = DEFAULT_STYLE,
    composition: str = "",
    visual_ledger: str = "",
) -> str:
    anchor_lines = "\n".join(format_anchor(anchor) for anchor in anchors)
    purpose_text = purpose or "show the current player-facing moment clearly"
    context_text = context or "current campaign scene"
    composition_text = (
        composition
        or "foreground decision point, readable character scale, clear threat "
        "or object placement, background kept secondary"
    )
    resolved_lines = build_resolved_table_lines(roll_summary, outcome)
    ledger_text = (
        f"\nActive visual ledger states:\n{visual_ledger}\n"
        if visual_ledger.strip()
        else ""
    )
    return f"""Original 5E-compatible fantasy campaign scene frame, unofficial and not using official D&D settings, logos, product art, named copyrighted characters, or commercial adventure identity.

Purpose: {sentence_text(purpose_text)}
Context: {sentence_text(context_text)}
Action: {sentence_text(action)}
{resolved_lines}
Style: {sentence_text(style)}
Composition: {sentence_text(composition_text)}

Canon anchors to preserve:
{anchor_lines}
{ledger_text}

Continuity constraints: reuse the listed anchors instead of redesigning them; preserve scale, silhouette, palette, visible gear, markings, and landmark relationships. If an anchor has an asset path, use that file as the visual reference when native image generation supports image inputs. Do not reveal unexplored map areas, hidden enemies, or secret mechanisms unless already discovered in play.
Avoid: official logos, official setting identifiers, copied product art, readable text, watermarks, and continuity-breaking redesigns.
Post-generation review: compare the result against the listed anchors before marking the new scene as canon; mark it as variant if useful but drifted, or rejected if it breaks continuity.
"""


def read_visual_ledger_excerpt(
    campaign_root: Path,
    max_characters: int = 700,
) -> str:
    ledger_path = campaign_root / "images" / "visual-ledger.md"
    if not ledger_path.exists():
        return ""
    lines = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line.startswith("|"):
            continue
        if (
            stripped_line.startswith("| ---")
            or "Must Preserve" in stripped_line
        ):
            continue
        if (
            "Current Visual State" in stripped_line
            or "Stable Layout" in stripped_line
        ):
            continue
        if "Format | Use For" in stripped_line:
            continue
        lines.append(stripped_line)
    text = " ".join(lines)
    if len(text) <= max_characters:
        return text
    return text[: max_characters - 1].rsplit(" ", 1)[0] + "..."


def build_resolved_table_lines(roll_summary: str, outcome: str) -> str:
    lines = []
    if roll_summary.strip():
        lines.append(f"Roll: {sentence_text(roll_summary)}")
    if outcome.strip():
        lines.append(f"Resolved outcome: {sentence_text(outcome)}")
    if not lines:
        return ""
    return "\n".join(lines)


def sentence_text(value: str) -> str:
    stripped_value = value.strip()
    if stripped_value.endswith((".", "!", "?")):
        return stripped_value
    return stripped_value + "."


def format_anchor(anchor: AnchorSummary) -> str:
    asset_text = anchor.asset_path or "no selected asset yet"
    excerpt_text = (
        f" Prior prompt summary: {anchor.prompt_excerpt}"
        if anchor.prompt_excerpt
        else ""
    )
    return (
        f"- Preserve {anchor.label} ({anchor.kind}, {anchor.status}); "
        f"asset: {asset_text}; prompt: {anchor.prompt_path}."
        f"{excerpt_text}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Questforge scene-frame prompt from reusable visual "
            "anchors."
        )
    )
    parser.add_argument("--campaign-root", required=True, type=Path)
    parser.add_argument("--session", required=True, type=int)
    parser.add_argument("--scene", required=True, type=int)
    parser.add_argument("--label", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--purpose", default="")
    parser.add_argument("--context", default="")
    parser.add_argument("--roll", dest="roll_summary", default="")
    parser.add_argument("--outcome", default="")
    parser.add_argument("--style", default=DEFAULT_STYLE)
    parser.add_argument("--composition", default="")
    parser.add_argument("--anchor-status", action="append")
    parser.add_argument("--anchor-kind", action="append")
    parser.add_argument("--anchor-label", action="append")
    parser.add_argument("--require-asset", action="store_true")
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = create_scene_frame_prompt(
        campaign_root=parsed_arguments.campaign_root,
        session_number=parsed_arguments.session,
        scene_number=parsed_arguments.scene,
        label=parsed_arguments.label,
        action=parsed_arguments.action,
        purpose=parsed_arguments.purpose,
        context=parsed_arguments.context,
        roll_summary=parsed_arguments.roll_summary,
        outcome=parsed_arguments.outcome,
        style=parsed_arguments.style,
        composition=parsed_arguments.composition,
        anchor_statuses=parsed_arguments.anchor_status,
        anchor_kinds=parsed_arguments.anchor_kind,
        anchor_labels=parsed_arguments.anchor_label,
        require_asset=parsed_arguments.require_asset,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
