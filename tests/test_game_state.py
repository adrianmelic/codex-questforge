from datetime import date

import pytest

from scripts.campaign_memory import create_campaign
from scripts.game_state import (
    add_character,
    add_item,
    add_shop_item,
    apply_damage,
    apply_level_up,
    award_xp,
    buy_item,
    create_checkpoint,
    default_character,
    equip_item,
    format_status,
    heal,
    level_up_options,
    load_state,
    record_death_save,
    restore_checkpoint,
    rest,
    save_state,
    set_spell_slots,
    spend_spell_slot,
    start_combat,
    end_turn,
    set_tactical_scene,
)


def create_stateful_campaign(tmp_path):
    paths = create_campaign(
        tmp_path,
        "The Amber Gate",
        session_date=date(2026, 6, 9),
    )
    state = load_state(paths.root)
    add_character(
        state,
        default_character(
            name="Mara Vey",
            class_name="Wizard",
            ancestry="Human",
            max_hp=8,
            armor_class=12,
            hit_die="d6",
        ),
    )
    save_state(paths.root, state)
    return paths, load_state(paths.root)


def test_game_state_tracks_inventory_equipment_and_status(tmp_path):
    paths, state = create_stateful_campaign(tmp_path)

    item = add_item(
        state,
        "Mara Vey",
        "Stormproof cloak",
        mechanical_effect="Advantage against cold rain exposure",
        value="12gp",
    )
    equip_item(state, "Mara Vey", item["id"], "cloak")
    save_state(paths.root, state)

    loaded = load_state(paths.root)
    character = loaded["characters"]["Mara Vey"]
    assert character["equipment"]["cloak"] == "stormproof-cloak"
    assert character["inventory"][0]["location"] == "equipped"
    assert "Stormproof cloak" in format_status(loaded)


def test_game_state_handles_shopping_and_currency(tmp_path):
    paths, state = create_stateful_campaign(tmp_path)
    state["characters"]["Mara Vey"]["currency"]["gp"] = 15

    add_shop_item(
        state,
        shop_id="low-door",
        shop_name="Low Door Outfitters",
        merchant="Sella",
        item_name="Iron lantern",
        price="5gp",
        stock=1,
        mechanical_effect="Bright light in a small radius",
    )
    buy_item(state, "Mara Vey", "low-door", "Iron lantern")

    character = state["characters"]["Mara Vey"]
    assert character["currency"]["gp"] == 10
    assert any(
        item["name"] == "Iron lantern" for item in character["inventory"]
    )
    assert state["shops"]["low-door"]["items"]["iron-lantern"]["stock"] == 0
    save_state(paths.root, state)


def test_game_state_tracks_xp_level_up_spell_slots_and_rest(tmp_path):
    paths, state = create_stateful_campaign(tmp_path)

    award_xp(state, "Mara Vey", 300, "Solved the bridge ward")
    options = level_up_options(state, "Mara Vey")
    assert options["pending_level_up"] is True
    assert options["available_level"] == 2

    apply_level_up(
        state,
        "Mara Vey",
        new_level=2,
        hp_increase=5,
        features=["Arcane recovery noted from SRD lookup"],
    )
    set_spell_slots(state, "Mara Vey", slot_level=1, maximum=3)
    spend_spell_slot(state, "Mara Vey", slot_level=1)
    assert (
        state["characters"]["Mara Vey"]["resources"]["spell_slots"]["1"][
            "used"
        ]
        == 1
    )

    rest(state, "Mara Vey", "long")
    character = state["characters"]["Mara Vey"]
    assert character["level"] == 2
    assert character["current_hp"] == character["max_hp"]
    assert character["resources"]["spell_slots"]["1"]["used"] == 0
    save_state(paths.root, state)


def test_game_state_handles_combat_damage_death_saves_and_healing(tmp_path):
    paths, state = create_stateful_campaign(tmp_path)

    start_combat(
        state,
        "Warehouse ambush",
        ["Mara Vey:14", "Dock Cutthroat:11:6:13:enemy"],
    )
    set_tactical_scene(
        state,
        summary="Crates form half cover around a lantern spill.",
        range_bands=["Mara to cutthroat: near"],
        terrain=["stacked crates"],
        hazards=["oil lamp"],
        interactables=["loose rope pulley"],
    )
    assert state["combat"]["turn_order"] == ["Mara Vey", "Dock Cutthroat"]

    end_turn(state)
    assert state["combat"]["current_turn_index"] == 1

    apply_damage(state, "Mara Vey", 20)
    character = state["characters"]["Mara Vey"]
    assert character["current_hp"] == 0
    assert any(
        condition["name"] == "Unconscious"
        for condition in character["conditions"]
    )

    record_death_save(state, "Mara Vey", "success")
    record_death_save(state, "Mara Vey", "success")
    record_death_save(state, "Mara Vey", "success")
    assert character["death_saves"]["stable"] is True

    heal(state, "Mara Vey", 4)
    assert character["current_hp"] == 4
    assert character["death_saves"]["stable"] is False
    save_state(paths.root, state)


def test_game_state_checkpoint_restore_rolls_back_state(tmp_path):
    paths, state = create_stateful_campaign(tmp_path)

    checkpoint = create_checkpoint(
        paths.root,
        state,
        label="Before the bad bargain",
        checkpoint_id="before-bargain",
    )
    assert checkpoint["id"] == "before-bargain"

    state = load_state(paths.root)
    apply_damage(state, "Mara Vey", 7)
    save_state(paths.root, state)
    assert load_state(paths.root)["characters"]["Mara Vey"]["current_hp"] == 1

    restore_checkpoint(paths.root, "before-bargain")
    restored = load_state(paths.root)
    assert restored["characters"]["Mara Vey"]["current_hp"] == 8


def test_game_state_rejects_spending_missing_spell_slot(tmp_path):
    _paths, state = create_stateful_campaign(tmp_path)

    with pytest.raises(ValueError, match="No level 2 spell slots"):
        spend_spell_slot(state, "Mara Vey", slot_level=2)
