"""Validate and compare creative conceptions for Questforge campaigns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ENVIRONMENT_FIELDS = (
    "biome",
    "climate",
    "season",
    "time_of_day",
    "surface",
    "social_scale",
    "water_relevance",
)
CONCEPTION_TEXT_FIELDS = (
    "community",
    "material_conflict",
    "threat",
    "tone",
    "aesthetic",
    "campaign_promise",
)
SENSORY_FIELDS = (
    "sight",
    "sound",
    "smell_or_taste",
    "touch_or_temperature",
)
PLACEHOLDER_PATTERN = re.compile(
    r"(?:<[^>]+>|\b(?:todo|tbd|placeholder)\b)",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
STOP_WORDS = {
    "a",
    "al",
    "and",
    "con",
    "de",
    "del",
    "el",
    "en",
    "for",
    "from",
    "in",
    "la",
    "las",
    "los",
    "of",
    "on",
    "para",
    "por",
    "the",
    "to",
    "un",
    "una",
    "y",
}


@dataclass(frozen=True)
class ConceptionComparison:
    """Similarity evidence between a candidate and one prior campaign."""

    campaign_root: str
    matched_environment_fields: list[str]
    environment_match_ratio: float
    narrative_similarity: float
    repeated_combination: bool


@dataclass(frozen=True)
class ConceptionAudit:
    """Validation and originality result for one campaign conception."""

    ok: bool
    environment_signature: str
    warnings: list[str]
    comparisons: list[ConceptionComparison]


def validate_conception(conception: dict) -> None:
    """Reject incomplete, placeholder, or structurally weak conceptions."""

    if not isinstance(conception, dict):
        raise ValueError("conception must be an object.")

    environment = required_mapping(conception, "environment")
    for field in ENVIRONMENT_FIELDS:
        required_text(environment, field, f"conception.environment.{field}")

    for field in CONCEPTION_TEXT_FIELDS:
        required_text(conception, field, f"conception.{field}")

    relationships = conception.get("npc_relationships")
    if not isinstance(relationships, list) or len(relationships) < 2:
        raise ValueError(
            "conception.npc_relationships must contain at least two NPCs."
        )
    for index, relationship in enumerate(relationships, start=1):
        if not isinstance(relationship, dict):
            raise ValueError(
                "Every conception.npc_relationships entry must be an object."
            )
        for field in ("npc", "role", "wants", "relationship"):
            required_text(
                relationship,
                field,
                f"conception.npc_relationships[{index}].{field}",
            )

    sensory_palette = required_mapping(conception, "sensory_palette")
    populated_senses = [
        field
        for field in SENSORY_FIELDS
        if valid_text(sensory_palette.get(field))
    ]
    if len(populated_senses) < 3:
        raise ValueError(
            "conception.sensory_palette must define at least three distinct "
            "sensory channels."
        )
    for field in populated_senses:
        required_text(
            sensory_palette,
            field,
            f"conception.sensory_palette.{field}",
        )

    distinctive_elements = conception.get("distinctive_elements")
    if (
        not isinstance(distinctive_elements, list)
        or len(distinctive_elements) < 2
    ):
        raise ValueError(
            "conception.distinctive_elements must contain at least two "
            "campaign-specific elements."
        )
    for index, value in enumerate(distinctive_elements, start=1):
        ensure_complete_text(
            value,
            f"conception.distinctive_elements[{index}]",
        )


def audit_conception(
    conception: dict,
    campaigns_dir: Path | None = None,
) -> ConceptionAudit:
    """Validate a conception and compare it with prior local campaigns."""

    validate_conception(conception)
    comparisons = []
    if campaigns_dir is not None and campaigns_dir.exists():
        for path, previous in load_prior_conceptions(campaigns_dir):
            comparisons.append(compare_conceptions(conception, previous, path))

    warnings = [
        repeated_message(comparison)
        for comparison in comparisons
        if comparison.repeated_combination
    ]
    return ConceptionAudit(
        ok=not warnings,
        environment_signature=environment_signature(conception),
        warnings=warnings,
        comparisons=sorted(
            comparisons,
            key=lambda value: (
                value.repeated_combination,
                value.environment_match_ratio,
                value.narrative_similarity,
            ),
            reverse=True,
        ),
    )


def require_original_conception(
    conception: dict,
    campaigns_dir: Path | None = None,
) -> ConceptionAudit:
    """Return an audit or fail before a repeated campaign is created."""

    audit = audit_conception(conception, campaigns_dir)
    if not audit.ok:
        raise ValueError(
            "Campaign conception repeats a recent environmental and narrative "
            "combination. Reconceive the setting, material conflict, threat, "
            "or social scale instead of only renaming it. "
            + " ".join(audit.warnings)
        )
    return audit


def compare_conceptions(
    candidate: dict,
    previous: dict,
    campaign_root: Path | str = "",
) -> ConceptionComparison:
    """Compare free-form briefs without imposing enumerated adventure types."""

    validate_conception(candidate)
    validate_conception(previous)
    candidate_environment = candidate["environment"]
    previous_environment = previous["environment"]
    matched_fields = [
        field
        for field in ENVIRONMENT_FIELDS
        if dimension_matches(
            candidate_environment[field],
            previous_environment[field],
        )
    ]
    environment_ratio = len(matched_fields) / len(ENVIRONMENT_FIELDS)
    narrative_similarity = jaccard(
        conception_tokens(candidate),
        conception_tokens(previous),
    )
    repeated = len(matched_fields) >= 5 or (
        len(matched_fields) >= 4 and narrative_similarity >= 0.35
    )
    return ConceptionComparison(
        campaign_root=str(campaign_root),
        matched_environment_fields=matched_fields,
        environment_match_ratio=round(environment_ratio, 3),
        narrative_similarity=round(narrative_similarity, 3),
        repeated_combination=repeated,
    )


def environment_signature(conception: dict) -> str:
    """Create a readable, stable signature from free-form dimensions."""

    validate_conception(conception)
    environment = conception["environment"]
    return " | ".join(
        f"{field}={normalize(environment[field])}"
        for field in ENVIRONMENT_FIELDS
    )


def conception_tokens(conception: dict) -> set[str]:
    """Return meaningful words used to compare narrative foundations."""

    values = [str(conception[field]) for field in CONCEPTION_TEXT_FIELDS]
    values.extend(str(value) for value in conception["distinctive_elements"])
    for relationship in conception["npc_relationships"]:
        values.extend(
            str(relationship[field])
            for field in ("role", "wants", "relationship")
        )
    return text_tokens(" ".join(values))


def load_prior_conceptions(
    campaigns_dir: Path,
) -> list[tuple[Path, dict]]:
    """Load only the canonical conception file from each direct campaign."""

    conceptions = []
    for path in sorted(campaigns_dir.glob("*/campaign-conception.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        conception = payload.get("conception", payload)
        if isinstance(conception, dict):
            conceptions.append((path.parent, conception))
    return conceptions


def conception_record(conception: dict, audit: ConceptionAudit) -> dict:
    """Build the persisted creative record for a campaign."""

    return {
        "schema_version": 1,
        "environment_signature": audit.environment_signature,
        "conception": conception,
    }


def repeated_message(comparison: ConceptionComparison) -> str:
    fields = ", ".join(comparison.matched_environment_fields)
    return (
        f"{comparison.campaign_root or 'prior campaign'} matches environment "
        f"fields [{fields}] with narrative similarity "
        f"{comparison.narrative_similarity:.3f}."
    )


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def dimension_matches(left: object, right: object) -> bool:
    """Match exact or strongly overlapping free-form dimension phrases."""

    if normalize(left) == normalize(right):
        return True
    left_tokens = text_tokens(str(left))
    right_tokens = text_tokens(str(right))
    if not left_tokens or not right_tokens:
        return False
    overlap = len(left_tokens & right_tokens) / min(
        len(left_tokens),
        len(right_tokens),
    )
    return overlap >= 0.6


def text_tokens(value: str) -> set[str]:
    tokens = {
        canonical_token(token)
        for token in TOKEN_PATTERN.findall(value)
        if len(token) >= 3
    }
    return tokens - STOP_WORDS


def canonical_token(value: str) -> str:
    token = value.casefold()
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def normalize(value: object) -> str:
    return " ".join(str(value).casefold().split())


def valid_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not PLACEHOLDER_PATTERN.search(value)
    )


def ensure_complete_text(value: object, label: str) -> str:
    if not valid_text(value):
        raise ValueError(
            f"{label} must be a completed non-placeholder string."
        )
    return str(value).strip()


def required_text(payload: dict, key: str, label: str) -> str:
    return ensure_complete_text(payload.get(key), label)


def required_mapping(payload: dict, key: str) -> dict:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"conception.{key} must be an object.")
    return value


def extract_conception(payload: dict) -> dict:
    conception = payload.get("conception", payload)
    if not isinstance(conception, dict):
        raise ValueError("Spec must contain a conception object.")
    return conception


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Questforge creative conception and compare it with "
            "recent campaign combinations."
        )
    )
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--campaigns-dir", type=Path)
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
    )
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    payload = json.loads(parsed_arguments.spec.read_text(encoding="utf-8"))
    audit = audit_conception(
        extract_conception(payload),
        parsed_arguments.campaigns_dir,
    )
    if parsed_arguments.format == "json":
        print(json.dumps(asdict(audit), indent=2, ensure_ascii=False))
    else:
        print(
            f"{'ok' if audit.ok else 'review'}: "
            f"{audit.environment_signature}"
        )
        for warning in audit.warnings:
            print(f"- {warning}")
    return 0 if audit.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
