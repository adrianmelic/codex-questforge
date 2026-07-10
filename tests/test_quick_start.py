import json

import pytest

from scripts.game_state import load_state
from scripts.quick_start import create_quick_start


def quick_start_spec():
    return {
        "campaign": {
            "name": "The Copper Ferry",
            "language": "en",
            "tone": "grounded harbor mystery",
            "boundaries": "non-graphic violence",
            "promise": "Choices change the harbor and its people.",
            "hooks": [
                "A ferry cable was cut.",
                "The pay ledger is missing.",
                "A storm is approaching.",
            ],
            "core_truths": ["The sabotage was practical, not magical."],
            "clue_routes": [
                "Inspect the cable.",
                "Question the ferryman.",
                "Follow the stolen ledger.",
            ],
            "faction_intents": ["The guild wants the ferry closed."],
            "outcomes": ["Expose the guild or bargain for repairs."],
        },
        "hero": {
            "name": "Mara Vey",
            "class_name": "Bard",
            "ancestry": "Human",
            "background": "Dock courier",
            "max_hp": 10,
            "armor_class": 13,
            "hit_die": "d8",
            "abilities": {"charisma": 16, "dexterity": 14},
            "skill_modifiers": {"persuasion": 5},
            "currency": {"gp": 10},
            "resources": {"spell_slots": {"1": {"max": 2, "used": 0}}},
            "spells": {
                "cantrips": ["Message"],
                "known": ["Healing Word"],
                "prepared": ["Healing Word"],
            },
            "features": ["Bardic Inspiration d6"],
            "notes": ["Open rolls by default."],
            "visual_description": "Human courier with a dark braid.",
            "visual_must_preserve": ["dark braid", "green courier coat"],
            "items": [
                {
                    "name": "Dockside lute",
                    "slot": "instrument",
                    "value": "35gp",
                },
                {"name": "Rope", "location": "backpack"},
            ],
        },
        "opening": {
            "title": "The Cut Cable",
            "location": "Copper Ferry",
            "pressure": "A worker hangs above the river.",
            "npc_intent": "The ferryman wants both worker and ledger saved.",
            "sensory_detail": "Fresh tar cuts through the rain.",
            "visible_risks": ["The worker may fall.", "The thief may escape."],
            "options": ["Reach the worker.", "Stop the thief."],
            "question": "What does Mara do?",
        },
        "visual": {
            "kind": "scene",
            "label": "Copper Ferry rescue",
            "prompt": "A grounded fantasy harbor rescue in heavy rain.",
        },
    }


def test_quick_start_creates_playable_consistent_campaign(tmp_path):
    campaign_root = create_quick_start(tmp_path, quick_start_spec())

    state = load_state(campaign_root)
    character = state["characters"]["Mara Vey"]
    assert character["equipment"]["instrument"] == "dockside-lute"
    assert character["inventory"][0]["location"] == "equipped"
    assert character["resources"]["spell_slots"]["1"]["max"] == 2
    assert state["checkpoints"][0]["label"] == "Before session start"

    manifest = json.loads(
        (campaign_root / "questforge.json").read_text(encoding="utf-8")
    )
    assert manifest["language"] == "en"
    assert "The Cut Cable" in (campaign_root / "opening-brief.md").read_text(
        encoding="utf-8"
    )
    assert "Inspect the cable" in (
        campaign_root / "dm" / "adventure-spine.md"
    ).read_text(encoding="utf-8")
    assert "Copper Ferry rescue" in (
        campaign_root / "images" / "visual-index.md"
    ).read_text(encoding="utf-8")
    assert "Human courier with a dark braid" in (
        campaign_root / "images" / "visual-ledger.md"
    ).read_text(encoding="utf-8")
    assert (campaign_root / "analytics" / "session-events.jsonl").exists()


def test_quick_start_refuses_to_overwrite_existing_campaign(tmp_path):
    spec = quick_start_spec()
    create_quick_start(tmp_path, spec)

    with pytest.raises(FileExistsError):
        create_quick_start(tmp_path, spec)


def test_quick_start_rejects_incomplete_spec(tmp_path):
    spec = quick_start_spec()
    del spec["hero"]["max_hp"]

    with pytest.raises((TypeError, ValueError)):
        create_quick_start(tmp_path, spec)


def test_quick_start_localizes_player_facing_files_in_spanish(tmp_path):
    spec = quick_start_spec()
    spec["campaign"]["name"] = "El Transbordador de Cobre"
    spec["campaign"]["language"] = "es"
    spec["opening"]["question"] = "¿Qué hace Mara?"

    campaign_root = create_quick_start(tmp_path, spec)

    opening = (campaign_root / "opening-brief.md").read_text(encoding="utf-8")
    journal = (campaign_root / "player-journal.md").read_text(encoding="utf-8")
    session = (campaign_root / "sessions" / "session-001.md").read_text(
        encoding="utf-8"
    )
    assert "## Promesa de campaña" in opening
    assert "- Ubicación:" in opening
    assert "# Diario del jugador" in journal
    assert "# Registro de sesión" in session
