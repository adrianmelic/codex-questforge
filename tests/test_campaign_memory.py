from datetime import date

import pytest

from scripts.campaign_memory import (
    add_inventory_item,
    award_loot,
    award_xp,
    create_campaign,
    create_next_session,
    format_visual_assets,
    list_inventory,
    list_visual_assets,
    record_hook_status,
    record_puzzle_beat,
    register_visual_asset,
    save_image_prompt,
    save_visual_prompt,
    set_visual_status,
    slugify,
)


def test_slugify_creates_stable_folder_names():
    assert slugify("The Amber Gate!") == "the-amber-gate"
    assert slugify("Tiradas de característica") == "tiradas-de-caracteristica"
    assert slugify("  ") == "campaign"


def test_create_campaign_writes_memory_structure(tmp_path):
    paths = create_campaign(
        campaigns_dir=tmp_path,
        name="The Amber Gate",
        tone="heroic mystery",
        boundaries="no graphic gore",
        session_date=date(2026, 5, 17),
    )

    assert paths.root.name == "the-amber-gate"
    assert paths.dm.is_dir()
    assert paths.adventure_spine.exists()
    assert paths.puzzle_ledger.exists()
    assert paths.characters.is_dir()
    assert paths.sessions.is_dir()
    assert paths.image_prompts.is_dir()
    assert paths.image_assets.is_dir()
    assert paths.image_viewers.is_dir()
    assert paths.checkpoints.is_dir()
    assert paths.audio.is_dir()
    assert not paths.audio_library.exists()
    assert paths.game_state.exists()
    assert paths.visual_index.exists()
    assert paths.visual_ledger.exists()
    assert paths.rules.is_dir()
    assert paths.opening_brief.exists()
    assert paths.player_journal.exists()
    visual_index_text = paths.visual_index.read_text(encoding="utf-8")
    assert visual_index_text.index("Statuses:") < visual_index_text.index(
        "| Kind |"
    )
    assert "- Campaign: The Amber Gate" in paths.campaign_state.read_text(
        encoding="utf-8"
    )
    assert "- Tone: heroic mystery" in paths.campaign_state.read_text(
        encoding="utf-8"
    )
    assert '"currentSession": 1' in paths.manifest.read_text(encoding="utf-8")
    assert '"adventureSpine": "dm/adventure-spine.md"' in (
        paths.manifest.read_text(encoding="utf-8")
    )
    assert '"gameState": "game-state.json"' in paths.manifest.read_text(
        encoding="utf-8"
    )
    assert '"campaign": "The Amber Gate"' in paths.game_state.read_text(
        encoding="utf-8"
    )
    assert (paths.sessions / "session-001.md").exists()


def test_create_campaign_refuses_to_overwrite_existing_campaign(tmp_path):
    create_campaign(tmp_path, "The Amber Gate", session_date=date(2026, 5, 17))

    with pytest.raises(FileExistsError):
        create_campaign(
            tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
        )


def test_create_next_session_updates_manifest(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )
    session_path = create_next_session(
        paths.root,
        session_date=date(2026, 5, 18),
        characters_present="Mara Vey",
        recap=[
            "Mara discovered the amber lantern is out of phase.",
            "Brother Caldus trusts Mara.",
        ],
        start_location="west side of the gorge bridge",
        pressure="the lantern waits at the edge of the ruin",
        next_choice="cross or parley with the whisper",
    )
    session_text = session_path.read_text(encoding="utf-8")

    assert session_path.name == "session-002.md"
    assert "- Session: 2" in session_text
    assert "- Characters present: Mara Vey" in session_text
    assert (
        "- Mara discovered the amber lantern is out of phase." in session_text
    )
    assert "- Brother Caldus trusts Mara." in session_text
    assert "- Location: west side of the gorge bridge" in session_text
    assert (
        "- Pressure: the lantern waits at the edge of the ruin" in session_text
    )
    assert (
        "- Player action: Pending choice: cross or parley with the whisper"
        in session_text
    )
    assert "- Party position: west side of the gorge bridge" in session_text
    assert (
        "- Immediate next choice: cross or parley with the whisper"
        in session_text
    )
    assert '"currentSession": 2' in paths.manifest.read_text(encoding="utf-8")


def test_save_image_prompt_writes_scene_prompt(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )
    prompt_path = save_image_prompt(
        paths.root,
        session_number=1,
        scene_number=2,
        prompt="A lantern-lit bridge above a storm gorge.",
    )

    assert prompt_path.name == "session-001-scene-002.md"
    assert prompt_path.read_text(encoding="utf-8").strip() == (
        "A lantern-lit bridge above a storm gorge."
    )


def test_save_visual_prompt_writes_metadata_and_index(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )
    prompt_path = save_visual_prompt(
        paths.root,
        session_number=1,
        scene_number=3,
        kind="item",
        label="Copper Map Tube",
        prompt="A sealed copper tube with amber wax.",
    )

    assert prompt_path.name == "session-001-scene-003-item-copper-map-tube.md"
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "kind: item" in prompt_text
    assert "label: Copper Map Tube" in prompt_text
    assert "A sealed copper tube with amber wax." in prompt_text

    index_text = paths.visual_index.read_text(encoding="utf-8")
    assert "| item | Copper Map Tube | 1 | 3 |" in index_text
    assert "Source Anchors" in index_text


