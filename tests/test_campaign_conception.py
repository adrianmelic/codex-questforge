import copy
import json

from scripts.campaign_conception import (
    ENVIRONMENT_FIELDS,
    audit_conception,
    compare_conceptions,
    conception_record,
    environment_signature,
    main,
    validate_conception,
)


def conception(
    *,
    biome,
    climate,
    season,
    time_of_day,
    surface,
    social_scale,
    water_relevance,
    community,
    material_conflict,
    threat,
    tone,
    aesthetic,
    campaign_promise,
    sensory_palette,
    distinctive_elements,
):
    return {
        "environment": {
            "biome": biome,
            "climate": climate,
            "season": season,
            "time_of_day": time_of_day,
            "surface": surface,
            "social_scale": social_scale,
            "water_relevance": water_relevance,
        },
        "community": community,
        "material_conflict": material_conflict,
        "threat": threat,
        "npc_relationships": [
            {
                "npc": "First NPC",
                "role": "local organizer",
                "wants": "protect a shared resource",
                "relationship": "former mentor of the second NPC",
            },
            {
                "npc": "Second NPC",
                "role": "outside inspector",
                "wants": "prove a costly failure",
                "relationship": "resentful former student of the first NPC",
            },
        ],
        "tone": tone,
        "aesthetic": aesthetic,
        "campaign_promise": campaign_promise,
        "sensory_palette": sensory_palette,
        "distinctive_elements": distinctive_elements,
    }


def independent_conceptions():
    return [
        conception(
            biome="terraced orchard",
            climate="mild dry upland",
            season="early autumn",
            time_of_day="late morning",
            surface="ochre soil and wooden ladders",
            social_scale="tenant hamlet",
            water_relevance="incidental household wells",
            community="Growers share one press and negotiate an annual tithe.",
            material_conflict="False weights divert the harvest to an estate.",
            threat="Collectors will seize the press before the next weighing.",
            tone="warm rural intrigue",
            aesthetic="red fruit, pale straw, work clothes, warm iron",
            campaign_promise="Community choices uncover a wider trade fraud.",
            sensory_palette={
                "sight": "red fruit in straw",
                "sound": "wooden gears and bees",
                "smell_or_taste": "sharp cider mash",
                "touch_or_temperature": "warm handles and dusty palms",
            },
            distinctive_elements=[
                "a carved communal press beam",
                "hollow counterfeit bronze weights",
            ],
        ),
        conception(
            biome="high limestone plateau",
            climate="thin clear alpine air",
            season="late spring thaw",
            time_of_day="white noon",
            surface="chalk scree and mirrored observatory tiles",
            social_scale="isolated scholarly enclave",
            water_relevance="snowmelt rationed for instruments",
            community="Astronomers and lens grinders share a remote observatory.",
            material_conflict="A cracked lens threatens the planting calendar.",
            threat="A rival patron will close the enclave after one false forecast.",
            tone="lucid scientific wonder under pressure",
            aesthetic="white stone, brass arcs, blue shadows, glass prisms",
            campaign_promise="Measurements and loyalties reshape distant harvests.",
            sensory_palette={
                "sight": "hard blue shadows and prism fire",
                "sound": "lens wheels clicking in thin air",
                "smell_or_taste": "hot brass and bitter tea",
                "touch_or_temperature": "cold stone under fierce sunlight",
            },
            distinctive_elements=[
                "a hand-ground lens charted with flaws",
                "signal mirrors aimed at three valleys",
            ],
        ),
        conception(
            biome="salina volcánica",
            climate="calor seco con aire mineral",
            season="final del verano",
            time_of_day="atardecer cobrizo",
            surface="costra de sal negra y vidrio natural",
            social_scale="caravana familiar itinerante",
            water_relevance="reserva escasa pero no escenario central",
            community="Una caravana de tintoreros protege recetas compartidas.",
            material_conflict="Un impuesto nuevo convierte los pigmentos en contrabando.",
            threat="Los recaudadores marcarán los animales y dividirán la caravana.",
            tone="aventura luminosa de viaje y lealtades",
            aesthetic="telas saturadas, sal oscura, cobre y cielo naranja",
            campaign_promise="Cada ruta elegida cambia alianzas y mercados futuros.",
            sensory_palette={
                "sight": "banderas violetas contra sal negra",
                "sound": "campanillas de carga y cuero tenso",
                "smell_or_taste": "minerales amargos y semillas tostadas",
                "touch_or_temperature": "calor seco bajo las sandalias",
            },
            distinctive_elements=[
                "pigmentos que revelan sellos fiscales borrados",
                "animales de carga con marcas familiares trenzadas",
            ],
        ),
        conception(
            biome="anfiteatro boscoso domesticado",
            climate="templado y estable",
            season="principio de primavera",
            time_of_day="amanecer durante el ensayo",
            surface="tablas pintadas, cuerdas y césped nuevo",
            social_scale="compañía teatral y barrio artesano",
            water_relevance="sin relevancia para el conflicto inicial",
            community="Actores, tramoyistas y artesanos preparan una obra pública.",
            material_conflict="El decorado principal es prueba en un juicio de propiedad.",
            threat="La función será clausurada y una familia perderá su taller.",
            tone="comedia tensa con consecuencias cívicas",
            aesthetic="pintura fresca, máscaras, flores y mecanismos visibles",
            campaign_promise="Interpretar papeles abre decisiones políticas reales.",
            sensory_palette={
                "sight": "telones verdes y máscaras recién doradas",
                "sound": "poleas, afinación y martillos pequeños",
                "smell_or_taste": "cola de piel y pan de desayuno",
                "touch_or_temperature": "rocío en el césped y tablas ásperas",
            },
            distinctive_elements=[
                "un dragón escénico desmontable usado como prueba legal",
                "marcas de carpintero ocultas bajo capas de pintura",
            ],
        ),
    ]


