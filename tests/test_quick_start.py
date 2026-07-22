import copy
import json
from pathlib import Path

import pytest

from scripts.game_state import load_state
from scripts.quick_start import create_quick_start


def quick_start_spec():
    return {
        "spec_version": 2,
        "conception": {
            "environment": {
                "biome": "terraced apple orchard",
                "climate": "mild upland air after a dry week",
                "season": "early autumn harvest",
                "time_of_day": "bright late morning",
                "surface": "packed ochre soil, ladders, and fallen fruit",
                "social_scale": "one tenant hamlet and its visiting factor",
                "water_relevance": "incidental; household wells are stable",
            },
            "community": (
                "Tenant growers share presses, tools, and the annual tithe."
            ),
            "material_conflict": (
                "Counterfeit scale weights are transferring the harvest from "
                "growers to the estate factor."
            ),
            "threat": (
                "The factor will seal the communal press by sunset and call "
                "armed collectors if the missing tally is not produced."
            ),
            "npc_relationships": [
                {
                    "npc": "Aven Rusk",
                    "role": "orchard forewoman",
                    "wants": "keep the press open without provoking arrests",
                    "relationship": (
                        "older sister of the factor's clerk and ashamed of "
                        "his complicity"
                    ),
                },
                {
                    "npc": "Pell Rusk",
                    "role": "estate clerk",
                    "wants": "recover the true weights before his fraud is exposed",
                    "relationship": (
                        "Aven's younger brother and secret debtor to the factor"
                    ),
                },
            ],
            "tone": "warm rural adventure with social pressure",
            "aesthetic": (
                "sunlit work clothes, ochre terraces, red fruit, iron tools"
            ),
            "campaign_promise": (
                "Practical choices reshape a close community while hidden "
                "trade routes widen the story beyond the valley."
            ),
            "sensory_palette": {
                "sight": "red fruit rolling through pale straw",
                "sound": "press gears, bees, and shouted weights",
                "smell_or_taste": "sharp cider mash and bruised apples",
                "touch_or_temperature": "warm iron handles and dusty palms",
            },
            "distinctive_elements": [
                "a communal press whose carved beam records old agreements",
                "matched bronze weights with one hollow counterfeit set",
            ],
        },
        "campaign": {
            "name": "The Crooked Harvest",
            "language": "en",
            "boundaries": "non-graphic violence",
            "hooks": [
                "A press worker is pinned beneath a sabotaged gear.",
                "The true harvest tally vanished during the noon weighing.",
                "A mule train bears the hamlet's seal on an unapproved road.",
            ],
            "core_truths": [
                "The false weights hide an ordinary fraud with dangerous allies."
            ],
            "clue_routes": [
                "Compare wear marks on the official and counterfeit weights.",
                "Win Pell's trust through Aven or his creditors.",
                "Trace the unapproved mule train through terrace witnesses.",
            ],
            "faction_intents": [
                "The estate factor wants the press closed before an audit."
            ],
            "outcomes": [
                "Expose the fraud and risk violent collection.",
                "Trade the tally for time and pursue the buyers upstream.",
            ],
        },
        "hero": {
            "name": "Mara Vey",
            "class_name": "Bard",
            "ancestry": "Human",
            "background": "Itinerant cooper",
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
            "visual_description": "Human cooper with a dark braid.",
            "visual_must_preserve": ["dark braid", "red work sash"],
            "items": [
                {
                    "name": "Travel lute",
                    "slot": "instrument",
                    "value": "35gp",
                },
                {"name": "Cooper's gauge", "location": "backpack"},
            ],
        },
        "opening": {
            "title": "The Jammed Press",
            "location": "Sunwheel communal press",
            "pressure": "A worker is pinned while the factor reaches for the tally.",
            "npc_intent": "Aven wants the worker safe and the true tally visible.",
            "sensory_detail": "Cider mash stings the air as iron teeth skip.",
            "visible_risks": [
                "The press beam may drop.",
                "The factor may leave with the only tally.",
            ],
            "options": ["Brace the press.", "Block the factor."],
            "question": "What does Mara do?",
        },
        "visual": {
            "kind": "scene",
            "label": "Sunwheel press crisis",
            "prompt": (
                "Grounded fantasy realism, a bright orchard press crisis, "
                "one clear moment, warm natural light, no text."
            ),
        },
    }


