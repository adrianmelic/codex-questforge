from scripts.visual_planner import plan_visual_beat


def test_visual_planner_skips_brief_rules_questions():
    plan = plan_visual_beat("Como funciona la ventaja en esta tirada?")

    assert plan.should_generate is False
    assert plan.format == "none"
    assert plan.use_gallery is False


def test_visual_planner_uses_comic_page_for_multi_moment_actions():
    plan = plan_visual_beat(
        "Saludo al posadero, le doy 5pp y luego bajo a desayunar."
    )

    assert plan.should_generate is True
    assert plan.format == "comic_page"
    assert plan.kind == "comic-page"
    assert plan.panel_count == 2
    assert plan.use_gallery is True
    assert plan.present_image_in_chat is True
    assert any(
        "visual-ledger.md" in item for item in plan.continuity_requirements
    )
    assert any("visual-gallery.html" in item for item in plan.next_steps)
    assert any("absolute-path Markdown" in item for item in plan.next_steps)


def test_visual_planner_uses_pov_360_for_lookaround_requests():
    plan = plan_visual_beat(
        "Quiero mirar alrededor de la taberna en 360 desde mis ojos."
    )

    assert plan.format == "pov_360"
    assert plan.kind == "pov-360"
    assert plan.present_image_in_chat is False
    assert plan.use_gallery is True
    assert any("panorama_viewer.py" in item for item in plan.next_steps)


def test_visual_planner_uses_inventory_board_for_inventory():
    plan = plan_visual_beat("Revisamos el inventario, monedas y loot.")

    assert plan.format == "inventory_board"
    assert plan.kind == "inventory"


def test_visual_planner_can_plan_chat_images_when_requested():
    plan = plan_visual_beat(
        "La puerta se abre y Nela entra.", visual_first=False
    )

    assert plan.should_generate is True
    assert plan.use_gallery is False
    assert plan.present_image_in_chat is True
