"""Plan Questforge visual beats before native image generation."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

try:
    from .comic_panels import classify_visual_format
except ImportError:  # pragma: no cover - direct script execution path
    from comic_panels import classify_visual_format


NO_VISUAL_PATTERNS = [
    "rules question",
    "quick clarification",
    "duda breve",
    "regla",
    "rules",
    "dc",
    "difficulty class",
    "modificador",
    "modifier",
    "advantage",
    "disadvantage",
    "ventaja",
    "desventaja",
]
PANORAMA_PATTERNS = [
    "360",
    "fotoesfera",
    "photosphere",
    "panorama",
    "panoramico",
    "pov",
    "look around",
    "mirar alrededor",
    "ver la sala",
    "ver el cuarto",
    "desde mis ojos",
]
MAP_PATTERNS = [
    "map",
    "mapa",
    "route",
    "ruta",
    "exits",
    "salidas",
    "where are",
    "donde estan",
    "distancia",
    "positions",
    "posiciones",
    "fog of war",
]
INVENTORY_PATTERNS = [
    "inventory",
    "inventario",
    "gear",
    "equipo",
    "mochila",
    "loot",
    "botin",
    "monedas",
]
MERCHANT_PATTERNS = [
    "merchant",
    "comerciante",
    "comprar",
    "vender",
    "tienda",
    "prices",
    "precios",
    "bargain",
    "regatear",
]
REFERENCE_PATTERNS = [
    "reference",
    "referencia",
    "canon",
    "canonical",
    "ficha",
    "sheet",
    "front view",
    "back view",
    "recurring",
    "recurrente",
]


@dataclass(frozen=True)
class VisualBeatPlan:
    """Decision for one possible visual beat."""

    should_generate: bool
    format: str
    kind: str
    panel_count: int
    use_gallery: bool
    present_image_in_chat: bool
    reason: str
    continuity_requirements: list[str]
    next_steps: list[str]


def plan_visual_beat(
    beat: str,
    visual_first: bool = True,
) -> VisualBeatPlan:
    """Choose the visual surface and prompt workflow for a table beat."""

    normalized_beat = " ".join(beat.strip().split())
    if not normalized_beat:
        raise ValueError("Beat summary cannot be empty.")
    text = normalize_text(normalized_beat)

    if is_non_visual_question(text):
        return VisualBeatPlan(
            should_generate=False,
            format="none",
            kind="none",
            panel_count=0,
            use_gallery=False,
            present_image_in_chat=False,
            reason="brief rules or clarification beat",
            continuity_requirements=[],
            next_steps=["Answer in chat without generating a visual."],
        )

    if contains_any(text, PANORAMA_PATTERNS):
        return build_plan(
            format_name="pov_360",
            kind="pov-360",
            panel_count=0,
            reason="the beat asks for first-person spatial inspection",
            visual_first=visual_first,
            extra_continuity=[
                "Use an equirectangular 360 panorama prompt.",
                "Create or update a panorama viewer after generation.",
            ],
        )

    if contains_any(text, MAP_PATTERNS):
        return build_plan(
            format_name="map_or_diagram",
            kind="map",
            panel_count=0,
            reason="the beat needs route, position, or spatial clarity",
            visual_first=visual_first,
            extra_continuity=[
                "Apply fog of war; reveal only explored or known areas.",
            ],
        )

    if contains_any(text, INVENTORY_PATTERNS):
        return build_plan(
            format_name="inventory_board",
            kind="inventory",
            panel_count=0,
            reason="the player needs a compact view of carried state",
            visual_first=visual_first,
            extra_continuity=[
                "Preserve recurring item appearance and current quantities.",
            ],
        )

    if contains_any(text, MERCHANT_PATTERNS):
        return build_plan(
            format_name="merchant_board",
            kind="merchant",
            panel_count=0,
            reason="the beat involves buying, selling, or comparing goods",
            visual_first=visual_first,
            extra_continuity=[
                "Show only known prices and visible item qualities.",
            ],
        )

    if contains_any(text, REFERENCE_PATTERNS):
        return build_plan(
            format_name="reference_plate",
            kind="character",
            panel_count=0,
            reason="the beat needs a reusable canon visual anchor",
            visual_first=visual_first,
            extra_continuity=[
                "Capture scale, silhouette, outfit, marks, and normal poses.",
            ],
        )

    comic_plan = classify_visual_format(normalized_beat)
    if comic_plan.panel_count in {2, 4, 6}:
        return build_plan(
            format_name="comic_page",
            kind="comic-page",
            panel_count=comic_plan.panel_count,
            reason=comic_plan.reason,
            visual_first=visual_first,
            extra_continuity=[
                "Use ordered panels with clear gutters and no merged timeline.",
            ],
        )

    return build_plan(
        format_name="single_scene",
        kind="scene",
        panel_count=1,
        reason="one place, one moment, one main action",
        visual_first=visual_first,
        extra_continuity=[],
    )


def build_plan(
    format_name: str,
    kind: str,
    panel_count: int,
    reason: str,
    visual_first: bool,
    extra_continuity: list[str],
) -> VisualBeatPlan:
    continuity_requirements = [
        "Read images/visual-ledger.md for active visible states.",
        "List and reuse relevant canon anchors from images/visual-index.md.",
        "Preserve player-visible roll outcome, damage, gear, and object scale.",
    ] + extra_continuity
    next_steps = [
        "Choose or build the format-specific native image prompt.",
        "Save the prompt with campaign_memory.py save-visual-prompt.",
        "Generate the image with native Codex/ChatGPT image generation only.",
        "Register the selected asset with campaign_memory.py register-visual-asset.",
    ]
    present_image_in_chat = kind != "pov-360"
    use_gallery = visual_first or kind == "pov-360"
    if present_image_in_chat:
        next_steps.append(
            "Embed the selected static image once in chat with absolute-path Markdown."
        )
    if use_gallery:
        next_steps.append(
            "Refresh visual-gallery.html for history and #latest."
        )
    if kind == "pov-360":
        next_steps.insert(
            4,
            "Create or refresh the local panorama viewer with panorama_viewer.py.",
        )
    if kind == "comic-page":
        next_steps.insert(
            1,
            "Use comic_panels.py prompt or the comic-page template.",
        )
    return VisualBeatPlan(
        should_generate=True,
        format=format_name,
        kind=kind,
        panel_count=panel_count,
        use_gallery=use_gallery,
        present_image_in_chat=present_image_in_chat,
        reason=reason,
        continuity_requirements=continuity_requirements,
        next_steps=next_steps,
    )


def is_non_visual_question(text: str) -> bool:
    if contains_any(text, INVENTORY_PATTERNS):
        return False
    if contains_any(text, PANORAMA_PATTERNS + MAP_PATTERNS):
        return False
    return "?" in text and contains_any(text, NO_VISUAL_PATTERNS)


def contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def normalize_text(value: str) -> str:
    replacements = {
        "\u00e1": "a",
        "\u00e9": "e",
        "\u00ed": "i",
        "\u00f3": "o",
        "\u00fa": "u",
        "\u00fc": "u",
        "\u00f1": "n",
        "\u00bf": "",
        "\u00a1": "",
    }
    normalized = value.casefold()
    for source, replacement in replacements.items():
        normalized = normalized.replace(source, replacement)
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan the visual format for a Questforge table beat."
    )
    parser.add_argument("--beat", required=True)
    parser.add_argument(
        "--chat-images",
        action="store_true",
        help=(
            "Plan static images primarily for chat. 360 assets still use a "
            "local viewer."
        ),
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = plan_visual_beat(
        beat=parsed_arguments.beat,
        visual_first=not parsed_arguments.chat_images,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
