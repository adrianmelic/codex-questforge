"""Soft narrative-pattern lint for Questforge drafts and session recaps."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MotifDefinition:
    category: str
    label: str
    patterns: tuple[str, ...]
    weird: bool = True


@dataclass(frozen=True)
class MotifHit:
    category: str
    label: str
    count: int
    examples: list[str]


@dataclass(frozen=True)
class NarrativeLintIssue:
    level: str
    code: str
    message: str
    categories: list[str]


@dataclass(frozen=True)
class NarrativeLintResult:
    ok: bool
    issue_count: int
    warning_count: int
    info_count: int
    motif_count: int
    category_count: int
    hits: list[MotifHit]
    issues: list[NarrativeLintIssue]


MOTIFS = (
    MotifDefinition(
        category="memory_trade",
        label="memory taken, given, erased, or traded",
        patterns=(
            r"\brecuerd\w+\b",
            r"\bmemoria\b",
            r"\bolvid\w+\b",
            r"\bnombre\s+borrad\w+\b",
            r"\bmemory\b",
            r"\bmemories\b",
            r"\bforget(?:s|ting|ten)?\b",
            r"\bforgot(?:ten)?\b",
            r"\berased?\s+(?:name|memory|memories)\b",
        ),
    ),
    MotifDefinition(
        category="sentient_contract",
        label="contract, bargain, debt, or oath with an object",
        patterns=(
            r"\bcontrato\b",
            r"\bpacto\b",
            r"\bdeuda\b",
            r"\bpromesa\b",
            r"\bobjeto\s+consciente\b",
            r"\bobjeto\s+viv\w+\b",
            r"\bcontract\b",
            r"\bbargain\b",
            r"\bdebt\b",
            r"\boath\b",
            r"\bsentient\s+object\b",
            r"\bconscious\s+object\b",
            r"\bliving\s+object\b",
        ),
    ),
    MotifDefinition(
        category="secret_rules",
        label="hidden rules that govern behavior",
        patterns=(
            r"\bregla\s+secreta\b",
            r"\breglas\s+secretas\b",
            r"\bley\s+oculta\b",
            r"\bleyes\s+ocultas\b",
            r"\bhidden\s+rule\b",
            r"\bsecret\s+rule\b",
            r"\brules?\s+no\s+one\b",
            r"\brules?\s+that\s+govern\b",
            r"\bgoverns?\s+(?:conduct|behavior|behaviour)\b",
        ),
    ),
    MotifDefinition(
        category="unsayable",
        label="things nobody can say aloud",
        patterns=(
            r"\bnadie\s+puede\s+decir\b",
            r"\bno\s+se\s+puede\s+decir\b",
            r"\bno\s+decir\s+en\s+voz\s+alta\b",
            r"\bno\s+puede\s+pronunciar\b",
            r"\bno\s+pronunciar\b",
            r"\bno\s+one\s+can\s+(?:say|speak|acknowledge)\b",
            r"\bcan't\s+(?:say|speak|acknowledge)\b",
            r"\bcannot\s+(?:say|speak|acknowledge)\b",
            r"\bout\s+loud\b",
            r"\bunspeakable\b",
            r"\bforbidden\s+word\b",
        ),
    ),
    MotifDefinition(
        category="hyperstition",
        label="belief, rumor, or story that makes itself real",
        patterns=(
            r"\bhiperstici.n\b",
            r"\brumor\s+que\s+se\s+vuelve\s+real\b",
            r"\bcreencia\s+lo\s+hace\s+real\b",
            r"\bhyperstition\b",
            r"\bstory\s+becomes\s+real\b",
            r"\brumou?r\s+becomes\s+real\b",
            r"\bbelief\s+makes\s+it\s+(?:true|real)\b",
            r"\bprophecy\s+(?:creates|causes)\b",
        ),
    ),
    MotifDefinition(
        category="dream_symbolism",
        label="dream, vision, mirror, or symbolic double",
        patterns=(
            r"\bsue.o\b",
            r"\bvisi(?:o|\xF3)n\b",
            r"\bespejo\b",
            r"\bdoble\b",
            r"\bdream\b",
            r"\bvision\b",
            r"\bmirror\b",
            r"\bdoppelganger\b",
            r"\bsymbolic\s+double\b",
        ),
    ),
    MotifDefinition(
        category="theme_overexplicit",
        label="explicit theme, lesson, meaning, or moral",
        patterns=(
            r"\bverdad\b",
            r"\bsignificado\b",
            r"\blecci(?:o|\xF3)n\b",
            r"\bdestino\b",
            r"\btheme\b",
            r"\bmeaning\b",
            r"\blesson\b",
            r"\bmoral\b",
            r"\btruth\b",
            r"\bdestiny\b",
        ),
        weird=False,
    ),
    MotifDefinition(
        category="tidy_convergence",
        label="everything neatly converges on one answer",
        patterns=(
            r"\btodo\s+encaja\b",
            r"\btodas?\s+las\s+pistas?\s+apuntan\b",
            r"\bevery\s+clue\s+points\b",
            r"\ball\s+roads\s+lead\b",
            r"\bperfectly\s+fits\b",
            r"\beverything\s+(?:fits|connects)\b",
        ),
        weird=False,
    ),
)

WEIRD_CATEGORIES = {motif.category for motif in MOTIFS if motif.weird}
MATERIAL_ANCHOR_GROUPS = {
    "livelihood": (
        r"\bdiner\w*\b",
        r"\bmoned\w*\b",
        r"\bsalari\w*\b",
        r"\btrabaj\w*\b",
        r"\balquiler\b",
        r"\bimpuest\w*\b",
        r"\bcosech\w*\b",
        r"\bmoney\b",
        r"\bcoin\w*\b",
        r"\bwage\w*\b",
        r"\bwork\w*\b",
        r"\brent\b",
        r"\btax(?:es)?\b",
        r"\bharvest\w*\b",
        r"\btrade\b",
    ),
    "resources": (
        r"\bcomid\w*\b",
        r"\bharin\w*\b",
        r"\bmedicin\w*\b",
        r"\ble.a\b",
        r"\bhambre\b",
        r"\bfood\b",
        r"\bflour\b",
        r"\bmedicine\b",
        r"\bfirewood\b",
        r"\bhunger\b",
        r"\bsuppl(?:y|ies)\b",
    ),
    "institutions": (
        r"\bley\b",
        r"\bgremi\w*\b",
        r"\bguardia\b",
        r"\bconsejo\b",
        r"\btemplo\b",
        r"\blaw\b",
        r"\bguild\b",
        r"\bguard\b",
        r"\bcouncil\b",
        r"\btemple\b",
    ),
    "relationships": (
        r"\bfamili\w*\b",
        r"\bvecin\w*\b",
        r"\brival\w*\b",
        r"\bherman\w*\b",
        r"\bfamily\b",
        r"\bneighbou?r\w*\b",
        r"\brival\w*\b",
        r"\bsibling\w*\b",
        r"\bsister\w*\b",
        r"\bbrother\w*\b",
    ),
    "logistics": (
        r"\bcamino\b",
        r"\bcarro\b",
        r"\bherramient\w*\b",
        r"\bpuente\b",
        r"\bruta\b",
        r"\broad\b",
        r"\bcart\b",
        r"\btool\w*\b",
        r"\bbridge\b",
        r"\broute\b",
        r"\btransport\w*\b",
    ),
    "built_environment": (
        r"\bmercado\b",
        r"\bforja\b",
        r"\btejado\b",
        r"\bmuro\b",
        r"\bcasa\b",
        r"\bmarket\b",
        r"\bforge\b",
        r"\broof\b",
        r"\bwall\b",
        r"\bhouse\b",
        r"\bworkshop\b",
    ),
    "terrain_and_materials": (
        r"\btierra\b",
        r"\bpiedra\b",
        r"\barena\b",
        r"\bhierro\b",
        r"\bmadera\b",
        r"\bbarro\b",
        r"\bsoil\b",
        r"\bstone\b",
        r"\bsand\b",
        r"\biron\b",
        r"\bwood\b",
        r"\bmud\b",
        r"\bgrass\b",
    ),
    "body_and_senses": (
        r"\bfr(?:i|\xED)o\b",
        r"\bcalor\b",
        r"\bfatiga\b",
        r"\bolor\b",
        r"\bsudor\b",
        r"\bcold\b",
        r"\bheat\b",
        r"\bfatigue\b",
        r"\bsmell\b",
        r"\bsweat\b",
        r"\bache\w*\b",
    ),
    "weather_and_light": (
        r"\blluvia\b",
        r"\bsol\b",
        r"\bviento\b",
        r"\btormenta\b",
        r"\bhelada\b",
        r"\bsequ(?:i|\xED)a\b",
        r"\brain\b",
        r"\bsun(?:light)?\b",
        r"\bwind\b",
        r"\bstorm\b",
        r"\bfrost\b",
        r"\bdrought\b",
    ),
}
ENVIRONMENTAL_MOTIFS = {
    "precipitation": (
        r"\blluvia\b",
        r"\btormenta\b",
        r"\brain\b",
        r"\bstorm\b",
    ),
    "fog": (r"\bniebla\b", r"\bbruma\b", r"\bfog\b", r"\bmist\b"),
    "darkness": (
        r"\boscur\w*\b",
        r"\bmedianoche\b",
        r"\bdark(?:ness)?\b",
        r"\bmidnight\b",
    ),
    "cold": (r"\bfr(?:i|\xED)o\b", r"\bhielo\b", r"\bcold\b", r"\bice\b"),
    "heat": (r"\bcalor\b", r"\bsol\b", r"\bheat\b", r"\bsun(?:light)?\b"),
    "wind": (r"\bviento\b", r"\bwind\b", r"\bgale\b"),
    "snow": (r"\bnieve\b", r"\bnevada\b", r"\bsnow\b", r"\bblizzard\b"),
    "water": (
        r"\bagua\b",
        r"\br(?:i|\xED)o\b",
        r"\bpuerto\b",
        r"\bwater\b",
        r"\briver\b",
        r"\bharbou?r\b",
    ),
    "dust": (
        r"\bpolvo\b",
        r"\bsequ(?:i|\xED)a\b",
        r"\bdust\b",
        r"\bdrought\b",
    ),
    "vegetation": (
        r"\bbosque\b",
        r"\bra(?:i|\xED)ces\b",
        r"\bforest\b",
        r"\broot\w*\b",
    ),
    "underground": (
        r"\bcueva\b",
        r"\bsubterr(?:a|\xE1)ne\w*\b",
        r"\bcave\b",
        r"\bunderground\b",
    ),
}

REVISION_NUDGES = (
    "Keep at most one metaphysical motif dominant in a scene or reveal.",
    "Add material pressure: livelihood, safety, status, relationships, law, "
    "scarcity, logistics, terrain, bodily needs, or work.",
    "Let secrets belong to people, institutions, factions, or logistics before "
    "making them cosmic rules.",
    "Preserve ambiguity and consequence; avoid making every clue point at the "
    "same symbolic answer.",
)


def lint_text(text: str) -> NarrativeLintResult:
    hits = find_motif_hits(text)
    issues = build_issues(text, hits)
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    info_count = sum(1 for issue in issues if issue.level == "info")
    motif_count = sum(hit.count for hit in hits)
    category_count = len({hit.category for hit in hits})
    return NarrativeLintResult(
        ok=warning_count == 0,
        issue_count=len(issues),
        warning_count=warning_count,
        info_count=info_count,
        motif_count=motif_count,
        category_count=category_count,
        hits=hits,
        issues=issues,
    )


def lint_documents(documents: list[str]) -> NarrativeLintResult:
    """Lint a corpus while preserving cross-opening repetition evidence."""

    if not documents:
        raise ValueError("At least one document is required.")
    individual_results = [lint_text(document) for document in documents]
    if len(individual_results) == 1:
        return individual_results[0]

    hits_by_category: dict[str, MotifHit] = {}
    issues_by_key: dict[
        tuple[str, str, tuple[str, ...]], NarrativeLintIssue
    ] = {}
    for result in individual_results:
        for hit in result.hits:
            existing = hits_by_category.get(hit.category)
            if existing is None:
                hits_by_category[hit.category] = hit
            else:
                hits_by_category[hit.category] = MotifHit(
                    category=hit.category,
                    label=hit.label,
                    count=existing.count + hit.count,
                    examples=(existing.examples + hit.examples)[:3],
                )
        for issue in result.issues:
            key = (issue.level, issue.code, tuple(issue.categories))
            issues_by_key.setdefault(key, issue)

    if len(documents) >= 3:
        for category, patterns in ENVIRONMENTAL_MOTIFS.items():
            document_hits = sum(
                1
                for document in documents
                if count_pattern_matches(document, patterns) > 0
            )
            if document_hits >= 3 and document_hits / len(documents) >= 0.75:
                issue = NarrativeLintIssue(
                    level="warning",
                    code="environmental_motif_repeated_across_openings",
                    message=(
                        f"The environmental motif '{category}' appears in "
                        f"{document_hits} of {len(documents)} drafts. Vary the "
                        "physical situation, not only names and lore."
                    ),
                    categories=[category],
                )
                key = (issue.level, issue.code, tuple(issue.categories))
                issues_by_key[key] = issue

    hits = sorted(hits_by_category.values(), key=lambda value: value.category)
    issues = list(issues_by_key.values())
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    info_count = sum(1 for issue in issues if issue.level == "info")
    return NarrativeLintResult(
        ok=warning_count == 0,
        issue_count=len(issues),
        warning_count=warning_count,
        info_count=info_count,
        motif_count=sum(hit.count for hit in hits),
        category_count=len(hits),
        hits=hits,
        issues=issues,
    )


def find_motif_hits(text: str) -> list[MotifHit]:
    hits = []
    for motif in MOTIFS:
        matches = []
        for pattern in motif.patterns:
            matches.extend(re.finditer(pattern, text, re.IGNORECASE))
        if not matches:
            continue
        matches.sort(key=lambda match: match.start())
        hits.append(
            MotifHit(
                category=motif.category,
                label=motif.label,
                count=len(matches),
                examples=[
                    snippet(text, match.start(), match.end())
                    for match in matches[:3]
                ],
            )
        )
    return hits


def build_issues(text: str, hits: list[MotifHit]) -> list[NarrativeLintIssue]:
    issues = []
    hit_counts = {hit.category: hit.count for hit in hits}
    categories = set(hit_counts)
    weird_categories = sorted(categories & WEIRD_CATEGORIES)

    if len(weird_categories) >= 3:
        issues.append(
            NarrativeLintIssue(
                level="warning",
                code="metaphysical_pileup",
                message=(
                    "Several AI-prone metaphysical motifs appear together. "
                    "Choose one to dominate, then ground the rest in concrete "
                    "NPC motives or local consequences."
                ),
                categories=weird_categories,
            )
        )
    if hit_counts.get("memory_trade", 0) >= 4:
        issues.append(
            NarrativeLintIssue(
                level="warning",
                code="dominant_memory_motif",
                message=(
                    "Memory loss, trade, or erasure is doing repeated work. "
                    "Keep it only if this scene pays off prior setup."
                ),
                categories=["memory_trade"],
            )
        )
    if hit_counts.get("secret_rules", 0) + hit_counts.get("unsayable", 0) >= 3:
        issues.append(
            NarrativeLintIssue(
                level="warning",
                code="secret_rule_stack",
                message=(
                    "Hidden conduct rules and unsayable truths are stacking. "
                    "Make the rule practical, institutional, or socially "
                    "enforced before making it metaphysical."
                ),
                categories=["secret_rules", "unsayable"],
            )
        )
    if hit_counts.get("theme_overexplicit", 0) >= 5:
        issues.append(
            NarrativeLintIssue(
                level="info",
                code="theme_overexplicit",
                message=(
                    "The draft may be stating theme too directly. Let the "
                    "player infer meaning from choices, costs, and NPC action."
                ),
                categories=["theme_overexplicit"],
            )
        )
    material_categories = material_anchor_categories(text)
    if weird_categories and len(material_categories) < 2:
        issues.append(
            NarrativeLintIssue(
                level="info",
                code="mundane_anchor_missing",
                message=(
                    "The weird premise lacks enough material anchors. Add "
                    "pressures from at least two concrete domains such as "
                    "livelihood, resources, institutions, relationships, "
                    "logistics, terrain, bodily needs, or built space."
                ),
                categories=weird_categories,
            )
        )
    for category, patterns in ENVIRONMENTAL_MOTIFS.items():
        if count_pattern_matches(text, patterns) >= 5:
            issues.append(
                NarrativeLintIssue(
                    level="warning",
                    code="environmental_crutch",
                    message=(
                        f"The environmental motif '{category}' is doing "
                        "repeated atmospheric work in one draft. Keep it when "
                        "it changes choices; otherwise diversify the material "
                        "and sensory anchors."
                    ),
                    categories=[category],
                )
            )
    return issues


def material_anchor_categories(text: str) -> set[str]:
    """Return distinct grounding domains instead of rewarding one keyword."""

    return {
        category
        for category, patterns in MATERIAL_ANCHOR_GROUPS.items()
        if count_pattern_matches(text, patterns) > 0
    }


def count_pattern_matches(text: str, patterns: Iterable[str]) -> int:
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


def snippet(text: str, start: int, end: int, radius: int = 48) -> str:
    prefix_start = max(0, start - radius)
    suffix_end = min(len(text), end + radius)
    value = text[prefix_start:suffix_end]
    return " ".join(value.split())


def format_markdown(result: NarrativeLintResult) -> str:
    lines = [
        "# Questforge Narrative Lint",
        "",
        (
            f"- Status: {'ok' if result.ok else 'review'}"
            f" ({result.warning_count} warnings, {result.info_count} info)"
        ),
        f"- Motifs found: {result.motif_count} across {result.category_count} categories",
        "",
    ]
    if result.issues:
        lines.append("## Findings")
        lines.append("")
        for issue in result.issues:
            categories = ", ".join(issue.categories)
            lines.append(
                f"- `{issue.level}` `{issue.code}` ({categories}): "
                f"{issue.message}"
            )
        lines.append("")
    else:
        lines.extend(["## Findings", "", "- None.", ""])

    if result.hits:
        lines.append("## Motif Hits")
        lines.append("")
        for hit in result.hits:
            lines.append(f"- `{hit.category}` x{hit.count}: {hit.label}")
            for example in hit.examples:
                lines.append(f"  - {example}")
        lines.append("")

    lines.append("## Revision Nudge")
    lines.append("")
    for nudge in REVISION_NUDGES:
        lines.append(f"- {nudge}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Soft-check Questforge drafts for overused AI-fiction narrative "
            "motif pileups."
        )
    )
    parser.add_argument("--text", action="append", default=[])
    parser.add_argument(
        "--file",
        action="append",
        type=Path,
        default=[],
        help="Text or Markdown file to lint. May be repeated.",
    )
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are found.",
    )
    return parser


def read_inputs(parsed_arguments: argparse.Namespace) -> list[str]:
    parts = list(parsed_arguments.text)
    for file_path in parsed_arguments.file:
        parts.append(file_path.read_text(encoding="utf-8"))
    if not parts:
        raise SystemExit("Provide --text or --file.")
    return parts


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = lint_documents(read_inputs(parsed_arguments))
    if parsed_arguments.format == "json":
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(format_markdown(result))
    if parsed_arguments.strict and result.warning_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
