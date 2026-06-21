"""Structured player-facing game state for Codex Questforge."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

STATE_VERSION = 1
STATE_FILENAME = "game-state.json"
CHECKPOINTS_DIR = "checkpoints"
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
PRICE_PATTERN = re.compile(
    r"^\s*(?P<amount>\d+(?:\.\d+)?)\s*(?P<coin>cp|sp|ep|gp|pp)\s*$",
    re.IGNORECASE,
)

COIN_VALUES_CP = {
    "cp": 1,
    "sp": 10,
    "ep": 50,
    "gp": 100,
    "pp": 1000,
}

LEVEL_XP_THRESHOLDS = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
    6: 14000,
    7: 23000,
    8: 34000,
    9: 48000,
    10: 64000,
    11: 85000,
    12: 100000,
    13: 120000,
    14: 140000,
    15: 165000,
    16: 195000,
    17: 225000,
    18: 265000,
    19: 305000,
    20: 355000,
}

DEFAULT_ABILITIES = {
    "strength": 10,
    "dexterity": 10,
    "constitution": 10,
    "intelligence": 10,
    "wisdom": 10,
    "charisma": 10,
}

EQUIPMENT_SLOTS = [
    "armor",
    "main_hand",
    "off_hand",
    "ranged",
    "cloak",
    "head",
    "hands",
    "feet",
    "ring_1",
    "ring_2",
    "amulet",
]


@dataclass(frozen=True)
class OperationResult:
    """Small structured result for CLI and tests."""

    ok: bool
    message: str


def slugify(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = SLUG_PATTERN.sub("-", ascii_value.strip().lower()).strip("-")
    return slug or "entry"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def state_path(campaign_root: Path) -> Path:
    return campaign_root / STATE_FILENAME


def checkpoints_dir(campaign_root: Path) -> Path:
    return campaign_root / CHECKPOINTS_DIR


def new_state(campaign_name: str = "") -> dict:
    return {
        "version": STATE_VERSION,
        "campaign": campaign_name,
        "updated_at": utc_now(),
        "table_mode": {
            "death": "heroic",
            "rollback": "checkpoint",
            "combat": "turn-based",
        },
        "active_character": "",
        "party": [],
        "characters": {},
        "combat": {
            "active": False,
            "name": "",
            "round": 0,
            "current_turn_index": 0,
            "turn_order": [],
            "combatants": {},
            "tactical_scene": empty_tactical_scene(),
            "log": [],
        },
        "shops": {},
        "checkpoints": [],
        "log": [],
    }


def empty_tactical_scene() -> dict:
    return {
        "summary": "",
        "range_bands": [],
        "terrain": [],
        "hazards": [],
        "interactables": [],
        "visual_prompt_hint": "",
    }


def load_state(campaign_root: Path) -> dict:
    path = state_path(campaign_root)
    if not path.exists():
        return new_state(campaign_root.name)
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(campaign_root: Path, state: dict) -> None:
    path = state_path(campaign_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = utc_now()
    path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def initialize_state(
    campaign_root: Path,
    campaign_name: str = "",
    overwrite: bool = False,
) -> dict:
    path = state_path(campaign_root)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Game state already exists: {path}")
    campaign_root.mkdir(parents=True, exist_ok=True)
    checkpoints_dir(campaign_root).mkdir(parents=True, exist_ok=True)
    state = new_state(campaign_name or campaign_root.name)
    save_state(campaign_root, state)
    return state


def default_character(
    name: str,
    class_name: str = "",
    ancestry: str = "",
    level: int = 1,
    xp: int = 0,
    max_hp: int = 10,
    armor_class: int = 10,
    hit_die: str = "d8",
) -> dict:
    if level < 1 or level > 20:
        raise ValueError("Level must be between 1 and 20.")
    if max_hp <= 0:
        raise ValueError("Max HP must be positive.")
    return {
        "name": name,
        "ancestry": ancestry,
        "class": class_name,
        "background": "",
        "level": level,
        "xp": xp,
        "proficiency_bonus": proficiency_bonus(level),
        "abilities": deepcopy(DEFAULT_ABILITIES),
        "skill_modifiers": {},
        "armor_class": armor_class,
        "max_hp": max_hp,
        "current_hp": max_hp,
        "temporary_hp": 0,
        "speed": 30,
        "initiative_modifier": 0,
        "hit_dice": {
            "die": hit_die,
            "total": level,
            "remaining": level,
        },
        "death_saves": {
            "successes": 0,
            "failures": 0,
            "stable": False,
            "dead": False,
        },
        "currency": {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0},
        "inventory": [],
        "equipment": {slot: "" for slot in EQUIPMENT_SLOTS},
        "resources": {
            "spell_slots": {},
            "limited_uses": {},
        },
        "spells": {
            "cantrips": [],
            "known": [],
            "prepared": [],
        },
        "conditions": [],
        "advancement": advancement_state(level, xp),
        "features": [],
        "notes": [],
    }


def proficiency_bonus(level: int) -> int:
    return 2 + ((level - 1) // 4)


def advancement_state(level: int, xp: int) -> dict:
    available_level = level_for_xp(xp)
    next_level = min(level + 1, 20)
    return {
        "available_level": available_level,
        "pending_level_up": available_level > level,
        "next_level_xp": LEVEL_XP_THRESHOLDS.get(next_level),
    }


def level_for_xp(xp: int) -> int:
    if xp < 0:
        raise ValueError("XP cannot be negative.")
    level = 1
    for candidate, threshold in LEVEL_XP_THRESHOLDS.items():
        if xp >= threshold:
            level = candidate
    return level


def add_character(state: dict, character: dict) -> OperationResult:
    name = character["name"].strip()
    if not name:
        raise ValueError("Character name is required.")
    if name in state["characters"]:
        raise ValueError(f"Character already exists: {name}")
    state["characters"][name] = character
    if name not in state["party"]:
        state["party"].append(name)
    if not state.get("active_character"):
        state["active_character"] = name
    append_log(state, f"Added character {name}.")
    return OperationResult(True, f"Added character: {name}")


def get_character(state: dict, name: str = "") -> dict:
    character_name = resolve_character_name(state, name)
    return state["characters"][character_name]


def resolve_character_name(state: dict, name: str = "") -> str:
    if not name:
        name = state.get("active_character", "")
    if name in state["characters"]:
        return name
    lowered = name.lower()
    matches = [
        character_name
        for character_name in state["characters"]
        if character_name.lower() == lowered
    ]
    if len(matches) == 1:
        return matches[0]
    if not state["characters"]:
        raise ValueError("No characters exist in game state.")
    raise KeyError(f"Unknown character: {name}")


def append_log(state: dict, message: str) -> None:
    state.setdefault("log", []).append({"at": utc_now(), "message": message})


def add_item(
    state: dict,
    character_name: str,
    name: str,
    quantity: int = 1,
    location: str = "backpack",
    slot: str = "",
    mechanical_effect: str = "",
    story_significance: str = "",
    value: str = "",
) -> dict:
    if quantity < 1:
        raise ValueError("Quantity must be positive.")
    if not name.strip():
        raise ValueError("Item name is required.")
    character = get_character(state, character_name)
    item = {
        "id": unique_item_id(character, name),
        "name": name.strip(),
        "quantity": quantity,
        "location": location,
        "equipped_slot": slot,
        "mechanical_effect": mechanical_effect,
        "story_significance": story_significance,
        "value": value,
        "attunement": "",
        "notes": "",
    }
    character["inventory"].append(item)
    if location == "equipped" and slot:
        equip_item(state, character["name"], item["id"], slot)
    append_log(state, f"{character['name']} gained item {item['name']}.")
    return item


def unique_item_id(character: dict, name: str) -> str:
    base = slugify(name)
    existing = {item["id"] for item in character["inventory"]}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def find_item(character: dict, query: str) -> dict:
    if not query.strip():
        raise ValueError("Item query is required.")
    for item in character["inventory"]:
        if item["id"] == query:
            return item
    lowered = query.lower()
    exact_matches = [
        item
        for item in character["inventory"]
        if item["name"].lower() == lowered
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    partial_matches = [
        item
        for item in character["inventory"]
        if lowered in item["name"].lower()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if partial_matches:
        raise ValueError(f"Ambiguous item query: {query}")
    raise KeyError(f"Unknown item: {query}")


def equip_item(
    state: dict,
    character_name: str,
    item_query: str,
    slot: str,
) -> OperationResult:
    if slot not in EQUIPMENT_SLOTS:
        raise ValueError(
            "Unsupported equipment slot. Use one of: "
            + ", ".join(EQUIPMENT_SLOTS)
        )
    character = get_character(state, character_name)
    item = find_item(character, item_query)
    previous_item_id = character["equipment"].get(slot, "")
    if previous_item_id:
        previous = find_item(character, previous_item_id)
        previous["location"] = "backpack"
        previous["equipped_slot"] = ""
    item["location"] = "equipped"
    item["equipped_slot"] = slot
    character["equipment"][slot] = item["id"]
    append_log(
        state, f"{character['name']} equipped {item['name']} in {slot}."
    )
    return OperationResult(True, f"Equipped {item['name']} in {slot}.")


def move_item(
    state: dict,
    character_name: str,
    item_query: str,
    location: str,
) -> OperationResult:
    character = get_character(state, character_name)
    item = find_item(character, item_query)
    if item.get("equipped_slot"):
        character["equipment"][item["equipped_slot"]] = ""
    item["location"] = location
    item["equipped_slot"] = ""
    append_log(
        state, f"{character['name']} moved {item['name']} to {location}."
    )
    return OperationResult(True, f"Moved {item['name']} to {location}.")


def adjust_currency(
    state: dict,
    character_name: str,
    cp: int = 0,
    sp: int = 0,
    ep: int = 0,
    gp: int = 0,
    pp: int = 0,
) -> OperationResult:
    character = get_character(state, character_name)
    currency = character["currency"]
    delta = {"cp": cp, "sp": sp, "ep": ep, "gp": gp, "pp": pp}
    for coin, amount in delta.items():
        currency[coin] = int(currency.get(coin, 0)) + amount
        if currency[coin] < 0:
            raise ValueError(f"Currency cannot go negative: {coin}")
    append_log(state, f"Adjusted currency for {character['name']}.")
    return OperationResult(True, f"Adjusted currency for {character['name']}.")


def currency_to_cp(currency: dict) -> int:
    return sum(
        int(currency.get(coin, 0)) * value
        for coin, value in COIN_VALUES_CP.items()
    )


def set_currency_from_cp(currency: dict, total_cp: int) -> None:
    if total_cp < 0:
        raise ValueError("Currency cannot go negative.")
    remaining = total_cp
    for coin in ("pp", "gp", "ep", "sp", "cp"):
        value = COIN_VALUES_CP[coin]
        currency[coin], remaining = divmod(remaining, value)


def parse_price_to_cp(price: str) -> int:
    amount, coin = parse_price(price)
    return int(amount * COIN_VALUES_CP[coin])


def parse_price(price: str) -> tuple[float, str]:
    match = PRICE_PATTERN.match(price)
    if not match:
        raise ValueError("Price must look like 5gp, 12sp, or 50cp.")
    amount = float(match.group("amount"))
    coin = match.group("coin").lower()
    return amount, coin


def add_shop_item(
    state: dict,
    shop_id: str,
    shop_name: str,
    merchant: str,
    item_name: str,
    price: str,
    stock: int = 1,
    mechanical_effect: str = "",
) -> dict:
    if stock < 0:
        raise ValueError("Stock cannot be negative.")
    shop_key = slugify(shop_id or shop_name)
    shop = state.setdefault("shops", {}).setdefault(
        shop_key,
        {
            "id": shop_key,
            "name": shop_name or shop_key,
            "merchant": merchant,
            "items": {},
        },
    )
    item_id = unique_shop_item_id(shop, item_name)
    shop["items"][item_id] = {
        "id": item_id,
        "name": item_name,
        "price": price,
        "price_cp": parse_price_to_cp(price),
        "stock": stock,
        "mechanical_effect": mechanical_effect,
    }
    append_log(state, f"Added shop item {item_name} to {shop['name']}.")
    return shop["items"][item_id]


def unique_shop_item_id(shop: dict, item_name: str) -> str:
    base = slugify(item_name)
    existing = set(shop.get("items", {}))
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def buy_item(
    state: dict,
    character_name: str,
    shop_id: str,
    item_query: str,
) -> OperationResult:
    character = get_character(state, character_name)
    shop = state.get("shops", {}).get(slugify(shop_id))
    if not shop:
        raise KeyError(f"Unknown shop: {shop_id}")
    item = find_shop_item(shop, item_query)
    if item["stock"] == 0:
        raise ValueError(f"Item is out of stock: {item['name']}")
    current_cp = currency_to_cp(character["currency"])
    if current_cp < item["price_cp"]:
        raise ValueError(
            f"Not enough money for {item['name']} ({item['price']})."
        )
    price_amount, price_coin = parse_price(item["price"])
    if price_amount.is_integer() and character["currency"].get(
        price_coin, 0
    ) >= int(price_amount):
        character["currency"][price_coin] -= int(price_amount)
    else:
        set_currency_from_cp(
            character["currency"], current_cp - item["price_cp"]
        )
    item["stock"] -= 1
    add_item(
        state,
        character["name"],
        item["name"],
        mechanical_effect=item.get("mechanical_effect", ""),
        value=item["price"],
    )
    append_log(state, f"{character['name']} bought {item['name']}.")
    return OperationResult(True, f"Bought {item['name']} for {item['price']}.")


def find_shop_item(shop: dict, query: str) -> dict:
    if query in shop.get("items", {}):
        return shop["items"][query]
    lowered = query.lower()
    matches = [
        item
        for item in shop.get("items", {}).values()
        if item["name"].lower() == lowered
    ]
    if len(matches) == 1:
        return matches[0]
    matches = [
        item
        for item in shop.get("items", {}).values()
        if lowered in item["name"].lower()
    ]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError(f"Ambiguous shop item: {query}")
    raise KeyError(f"Unknown shop item: {query}")


def award_xp(
    state: dict, character_name: str, amount: int, reason: str
) -> OperationResult:
    if amount <= 0:
        raise ValueError("XP amount must be positive.")
    character = get_character(state, character_name)
    character["xp"] += amount
    character["advancement"] = advancement_state(
        character["level"], character["xp"]
    )
    append_log(state, f"{character['name']} gained {amount} XP: {reason}")
    return OperationResult(
        True, f"Awarded {amount} XP to {character['name']}."
    )


def level_up_options(state: dict, character_name: str) -> dict:
    character = get_character(state, character_name)
    advancement = advancement_state(character["level"], character["xp"])
    character["advancement"] = advancement
    target_level = min(character["level"] + 1, advancement["available_level"])
    choices = [
        "Roll or choose HP increase using the class hit die and Constitution modifier.",
        "Update proficiency bonus if the new level changes it.",
        "Consult local SRD rules for class features, subclass choices, and spellcasting changes.",
        "Record every chosen feature in game-state.json before play continues.",
    ]
    class_name = character.get("class", "").lower()
    if class_name in {
        "wizard",
        "cleric",
        "druid",
        "sorcerer",
        "bard",
        "warlock",
        "paladin",
        "ranger",
    }:
        choices.append(
            "Review known/prepared spells and spell slots before the next scene."
        )
    if class_name in {"fighter", "rogue", "barbarian", "monk"}:
        choices.append(
            "Review weapon tactics, limited-use features, and defensive options."
        )
    return {
        "character": character["name"],
        "current_level": character["level"],
        "xp": character["xp"],
        "available_level": advancement["available_level"],
        "pending_level_up": advancement["pending_level_up"],
        "target_level": target_level,
        "choices": choices,
    }


def apply_level_up(
    state: dict,
    character_name: str,
    new_level: int,
    hp_increase: int,
    features: list[str] | None = None,
    force: bool = False,
) -> OperationResult:
    if new_level < 2 or new_level > 20:
        raise ValueError("New level must be between 2 and 20.")
    if hp_increase < 1:
        raise ValueError("HP increase must be positive.")
    character = get_character(state, character_name)
    available_level = level_for_xp(character["xp"])
    if not force and new_level > available_level:
        raise ValueError(
            f"{character['name']} has XP for level {available_level}, "
            f"not level {new_level}."
        )
    if new_level <= character["level"]:
        raise ValueError("New level must be higher than current level.")
    character["level"] = new_level
    character["proficiency_bonus"] = proficiency_bonus(new_level)
    character["max_hp"] += hp_increase
    character["current_hp"] += hp_increase
    character["hit_dice"]["total"] = new_level
    character["hit_dice"]["remaining"] = min(
        new_level,
        character["hit_dice"].get("remaining", 0) + 1,
    )
    for feature in features or []:
        if feature.strip():
            character["features"].append(feature.strip())
    character["advancement"] = advancement_state(new_level, character["xp"])
    append_log(state, f"{character['name']} reached level {new_level}.")
    return OperationResult(
        True, f"{character['name']} reached level {new_level}."
    )


def set_spell_slots(
    state: dict,
    character_name: str,
    slot_level: int,
    maximum: int,
) -> OperationResult:
    if slot_level < 1 or slot_level > 9:
        raise ValueError("Spell slot level must be between 1 and 9.")
    if maximum < 0:
        raise ValueError("Spell slot maximum cannot be negative.")
    character = get_character(state, character_name)
    slots = character["resources"].setdefault("spell_slots", {})
    existing_used = slots.get(str(slot_level), {}).get("used", 0)
    slots[str(slot_level)] = {
        "max": maximum,
        "used": min(existing_used, maximum),
    }
    append_log(
        state, f"Set level {slot_level} spell slots for {character['name']}."
    )
    return OperationResult(
        True, f"Set level {slot_level} spell slots to {maximum}."
    )


def spend_spell_slot(
    state: dict,
    character_name: str,
    slot_level: int,
) -> OperationResult:
    character = get_character(state, character_name)
    slots = character["resources"].setdefault("spell_slots", {})
    slot = slots.get(str(slot_level))
    if not slot:
        raise ValueError(f"No level {slot_level} spell slots are available.")
    if slot["used"] >= slot["max"]:
        raise ValueError(f"All level {slot_level} spell slots are spent.")
    slot["used"] += 1
    append_log(
        state, f"{character['name']} spent a level {slot_level} spell slot."
    )
    return OperationResult(True, f"Spent one level {slot_level} spell slot.")


def add_condition(
    state: dict,
    character_name: str,
    name: str,
    effect: str = "",
    ends_on: str = "",
) -> OperationResult:
    character = get_character(state, character_name)
    condition = {
        "name": name,
        "effect": effect,
        "ends_on": ends_on,
    }
    character["conditions"].append(condition)
    append_log(state, f"{character['name']} gained condition {name}.")
    return OperationResult(True, f"Added condition: {name}")


def remove_condition(
    state: dict,
    character_name: str,
    name: str,
) -> OperationResult:
    character = get_character(state, character_name)
    before = len(character["conditions"])
    character["conditions"] = [
        condition
        for condition in character["conditions"]
        if condition["name"].lower() != name.lower()
    ]
    if len(character["conditions"]) == before:
        raise KeyError(f"Unknown condition: {name}")
    append_log(state, f"{character['name']} removed condition {name}.")
    return OperationResult(True, f"Removed condition: {name}")


def apply_damage(
    state: dict,
    character_name: str,
    amount: int,
    damage_type: str = "",
) -> OperationResult:
    if amount < 0:
        raise ValueError("Damage cannot be negative.")
    character = get_character(state, character_name)
    remaining = amount
    temporary_hp = int(character.get("temporary_hp", 0))
    absorbed = min(temporary_hp, remaining)
    character["temporary_hp"] = temporary_hp - absorbed
    remaining -= absorbed
    character["current_hp"] = max(0, int(character["current_hp"]) - remaining)
    sync_combatant_from_character(state, character)
    if character["current_hp"] == 0:
        handle_zero_hp(state, character)
    label = f" {damage_type}" if damage_type else ""
    append_log(state, f"{character['name']} took {amount}{label} damage.")
    return OperationResult(True, f"{character['name']} took {amount} damage.")


def heal(state: dict, character_name: str, amount: int) -> OperationResult:
    if amount < 0:
        raise ValueError("Healing cannot be negative.")
    character = get_character(state, character_name)
    if character["death_saves"].get("dead"):
        raise ValueError("Dead characters need a table ruling before healing.")
    character["current_hp"] = min(
        int(character["max_hp"]),
        int(character["current_hp"]) + amount,
    )
    if character["current_hp"] > 0:
        reset_death_saves(character)
    sync_combatant_from_character(state, character)
    append_log(state, f"{character['name']} healed {amount} HP.")
    return OperationResult(True, f"{character['name']} healed {amount} HP.")


def handle_zero_hp(state: dict, character: dict) -> None:
    death_mode = state.get("table_mode", {}).get("death", "heroic")
    if death_mode == "narrative":
        character["death_saves"] = {
            "successes": 3,
            "failures": 0,
            "stable": True,
            "dead": False,
        }
        add_or_update_condition(
            character,
            "Defeated",
            "Unable to keep fighting; fate is resolved narratively.",
            "scene_end",
        )
        return
    character["death_saves"] = {
        "successes": 0,
        "failures": 0,
        "stable": False,
        "dead": False,
    }
    add_or_update_condition(
        character,
        "Unconscious",
        "At 0 HP and making death saves unless stabilized.",
        "healed_or_stabilized",
    )


def add_or_update_condition(
    character: dict,
    name: str,
    effect: str,
    ends_on: str,
) -> None:
    for condition in character["conditions"]:
        if condition["name"].lower() == name.lower():
            condition["effect"] = effect
            condition["ends_on"] = ends_on
            return
    character["conditions"].append(
        {"name": name, "effect": effect, "ends_on": ends_on}
    )


def reset_death_saves(character: dict) -> None:
    character["death_saves"] = {
        "successes": 0,
        "failures": 0,
        "stable": False,
        "dead": False,
    }
    character["conditions"] = [
        condition
        for condition in character["conditions"]
        if condition["name"].lower() not in {"unconscious", "defeated"}
    ]


def record_death_save(
    state: dict,
    character_name: str,
    result: str,
) -> OperationResult:
    character = get_character(state, character_name)
    saves = character["death_saves"]
    if character["current_hp"] > 0:
        raise ValueError("Death saves only apply at 0 HP.")
    if saves.get("dead"):
        raise ValueError("Character is already dead.")
    if result == "critical-success":
        character["current_hp"] = 1
        reset_death_saves(character)
        message = f"{character['name']} returns to 1 HP."
    elif result == "success":
        saves["successes"] += 1
        message = f"{character['name']} marks one death save success."
    elif result == "failure":
        saves["failures"] += 1
        message = f"{character['name']} marks one death save failure."
    elif result == "critical-failure":
        saves["failures"] += 2
        message = f"{character['name']} marks two death save failures."
    else:
        raise ValueError(
            "Death save result must be success, failure, "
            "critical-success, or critical-failure."
        )
    if saves.get("successes", 0) >= 3:
        saves["stable"] = True
        add_or_update_condition(
            character,
            "Stable",
            "At 0 HP, unconscious, no longer making death saves.",
            "healed",
        )
    if saves.get("failures", 0) >= 3:
        saves["dead"] = True
        add_or_update_condition(
            character,
            "Dead",
            "Death is final unless the table uses a resurrection or rollback ruling.",
            "table_ruling",
        )
    sync_combatant_from_character(state, character)
    append_log(state, message)
    return OperationResult(True, message)


def rest(
    state: dict,
    character_name: str,
    kind: str,
) -> OperationResult:
    if kind not in {"short", "long"}:
        raise ValueError("Rest kind must be short or long.")
    character = get_character(state, character_name)
    if kind == "long":
        if not character["death_saves"].get("dead"):
            character["current_hp"] = character["max_hp"]
            character["temporary_hp"] = 0
            reset_death_saves(character)
        recover_spell_slots(character)
        recover_hit_dice(character)
        recover_limited_uses(character, "long_rest")
        clear_rest_conditions(character, {"long_rest", "short_or_long_rest"})
    else:
        recover_limited_uses(character, "short_rest")
        clear_rest_conditions(character, {"short_rest", "short_or_long_rest"})
    sync_combatant_from_character(state, character)
    append_log(state, f"{character['name']} completed a {kind} rest.")
    return OperationResult(
        True, f"Completed {kind} rest for {character['name']}."
    )


def recover_spell_slots(character: dict) -> None:
    for slot in character["resources"].get("spell_slots", {}).values():
        slot["used"] = 0


def recover_hit_dice(character: dict) -> None:
    hit_dice = character["hit_dice"]
    total = int(hit_dice.get("total", character["level"]))
    remaining = int(hit_dice.get("remaining", 0))
    hit_dice["remaining"] = min(total, remaining + max(1, total // 2))


def recover_limited_uses(character: dict, recovery: str) -> None:
    for resource in character["resources"].get("limited_uses", {}).values():
        if resource.get("recovery") in {recovery, "short_or_long_rest"}:
            resource["used"] = 0


def clear_rest_conditions(character: dict, rest_markers: set[str]) -> None:
    character["conditions"] = [
        condition
        for condition in character["conditions"]
        if condition.get("ends_on") not in rest_markers
    ]


def spend_hit_die(
    state: dict,
    character_name: str,
    healing: int,
) -> OperationResult:
    character = get_character(state, character_name)
    hit_dice = character["hit_dice"]
    if hit_dice.get("remaining", 0) <= 0:
        raise ValueError("No hit dice remain.")
    hit_dice["remaining"] -= 1
    heal(state, character["name"], healing)
    append_log(state, f"{character['name']} spent one hit die.")
    return OperationResult(True, f"Spent one hit die and healed {healing}.")


def parse_combatant(text: str) -> dict:
    parts = [part.strip() for part in text.split(":")]
    if len(parts) < 2:
        raise ValueError(
            "Combatants must look like name:initiative[:hp][:ac][:side]."
        )
    name = parts[0]
    initiative = int(parts[1])
    hp = int(parts[2]) if len(parts) > 2 and parts[2] else 1
    armor_class = int(parts[3]) if len(parts) > 3 and parts[3] else 10
    side = parts[4] if len(parts) > 4 and parts[4] else "enemy"
    return {
        "name": name,
        "initiative": initiative,
        "max_hp": hp,
        "current_hp": hp,
        "armor_class": armor_class,
        "side": side,
        "conditions": [],
        "defeated": False,
    }


def start_combat(
    state: dict,
    name: str,
    combatants: list[str],
) -> OperationResult:
    parsed_combatants = [parse_combatant(value) for value in combatants]
    for combatant in parsed_combatants:
        if combatant["name"] in state.get("characters", {}):
            character = state["characters"][combatant["name"]]
            combatant["max_hp"] = character["max_hp"]
            combatant["current_hp"] = character["current_hp"]
            combatant["armor_class"] = character["armor_class"]
            combatant["side"] = "party"
            combatant["conditions"] = deepcopy(character["conditions"])
    parsed_combatants.sort(key=lambda item: item["initiative"], reverse=True)
    state["combat"] = {
        "active": True,
        "name": name or "Combat",
        "round": 1,
        "current_turn_index": 0,
        "turn_order": [combatant["name"] for combatant in parsed_combatants],
        "combatants": {
            combatant["name"]: combatant for combatant in parsed_combatants
        },
        "tactical_scene": empty_tactical_scene(),
        "log": [f"Combat started: {name or 'Combat'}."],
    }
    append_log(state, f"Combat started: {name or 'Combat'}.")
    return OperationResult(True, f"Started combat: {name or 'Combat'}.")


def sync_combatant_from_character(state: dict, character: dict) -> None:
    combat = state.get("combat", {})
    if not combat.get("active"):
        return
    combatant = combat.get("combatants", {}).get(character["name"])
    if not combatant:
        return
    combatant["current_hp"] = character["current_hp"]
    combatant["max_hp"] = character["max_hp"]
    combatant["armor_class"] = character["armor_class"]
    combatant["conditions"] = deepcopy(character["conditions"])
    combatant["defeated"] = character["current_hp"] == 0


def end_turn(state: dict) -> OperationResult:
    combat = state.get("combat", {})
    if not combat.get("active"):
        raise ValueError("No active combat.")
    order = combat["turn_order"]
    if not order:
        raise ValueError("Combat has no turn order.")
    for _ in range(len(order)):
        combat["current_turn_index"] = (
            int(combat["current_turn_index"]) + 1
        ) % len(order)
        if combat["current_turn_index"] == 0:
            combat["round"] += 1
        active_name = order[combat["current_turn_index"]]
        if not combat["combatants"][active_name].get("defeated"):
            break
    active_name = order[combat["current_turn_index"]]
    combat["log"].append(f"Turn passes to {active_name}.")
    return OperationResult(
        True,
        f"Round {combat['round']}, turn: {active_name}.",
    )


def record_combat_action(
    state: dict,
    actor: str,
    summary: str,
    target: str = "",
    damage: int = 0,
) -> OperationResult:
    combat = state.get("combat", {})
    if not combat.get("active"):
        raise ValueError("No active combat.")
    if actor not in combat["combatants"]:
        raise KeyError(f"Unknown combatant: {actor}")
    if damage and target:
        apply_damage_to_combatant(state, target, damage)
    entry = summary.strip() or f"{actor} acts."
    combat["log"].append(entry)
    append_log(state, f"Combat action: {entry}")
    return OperationResult(True, entry)


def apply_damage_to_combatant(state: dict, target: str, damage: int) -> None:
    combat = state.get("combat", {})
    combatant = combat.get("combatants", {}).get(target)
    if not combatant:
        raise KeyError(f"Unknown combatant: {target}")
    if target in state.get("characters", {}):
        apply_damage(state, target, damage)
        return
    combatant["current_hp"] = max(0, int(combatant["current_hp"]) - damage)
    combatant["defeated"] = combatant["current_hp"] == 0


def end_combat(state: dict) -> OperationResult:
    combat = state.get("combat", {})
    if not combat.get("active"):
        raise ValueError("No active combat.")
    combat["active"] = False
    combat["log"].append("Combat ended.")
    append_log(state, "Combat ended.")
    return OperationResult(True, "Combat ended.")


def set_tactical_scene(
    state: dict,
    summary: str,
    range_bands: list[str],
    terrain: list[str],
    hazards: list[str],
    interactables: list[str],
    visual_prompt_hint: str = "",
) -> OperationResult:
    combat = state.setdefault("combat", {})
    tactical_scene = {
        "summary": summary,
        "range_bands": range_bands,
        "terrain": terrain,
        "hazards": hazards,
        "interactables": interactables,
        "visual_prompt_hint": visual_prompt_hint,
    }
    combat["tactical_scene"] = tactical_scene
    append_log(state, "Updated tactical scene.")
    return OperationResult(True, "Updated tactical scene.")


def create_checkpoint(
    campaign_root: Path,
    state: dict,
    label: str,
    note: str = "",
    checkpoint_id: str = "",
) -> dict:
    if not label.strip():
        raise ValueError("Checkpoint label is required.")
    checkpoint_id = (
        checkpoint_id or f"{slugify(label)}-{utc_now().replace(':', '')}"
    )
    checkpoint_path = checkpoints_dir(campaign_root) / f"{checkpoint_id}.json"
    if checkpoint_path.exists():
        raise FileExistsError(f"Checkpoint already exists: {checkpoint_path}")
    metadata = {
        "id": checkpoint_id,
        "label": label,
        "note": note,
        "created_at": utc_now(),
        "path": f"{CHECKPOINTS_DIR}/{checkpoint_id}.json",
    }
    state.setdefault("checkpoints", []).append(metadata)
    save_state(campaign_root, state)
    checkpoints_dir(campaign_root).mkdir(parents=True, exist_ok=True)
    shutil.copy2(state_path(campaign_root), checkpoint_path)
    return metadata


def restore_checkpoint(
    campaign_root: Path, checkpoint_id: str
) -> OperationResult:
    checkpoint_path = checkpoints_dir(campaign_root) / f"{checkpoint_id}.json"
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint_path}")
    state = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    append_log(state, f"Restored checkpoint {checkpoint_id}.")
    save_state(campaign_root, state)
    return OperationResult(True, f"Restored checkpoint: {checkpoint_id}")


def format_status(state: dict) -> str:
    lines = ["# Questforge Game State", ""]
    if state.get("campaign"):
        lines.append(f"- Campaign: {state['campaign']}")
    if state.get("active_character"):
        lines.append(f"- Active character: {state['active_character']}")
    lines.append("")
    lines.extend(format_character_table(state))
    lines.append("")
    active_name = state.get("active_character")
    if active_name and active_name in state.get("characters", {}):
        lines.extend(format_character_detail(state["characters"][active_name]))
        lines.append("")
    if state.get("combat", {}).get("active"):
        lines.extend(format_combat(state["combat"]))
        lines.append("")
    if state.get("shops"):
        lines.extend(format_shops(state))
        lines.append("")
    if state.get("checkpoints"):
        lines.append("## Checkpoints")
        for checkpoint in state["checkpoints"][-5:]:
            lines.append(f"- `{checkpoint['id']}`: {checkpoint['label']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_character_table(state: dict) -> list[str]:
    lines = [
        "## Party",
        "",
        "| Character | Level | XP | HP | AC | Conditions |",
        "| --- | ---: | ---: | --- | ---: | --- |",
    ]
    for name in state.get("party", []):
        character = state["characters"].get(name)
        if not character:
            continue
        conditions = ", ".join(
            condition["name"] for condition in character.get("conditions", [])
        )
        lines.append(
            f"| {name} | {character['level']} | {character['xp']} | "
            f"{character['current_hp']}/{character['max_hp']} | "
            f"{character['armor_class']} | {conditions or '-'} |"
        )
    return lines


def format_character_detail(character: dict) -> list[str]:
    lines = [f"## {character['name']}", ""]
    lines.append("### Equipment")
    for slot in EQUIPMENT_SLOTS:
        item_id = character["equipment"].get(slot)
        if item_id:
            item = find_item(character, item_id)
            lines.append(f"- {slot}: {item['name']}")
    if all(not character["equipment"].get(slot) for slot in EQUIPMENT_SLOTS):
        lines.append("- Nothing equipped.")
    lines.extend(["", "### Inventory"])
    if not character["inventory"]:
        lines.append("- Empty.")
    for item in character["inventory"]:
        location = item["location"]
        if item.get("equipped_slot"):
            location = f"equipped: {item['equipped_slot']}"
        lines.append(
            f"- `{item['id']}` {item['name']} x{item['quantity']} "
            f"({location})"
        )
    lines.extend(["", "### Resources"])
    spell_slots = character["resources"].get("spell_slots", {})
    if spell_slots:
        for level, slot in sorted(
            spell_slots.items(), key=lambda item: int(item[0])
        ):
            remaining = slot["max"] - slot["used"]
            lines.append(
                f"- Spell slots L{level}: {remaining}/{slot['max']} available"
            )
    else:
        lines.append("- No spell slots tracked.")
    hit_dice = character["hit_dice"]
    lines.append(
        f"- Hit dice: {hit_dice['remaining']}/{hit_dice['total']} "
        f"{hit_dice['die']}"
    )
    if character["advancement"].get("pending_level_up"):
        lines.append(
            f"- Level up pending: level "
            f"{character['advancement']['available_level']} available"
        )
    return lines


def format_combat(combat: dict) -> list[str]:
    lines = [
        "## Combat",
        "",
        f"- Name: {combat['name']}",
        f"- Round: {combat['round']}",
    ]
    order = combat.get("turn_order", [])
    if order:
        active = order[combat.get("current_turn_index", 0)]
        lines.append(f"- Current turn: {active}")
    lines.extend(["", "| Combatant | Side | Init | HP | AC | Status |"])
    lines.append("| --- | --- | ---: | --- | ---: | --- |")
    for name in order:
        combatant = combat["combatants"][name]
        status = "defeated" if combatant.get("defeated") else "active"
        lines.append(
            f"| {name} | {combatant['side']} | {combatant['initiative']} | "
            f"{combatant['current_hp']}/{combatant['max_hp']} | "
            f"{combatant['armor_class']} | {status} |"
        )
    scene = combat.get("tactical_scene", {})
    if scene.get("summary"):
        lines.extend(["", "### Tactical Scene", f"- {scene['summary']}"])
    for key, label in (
        ("terrain", "Terrain"),
        ("hazards", "Hazards"),
        ("interactables", "Interactables"),
    ):
        values = scene.get(key, [])
        if values:
            lines.append(f"- {label}: " + "; ".join(values))
    return lines


def format_shops(state: dict) -> list[str]:
    lines = ["## Shops"]
    for shop in state["shops"].values():
        lines.append(f"- {shop['name']} ({shop.get('merchant', 'merchant')})")
        for item in shop.get("items", {}).values():
            lines.append(
                f"  - `{item['id']}` {item['name']}: {item['price']} "
                f"(stock {item['stock']})"
            )
    return lines


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--campaign-root", required=True, type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage structured Questforge player game state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create game-state.json.")
    add_common_arguments(init_parser)
    init_parser.add_argument("--campaign-name", default="")
    init_parser.add_argument("--overwrite", action="store_true")

    status_parser = subparsers.add_parser("status", help="Show game state.")
    add_common_arguments(status_parser)
    status_parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )

    character_parser = subparsers.add_parser("add-character")
    add_common_arguments(character_parser)
    character_parser.add_argument("--name", required=True)
    character_parser.add_argument("--class-name", default="")
    character_parser.add_argument("--ancestry", default="")
    character_parser.add_argument("--level", type=int, default=1)
    character_parser.add_argument("--xp", type=int, default=0)
    character_parser.add_argument("--max-hp", type=int, default=10)
    character_parser.add_argument("--armor-class", type=int, default=10)
    character_parser.add_argument("--hit-die", default="d8")

    item_parser = subparsers.add_parser("add-item")
    add_common_arguments(item_parser)
    item_parser.add_argument("--character", default="")
    item_parser.add_argument("--name", required=True)
    item_parser.add_argument("--quantity", type=int, default=1)
    item_parser.add_argument("--location", default="backpack")
    item_parser.add_argument("--slot", default="")
    item_parser.add_argument("--mechanical-effect", default="")
    item_parser.add_argument("--story-significance", default="")
    item_parser.add_argument("--value", default="")

    equip_parser = subparsers.add_parser("equip")
    add_common_arguments(equip_parser)
    equip_parser.add_argument("--character", default="")
    equip_parser.add_argument("--item", required=True)
    equip_parser.add_argument("--slot", required=True)

    move_parser = subparsers.add_parser("move-item")
    add_common_arguments(move_parser)
    move_parser.add_argument("--character", default="")
    move_parser.add_argument("--item", required=True)
    move_parser.add_argument("--location", required=True)

    money_parser = subparsers.add_parser("adjust-currency")
    add_common_arguments(money_parser)
    money_parser.add_argument("--character", default="")
    for coin in COIN_VALUES_CP:
        money_parser.add_argument(f"--{coin}", type=int, default=0)

    shop_parser = subparsers.add_parser("add-shop-item")
    add_common_arguments(shop_parser)
    shop_parser.add_argument("--shop-id", required=True)
    shop_parser.add_argument("--shop-name", default="")
    shop_parser.add_argument("--merchant", default="")
    shop_parser.add_argument("--item-name", required=True)
    shop_parser.add_argument("--price", required=True)
    shop_parser.add_argument("--stock", type=int, default=1)
    shop_parser.add_argument("--mechanical-effect", default="")

    buy_parser = subparsers.add_parser("buy-item")
    add_common_arguments(buy_parser)
    buy_parser.add_argument("--character", default="")
    buy_parser.add_argument("--shop-id", required=True)
    buy_parser.add_argument("--item", required=True)

    xp_parser = subparsers.add_parser("award-xp")
    add_common_arguments(xp_parser)
    xp_parser.add_argument("--character", default="")
    xp_parser.add_argument("--amount", required=True, type=int)
    xp_parser.add_argument("--reason", required=True)

    level_options_parser = subparsers.add_parser("level-up-options")
    add_common_arguments(level_options_parser)
    level_options_parser.add_argument("--character", default="")
    level_options_parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )

    level_parser = subparsers.add_parser("apply-level-up")
    add_common_arguments(level_parser)
    level_parser.add_argument("--character", default="")
    level_parser.add_argument("--new-level", required=True, type=int)
    level_parser.add_argument("--hp-increase", required=True, type=int)
    level_parser.add_argument("--feature", action="append", default=[])
    level_parser.add_argument("--force", action="store_true")

    slot_parser = subparsers.add_parser("set-spell-slots")
    add_common_arguments(slot_parser)
    slot_parser.add_argument("--character", default="")
    slot_parser.add_argument("--slot-level", required=True, type=int)
    slot_parser.add_argument("--max", required=True, type=int)

    spend_slot_parser = subparsers.add_parser("spend-spell-slot")
    add_common_arguments(spend_slot_parser)
    spend_slot_parser.add_argument("--character", default="")
    spend_slot_parser.add_argument("--slot-level", required=True, type=int)

    condition_parser = subparsers.add_parser("add-condition")
    add_common_arguments(condition_parser)
    condition_parser.add_argument("--character", default="")
    condition_parser.add_argument("--name", required=True)
    condition_parser.add_argument("--effect", default="")
    condition_parser.add_argument("--ends-on", default="")

    remove_condition_parser = subparsers.add_parser("remove-condition")
    add_common_arguments(remove_condition_parser)
    remove_condition_parser.add_argument("--character", default="")
    remove_condition_parser.add_argument("--name", required=True)

    damage_parser = subparsers.add_parser("apply-damage")
    add_common_arguments(damage_parser)
    damage_parser.add_argument("--character", default="")
    damage_parser.add_argument("--amount", required=True, type=int)
    damage_parser.add_argument("--type", default="")

    heal_parser = subparsers.add_parser("heal")
    add_common_arguments(heal_parser)
    heal_parser.add_argument("--character", default="")
    heal_parser.add_argument("--amount", required=True, type=int)

    death_parser = subparsers.add_parser("death-save")
    add_common_arguments(death_parser)
    death_parser.add_argument("--character", default="")
    death_parser.add_argument("--result", required=True)

    rest_parser = subparsers.add_parser("rest")
    add_common_arguments(rest_parser)
    rest_parser.add_argument("--character", default="")
    rest_parser.add_argument(
        "--kind", choices=("short", "long"), required=True
    )

    hit_die_parser = subparsers.add_parser("spend-hit-die")
    add_common_arguments(hit_die_parser)
    hit_die_parser.add_argument("--character", default="")
    hit_die_parser.add_argument("--healing", required=True, type=int)

    combat_parser = subparsers.add_parser("start-combat")
    add_common_arguments(combat_parser)
    combat_parser.add_argument("--name", default="")
    combat_parser.add_argument(
        "--combatant",
        action="append",
        default=[],
        help="name:initiative[:hp][:ac][:side]",
    )

    subparsers.add_parser("end-turn", parents=[campaign_root_parent()])
    subparsers.add_parser("end-combat", parents=[campaign_root_parent()])

    combat_action_parser = subparsers.add_parser("combat-action")
    add_common_arguments(combat_action_parser)
    combat_action_parser.add_argument("--actor", required=True)
    combat_action_parser.add_argument("--summary", required=True)
    combat_action_parser.add_argument("--target", default="")
    combat_action_parser.add_argument("--damage", type=int, default=0)

    tactical_parser = subparsers.add_parser("set-tactical-scene")
    add_common_arguments(tactical_parser)
    tactical_parser.add_argument("--summary", required=True)
    tactical_parser.add_argument("--range-band", action="append", default=[])
    tactical_parser.add_argument("--terrain", action="append", default=[])
    tactical_parser.add_argument("--hazard", action="append", default=[])
    tactical_parser.add_argument("--interactable", action="append", default=[])
    tactical_parser.add_argument("--visual-prompt-hint", default="")

    checkpoint_parser = subparsers.add_parser("checkpoint")
    add_common_arguments(checkpoint_parser)
    checkpoint_parser.add_argument("--label", required=True)
    checkpoint_parser.add_argument("--note", default="")
    checkpoint_parser.add_argument("--id", default="")

    restore_parser = subparsers.add_parser("restore-checkpoint")
    add_common_arguments(restore_parser)
    restore_parser.add_argument("--id", required=True)

    return parser


def campaign_root_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    add_common_arguments(parent)
    return parent


def load_mutable_state(parsed_arguments) -> dict:
    return load_state(parsed_arguments.campaign_root)


def save_and_print(
    campaign_root: Path,
    state: dict,
    result: OperationResult | dict,
) -> int:
    save_state(campaign_root, state)
    if isinstance(result, OperationResult):
        print(result.message)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def format_level_options(options: dict) -> str:
    lines = [
        "# Level Up Options",
        "",
        f"- Character: {options['character']}",
        f"- Current level: {options['current_level']}",
        f"- XP: {options['xp']}",
        f"- Available level: {options['available_level']}",
        f"- Pending level up: {str(options['pending_level_up']).lower()}",
        "",
        "## Guided Choices",
    ]
    for choice in options["choices"]:
        lines.append(f"- {choice}")
    return "\n".join(lines) + "\n"


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)

    if parsed_arguments.command == "init":
        initialize_state(
            parsed_arguments.campaign_root,
            parsed_arguments.campaign_name,
            overwrite=parsed_arguments.overwrite,
        )
        print(
            f"Created game state: {state_path(parsed_arguments.campaign_root)}"
        )
        return 0

    state = load_mutable_state(parsed_arguments)

    if parsed_arguments.command == "status":
        if parsed_arguments.format == "json":
            print(json.dumps(state, indent=2, ensure_ascii=False))
        else:
            print(format_status(state), end="")
        return 0

    if parsed_arguments.command == "add-character":
        character = default_character(
            name=parsed_arguments.name,
            class_name=parsed_arguments.class_name,
            ancestry=parsed_arguments.ancestry,
            level=parsed_arguments.level,
            xp=parsed_arguments.xp,
            max_hp=parsed_arguments.max_hp,
            armor_class=parsed_arguments.armor_class,
            hit_die=parsed_arguments.hit_die,
        )
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            add_character(state, character),
        )

    if parsed_arguments.command == "add-item":
        item = add_item(
            state,
            parsed_arguments.character,
            parsed_arguments.name,
            quantity=parsed_arguments.quantity,
            location=parsed_arguments.location,
            slot=parsed_arguments.slot,
            mechanical_effect=parsed_arguments.mechanical_effect,
            story_significance=parsed_arguments.story_significance,
            value=parsed_arguments.value,
        )
        return save_and_print(parsed_arguments.campaign_root, state, item)

    if parsed_arguments.command == "equip":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            equip_item(
                state,
                parsed_arguments.character,
                parsed_arguments.item,
                parsed_arguments.slot,
            ),
        )

    if parsed_arguments.command == "move-item":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            move_item(
                state,
                parsed_arguments.character,
                parsed_arguments.item,
                parsed_arguments.location,
            ),
        )

    if parsed_arguments.command == "adjust-currency":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            adjust_currency(
                state,
                parsed_arguments.character,
                cp=parsed_arguments.cp,
                sp=parsed_arguments.sp,
                ep=parsed_arguments.ep,
                gp=parsed_arguments.gp,
                pp=parsed_arguments.pp,
            ),
        )

    if parsed_arguments.command == "add-shop-item":
        item = add_shop_item(
            state,
            parsed_arguments.shop_id,
            parsed_arguments.shop_name,
            parsed_arguments.merchant,
            parsed_arguments.item_name,
            parsed_arguments.price,
            stock=parsed_arguments.stock,
            mechanical_effect=parsed_arguments.mechanical_effect,
        )
        return save_and_print(parsed_arguments.campaign_root, state, item)

    if parsed_arguments.command == "buy-item":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            buy_item(
                state,
                parsed_arguments.character,
                parsed_arguments.shop_id,
                parsed_arguments.item,
            ),
        )

    if parsed_arguments.command == "award-xp":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            award_xp(
                state,
                parsed_arguments.character,
                parsed_arguments.amount,
                parsed_arguments.reason,
            ),
        )

    if parsed_arguments.command == "level-up-options":
        options = level_up_options(state, parsed_arguments.character)
        save_state(parsed_arguments.campaign_root, state)
        if parsed_arguments.format == "json":
            print(json.dumps(options, indent=2, ensure_ascii=False))
        else:
            print(format_level_options(options), end="")
        return 0

    if parsed_arguments.command == "apply-level-up":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            apply_level_up(
                state,
                parsed_arguments.character,
                parsed_arguments.new_level,
                parsed_arguments.hp_increase,
                features=parsed_arguments.feature,
                force=parsed_arguments.force,
            ),
        )

    if parsed_arguments.command == "set-spell-slots":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            set_spell_slots(
                state,
                parsed_arguments.character,
                parsed_arguments.slot_level,
                parsed_arguments.max,
            ),
        )

    if parsed_arguments.command == "spend-spell-slot":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            spend_spell_slot(
                state,
                parsed_arguments.character,
                parsed_arguments.slot_level,
            ),
        )

    if parsed_arguments.command == "add-condition":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            add_condition(
                state,
                parsed_arguments.character,
                parsed_arguments.name,
                effect=parsed_arguments.effect,
                ends_on=parsed_arguments.ends_on,
            ),
        )

    if parsed_arguments.command == "remove-condition":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            remove_condition(
                state,
                parsed_arguments.character,
                parsed_arguments.name,
            ),
        )

    if parsed_arguments.command == "apply-damage":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            apply_damage(
                state,
                parsed_arguments.character,
                parsed_arguments.amount,
                parsed_arguments.type,
            ),
        )

    if parsed_arguments.command == "heal":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            heal(state, parsed_arguments.character, parsed_arguments.amount),
        )

    if parsed_arguments.command == "death-save":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            record_death_save(
                state,
                parsed_arguments.character,
                parsed_arguments.result,
            ),
        )

    if parsed_arguments.command == "rest":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            rest(state, parsed_arguments.character, parsed_arguments.kind),
        )

    if parsed_arguments.command == "spend-hit-die":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            spend_hit_die(
                state,
                parsed_arguments.character,
                parsed_arguments.healing,
            ),
        )

    if parsed_arguments.command == "start-combat":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            start_combat(
                state,
                parsed_arguments.name,
                parsed_arguments.combatant,
            ),
        )

    if parsed_arguments.command == "end-turn":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            end_turn(state),
        )

    if parsed_arguments.command == "combat-action":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            record_combat_action(
                state,
                parsed_arguments.actor,
                parsed_arguments.summary,
                target=parsed_arguments.target,
                damage=parsed_arguments.damage,
            ),
        )

    if parsed_arguments.command == "end-combat":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            end_combat(state),
        )

    if parsed_arguments.command == "set-tactical-scene":
        return save_and_print(
            parsed_arguments.campaign_root,
            state,
            set_tactical_scene(
                state,
                parsed_arguments.summary,
                parsed_arguments.range_band,
                parsed_arguments.terrain,
                parsed_arguments.hazard,
                parsed_arguments.interactable,
                parsed_arguments.visual_prompt_hint,
            ),
        )

    if parsed_arguments.command == "checkpoint":
        checkpoint = create_checkpoint(
            parsed_arguments.campaign_root,
            state,
            parsed_arguments.label,
            note=parsed_arguments.note,
            checkpoint_id=parsed_arguments.id,
        )
        print(json.dumps(checkpoint, indent=2, ensure_ascii=False))
        return 0

    if parsed_arguments.command == "restore-checkpoint":
        result = restore_checkpoint(
            parsed_arguments.campaign_root, parsed_arguments.id
        )
        print(result.message)
        return 0

    raise AssertionError(f"Unhandled command: {parsed_arguments.command}")


if __name__ == "__main__":
    raise SystemExit(main())