def test_register_visual_asset_copies_asset_and_updates_index(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )
    prompt_path = save_visual_prompt(
        paths.root,
        session_number=1,
        scene_number=3,
        kind="item",
        label="Copper Map Tube",
        prompt="A sealed copper tube with amber wax.",
    )
    source_asset = tmp_path / "generated.png"
    source_asset.write_bytes(b"fake-png")

    asset_path = register_visual_asset(
        paths.root,
        asset_source=source_asset,
        asset_filename="copper-map-tube.png",
        prompt_path=prompt_path.relative_to(paths.root),
    )

    assert asset_path == paths.image_assets / "copper-map-tube.png"
    assert asset_path.read_bytes() == b"fake-png"
    index_text = paths.visual_index.read_text(encoding="utf-8")
    assert "| item | Copper Map Tube | 1 | 3 |" in index_text
    assert (
        "images/prompts/session-001-scene-003-item-copper-map-tube.md"
        in index_text
    )
    assert "asset-saved | images/assets/copper-map-tube.png" in index_text


def test_register_visual_asset_can_match_by_visual_metadata(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )
    save_visual_prompt(
        paths.root,
        session_number=1,
        scene_number=3,
        kind="item",
        label="Copper Map Tube",
        prompt="A sealed copper tube with amber wax.",
    )
    asset = paths.image_assets / "copper-map-tube.png"
    asset.write_bytes(b"fake-png")

    register_visual_asset(
        paths.root,
        asset_path=asset,
        kind="item",
        label="Copper Map Tube",
        session_number=1,
        scene_number=3,
    )

    index_text = paths.visual_index.read_text(encoding="utf-8")
    assert "asset-saved | images/assets/copper-map-tube.png" in index_text


def test_set_visual_status_marks_canon_without_changing_asset(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )
    save_visual_prompt(
        paths.root,
        session_number=0,
        scene_number=1,
        kind="character",
        label="Mara Vey Reference Sheet",
        prompt="Mara from several angles.",
    )

    set_visual_status(
        paths.root,
        status="canon",
        kind="character",
        label="Mara Vey Reference Sheet",
        session_number=0,
        scene_number=1,
    )

    index_text = paths.visual_index.read_text(encoding="utf-8")
    assert "| character | Mara Vey Reference Sheet | 0 | 1 |" in index_text
    assert (
        "images/prompts/session-000-scene-001-character-mara-vey-reference-sheet.md | "
        "canon |"
    ) in index_text


def test_campaign_memory_records_inventory_xp_and_loot(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )

    add_inventory_item(
        paths.root,
        item="Bandaged left hand",
        holder="Mara Vey",
        mechanical_effect="Disadvantage on delicate left-hand tasks",
        story_significance="Visible injury until treated",
    )
    award_xp(
        paths.root,
        character="Mara Vey",
        amount=50,
        reason="Disarmed the bridge ward without killing the guard",
        session_number=1,
        scene_number=4,
    )
    award_loot(
        paths.root,
        item="Amber wax seal",
        holder="Mara Vey",
        source="bridge ward",
        value="clue",
        notes="Opens a social route with the abbey",
    )

    state_text = paths.campaign_state.read_text(encoding="utf-8")
    assert "Bandaged left hand" in state_text
    assert "Disarmed the bridge ward" in state_text
    assert "Amber wax seal" in state_text
    assert "## Loot Ledger" in state_text
    assert "## Experience And Advancement" in state_text

    inventory = list_inventory(paths.root)
    assert "Bandaged left hand" in inventory
    assert "Amber wax seal" not in inventory


def test_campaign_memory_records_spine_and_puzzle_beats(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )

    record_hook_status(
        paths.root,
        hook="The shrine register has your name",
        origin="opening brief",
        status="changed",
        current_meaning="the House of Weights now controls the name ledger",
        next_payoff="recover the scraped page before the council corrects it",
    )
    record_puzzle_beat(
        paths.root,
        title="Three Bell Marks",
        kind="symbolic_order",
        required_clues=[
            "one bell means sleep",
            "the dawn bell did not finish",
        ],
        ask_at_table="Which bell mark do you touch first?",
        solution="touch the unfinished dawn mark",
        fallback="a clerk wakes, but the side archive opens",
        reward="archive access without using the white key",
        symbolic_weight="unfinished promises can still point the way",
    )

    spine_text = paths.adventure_spine.read_text(encoding="utf-8")
    puzzle_text = paths.puzzle_ledger.read_text(encoding="utf-8")

    assert "The shrine register has your name" in spine_text
    assert "changed" in spine_text
    assert "Three Bell Marks" in puzzle_text
    assert "symbolic_order" in puzzle_text


def test_list_visual_assets_filters_canon_entries_with_assets(tmp_path):
    paths = create_campaign(
        tmp_path, "The Amber Gate", session_date=date(2026, 5, 17)
    )
    prompt_path = save_visual_prompt(
        paths.root,
        session_number=0,
        scene_number=1,
        kind="character",
        label="Mara Vey Reference Sheet",
        prompt="Mara from several angles.",
    )
    save_visual_prompt(
        paths.root,
        session_number=1,
        scene_number=2,
        kind="item",
        label="Copper Map Tube",
        prompt="A sealed copper tube with amber wax.",
    )
    source_asset = tmp_path / "mara.png"
    source_asset.write_bytes(b"fake-png")
    register_visual_asset(
        paths.root,
        asset_source=source_asset,
        asset_filename="mara-vey-reference.png",
        prompt_path=prompt_path.relative_to(paths.root),
        status="canon",
    )

    entries = list_visual_assets(
        paths.root,
        statuses=["canon"],
        kinds=["character"],
        require_asset=True,
    )

    assert len(entries) == 1
    assert entries[0].label == "Mara Vey Reference Sheet"
    assert entries[0].asset_path == "images/assets/mara-vey-reference.png"

    table = format_visual_assets(entries)
    assert "Mara Vey Reference Sheet" in table
    assert "images/assets/mara-vey-reference.png" in table
