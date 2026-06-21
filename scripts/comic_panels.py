"""Plan Questforge visual format and comic-page prompts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

SEQUENCE_PATTERNS = [
    "después",
    "luego",
    "mientras",
    "antes de",
    "vuelve",
    "volver",
    "camino a",
    "paga",
    "pago",
    "pagar",
    "desayuna",
    "entra",
    "sale",
    "baja",
    "bajo",
    "bajar",
    "sube",
    "subo",
    "subir",
    "recupera",
    "then",
    "after",
    "while",
    "before",
    "returns",
    "pays",
    "pay",
    "eats",
    "breakfast",
    "downstairs",
    "enters",
    "leaves",
]
TACTICAL_PATTERNS = [
    "persecución",
    "infiltración",
    "contravigilancia",
    "huida",
    "ruta",
    "tramos",
]
MAP_PATTERNS = ["mapa", "ruta", "dónde", "salida", "entrada", "distancia"]


@dataclass(frozen=True)
class VisualFormatPlan:
    """Chosen visual format before requesting image generation."""

    kind: str
    panel_count: int
    reason: str


def classify_visual_format(summary: str) -> VisualFormatPlan:
    text = summary.casefold()
    sequence_hits = count_pattern_hits(text, SEQUENCE_PATTERNS)
    tactical_hits = count_pattern_hits(text, TACTICAL_PATTERNS)
    map_hits = count_pattern_hits(text, MAP_PATTERNS)

    if map_hits and ("ver" in text or "entender" in text or "decidir" in text):
        return VisualFormatPlan(
            kind="map_or_diagram",
            panel_count=0,
            reason="the request is spatial and needs route clarity",
        )
    if tactical_hits >= 2 or sequence_hits >= 5:
        return VisualFormatPlan(
            kind="comic_page_6",
            panel_count=6,
            reason="the beat chains tactical movement across several moments",
        )
    if tactical_hits or sequence_hits >= 4:
        return VisualFormatPlan(
            kind="comic_page_4",
            panel_count=4,
            reason="the beat contains multiple actions or time slices",
        )
    if sequence_hits >= 2:
        return VisualFormatPlan(
            kind="comic_page_2",
            panel_count=2,
            reason="the beat contains two distinct moments",
        )
    return VisualFormatPlan(
        kind="single_scene",
        panel_count=1,
        reason="one place, one moment, one main action",
    )


def count_pattern_hits(text: str, patterns: list[str]) -> int:
    return sum(1 for pattern in patterns if re.search(rf"\b{pattern}\b", text))


def build_comic_prompt(
    title: str,
    panels: list[str],
    continuity: str = "",
    style: str = "",
) -> str:
    if len(panels) not in {2, 4, 6}:
        raise ValueError("Comic pages must use 2, 4, or 6 panels.")
    panel_lines = "\n".join(
        f"{index}. {panel.strip()}" for index, panel in enumerate(panels, 1)
    )
    continuity_text = sentence(
        continuity.strip() or "preserve current visual ledger"
    )
    style_text = sentence(
        style.strip()
        or (
            "dark rural fantasy, painterly comic page, clear gutters, readable "
            "staging, no speech bubbles, no readable text"
        )
    )
    return f"""Original 5E-compatible fantasy comic page, unofficial and not using official D&D settings, logos, product art, named copyrighted characters, or commercial adventure identity.

Title: {title.strip()}
Format: {len(panels)} ordered panels with clear gutters.
Panel order:
{panel_lines}

Continuity: {continuity_text}
Style: {style_text}
Avoid: speech bubbles, captions, readable lettering, merged timelines, repeated impossible body positions, official logos, copied product art.
Post-generation review: reject the image if multiple moments are collapsed into one physical scene instead of clear panels.
"""


def sentence(value: str) -> str:
    stripped_value = value.strip()
    if stripped_value.endswith((".", "!", "?")):
        return stripped_value
    return stripped_value + "."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify or build Questforge comic-page prompts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify_parser = subparsers.add_parser("classify")
    classify_parser.add_argument("--summary", required=True)

    prompt_parser = subparsers.add_parser("prompt")
    prompt_parser.add_argument("--title", required=True)
    prompt_parser.add_argument("--panel", action="append", required=True)
    prompt_parser.add_argument("--continuity", default="")
    prompt_parser.add_argument("--style", default="")
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    if parsed_arguments.command == "classify":
        print(
            json.dumps(
                asdict(classify_visual_format(parsed_arguments.summary)),
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    print(
        build_comic_prompt(
            title=parsed_arguments.title,
            panels=parsed_arguments.panel,
            continuity=parsed_arguments.continuity,
            style=parsed_arguments.style,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