def test_quick_start_creates_playable_consistent_campaign(tmp_path):
    campaign_root = create_quick_start(tmp_path, quick_start_spec())

    state = load_state(campaign_root)
    character = state["characters"]["Mara Vey"]
    assert character["equipment"]["instrument"] == "travel-lute"
    assert character["inventory"][0]["location"] == "equipped"
    assert character["resources"]["spell_slots"]["1"]["max"] == 2
    assert state["checkpoints"][0]["label"] == "Before session start"

    manifest = json.loads(
        (campaign_root / "questforge.json").read_text(encoding="utf-8")
    )
    assert manifest["language"] == "en"
    assert manifest["creative_conception"]["path"] == (
        "campaign-conception.json"
    )
    conception = json.loads(
        (campaign_root / "campaign-conception.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        "biome=terraced apple orchard" in conception["environment_signature"]
    )
    assert "The Jammed Press" in (
        campaign_root / "opening-brief.md"
    ).read_text(encoding="utf-8")
    spine = (campaign_root / "dm" / "adventure-spine.md").read_text(
        encoding="utf-8"
    )
    assert "Compare wear marks" in spine
    assert "NPC Relationship Web" in spine
    assert "Sunwheel press crisis" in (
        campaign_root / "images" / "visual-index.md"
    ).read_text(encoding="utf-8")
    assert "Human cooper with a dark braid" in (
        campaign_root / "images" / "visual-ledger.md"
    ).read_text(encoding="utf-8")
    assert (campaign_root / "analytics" / "session-events.jsonl").exists()


def test_quick_start_refuses_to_overwrite_existing_campaign(tmp_path):
    spec = quick_start_spec()
    create_quick_start(tmp_path, spec)

    with pytest.raises(FileExistsError):
        create_quick_start(tmp_path, spec)


def test_quick_start_rejects_repeated_conception_under_new_names(tmp_path):
    create_quick_start(tmp_path, quick_start_spec())
    repeated = copy.deepcopy(quick_start_spec())
    repeated["campaign"]["name"] = "The Bent Scales"
    repeated["hero"]["name"] = "Orin Vale"
    repeated["opening"]["question"] = "What does Orin do?"

    with pytest.raises(ValueError, match="repeats a recent"):
        create_quick_start(tmp_path, repeated)


def test_quick_start_rejects_incomplete_spec(tmp_path):
    spec = quick_start_spec()
    del spec["conception"]["environment"]["biome"]

    with pytest.raises((TypeError, ValueError)):
        create_quick_start(tmp_path, spec)


def test_quick_start_requires_exactly_three_clue_routes(tmp_path):
    spec = quick_start_spec()
    spec["campaign"]["clue_routes"].pop()

    with pytest.raises(ValueError, match="exactly 3"):
        create_quick_start(tmp_path, spec)


def test_neutral_template_cannot_be_run_unchanged(tmp_path):
    template_path = (
        Path(__file__).resolve().parents[1]
        / "templates"
        / "quick-start-spec.json"
    )
    template = json.loads(template_path.read_text(encoding="utf-8"))

    with pytest.raises(ValueError):
        create_quick_start(tmp_path, template)


def test_quick_start_localizes_player_facing_files_in_spanish(tmp_path):
    spec = quick_start_spec()
    spec["campaign"]["name"] = "La Cosecha Torcida"
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


def test_four_bilingual_starts_create_materially_distinct_campaigns(tmp_path):
    variants = [
        {
            "name": "The Crooked Harvest",
            "language": "en",
            "environment": {
                "biome": "terraced orchard",
                "climate": "mild dry upland",
                "season": "early autumn",
                "time_of_day": "late morning",
                "surface": "ochre soil and wooden ladders",
                "social_scale": "tenant hamlet",
                "water_relevance": "incidental household wells",
            },
            "community": "Tenant growers share one communal press.",
            "conflict": "False weights divert the apple harvest.",
            "threat": "Collectors will seize the press by sunset.",
            "tone": "warm rural intrigue",
            "aesthetic": "red fruit, straw, ochre soil, warm iron",
            "promise": "Community choices expose a wider trade fraud.",
            "location": "Sunwheel communal press",
            "pressure": "A worker is pinned while the factor takes the tally.",
            "sensory": "Cider mash stings the air as iron teeth skip.",
        },
        {
            "name": "The Broken Meridian",
            "language": "en",
            "environment": {
                "biome": "high limestone plateau",
                "climate": "thin clear alpine air",
                "season": "late spring thaw",
                "time_of_day": "white noon",
                "surface": "chalk scree and mirrored tiles",
                "social_scale": "isolated scholarly enclave",
                "water_relevance": "snowmelt reserved for instruments",
            },
            "community": "Astronomers and lens grinders share an observatory.",
            "conflict": "A cracked lens invalidates the planting calendar.",
            "threat": "A patron will close the enclave after one false forecast.",
            "tone": "lucid scientific wonder under pressure",
            "aesthetic": "white stone, brass arcs, blue shadows, prisms",
            "promise": "Measurements and loyalties reshape distant valleys.",
            "location": "Meridian lens hall",
            "pressure": "A signal mirror slips while an inspector seals the chart.",
            "sensory": "Lens wheels click in thin air above hot brass.",
        },
        {
            "name": "Las Marcas de Sal",
            "language": "es",
            "environment": {
                "biome": "salina volcánica",
                "climate": "calor seco mineral",
                "season": "final del verano",
                "time_of_day": "atardecer cobrizo",
                "surface": "sal negra y vidrio natural",
                "social_scale": "caravana familiar itinerante",
                "water_relevance": "reserva escasa fuera del conflicto",
            },
            "community": "Una caravana de tintoreros comparte recetas y animales.",
            "conflict": "Un impuesto convierte los pigmentos en contrabando.",
            "threat": "Los recaudadores dividirán la caravana al anochecer.",
            "tone": "aventura luminosa de viaje y lealtades",
            "aesthetic": "telas violetas, sal negra, cobre y cielo naranja",
            "promise": "Cada ruta cambia alianzas y mercados futuros.",
            "location": "círculo de carga de la caravana",
            "pressure": "Un recaudador marca los animales mientras arde un fardo.",
            "sensory": "Las campanillas vibran sobre sal caliente y cuero tenso.",
        },
        {
            "name": "La Última Tramoya",
            "language": "es",
            "environment": {
                "biome": "anfiteatro boscoso domesticado",
                "climate": "templado estable",
                "season": "principio de primavera",
                "time_of_day": "amanecer durante el ensayo",
                "surface": "tablas pintadas, cuerdas y césped nuevo",
                "social_scale": "compañía teatral y barrio artesano",
                "water_relevance": "sin relevancia para el conflicto",
            },
            "community": "Actores y artesanos preparan una obra pública.",
            "conflict": "El decorado principal es prueba en un juicio de propiedad.",
            "threat": "La función será clausurada y un taller será embargado.",
            "tone": "comedia tensa con consecuencias cívicas",
            "aesthetic": "pintura fresca, máscaras, flores y poleas visibles",
            "promise": "Interpretar papeles abre decisiones políticas reales.",
            "location": "escenario del anfiteatro",
            "pressure": "Una polea cae mientras el alguacil incauta el decorado.",
            "sensory": "La cola de piel y el pan caliente cubren olor a serrín.",
        },
    ]

    campaign_roots = []
    for index, variant in enumerate(variants, start=1):
        spec = quick_start_spec()
        spec["campaign"]["name"] = variant["name"]
        spec["campaign"]["language"] = variant["language"]
        if variant["language"] == "es":
            spec["campaign"]["hooks"] = [
                variant["pressure"],
                f"Desaparece una prueba de {variant['location']}.",
                f"Un testigo cambia de bando en la campaña {index}.",
            ]
            spec["campaign"]["clue_routes"] = [
                f"Examinar pruebas materiales en {variant['location']}.",
                f"Usar la relación entre los dos PNJ de la campaña {index}.",
                f"Seguir a quien se beneficia del conflicto: {variant['conflict']}",
            ]
            spec["campaign"]["outcomes"] = [
                f"Proteger a la comunidad en la campaña {index}.",
                f"Cambiar seguridad inmediata por pruebas en la campaña {index}.",
            ]
        else:
            spec["campaign"]["hooks"] = [
                variant["pressure"],
                f"Evidence disappears from {variant['location']}.",
                f"A witness changes sides in campaign {index}.",
            ]
            spec["campaign"]["clue_routes"] = [
                f"Inspect physical evidence at {variant['location']}.",
                f"Use the relationship between the two local NPCs in campaign {index}.",
                f"Follow who profits from this conflict: {variant['conflict']}",
            ]
            spec["campaign"]["outcomes"] = [
                f"Protect the community in campaign {index}.",
                f"Trade immediate safety for evidence in campaign {index}.",
            ]
        spec["campaign"]["core_truths"] = [variant["conflict"]]
        spec["campaign"]["faction_intents"] = [variant["threat"]]

        creative = spec["conception"]
        creative["environment"] = variant["environment"]
        creative["community"] = variant["community"]
        creative["material_conflict"] = variant["conflict"]
        creative["threat"] = variant["threat"]
        creative["tone"] = variant["tone"]
        creative["aesthetic"] = variant["aesthetic"]
        creative["campaign_promise"] = variant["promise"]
        creative["npc_relationships"][0]["wants"] = variant["community"]
        creative["npc_relationships"][1]["wants"] = variant["conflict"]
        creative["sensory_palette"] = {
            "sight": variant["aesthetic"],
            "sound": variant["sensory"],
            "smell_or_taste": f"Material traces from campaign {index}",
            "touch_or_temperature": variant["environment"]["climate"],
        }
        creative["distinctive_elements"] = [
            f"A campaign-specific working object for start {index}",
            f"A local mark tied to this conflict: {variant['conflict']}",
        ]

        spec["opening"].update(
            {
                "title": f"Opening {index}",
                "location": variant["location"],
                "pressure": variant["pressure"],
                "npc_intent": variant["community"],
                "sensory_detail": variant["sensory"],
                "question": (
                    "What do you do?"
                    if variant["language"] == "en"
                    else "¿Qué haces?"
                ),
            }
        )
        spec["visual"]["label"] = f"Opening visual {index}"
        spec["visual"]["prompt"] = (
            f"Original grounded fantasy scene at {variant['location']}; "
            f"{variant['aesthetic']}; one clear actionable moment; no text."
        )
        campaign_roots.append(create_quick_start(tmp_path, spec))

    records = [
        json.loads(
            (root / "campaign-conception.json").read_text(encoding="utf-8")
        )
        for root in campaign_roots
    ]
    signatures = {record["environment_signature"] for record in records}
    conflicts = {
        record["conception"]["material_conflict"] for record in records
    }
    locations = {
        (root / "opening-brief.md").read_text(encoding="utf-8")
        for root in campaign_roots
    }

    assert len(signatures) == 4
    assert len(conflicts) == 4
    assert len(locations) == 4
    assert sum("## Campaign Promise" in text for text in locations) == 2
    assert sum("## Promesa de campaña" in text for text in locations) == 2
