"""Campaign memory helpers for Codex Questforge."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = PLUGIN_ROOT / "templates"
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
SESSION_PATTERN = re.compile(r"session-(?P<number>\d{3})\.md$")
VISUAL_STATUSES = {
    "prompt-saved",
    "asset-saved",
    "canon",
    "variant",
    "rejected",
}


@dataclass(frozen=True)
class CampaignPaths:
    """Filesystem paths for a Questforge campaign."""

    root: Path
    dm: Path
    adventure_spine: Path
    puzzle_ledger: Path
    campaign_state: Path
    player_journal: Path
    visual_bible: Path
    opening_brief: Path
    characters: Path
    sessions: Path
    image_prompts: Path
    image_assets: Path
    image_viewers: Path
    visual_index: Path
    visual_ledger: Path
    game_state: Path
    checkpoints: Path
    audio: Path
    audio_library: Path
    rules: Path
    manifest: Path


@dataclass(frozen=True)
class VisualIndexEntry:
    """One tracked visual prompt or generated asset."""

    kind: str
    label: str
    session_number: int
    scene_number: int
    prompt_path: str
    status: str
    asset_path: str
    source_anchors: str = ""
    continuity_tags: str = ""
    review_notes: str = ""


def slugify(value: str) -> str:
    """Convert a campaign name to a stable folder slug."""

    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = SLUG_PATTERN.sub("-", ascii_value.strip().lower()).strip("-")
    return slug or "campaign"


def get_campaign_paths(campaign_root: Path) -> CampaignPaths:
    return CampaignPaths(
        root=campaign_root,
        dm=campaign_root / "dm",
        adventure_spine=campaign_root / "dm" / "adventure-spine.md",
        puzzle_ledger=campaign_root / "dm" / "puzzle-ledger.md",
        campaign_state=campaign_root / "campaign-state.md",
        player_journal=campaign_root / "player-journal.md",
        visual_bible=campaign_root / "visual-bible.md",
        opening_brief=campaign_root / "opening-brief.md",
        characters=campaign_root / "characters",
        sessions=campaign_root / "sessions",
        image_prompts=campaign_root / "images" / "prompts",
        image_assets=campaign_root / "images" / "assets",
        image_viewers=campaign_root / "images" / "viewers",
        visual_index=campaign_root / "images" / "visual-index.md",
        visual_ledger=campaign_root / "images" / "visual-ledger.md",
        game_state=campaign_root / "game-state.json",
        checkpoints=campaign_root / "checkpoints",
        audio=campaign_root / "audio",
        audio_library=campaign_root / "audio" / "library.json",
        rules=campaign_root / "rules",
        manifest=campaign_root / "questforge.json",
    )


def read_template(template_name: str) -> str:
    return (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")


def write_text_once(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def ensure_template_file(path: Path, template_name: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        read_template(template_name),
        encoding="utf-8",
        newline="\n",
    )


def create_campaign(
    campaigns_dir: Path,
    name: str,
    tone: str = "",
    boundaries: str = "",
    session_date: date | None = None,
) -> CampaignPaths:
    """Create a campaign workspace from Questforge templates."""

    session_date = session_date or date.today()
    campaign_root = campaigns_dir / slugify(name)
    paths = get_campaign_paths(campaign_root)

    for directory in (
        paths.root,
        paths.dm,
        paths.characters,
        paths.sessions,
        paths.image_prompts,
        paths.image_assets,
        paths.image_viewers,
        paths.checkpoints,
        paths.audio,
        paths.rules,
    ):
        directory.mkdir(parents=True, exist_ok=False)

    campaign_state = read_template("campaign-state.md")
    campaign_state = campaign_state.replace(
        "- Campaign:", f"- Campaign: {name}"
    )
    campaign_state = campaign_state.replace("- Tone:", f"- Tone: {tone}")
    campaign_state = campaign_state.replace(
        "- Content boundaries:",
        f"- Content boundaries: {boundaries}",
    )
    campaign_state = campaign_state.replace(
        "- SRD attribution included: no",
        "- SRD attribution included: yes",
    )
    write_text_once(paths.campaign_state, campaign_state)
    write_text_once(paths.adventure_spine, read_template("adventure-spine.md"))
    write_text_once(paths.puzzle_ledger, read_template("puzzle-ledger.md"))
    write_text_once(paths.visual_bible, read_template("visual-bible.md"))
    write_text_once(paths.visual_index, read_template("visual-index.md"))
    write_text_once(paths.visual_ledger, read_template("visual-ledger.md"))
    game_state = read_template("game-state.json")
    game_state = game_state.replace(
        '"campaign": ""',
        f'"campaign": {json.dumps(name, ensure_ascii=False)}',
    )
    game_state = game_state.replace(
        '"updated_at": ""',
        f'"updated_at": {json.dumps(session_date.isoformat())}',
    )
    write_text_once(paths.game_state, game_state)
    write_text_once(paths.opening_brief, read_template("opening-brief.md"))
    write_text_once(paths.player_journal, read_template("player-journal.md"))
    write_text_once(
        paths.sessions / "session-001.md",
        create_session_text(name, 1, session_date),
    )
    write_text_once(paths.manifest, create_manifest(name, session_date))
    return paths


def create_manifest(name: str, session_date: date) -> str:
    payload = {
        "campaign": name,
        "system": "5E-compatible, SRD-grounded",
        "created": session_date.isoformat(),
        "currentSession": 1,
        "imageGeneration": "native Codex/ChatGPT only; no API calls",
        "dmFiles": {
            "adventureSpine": "dm/adventure-spine.md",
            "puzzleLedger": "dm/puzzle-ledger.md",
        },
        "gameState": "game-state.json",
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def create_session_text(
    campaign_name: str,
    session_number: int,
    session_date: date | None = None,
    characters_present: str = "",
    recap: list[str] | None = None,
    start_location: str = "",
    pressure: str = "",
    next_choice: str = "",
) -> str:
    session_date = session_date or date.today()
    session_text = read_template("session-log.md")
    session_text = session_text.replace(
        "- Campaign:", f"- Campaign: {campaign_name}"
    )
    session_text = session_text.replace(
        "- Session:", f"- Session: {session_number}"
    )
    session_text = session_text.replace(
        "- Date:",
        f"- Date: {session_date.isoformat()}",
    )
    if characters_present:
        session_text = session_text.replace(
            "- Characters present:",
            f"- Characters present: {characters_present}",
        )
    if recap:
        recap_text = "\n".join(f"- {item}" for item in recap)
        session_text = session_text.replace("- \n", f"{recap_text}\n", 1)
    if start_location:
        session_text = session_text.replace(
            "- Location:",
            f"- Location: {start_location}",
            1,
        )
        session_text = session_text.replace(
            "- Party position:",
            f"- Party position: {start_location}",
            1,
        )
    if pressure:
        session_text = session_text.replace(
            "- Pressure:",
            f"- Pressure: {pressure}",
            1,
        )
    if next_choice:
        session_text = session_text.replace(
            "- Player action:",
            f"- Player action: Pending choice: {next_choice}",
            1,
        )
        session_text = session_text.replace(
            "- Immediate next choice:",
            f"- Immediate next choice: {next_choice}",
            1,
        )
    return session_text


def get_campaign_name(paths: CampaignPaths) -> str:
    if paths.manifest.exists():
        payload = json.loads(paths.manifest.read_text(encoding="utf-8"))
        return str(payload.get("campaign", paths.root.name))
    return paths.root.name


def existing_session_numbers(sessions_dir: Path) -> list[int]:
    numbers: list[int] = []
    if not sessions_dir.exists():
        return numbers
    for path in sessions_dir.iterdir():
        match = SESSION_PATTERN.match(path.name)
        if match:
            numbers.append(int(match.group("number")))
    return sorted(numbers)


def create_next_session(
    campaign_root: Path,
    session_date: date | None = None,
    characters_present: str = "",
    recap: list[str] | None = None,
    start_location: str = "",
    pressure: str = "",
    next_choice: str = "",
) -> Path:
    paths = get_campaign_paths(campaign_root)
    if not paths.root.exists():
        raise FileNotFoundError(f"Missing campaign root: {campaign_root}")

    session_numbers = existing_session_numbers(paths.sessions)
    next_number = (session_numbers[-1] + 1) if session_numbers else 1
    session_path = paths.sessions / f"session-{next_number:03d}.md"
    write_text_once(
        session_path,
        create_session_text(
            get_campaign_name(paths),
            next_number,
            session_date,
            characters_present=characters_present,
            recap=recap,
            start_location=start_location,
            pressure=pressure,
            next_choice=next_choice,
        ),
    )
    update_manifest_current_session(paths, next_number)
    return session_path


def update_manifest_current_session(
    paths: CampaignPaths, session_number: int
) -> None:
    if not paths.manifest.exists():
        return
    payload = json.loads(paths.manifest.read_text(encoding="utf-8"))
    payload["currentSession"] = session_number
    paths.manifest.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def save_image_prompt(
    campaign_root: Path,
    session_number: int,
    scene_number: int,
    prompt: str,
) -> Path:
    paths = get_campaign_paths(campaign_root)
    if not prompt.strip():
        raise ValueError("Image prompt cannot be empty.")
    prompt_path = (
        paths.image_prompts
        / f"session-{session_number:03d}-scene-{scene_number:03d}.md"
    )
    write_text_once(prompt_path, prompt.strip() + "\n")
    return prompt_path


def save_visual_prompt(
    campaign_root: Path,
    session_number: int,
    scene_number: int,
    kind: str,
    label: str,
    prompt: str,
) -> Path:
    """Save a typed visual prompt and register it in the visual index."""

    paths = get_campaign_paths(campaign_root)
    if not prompt.strip():
        raise ValueError("Visual prompt cannot be empty.")
    visual_kind = slugify(kind)
    visual_label = label.strip() or visual_kind
    label_slug = slugify(visual_label)
    prompt_path = (
        paths.image_prompts
        / f"session-{session_number:03d}-scene-{scene_number:03d}"
        f"-{visual_kind}-{label_slug}.md"
    )
    body = "\n".join(
        [
            "---",
            f"kind: {visual_kind}",
            f"label: {visual_label}",
            f"session: {session_number}",
            f"scene: {scene_number}",
            "status: prompt-saved",
            "---",
            "",
            prompt.strip(),
            "",
        ]
    )
    write_text_once(prompt_path, body)
    append_visual_index(
        paths.visual_index,
        kind=visual_kind,
        label=visual_label,
        session_number=session_number,
        scene_number=scene_number,
        prompt_path=prompt_path.relative_to(paths.root),
    )
    return prompt_path


def add_inventory_item(
    campaign_root: Path,
    item: str,
    holder: str,
    mechanical_effect: str = "",
    story_significance: str = "",
) -> None:
    """Append a campaign inventory row."""

    if not item.strip() or not holder.strip():
        raise ValueError("Inventory item and holder are required.")
    paths = get_campaign_paths(campaign_root)
    append_markdown_table_row(
        paths.campaign_state,
        section="## Inventory And Rewards",
        header=("| Item | Holder | Mechanical Effect | Story Significance |"),
        separator="| --- | --- | --- | --- |",
        row=(
            f"| {markdown_cell(item)} | {markdown_cell(holder)} | "
            f"{markdown_cell(mechanical_effect)} | "
            f"{markdown_cell(story_significance)} |"
        ),
    )


def award_xp(
    campaign_root: Path,
    character: str,
    amount: int,
    reason: str,
    session_number: int | None = None,
    scene_number: int | None = None,
) -> None:
    """Record XP for meaningful accomplishments."""

    if not character.strip():
        raise ValueError("XP character is required.")
    if amount <= 0:
        raise ValueError("XP amount must be positive.")
    if not reason.strip():
        raise ValueError("XP reason is required.")
    paths = get_campaign_paths(campaign_root)
    append_markdown_table_row(
        paths.campaign_state,
        section="## Experience And Advancement",
        header="| Character | XP | Reason | Session | Scene |",
        separator="| --- | ---: | --- | ---: | ---: |",
        row=(
            f"| {markdown_cell(character)} | {amount} | "
            f"{markdown_cell(reason)} | {optional_number(session_number)} | "
            f"{optional_number(scene_number)} |"
        ),
    )


def award_loot(
    campaign_root: Path,
    item: str,
    holder: str,
    source: str = "",
    value: str = "",
    notes: str = "",
) -> None:
    """Record notable loot without forcing every mundane object into play."""

    if not item.strip() or not holder.strip():
        raise ValueError("Loot item and holder are required.")
    paths = get_campaign_paths(campaign_root)
    append_markdown_table_row(
        paths.campaign_state,
        section="## Loot Ledger",
        header="| Item | Holder | Source | Value | Notes |",
        separator="| --- | --- | --- | --- | --- |",
        row=(
            f"| {markdown_cell(item)} | {markdown_cell(holder)} | "
            f"{markdown_cell(source)} | {markdown_cell(value)} | "
            f"{markdown_cell(notes)} |"
        ),
    )


def list_inventory(campaign_root: Path) -> str:
    """Return the campaign inventory table as Markdown."""

    paths = get_campaign_paths(campaign_root)
    return extract_markdown_section(
        paths.campaign_state,
        section="## Inventory And Rewards",
    )


def record_hook_status(
    campaign_root: Path,
    hook: str,
    origin: str,
    status: str,
    current_meaning: str,
    next_payoff: str,
) -> None:
    """Record how an opening hook changed during live play."""

    allowed_statuses = {"active", "merged", "changed", "resolved", "retired"}
    if status not in allowed_statuses:
        raise ValueError(
            "Hook status must be one of: "
            + ", ".join(sorted(allowed_statuses))
        )
    if not hook.strip() or not current_meaning.strip():
        raise ValueError("Hook and current meaning are required.")
    paths = get_campaign_paths(campaign_root)
    ensure_template_file(paths.adventure_spine, "adventure-spine.md")
    append_markdown_table_row(
        paths.adventure_spine,
        section="## Hook Ledger",
        header=("| Hook | Origin | Status | Current Meaning | Next Payoff |"),
        separator="| --- | --- | --- | --- | --- |",
        row=(
            f"| {markdown_cell(hook)} | {markdown_cell(origin)} | "
            f"{markdown_cell(status)} | {markdown_cell(current_meaning)} | "
            f"{markdown_cell(next_payoff)} |"
        ),
    )


def record_puzzle_beat(
    campaign_root: Path,
    title: str,
    kind: str,
    required_clues: list[str],
    ask_at_table: str,
    solution: str,
    fallback: str,
    reward: str,
    symbolic_weight: str = "",
    status: str = "prepared",
) -> None:
    """Record a non-blocking deduction beat or small minigame."""

    allowed_statuses = {"prepared", "offered", "solved", "hinted", "bypassed"}
    if status not in allowed_statuses:
        raise ValueError(
            "Puzzle status must be one of: "
            + ", ".join(sorted(allowed_statuses))
        )
    required_values = {
        "title": title,
        "kind": kind,
        "ask_at_table": ask_at_table,
        "solution": solution,
        "fallback": fallback,
        "reward": reward,
    }
    for field_name, value in required_values.items():
        if not value.strip():
            raise ValueError(f"Puzzle {field_name} is required.")
    paths = get_campaign_paths(campaign_root)
    ensure_template_file(paths.puzzle_ledger, "puzzle-ledger.md")
    append_markdown_table_row(
        paths.puzzle_ledger,
        section="## Puzzle Beat Ledger",
        header=(
            "| Title | Kind | Status | Required Clues | Ask At Table | "
            "Solution | Fallback | Reward | Symbolic Weight |"
        ),
        separator="| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        row=(
            f"| {markdown_cell(title)} | {markdown_cell(kind)} | "
            f"{markdown_cell(status)} | "
            f"{markdown_cell('; '.join(required_clues))} | "
            f"{markdown_cell(ask_at_table)} | {markdown_cell(solution)} | "
            f"{markdown_cell(fallback)} | {markdown_cell(reward)} | "
            f"{markdown_cell(symbolic_weight)} |"
        ),
    )


def append_visual_index(
    visual_index_path: Path,
    kind: str,
    label: str,
    session_number: int,
    scene_number: int,
    prompt_path: Path,
) -> None:
    visual_index_path.parent.mkdir(parents=True, exist_ok=True)
    if not visual_index_path.exists():
        visual_index_path.write_text(
            read_template("visual-index.md"),
            encoding="utf-8",
            newline="\n",
        )
    row = (
        f"| {kind} | {label} | {session_number} | {scene_number} | "
        f"{prompt_path.as_posix()} | prompt-saved | | | | |\n"
    )
    with visual_index_path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(row)


def register_visual_asset(
    campaign_root: Path,
    asset_path: Path | None = None,
    asset_source: Path | None = None,
    asset_filename: str = "",
    prompt_path: Path | None = None,
    kind: str = "",
    label: str = "",
    session_number: int | None = None,
    scene_number: int | None = None,
    status: str = "asset-saved",
) -> Path:
    """Register a generated native image asset in the visual index."""

    validate_visual_status(status)
    paths = get_campaign_paths(campaign_root)
    if not paths.visual_index.exists():
        raise FileNotFoundError(f"Missing visual index: {paths.visual_index}")
    if asset_path is None and asset_source is None:
        raise ValueError("Provide asset_path or asset_source.")
    if prompt_path is None and not (
        kind
        and label
        and session_number is not None
        and scene_number is not None
    ):
        raise ValueError(
            "Provide prompt_path or kind, label, session_number, and "
            "scene_number."
        )

    asset_reference = resolve_asset_reference(
        paths,
        asset_path=asset_path,
        asset_source=asset_source,
        asset_filename=asset_filename,
    )
    update_visual_index_asset(
        paths.visual_index,
        asset_reference=asset_reference,
        status=status,
        prompt_path=normalize_prompt_reference(paths, prompt_path),
        kind=slugify(kind) if kind else "",
        label=label,
        session_number=session_number,
        scene_number=scene_number,
    )
    return paths.root / asset_reference


def set_visual_status(
    campaign_root: Path,
    status: str,
    prompt_path: Path | None = None,
    kind: str = "",
    label: str = "",
    session_number: int | None = None,
    scene_number: int | None = None,
) -> None:
    """Mark a visual row as canon, variant, rejected, or another status."""

    validate_visual_status(status)
    paths = get_campaign_paths(campaign_root)
    if not paths.visual_index.exists():
        raise FileNotFoundError(f"Missing visual index: {paths.visual_index}")
    if prompt_path is None and not (
        kind
        and label
        and session_number is not None
        and scene_number is not None
    ):
        raise ValueError(
            "Provide prompt_path or kind, label, session_number, and "
            "scene_number."
        )
    update_visual_index_status(
        paths.visual_index,
        status=status,
        prompt_path=normalize_prompt_reference(paths, prompt_path),
        kind=slugify(kind) if kind else "",
        label=label,
        session_number=session_number,
        scene_number=scene_number,
    )


def list_visual_assets(
    campaign_root: Path,
    statuses: list[str] | None = None,
    kinds: list[str] | None = None,
    label_contains: str = "",
    require_asset: bool = False,
) -> list[VisualIndexEntry]:
    """List visual index entries for prompt reuse and continuity review."""

    paths = get_campaign_paths(campaign_root)
    if not paths.visual_index.exists():
        raise FileNotFoundError(f"Missing visual index: {paths.visual_index}")

    requested_statuses = {status for status in statuses or []}
    unsupported_statuses = requested_statuses - VISUAL_STATUSES
    if unsupported_statuses:
        unsupported = ", ".join(sorted(unsupported_statuses))
        supported = ", ".join(sorted(VISUAL_STATUSES))
        raise ValueError(
            f"Unsupported visual status filter {unsupported}; use one of: "
            f"{supported}."
        )

    requested_kinds = {slugify(kind) for kind in kinds or []}
    label_filter = label_contains.casefold()
    entries = read_visual_index(paths.visual_index)
    filtered_entries: list[VisualIndexEntry] = []
    for entry in entries:
        if requested_statuses and entry.status not in requested_statuses:
            continue
        if requested_kinds and entry.kind not in requested_kinds:
            continue
        if label_filter and label_filter not in entry.label.casefold():
            continue
        if require_asset and not entry.asset_path:
            continue
        filtered_entries.append(entry)
    return filtered_entries


def read_visual_index(visual_index_path: Path) -> list[VisualIndexEntry]:
    """Read visual-index Markdown rows into structured entries."""

    entries: list[VisualIndexEntry] = []
    for line in visual_index_path.read_text(encoding="utf-8").splitlines():
        cells = parse_visual_index_row(line)
        if not cells:
            continue
        session_number = optional_int(cells[2])
        scene_number = optional_int(cells[3])
        if session_number is None or scene_number is None:
            continue
        entries.append(
            VisualIndexEntry(
                kind=cells[0],
                label=cells[1],
                session_number=session_number,
                scene_number=scene_number,
                prompt_path=cells[4].replace("\\", "/"),
                status=cells[5],
                asset_path=cells[6].replace("\\", "/"),
                source_anchors=cells[7],
                continuity_tags=cells[8],
                review_notes=cells[9],
            )
        )
    return entries


def format_visual_assets(entries: list[VisualIndexEntry]) -> str:
    """Format visual entries as a compact Markdown table."""

    if not entries:
        return "No visual assets matched."

    rows = [
        "| Kind | Label | Session | Scene | Status | Asset Path | Prompt Path |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for entry in entries:
        rows.append(
            (
                f"| {entry.kind} | {entry.label} | "
                f"{entry.session_number} | {entry.scene_number} | "
                f"{entry.status} | {entry.asset_path} | {entry.prompt_path} |"
            )
        )
    return "\n".join(rows)


def validate_visual_status(status: str) -> None:
    if status not in VISUAL_STATUSES:
        supported = ", ".join(sorted(VISUAL_STATUSES))
        raise ValueError(
            f"Unsupported visual status {status!r}; use one of: {supported}."
        )


def resolve_asset_reference(
    paths: CampaignPaths,
    asset_path: Path | None,
    asset_source: Path | None,
    asset_filename: str = "",
) -> Path:
    if asset_source is not None:
        if not asset_source.exists():
            raise FileNotFoundError(f"Missing asset source: {asset_source}")
        filename = asset_filename or asset_source.name
        destination = paths.image_assets / filename
        if destination.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing asset: {destination}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset_source, destination)
        return destination.relative_to(paths.root)

    assert asset_path is not None
    if asset_path.is_absolute():
        resolved_asset_path = asset_path.resolve()
        try:
            return resolved_asset_path.relative_to(paths.root.resolve())
        except ValueError as error:
            raise ValueError(
                "Absolute asset_path must be inside the campaign root."
            ) from error
    resolved_asset_path = paths.root / asset_path
    if not resolved_asset_path.exists():
        raise FileNotFoundError(f"Missing asset path: {resolved_asset_path}")
    return asset_path


def normalize_prompt_reference(
    paths: CampaignPaths,
    prompt_path: Path | None,
) -> str:
    if prompt_path is None:
        return ""
    if prompt_path.is_absolute():
        return (
            prompt_path.resolve().relative_to(paths.root.resolve()).as_posix()
        )
    return prompt_path.as_posix()


def update_visual_index_asset(
    visual_index_path: Path,
    asset_reference: Path,
    status: str,
    prompt_path: str = "",
    kind: str = "",
    label: str = "",
    session_number: int | None = None,
    scene_number: int | None = None,
) -> None:
    lines = visual_index_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    updated_count = 0
    for line in lines:
        cells = parse_visual_index_row(line)
        if cells and visual_index_row_matches(
            cells,
            prompt_path=prompt_path,
            kind=kind,
            label=label,
            session_number=session_number,
            scene_number=scene_number,
        ):
            cells[5] = status
            cells[6] = asset_reference.as_posix()
            line = "| " + " | ".join(cells) + " |"
            updated_count += 1
        updated_lines.append(line)

    if updated_count != 1:
        raise ValueError(
            f"Expected exactly one visual index row to update; found "
            f"{updated_count}."
        )
    visual_index_path.write_text(
        "\n".join(updated_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def update_visual_index_status(
    visual_index_path: Path,
    status: str,
    prompt_path: str = "",
    kind: str = "",
    label: str = "",
    session_number: int | None = None,
    scene_number: int | None = None,
) -> None:
    lines = visual_index_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    updated_count = 0
    for line in lines:
        cells = parse_visual_index_row(line)
        if cells and visual_index_row_matches(
            cells,
            prompt_path=prompt_path,
            kind=kind,
            label=label,
            session_number=session_number,
            scene_number=scene_number,
        ):
            cells[5] = status
            line = "| " + " | ".join(cells) + " |"
            updated_count += 1
        updated_lines.append(line)

    if updated_count != 1:
        raise ValueError(
            f"Expected exactly one visual index row to update; found "
            f"{updated_count}."
        )
    visual_index_path.write_text(
        "\n".join(updated_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_visual_index_row(line: str) -> list[str] | None:
    stripped_line = line.strip()
    if not stripped_line.startswith("|") or not stripped_line.endswith("|"):
        return None
    cells = [cell.strip() for cell in stripped_line.strip("|").split("|")]
    if len(cells) < 7 or cells[0] in {"Kind", "---"}:
        return None
    if len(cells) < 10:
        cells.extend([""] * (10 - len(cells)))
    return cells


def visual_index_row_matches(
    cells: list[str],
    prompt_path: str = "",
    kind: str = "",
    label: str = "",
    session_number: int | None = None,
    scene_number: int | None = None,
) -> bool:
    if prompt_path:
        return cells[4].replace("\\", "/") == prompt_path
    return (
        cells[0] == kind
        and cells[1] == label
        and optional_int(cells[2]) == session_number
        and optional_int(cells[3]) == scene_number
    )


def optional_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def optional_number(value: int | None) -> str:
    return "" if value is None else str(value)


def markdown_cell(value: str) -> str:
    return " ".join(value.strip().split()).replace("|", "\\|")


def append_markdown_table_row(
    path: Path,
    section: str,
    header: str,
    separator: str,
    row: str,
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing Markdown file: {path}")
    text = path.read_text(encoding="utf-8")
    if section not in text:
        text = text.rstrip() + f"\n\n{section}\n\n{header}\n{separator}\n"
    lines = text.splitlines()
    section_index = lines.index(section)
    next_section_index = find_next_section(lines, section_index + 1)
    section_lines = lines[section_index:next_section_index]
    if header not in section_lines:
        insert_at = section_index + 1
        while insert_at < len(lines) and lines[insert_at].strip():
            insert_at += 1
        lines[insert_at:insert_at] = ["", header, separator]
        next_section_index += 3
    lines.insert(next_section_index, row)
    path.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )


def find_next_section(lines: list[str], start_index: int) -> int:
    for index in range(start_index, len(lines)):
        if lines[index].startswith("## "):
            return index
    return len(lines)


def extract_markdown_section(path: Path, section: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing Markdown file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        section_index = lines.index(section)
    except ValueError:
        return ""
    next_section_index = find_next_section(lines, section_index + 1)
    return "\n".join(lines[section_index:next_section_index]).strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Questforge campaign memory."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser(
        "new", help="Create a campaign workspace."
    )
    new_parser.add_argument("--campaigns-dir", required=True, type=Path)
    new_parser.add_argument("--name", required=True)
    new_parser.add_argument("--tone", default="")
    new_parser.add_argument("--boundaries", default="")
    new_parser.add_argument("--date", dest="date_text")

    session_parser = subparsers.add_parser(
        "next-session",
        help="Create the next session log.",
    )
    session_parser.add_argument("--campaign-root", required=True, type=Path)
    session_parser.add_argument("--date", dest="date_text")
    session_parser.add_argument("--characters-present", default="")
    session_parser.add_argument("--recap", action="append")
    session_parser.add_argument("--start-location", default="")
    session_parser.add_argument("--pressure", default="")
    session_parser.add_argument("--next-choice", default="")

    prompt_parser = subparsers.add_parser(
        "save-image-prompt",
        help="Save a native image generation prompt for a scene.",
    )
    prompt_parser.add_argument("--campaign-root", required=True, type=Path)
    prompt_parser.add_argument("--session", required=True, type=int)
    prompt_parser.add_argument("--scene", required=True, type=int)
    prompt_parser.add_argument("--prompt", required=True)

    visual_parser = subparsers.add_parser(
        "save-visual-prompt",
        help="Save a typed visual prompt and register it in the visual index.",
    )
    visual_parser.add_argument("--campaign-root", required=True, type=Path)
    visual_parser.add_argument("--session", required=True, type=int)
    visual_parser.add_argument("--scene", required=True, type=int)
    visual_parser.add_argument("--kind", required=True)
    visual_parser.add_argument("--label", required=True)
    visual_parser.add_argument("--prompt", required=True)

    inventory_parser = subparsers.add_parser(
        "add-inventory-item",
        help="Record a meaningful inventory item or stateful object.",
    )
    inventory_parser.add_argument("--campaign-root", required=True, type=Path)
    inventory_parser.add_argument("--item", required=True)
    inventory_parser.add_argument("--holder", required=True)
    inventory_parser.add_argument("--mechanical-effect", default="")
    inventory_parser.add_argument("--story-significance", default="")

    xp_parser = subparsers.add_parser(
        "award-xp",
        help="Record XP for a meaningful accomplishment.",
    )
    xp_parser.add_argument("--campaign-root", required=True, type=Path)
    xp_parser.add_argument("--character", required=True)
    xp_parser.add_argument("--amount", required=True, type=int)
    xp_parser.add_argument("--reason", required=True)
    xp_parser.add_argument("--session", type=int)
    xp_parser.add_argument("--scene", type=int)

    loot_parser = subparsers.add_parser(
        "award-loot",
        help="Record notable loot without filling play with junk objects.",
    )
    loot_parser.add_argument("--campaign-root", required=True, type=Path)
    loot_parser.add_argument("--item", required=True)
    loot_parser.add_argument("--holder", required=True)
    loot_parser.add_argument("--source", default="")
    loot_parser.add_argument("--value", default="")
    loot_parser.add_argument("--notes", default="")

    list_inventory_parser = subparsers.add_parser(
        "list-inventory",
        help="Print the campaign inventory table.",
    )
    list_inventory_parser.add_argument(
        "--campaign-root", required=True, type=Path
    )

    hook_parser = subparsers.add_parser(
        "record-hook-status",
        help="Record whether an opening hook is active, merged, or resolved.",
    )
    hook_parser.add_argument("--campaign-root", required=True, type=Path)
    hook_parser.add_argument("--hook", required=True)
    hook_parser.add_argument("--origin", default="")
    hook_parser.add_argument("--status", required=True)
    hook_parser.add_argument("--current-meaning", required=True)
    hook_parser.add_argument("--next-payoff", default="")

    puzzle_parser = subparsers.add_parser(
        "record-puzzle-beat",
        help="Record a non-blocking deduction beat or minigame.",
    )
    puzzle_parser.add_argument("--campaign-root", required=True, type=Path)
    puzzle_parser.add_argument("--title", required=True)
    puzzle_parser.add_argument("--kind", required=True)
    puzzle_parser.add_argument("--required-clue", action="append", default=[])
    puzzle_parser.add_argument("--ask-at-table", required=True)
    puzzle_parser.add_argument("--solution", required=True)
    puzzle_parser.add_argument("--fallback", required=True)
    puzzle_parser.add_argument("--reward", required=True)
    puzzle_parser.add_argument("--symbolic-weight", default="")
    puzzle_parser.add_argument("--status", default="prepared")

    asset_parser = subparsers.add_parser(
        "register-visual-asset",
        help="Copy or register a generated native image asset.",
    )
    asset_parser.add_argument("--campaign-root", required=True, type=Path)
    asset_parser.add_argument("--asset-path", type=Path)
    asset_parser.add_argument("--asset-source", type=Path)
    asset_parser.add_argument("--asset-filename", default="")
    asset_parser.add_argument("--prompt-path", type=Path)
    asset_parser.add_argument("--kind", default="")
    asset_parser.add_argument("--label", default="")
    asset_parser.add_argument("--session", type=int)
    asset_parser.add_argument("--scene", type=int)
    asset_parser.add_argument("--status", default="asset-saved")

    status_parser = subparsers.add_parser(
        "set-visual-status",
        help="Mark a visual prompt or asset as canon, variant, or rejected.",
    )
    status_parser.add_argument("--campaign-root", required=True, type=Path)
    status_parser.add_argument("--status", required=True)
    status_parser.add_argument("--prompt-path", type=Path)
    status_parser.add_argument("--kind", default="")
    status_parser.add_argument("--label", default="")
    status_parser.add_argument("--session", type=int)
    status_parser.add_argument("--scene", type=int)

    list_assets_parser = subparsers.add_parser(
        "list-visual-assets",
        help="List visual prompts and assets for continuity reuse.",
    )
    list_assets_parser.add_argument(
        "--campaign-root", required=True, type=Path
    )
    list_assets_parser.add_argument("--status", action="append")
    list_assets_parser.add_argument("--kind", action="append")
    list_assets_parser.add_argument("--label-contains", default="")
    list_assets_parser.add_argument("--require-asset", action="store_true")
    list_assets_parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )

    return parser


def parse_date(date_text: str | None) -> date | None:
    if date_text is None:
        return None
    return date.fromisoformat(date_text)


def main(arguments: Iterable[str] | None = None) -> int:
    parser = build_parser()
    parsed_arguments = parser.parse_args(arguments)

    if parsed_arguments.command == "new":
        paths = create_campaign(
            campaigns_dir=parsed_arguments.campaigns_dir,
            name=parsed_arguments.name,
            tone=parsed_arguments.tone,
            boundaries=parsed_arguments.boundaries,
            session_date=parse_date(parsed_arguments.date_text),
        )
        print(f"Created campaign: {paths.root}")
        return 0

    if parsed_arguments.command == "next-session":
        session_path = create_next_session(
            parsed_arguments.campaign_root,
            session_date=parse_date(parsed_arguments.date_text),
            characters_present=parsed_arguments.characters_present,
            recap=parsed_arguments.recap,
            start_location=parsed_arguments.start_location,
            pressure=parsed_arguments.pressure,
            next_choice=parsed_arguments.next_choice,
        )
        print(f"Created session: {session_path}")
        return 0

    if parsed_arguments.command == "save-image-prompt":
        prompt_path = save_image_prompt(
            campaign_root=parsed_arguments.campaign_root,
            session_number=parsed_arguments.session,
            scene_number=parsed_arguments.scene,
            prompt=parsed_arguments.prompt,
        )
        print(f"Saved image prompt: {prompt_path}")
        return 0

    if parsed_arguments.command == "add-inventory-item":
        add_inventory_item(
            campaign_root=parsed_arguments.campaign_root,
            item=parsed_arguments.item,
            holder=parsed_arguments.holder,
            mechanical_effect=parsed_arguments.mechanical_effect,
            story_significance=parsed_arguments.story_significance,
        )
        print(f"Added inventory item: {parsed_arguments.item}")
        return 0

    if parsed_arguments.command == "award-xp":
        award_xp(
            campaign_root=parsed_arguments.campaign_root,
            character=parsed_arguments.character,
            amount=parsed_arguments.amount,
            reason=parsed_arguments.reason,
            session_number=parsed_arguments.session,
            scene_number=parsed_arguments.scene,
        )
        print(f"Awarded XP: {parsed_arguments.amount}")
        return 0

    if parsed_arguments.command == "award-loot":
        award_loot(
            campaign_root=parsed_arguments.campaign_root,
            item=parsed_arguments.item,
            holder=parsed_arguments.holder,
            source=parsed_arguments.source,
            value=parsed_arguments.value,
            notes=parsed_arguments.notes,
        )
        print(f"Awarded loot: {parsed_arguments.item}")
        return 0

    if parsed_arguments.command == "list-inventory":
        print(list_inventory(parsed_arguments.campaign_root))
        return 0

    if parsed_arguments.command == "record-hook-status":
        record_hook_status(
            campaign_root=parsed_arguments.campaign_root,
            hook=parsed_arguments.hook,
            origin=parsed_arguments.origin,
            status=parsed_arguments.status,
            current_meaning=parsed_arguments.current_meaning,
            next_payoff=parsed_arguments.next_payoff,
        )
        print(f"Recorded hook status: {parsed_arguments.hook}")
        return 0

    if parsed_arguments.command == "record-puzzle-beat":
        record_puzzle_beat(
            campaign_root=parsed_arguments.campaign_root,
            title=parsed_arguments.title,
            kind=parsed_arguments.kind,
            required_clues=parsed_arguments.required_clue,
            ask_at_table=parsed_arguments.ask_at_table,
            solution=parsed_arguments.solution,
            fallback=parsed_arguments.fallback,
            reward=parsed_arguments.reward,
            symbolic_weight=parsed_arguments.symbolic_weight,
            status=parsed_arguments.status,
        )
        print(f"Recorded puzzle beat: {parsed_arguments.title}")
        return 0

    if parsed_arguments.command == "register-visual-asset":
        asset_path = register_visual_asset(
            campaign_root=parsed_arguments.campaign_root,
            asset_path=parsed_arguments.asset_path,
            asset_source=parsed_arguments.asset_source,
            asset_filename=parsed_arguments.asset_filename,
            prompt_path=parsed_arguments.prompt_path,
            kind=parsed_arguments.kind,
            label=parsed_arguments.label,
            session_number=parsed_arguments.session,
            scene_number=parsed_arguments.scene,
            status=parsed_arguments.status,
        )
        print(f"Registered visual asset: {asset_path}")
        return 0

    if parsed_arguments.command == "set-visual-status":
        set_visual_status(
            campaign_root=parsed_arguments.campaign_root,
            status=parsed_arguments.status,
            prompt_path=parsed_arguments.prompt_path,
            kind=parsed_arguments.kind,
            label=parsed_arguments.label,
            session_number=parsed_arguments.session,
            scene_number=parsed_arguments.scene,
        )
        print(f"Updated visual status: {parsed_arguments.status}")
        return 0

    if parsed_arguments.command == "list-visual-assets":
        entries = list_visual_assets(
            campaign_root=parsed_arguments.campaign_root,
            statuses=parsed_arguments.status,
            kinds=parsed_arguments.kind,
            label_contains=parsed_arguments.label_contains,
            require_asset=parsed_arguments.require_asset,
        )
        if parsed_arguments.format == "json":
            print(
                json.dumps(
                    [asdict(entry) for entry in entries],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(format_visual_assets(entries))
        return 0

    prompt_path = save_visual_prompt(
        campaign_root=parsed_arguments.campaign_root,
        session_number=parsed_arguments.session,
        scene_number=parsed_arguments.scene,
        kind=parsed_arguments.kind,
        label=parsed_arguments.label,
        prompt=parsed_arguments.prompt,
    )
    print(f"Saved visual prompt: {prompt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
