"""Create a playable Questforge campaign from one structured spec."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Iterable

try:
    from .campaign_memory import create_campaign, save_visual_prompt, slugify
    from .game_state import (
        add_character,
        add_item,
        create_checkpoint,
        default_character,
        load_state,
        save_state,
    )
    from .session_analytics import append_event
except ImportError:  # pragma: no cover - direct script execution path
    from campaign_memory import create_campaign, save_visual_prompt, slugify
    from game_state import (
        add_character,
        add_item,
        create_checkpoint,
        default_character,
        load_state,
        save_state,
    )
    from session_analytics import append_event


PLAYER_LABELS = {
    "en": {
        "campaign_promise": "Campaign Promise",
        "active_hooks": "Active Hooks",
        "location": "Location",
        "pressure": "Pressure",
        "npc_intent": "NPC intent",
        "sensory_detail": "Sensory detail",
        "visible_risks": "Visible Risks",
        "approaches": "Possible Approaches",
        "fallback_action": "Attempt any plausible action.",
        "player_journal": "Player Journal",
        "campaign": "Campaign",
        "hero": "Hero",
        "current_objective": "Current objective",
        "immediate_risk": "Immediate risk",
        "known_clues": "Known Clues And NPCs",
        "open_threads": "Open Threads",
        "none_yet": "None yet.",
        "ancestry": "Ancestry",
        "class": "Class",
        "background": "Background",
        "hp": "HP",
        "ac": "AC",
        "xp": "XP",
        "features": "Features",
        "notes": "Notes",
        "session_log": "Session Log",
        "session": "Session",
        "date": "Date",
        "character_present": "Character present",
        "scenes": "Scenes",
        "scene": "Scene",
        "opening_question": "Opening question",
    },
    "es": {
        "campaign_promise": "Promesa de campaña",
        "active_hooks": "Ganchos activos",
        "location": "Ubicación",
        "pressure": "Presión",
        "npc_intent": "Intención del PNJ",
        "sensory_detail": "Detalle sensorial",
        "visible_risks": "Riesgos visibles",
        "approaches": "Enfoques posibles",
        "fallback_action": "Intentar cualquier acción plausible.",
        "player_journal": "Diario del jugador",
        "campaign": "Campaña",
        "hero": "Héroe",
        "current_objective": "Objetivo actual",
        "immediate_risk": "Riesgo inmediato",
        "known_clues": "Pistas y PNJ conocidos",
        "open_threads": "Hilos abiertos",
        "none_yet": "Todavía ninguno.",
        "ancestry": "Linaje",
        "class": "Clase",
        "background": "Trasfondo",
        "hp": "PG",
        "ac": "CA",
        "xp": "PX",
        "features": "Rasgos",
        "notes": "Notas",
        "session_log": "Registro de sesión",
        "session": "Sesión",
        "date": "Fecha",
        "character_present": "Personaje presente",
        "scenes": "Escenas",
        "scene": "Escena",
        "opening_question": "Pregunta inicial",
    },
}


def create_quick_start(workspace_root: Path, spec: dict) -> Path:
    """Create and populate one campaign without repeated setup commands."""

    campaign_spec = required_mapping(spec, "campaign")
    hero_spec = required_mapping(spec, "hero")
    opening_spec = required_mapping(spec, "opening")
    campaign_name = required_text(campaign_spec, "name")
    hero_name = required_text(hero_spec, "name")

    campaigns_dir = workspace_root.expanduser().resolve() / "campaigns"
    campaigns_dir.mkdir(parents=True, exist_ok=True)
    paths = create_campaign(
        campaigns_dir=campaigns_dir,
        name=campaign_name,
        tone=str(campaign_spec.get("tone", "")),
        boundaries=str(campaign_spec.get("boundaries", "")),
        session_date=date.today(),
    )

    state = load_state(paths.root)
    character = default_character(
        name=hero_name,
        class_name=required_text(hero_spec, "class_name"),
        ancestry=required_text(hero_spec, "ancestry"),
        level=positive_int(hero_spec.get("level", 1), "hero.level"),
        xp=nonnegative_int(hero_spec.get("xp", 0), "hero.xp"),
        max_hp=positive_int(hero_spec.get("max_hp"), "hero.max_hp"),
        armor_class=positive_int(
            hero_spec.get("armor_class"), "hero.armor_class"
        ),
        hit_die=str(hero_spec.get("hit_die", "d8")),
    )
    apply_character_details(character, hero_spec)
    add_character(state, character)
    for item_spec in hero_spec.get("items", []):
        if not isinstance(item_spec, dict):
            raise ValueError("Every hero.items entry must be an object.")
        add_item(
            state,
            hero_name,
            required_text(item_spec, "name"),
            quantity=positive_int(
                item_spec.get("quantity", 1), "item.quantity"
            ),
            location=str(item_spec.get("location", "backpack")),
            slot=str(item_spec.get("slot", "")),
            mechanical_effect=str(item_spec.get("mechanical_effect", "")),
            story_significance=str(item_spec.get("story_significance", "")),
            value=str(item_spec.get("value", "")),
        )
    save_state(paths.root, state)
    create_checkpoint(
        paths.root,
        state,
        label=str(spec.get("checkpoint_label", "Before session start")),
    )

    language = str(campaign_spec.get("language", "en"))
    paths.opening_brief.write_text(
        render_opening(campaign_spec, opening_spec, language),
        encoding="utf-8",
        newline="\n",
    )
    paths.adventure_spine.write_text(
        render_spine(campaign_spec),
        encoding="utf-8",
        newline="\n",
    )
    paths.player_journal.write_text(
        render_player_journal(
            campaign_name,
            hero_name,
            opening_spec,
            language,
        ),
        encoding="utf-8",
        newline="\n",
    )
    (paths.characters / f"{slugify(hero_name)}.md").write_text(
        render_character_sheet(character, language),
        encoding="utf-8",
        newline="\n",
    )
    seed_visual_continuity(paths, hero_spec, opening_spec)
    session_path = paths.sessions / "session-001.md"
    session_path.write_text(
        render_session(campaign_name, hero_name, opening_spec, language),
        encoding="utf-8",
        newline="\n",
    )

    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    manifest["language"] = language
    paths.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    visual_spec = spec.get("visual")
    if isinstance(visual_spec, dict) and visual_spec.get("prompt"):
        save_visual_prompt(
            campaign_root=paths.root,
            session_number=1,
            scene_number=1,
            kind=str(visual_spec.get("kind", "scene")),
            label=required_text(visual_spec, "label"),
            prompt=required_text(visual_spec, "prompt"),
        )

    append_event(
        paths.root,
        {
            "event_type": "session_start",
            "session": 1,
            "scene": 1,
            "summary": f"{hero_name} enters {opening_spec.get('location', '')}.",
            "tags": ["quick-start", language],
        },
    )
    return paths.root


def apply_character_details(character: dict, hero_spec: dict) -> None:
    """Apply validated optional hero fields to the default character."""

    for key in ("abilities", "skill_modifiers", "currency"):
        value = hero_spec.get(key)
        if value is not None:
            if not isinstance(value, dict):
                raise ValueError(f"hero.{key} must be an object.")
            character[key].update(value)
    for key in ("resources", "spells"):
        value = hero_spec.get(key)
        if value is not None:
            if not isinstance(value, dict):
                raise ValueError(f"hero.{key} must be an object.")
            deep_update(character[key], value)
    for key in ("features", "notes"):
        value = hero_spec.get(key)
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(f"hero.{key} must be a list.")
            character[key] = [str(item) for item in value]
    for key in ("initiative_modifier", "speed"):
        if key in hero_spec:
            character[key] = int(hero_spec[key])
    if "background" in hero_spec:
        character["background"] = str(hero_spec["background"])


def deep_update(target: dict, updates: dict) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_update(target[key], value)
        else:
            target[key] = value


def render_opening(campaign: dict, opening: dict, language: str) -> str:
    labels = labels_for(language)
    hooks = markdown_bullets(campaign.get("hooks", []), labels["none_yet"])
    risks = markdown_bullets(
        opening.get("visible_risks", []), labels["none_yet"]
    )
    options = markdown_numbered(
        opening.get("options", []), labels["fallback_action"]
    )
    return (
        f"# {campaign['name']}\n\n"
        f"## {labels['campaign_promise']}\n\n"
        f"{campaign.get('promise', '')}\n\n"
        f"## {labels['active_hooks']}\n\n"
        f"{hooks}\n\n"
        f"## {opening.get('title', 'Opening Scene')}\n\n"
        f"- {labels['location']}: {opening.get('location', '')}\n"
        f"- {labels['pressure']}: {opening.get('pressure', '')}\n"
        f"- {labels['npc_intent']}: {opening.get('npc_intent', '')}\n"
        f"- {labels['sensory_detail']}: {opening.get('sensory_detail', '')}\n\n"
        f"### {labels['visible_risks']}\n\n"
        f"{risks}\n\n"
        f"### {labels['approaches']}\n\n"
        f"{options}\n\n"
        f"**{opening.get('question', 'What do you do?')}**\n"
    )


def render_spine(campaign: dict) -> str:
    return (
        "# Adventure Spine\n\n"
        "## Core Truths\n\n"
        f"{markdown_bullets(campaign.get('core_truths', []))}\n\n"
        "## Active Hooks\n\n"
        f"{markdown_bullets(campaign.get('hooks', []))}\n\n"
        "## Clue Routes\n\n"
        f"{markdown_bullets(campaign.get('clue_routes', []))}\n\n"
        "## Faction Intent\n\n"
        f"{markdown_bullets(campaign.get('faction_intents', []))}\n\n"
        "## Plausible Outcomes\n\n"
        f"{markdown_bullets(campaign.get('outcomes', []))}\n"
    )


def render_player_journal(
    campaign_name: str,
    hero_name: str,
    opening: dict,
    language: str,
) -> str:
    labels = labels_for(language)
    return (
        f"# {labels['player_journal']}\n\n"
        f"- {labels['campaign']}: {campaign_name}\n"
        f"- {labels['hero']}: {hero_name}\n"
        f"- {labels['current_objective']}: {opening.get('question', '')}\n"
        f"- {labels['immediate_risk']}: {opening.get('pressure', '')}\n"
        f"- {labels['location']}: {opening.get('location', '')}\n\n"
        f"## {labels['known_clues']}\n\n- {labels['none_yet']}\n\n"
        f"## {labels['open_threads']}\n\n"
        f"{markdown_bullets(opening.get('visible_risks', []), labels['none_yet'])}\n"
    )


def render_character_sheet(character: dict, language: str) -> str:
    labels = labels_for(language)
    return (
        f"# {character['name']}\n\n"
        f"- {labels['ancestry']}: {character['ancestry']}\n"
        f"- {labels['class']}: {character['class']} {character['level']}\n"
        f"- {labels['background']}: {character['background']}\n"
        f"- {labels['hp']}: {character['current_hp']}/{character['max_hp']}\n"
        f"- {labels['ac']}: {character['armor_class']}\n"
        f"- {labels['xp']}: {character['xp']}\n\n"
        f"## {labels['features']}\n\n"
        f"{markdown_bullets(character.get('features', []), labels['none_yet'])}\n\n"
        f"## {labels['notes']}\n\n"
        f"{markdown_bullets(character.get('notes', []), labels['none_yet'])}\n"
    )


def render_session(
    campaign_name: str,
    hero_name: str,
    opening: dict,
    language: str,
) -> str:
    labels = labels_for(language)
    return (
        f"# {labels['session_log']}\n\n"
        f"## {labels['session']}\n\n"
        f"- {labels['campaign']}: {campaign_name}\n"
        f"- {labels['session']}: 1\n"
        f"- {labels['date']}: {date.today().isoformat()}\n"
        f"- {labels['character_present']}: {hero_name}\n\n"
        f"## {labels['scenes']}\n\n"
        f"### {labels['scene']} 1\n\n"
        f"- {labels['location']}: {opening.get('location', '')}\n"
        f"- {labels['pressure']}: {opening.get('pressure', '')}\n"
        f"- {labels['opening_question']}: {opening.get('question', '')}\n"
    )


def seed_visual_continuity(paths, hero: dict, opening: dict) -> None:
    description = str(hero.get("visual_description", "")).strip()
    if not description:
        return
    must_preserve = ", ".join(
        str(value) for value in hero.get("visual_must_preserve", [])
    )
    may_drift = str(hero.get("visual_may_drift", "Minor pose and expression"))
    ledger = paths.visual_ledger.read_text(encoding="utf-8")
    entity_separator = "| --- | --- | --- | --- |"
    entity_row = (
        f"| {pipe_safe(hero['name'])} | {pipe_safe(description)} | "
        f"{pipe_safe(must_preserve)} | {pipe_safe(may_drift)} |"
    )
    ledger = ledger.replace(
        entity_separator,
        f"{entity_separator}\n{entity_row}",
        1,
    )
    paths.visual_ledger.write_text(
        ledger,
        encoding="utf-8",
        newline="\n",
    )

    bible = paths.visual_bible.read_text(encoding="utf-8")
    character_separator = "| --- | --- | --- | --- | --- |"
    character_row = (
        f"| {pipe_safe(hero['name'])} | {pipe_safe(description)} | "
        f"{pipe_safe(str(hero.get('visual_clothing', '')))} | "
        f"{pipe_safe(str(hero.get('visual_gear', '')))} | "
        f"{pipe_safe(str(hero.get('visual_colors', '')))} |"
    )
    bible = bible.replace(
        character_separator,
        f"{character_separator}\n{character_row}",
        1,
    )
    paths.visual_bible.write_text(
        bible,
        encoding="utf-8",
        newline="\n",
    )

    location = str(opening.get("location", "")).strip()
    if location:
        ledger = paths.visual_ledger.read_text(encoding="utf-8")
        location_separator = "| --- | --- | --- | --- |"
        location_row = (
            f"| {pipe_safe(location)} | To establish in the first image | "
            "Opening scene | Preserve player-known spatial relationships |"
        )
        second_separator_index = ledger.find(
            location_separator,
            ledger.find(location_separator) + len(location_separator),
        )
        third_separator_index = ledger.find(
            location_separator,
            second_separator_index + len(location_separator),
        )
        if third_separator_index >= 0:
            insert_at = third_separator_index + len(location_separator)
            ledger = (
                ledger[:insert_at] + "\n" + location_row + ledger[insert_at:]
            )
            paths.visual_ledger.write_text(
                ledger,
                encoding="utf-8",
                newline="\n",
            )


def pipe_safe(value: str) -> str:
    return value.replace("|", "/").replace("\n", " ").strip()


def markdown_bullets(values: object, empty_value: str = "None yet.") -> str:
    if not isinstance(values, list) or not values:
        return f"- {empty_value}"
    return "\n".join(f"- {value}" for value in values)


def markdown_numbered(
    values: object,
    fallback_action: str = "Attempt any plausible action.",
) -> str:
    if not isinstance(values, list) or not values:
        return f"1. {fallback_action}"
    return "\n".join(
        f"{index}. {value}" for index, value in enumerate(values, start=1)
    )


def required_mapping(payload: dict, key: str) -> dict:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object.")
    return value


def labels_for(language: str) -> dict[str, str]:
    return PLAYER_LABELS.get(language.casefold(), PLAYER_LABELS["en"])


def required_text(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string.")
    return value.strip()


def positive_int(value: object, label: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise ValueError(f"{label} must be positive.")
    return parsed


def nonnegative_int(value: object, label: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{label} cannot be negative.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a playable Questforge campaign from one spec."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    return parser


def main(arguments: Iterable[str] | None = None) -> int:
    parsed_arguments = build_parser().parse_args(arguments)
    spec = json.loads(parsed_arguments.spec.read_text(encoding="utf-8"))
    campaign_root = create_quick_start(
        parsed_arguments.workspace_root,
        spec,
    )
    print(json.dumps({"campaign_root": str(campaign_root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