def test_independent_english_and_spanish_starts_differ_materially():
    starts = independent_conceptions()
    for start in starts:
        validate_conception(start)

    comparisons = [
        compare_conceptions(left, right)
        for index, left in enumerate(starts)
        for right in starts[index + 1 :]
    ]

    assert all(not result.repeated_combination for result in comparisons)
    assert all(
        len(result.matched_environment_fields) <= 1 for result in comparisons
    )
    assert all(result.narrative_similarity < 0.25 for result in comparisons)


def test_repetition_detection_uses_foundations_not_campaign_names():
    original = independent_conceptions()[0]
    renamed = copy.deepcopy(original)
    renamed["campaign_promise"] = (
        "A differently titled adventure still using the same physical base."
    )

    comparison = compare_conceptions(original, renamed, "renamed-campaign")

    assert comparison.repeated_combination is True
    assert set(comparison.matched_environment_fields) == set(
        ENVIRONMENT_FIELDS
    )


def test_repetition_detection_catches_lightly_rephrased_dimensions():
    original = independent_conceptions()[0]
    paraphrased = copy.deepcopy(original)
    paraphrased["environment"].update(
        {
            "biome": "apple orchard on terraces",
            "climate": "dry mild upland",
            "season": "autumn harvest",
            "time_of_day": "late in the morning",
            "surface": "wooden ladders over ochre soil",
        }
    )

    comparison = compare_conceptions(original, paraphrased)

    assert comparison.repeated_combination is True
    assert len(comparison.matched_environment_fields) >= 5


def test_water_is_allowed_when_it_is_an_intentional_dimension():
    riverside = copy.deepcopy(independent_conceptions()[1])
    riverside["environment"]["biome"] = "broad inhabited river delta"
    riverside["environment"][
        "water_relevance"
    ] = "central transport route and source of seasonal risk"

    validate_conception(riverside)

    assert "water_relevance=central transport route" in environment_signature(
        riverside
    )


def test_audit_reads_prior_campaign_conception_records(tmp_path):
    campaigns_dir = tmp_path / "campaigns"
    prior_root = campaigns_dir / "prior"
    prior_root.mkdir(parents=True)
    prior = independent_conceptions()[0]
    prior_audit = audit_conception(prior)
    (prior_root / "campaign-conception.json").write_text(
        json.dumps(conception_record(prior, prior_audit)),
        encoding="utf-8",
    )

    audit = audit_conception(copy.deepcopy(prior), campaigns_dir)

    assert audit.ok is False
    assert audit.comparisons[0].campaign_root.endswith("prior")


def test_cli_reports_distinct_candidate(tmp_path, capsys):
    spec_path = tmp_path / "candidate.json"
    spec_path.write_text(
        json.dumps({"conception": independent_conceptions()[2]}),
        encoding="utf-8",
    )

    exit_code = main(["--spec", str(spec_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert "salina volcánica" in payload["environment_signature"]
