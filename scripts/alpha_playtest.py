"""Long-form alpha playtests for Codex Questforge."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

try:
    from .campaign_memory import (
        create_campaign,
        create_next_session,
        save_visual_prompt,
        slugify,
    )
    from .roll_dice import roll_dice
except ImportError:  # pragma: no cover - direct script execution path
    from campaign_memory import (
        create_campaign,
        create_next_session,
        save_visual_prompt,
        slugify,
    )
    from roll_dice import roll_dice


@dataclass(frozen=True)
class Turn:
    """One deterministic playtest turn."""

    speaker: str
    text: str


@dataclass(frozen=True)
class VisualBeat:
    """A visual prompt that should be persisted during a playtest."""

    scene_number: int
    kind: str
    label: str
    prompt: str


@dataclass(frozen=True)
class Scenario:
    """A long-form alpha playtest scenario."""

    slug: str
    title: str
    mode: str
    tone: str
    boundaries: str
    hero_name: str
    hero_concept: str
    premise: str
    next_choice: str
    meaningful_choice_count: int
    rules_queries: list[str]
    roll_expressions: list[str]
    random_seed: int
    continuity_anchors: list[str]
    fun_targets: list[str]
    watch_risks: list[str]
    turns: list[Turn]
    visual_beats: list[VisualBeat]


@dataclass(frozen=True)
class ScenarioResult:
    """Evidence produced by one alpha playtest scenario."""

    slug: str
    title: str
    mode: str
    campaign_root: str
    transcript_path: str
    report_path: str
    next_session_path: str
    turn_count: int
    meaningful_choice_count: int
    rules_query_count: int
    roll_count: int
    visual_prompt_count: int
    visual_kinds: list[str]
    continuity_anchor_count: int
    fun_score: int
    passed: bool


@dataclass(frozen=True)
class AlphaPlaytestResult:
    """Summary of a complete alpha playtest run."""

    output_dir: str
    summary_path: str
    scenario_count: int
    total_turn_count: int
    total_visual_prompt_count: int
    minimum_fun_score: int
    passed: bool
    scenarios: list[ScenarioResult]


def run_alpha_playtests(
    output_dir: Path,
    session_date: date | None = None,
) -> AlphaPlaytestResult:
    """Run deterministic long-form playtests across several play styles."""

    session_date = session_date or date.today()
    output_dir.mkdir(parents=True, exist_ok=False)
    campaigns_dir = output_dir / "campaigns"
    scenario_results: list[ScenarioResult] = []

    for scenario in build_scenarios():
        scenario_results.append(
            run_scenario(campaigns_dir, scenario, session_date)
        )

    summary_path = output_dir / "alpha-playtest-summary.md"
    summary_path.write_text(
        build_summary_report(scenario_results, session_date),
        encoding="utf-8",
        newline="\n",
    )

    total_turns = sum(result.turn_count for result in scenario_results)
    total_visuals = sum(
        result.visual_prompt_count for result in scenario_results
    )
    minimum_fun_score = min(result.fun_score for result in scenario_results)
    passed = all(result.passed for result in scenario_results)
    return AlphaPlaytestResult(
        output_dir=str(output_dir),
        summary_path=str(summary_path),
        scenario_count=len(scenario_results),
        total_turn_count=total_turns,
        total_visual_prompt_count=total_visuals,
        minimum_fun_score=minimum_fun_score,
        passed=passed,
        scenarios=scenario_results,
    )


def run_scenario(
    campaigns_dir: Path,
    scenario: Scenario,
    session_date: date,
) -> ScenarioResult:
    paths = create_campaign(
        campaigns_dir=campaigns_dir,
        name=scenario.title,
        tone=scenario.tone,
        boundaries=scenario.boundaries,
        session_date=session_date,
    )
    write_alpha_hero(
        paths.characters / f"{slugify(scenario.hero_name)}.md", scenario
    )

    random_generator = random.Random(scenario.random_seed)
    roll_summaries = [
        roll_dice(expression, random_generator=random_generator).summary()
        for expression in scenario.roll_expressions
    ]
    visual_paths = [
        save_visual_prompt(
            paths.root,
            session_number=1,
            scene_number=visual_beat.scene_number,
            kind=visual_beat.kind,
            label=visual_beat.label,
            prompt=visual_beat.prompt,
        )
        for visual_beat in scenario.visual_beats
    ]
    transcript_text = build_transcript(scenario, roll_summaries, session_date)
    transcript_path = paths.root / "alpha-playtest-transcript.md"
    transcript_path.write_text(
        transcript_text,
        encoding="utf-8",
        newline="\n",
    )
    paths.sessions.joinpath("session-001.md").write_text(
        build_session_log(scenario, roll_summaries, session_date),
        encoding="utf-8",
        newline="\n",
    )
    paths.campaign_state.write_text(
        build_campaign_state(scenario, session_date),
        encoding="utf-8",
        newline="\n",
    )
    next_session = create_next_session(
        paths.root,
        session_date=session_date,
        characters_present=scenario.hero_name,
        recap=[
            scenario.premise,
            f"{scenario.hero_name} has created or confirmed "
            f"{len(scenario.continuity_anchors)} continuity anchors.",
            "The table has a clear next decision and no hidden map spoilers.",
        ],
        start_location="the active scene established in session 1",
        pressure=scenario.next_choice,
        next_choice=scenario.next_choice,
    )
    visual_kinds = sorted(
        {visual_kind_from_prompt_path(path) for path in visual_paths}
    )
    fun_score = score_scenario(
        turn_count=count_transcript_turns(transcript_text),
        meaningful_choice_count=scenario.meaningful_choice_count,
        rules_query_count=len(scenario.rules_queries),
        roll_count=len(roll_summaries),
        visual_prompt_count=len(visual_paths),
        visual_kind_count=len(visual_kinds),
        continuity_anchor_count=len(scenario.continuity_anchors),
        has_next_choice=bool(scenario.next_choice),
    )
    passed = fun_score >= 85
    report_path = paths.root / "alpha-playtest-report.md"
    report_path.write_text(
        build_scenario_report(
            scenario,
            roll_summaries,
            visual_paths,
            transcript_path,
            next_session,
            fun_score,
            passed,
        ),
        encoding="utf-8",
        newline="\n",
    )
    return ScenarioResult(
        slug=scenario.slug,
        title=scenario.title,
        mode=scenario.mode,
        campaign_root=str(paths.root),
        transcript_path=str(transcript_path),
        report_path=str(report_path),
        next_session_path=str(next_session),
        turn_count=count_transcript_turns(transcript_text),
        meaningful_choice_count=scenario.meaningful_choice_count,
        rules_query_count=len(scenario.rules_queries),
        roll_count=len(roll_summaries),
        visual_prompt_count=len(visual_paths),
        visual_kinds=visual_kinds,
        continuity_anchor_count=len(scenario.continuity_anchors),
        fun_score=fun_score,
        passed=passed,
    )


def write_alpha_hero(path: Path, scenario: Scenario) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {scenario.hero_name}",
                "",
                f"- Concept: {scenario.hero_concept}",
                "- Level: 1",
                "- Playtest role: stress-test player clarity and table feel",
                "- Visual anchors:",
                *[
                    f"  - {anchor}"
                    for anchor in scenario.continuity_anchors[:3]
                ],
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def visual_kind_from_prompt_path(path: Path) -> str:
    tail = path.name.split("-scene-", maxsplit=1)[1]
    return tail.split("-", maxsplit=2)[1]


def count_transcript_turns(transcript_text: str) -> int:
    return sum(
        1
        for line in transcript_text.splitlines()
        if line.startswith("### Turn ")
    )


def build_transcript(
    scenario: Scenario,
    roll_summaries: list[str],
    session_date: date,
) -> str:
    roll_lines = "\n".join(f"- {summary}" for summary in roll_summaries)
    turn_sections = []
    for index, turn in enumerate(scenario.turns, start=1):
        text = turn.text
        for roll_index, roll_summary in enumerate(roll_summaries, start=1):
            text = text.replace(f"{{ROLL_{roll_index}}}", roll_summary)
        turn_sections.append(
            "\n".join(
                [
                    f"### Turn {index} - {turn.speaker}",
                    "",
                    text.strip(),
                    "",
                ]
            )
        )
    return (
        "\n".join(
            [
                "# Questforge Alpha Playtest Transcript",
                "",
                "## Session",
                "",
                f"- Campaign: {scenario.title}",
                f"- Date: {session_date.isoformat()}",
                f"- Mode: {scenario.mode}",
                f"- Hero: {scenario.hero_name}",
                "",
                "## Premise",
                "",
                scenario.premise,
                "",
                "## Open Rolls",
                "",
                roll_lines,
                "",
                "## Turns",
                "",
                *turn_sections,
            ]
        ).strip()
        + "\n"
    )


def build_session_log(
    scenario: Scenario,
    roll_summaries: list[str],
    session_date: date,
) -> str:
    visual_kinds = ", ".join(
        sorted({visual_beat.kind for visual_beat in scenario.visual_beats})
    )
    rules = "\n".join(
        f"| {query} | Used when the action became uncertain and meaningful. | no |"
        for query in scenario.rules_queries
    )
    rolls = "; ".join(roll_summaries)
    return f"""# Session Log

## Session

- Campaign: {scenario.title}
- Session: 1
- Date: {session_date.isoformat()}
- Characters present: {scenario.hero_name}

## Recap

- {scenario.premise}

## Scenes

### Scene 1

- Location: opening pressure point for {scenario.mode}.
- Pressure: {scenario.next_choice}
- Player action: chooses among risky, legible options.
- Roll: {rolls}
- Outcome: state changes and a future decision are recorded.
- State changes: continuity anchors, visuals, and next session pressure saved.
- Visual prompts saved: {visual_kinds}.

## Rules Rulings

| Ruling | Reason | Keep As House Rule |
| --- | --- | --- |
{rules}

## End State

- Party position: ready to continue from the established scene.
- Immediate next choice: {scenario.next_choice}
- Changed clocks: scenario pressure advanced.
- Changed NPC attitudes: at least one relationship changed.
- Rewards: clarity, clue, item, or tactical position.
- Damage, conditions, resources: tracked in transcript when relevant.
"""


def build_campaign_state(scenario: Scenario, session_date: date) -> str:
    anchors = "\n".join(
        f"- {anchor}" for anchor in scenario.continuity_anchors
    )
    visual_rows = "\n".join(
        (
            f"| {visual_beat.label} | {visual_beat.kind} | "
            f"session 1 scene {visual_beat.scene_number} | prompt-saved |"
        )
        for visual_beat in scenario.visual_beats
    )
    return f"""# Campaign State

## Metadata

- Campaign: {scenario.title}
- System: 5E-compatible, SRD-grounded
- Tone: {scenario.tone}
- Content boundaries: {scenario.boundaries}
- SRD attribution included: yes
- Last updated: {session_date.isoformat()}

## Party

| Character | Player | Concept | Level | Notes |
| --- | --- | --- | --- | --- |
| {scenario.hero_name} | Alpha self-play | {scenario.hero_concept} | 1 | Stress-test player clarity |

## Current Situation

- Premise: {scenario.premise}
- Immediate pressure: {scenario.next_choice}
- Meaningful choices observed: {scenario.meaningful_choice_count}

## Continuity Anchors

{anchors}

## Visual Continuity

| Subject | Type | Location | Status |
| --- | --- | --- | --- |
{visual_rows}

## Open Threads

- Can the next session start without chat memory?
- Does the next decision feel risky, fair, and exciting?
- Which visual anchor should be reused first?
"""


def score_scenario(
    turn_count: int,
    meaningful_choice_count: int,
    rules_query_count: int,
    roll_count: int,
    visual_prompt_count: int,
    visual_kind_count: int,
    continuity_anchor_count: int,
    has_next_choice: bool,
) -> int:
    score = 0
    score += min(turn_count, 24)
    score += min(meaningful_choice_count * 6, 24)
    score += 10 if rules_query_count else 0
    score += 10 if roll_count else 0
    score += min(visual_prompt_count * 4, 24)
    score += min(visual_kind_count * 3, 15)
    score += min(continuity_anchor_count * 3, 12)
    score += 5 if has_next_choice else 0
    return min(score, 100)


def build_scenario_report(
    scenario: Scenario,
    roll_summaries: list[str],
    visual_paths: list[Path],
    transcript_path: Path,
    next_session_path: Path,
    fun_score: int,
    passed: bool,
) -> str:
    target_lines = "\n".join(f"- {target}" for target in scenario.fun_targets)
    risk_lines = "\n".join(f"- {risk}" for risk in scenario.watch_risks)
    anchor_lines = "\n".join(
        f"- {anchor}" for anchor in scenario.continuity_anchors
    )
    visual_lines = "\n".join(f"- `{path.name}`" for path in visual_paths)
    roll_lines = "\n".join(f"- `{summary}`" for summary in roll_summaries)
    result_text = "Pass" if passed else "Needs work"
    return f"""# Questforge Alpha Playtest Report

## Result

{result_text}. Fun score: {fun_score}/100.

## Scenario

- Title: {scenario.title}
- Mode: {scenario.mode}
- Hero: {scenario.hero_name}
- Transcript: `{transcript_path.name}`
- Next session: `{next_session_path.name}`

## Fun Targets

{target_lines}

## Evidence

- Turns: {len(scenario.turns)}
- Meaningful choices: {scenario.meaningful_choice_count}
- Rule lookups or rulings: {len(scenario.rules_queries)}
- Rolls: {len(roll_summaries)}
- Visual prompts: {len(visual_paths)}

## Rolls

{roll_lines}

## Visual Prompts

{visual_lines}

## Continuity Anchors

{anchor_lines}

## Watch Risks

{risk_lines}

## Next Play Question

{scenario.next_choice}
"""


def build_summary_report(
    scenario_results: list[ScenarioResult],
    session_date: date,
) -> str:
    rows = "\n".join(
        (
            f"| {result.title} | {result.mode} | {result.turn_count} | "
            f"{result.visual_prompt_count} | {', '.join(result.visual_kinds)} | "
            f"{result.fun_score} | {'pass' if result.passed else 'needs work'} |"
        )
        for result in scenario_results
    )
    weakest = min(scenario_results, key=lambda result: result.fun_score)
    total_turns = sum(result.turn_count for result in scenario_results)
    total_visuals = sum(
        result.visual_prompt_count for result in scenario_results
    )
    return f"""# Questforge Alpha Playtest Summary

## Run

- Date: {session_date.isoformat()}
- Scenarios: {len(scenario_results)}
- Total turns: {total_turns}
- Total visual prompts: {total_visuals}
- Weakest score: {weakest.title} at {weakest.fun_score}/100

## Scenario Matrix

| Scenario | Mode | Turns | Visuals | Visual Kinds | Fun Score | Result |
| --- | --- | ---: | ---: | --- | ---: | --- |
{rows}

## Readout

The harness is meant to catch boring play, unclear next actions, weak visual
cadence, missing rules pressure, and continuity that cannot survive a resumed
session. A passing run is not proof that every table will love the plugin, but
it is stronger evidence than a smoke test because it covers mystery, social
commerce, and dungeon pressure with persistent visual artifacts.
"""


def build_scenarios() -> list[Scenario]:
    return [
        build_amber_gate_scenario(),
        build_saltglass_market_scenario(),
        build_rootbound_vault_scenario(),
    ]


def original_visual_prompt(subject: str, purpose: str, style: str) -> str:
    return (
        "Original 5E-compatible fantasy visual, unofficial and not using "
        "official D&D setting, logo, product art, or named copyrighted "
        f"characters. Subject: {subject}. Purpose: {purpose}. Style: {style}. "
        "Avoid official logos, copied product art, readable text, and "
        "commercial adventure identity."
    )


def build_amber_gate_scenario() -> Scenario:
    turns = [
        Turn(
            "DM",
            "The bridge is slick with black rain. The far lantern burns in a "
            "place the storm refuses to touch. Mara can study it, cross now, "
            "or push Brother Caldus for the truth.",
        ),
        Turn(
            "Player",
            "Mara studies the rain first. She does not step onto the bridge "
            "until she knows whether the lantern is bait.",
        ),
        Turn(
            "DM",
            "Ruling target: ability checks. Wisdom (Survival) fits the "
            "weather and tracks. The stakes are clear: a success reveals the "
            "safe edge of the phenomenon, and a failure advances the gate.",
        ),
        Turn(
            "Player",
            "She accepts the risk and uses the bow tip to mark the wet stones "
            "where rain changes direction.",
        ),
        Turn(
            "DM",
            "Open roll: {ROLL_1}. Success. The rain curves around the lantern "
            "in a perfect oval. The bridge is not haunted by a light; it is "
            "overlapping another place.",
        ),
        Turn(
            "Player",
            "Mara asks Caldus what the copper tube has to do with an "
            "overlapping place.",
        ),
        Turn(
            "DM",
            "Caldus admits the tube came from a shrine that should be on the "
            "far side. He has hidden it for thirty years because the road on "
            "the seal changes after every storm.",
        ),
        Turn(
            "Player",
            "Mara wants the tube visible and sketched before anyone opens it.",
        ),
        Turn(
            "DM",
            "Visual saved: Copper Map Tube. The prompt locks the amber wax, "
            "dented cap, pilgrim-road etching, and leather cord.",
        ),
        Turn(
            "Player",
            "She asks whether the whisper wants Caldus, the tube, or the seal.",
        ),
        Turn(
            "DM",
            "The whisper says, 'Only the road remembers its door.' Caldus "
            "flinches at the word door. His attitude changes from frightened "
            "guide to frightened witness.",
        ),
        Turn(
            "Player",
            "Mara sketches a fog-of-war map and marks only the west approach, "
            "the bridge span, the lanterns, and the abbey silhouette.",
        ),
        Turn(
            "DM",
            "Visual saved: Gorge Bridge Fog Map. Hidden rooms, secret paths, "
            "traps, and creature positions remain under blank mist.",
        ),
        Turn(
            "Player",
            "She tries to speak to the whisper without promising the tube.",
        ),
        Turn(
            "DM",
            "Ruling target: social checks. A cautious parley uses Charisma "
            "(Persuasion), but the whisper can only answer in landmarks. The "
            "DC is moderate because Mara offers attention, not obedience.",
        ),
        Turn(
            "Player",
            "Mara says she can return the road to memory, but not to a thief.",
        ),
        Turn(
            "DM",
            "Open roll: {ROLL_2}. Partial success. The whisper shows the "
            "first safe stone and demands that Caldus be kept away from the "
            "third lantern.",
        ),
        Turn(
            "Player",
            "Mara chooses to hold position. She wants a recap image before "
            "the next session so the table remembers the spatial tension.",
        ),
        Turn(
            "DM",
            "Visual saved: Rain Bent Around The Lantern. Abbey Gate clock "
            "advances to 2/6, but Mara now has a fair route onto the bridge.",
        ),
        Turn(
            "Player",
            "Next time, Mara will either cross by the safe stones, challenge "
            "the whisper's claim, or open the tube despite Caldus's fear.",
        ),
    ]
    return Scenario(
        slug="amber-gate",
        title="The Amber Gate Alpha",
        mode="mystery exploration",
        tone="heroic mystery with eerie ruins",
        boundaries="no graphic gore",
        hero_name="Mara Vey",
        hero_concept="practical human ranger",
        premise="A bridge, a copper tube, and an out-of-phase lantern turn a "
        "simple escort into a mystery with spatial stakes.",
        next_choice="cross by the safe stones, challenge the whisper, or open the tube",
        meaningful_choice_count=4,
        rules_queries=["ability checks", "social checks"],
        roll_expressions=["d20+4", "d20+2"],
        random_seed=19,
        continuity_anchors=[
            "Mara's dark travel cloak and wrapped bow",
            "Brother Caldus clutching the copper tube",
            "three amber lanterns on the rain-slick gorge bridge",
            "fog-of-war bridge map that hides the abbey interior",
        ],
        fun_targets=[
            "Open with pressure in the first message.",
            "Make the player choose between safety, truth, and momentum.",
            "Use visuals as memory anchors, not decoration.",
            "End with a clear next session decision.",
        ],
        watch_risks=[
            "Too many proper nouns could bury the actionable choice.",
            "The whisper must stay interpretable enough to be fun.",
        ],
        turns=turns,
        visual_beats=[
            VisualBeat(
                1,
                "location",
                "Gorge Bridge",
                original_visual_prompt(
                    "rain-slick green stone bridge over a storm gorge, three "
                    "amber lanterns glowing across the span",
                    "establish the opening spatial problem",
                    "painterly fantasy realism, cinematic wide shot",
                ),
            ),
            VisualBeat(
                1,
                "item",
                "Copper Map Tube",
                original_visual_prompt(
                    "sealed copper map tube with amber wax, pilgrim-road "
                    "etching, dented cap, and leather cord",
                    "persistent clue and inventory object",
                    "isolated prop view on wet dark stone",
                ),
            ),
            VisualBeat(
                2,
                "map",
                "Gorge Bridge Fog Map",
                original_visual_prompt(
                    "fog-of-war parchment map showing only the west approach, "
                    "bridge span, three lantern marks, and distant abbey "
                    "silhouette while hiding unexplored spaces",
                    "make spatial choices fair without spoilers",
                    "table-useful parchment map with sparse labels",
                ),
            ),
            VisualBeat(
                3,
                "recap",
                "Rain Bent Around The Lantern",
                original_visual_prompt(
                    "Mara Vey noticing rain bending around a floating amber "
                    "lantern while Brother Caldus clutches the copper tube",
                    "end-of-session memory postcard",
                    "heroic mystery, cool storm light, warm amber glow",
                ),
            ),
            VisualBeat(
                3,
                "symbol",
                "Pilgrim Road Seal",
                original_visual_prompt(
                    "amber wax seal stamped with a winding pilgrim-road mark "
                    "and tiny bridge notch",
                    "recurring faction or location symbol",
                    "macro prop detail, high texture, no readable text",
                ),
            ),
        ],
    )


def build_saltglass_market_scenario() -> Scenario:
    turns = [
        Turn(
            "DM",
            "The market is built under blue glass awnings that ring when the "
            "wind changes. The user can shop, investigate the missing caravan, "
            "or confront the merchant who recognizes the hero's signet.",
        ),
        Turn(
            "Player",
            "Ilyra wants to browse first and learn what people are afraid to "
            "sell openly.",
        ),
        Turn(
            "DM",
            "Visual saved: Saltglass Market. The scene shows price boards, "
            "blue awnings, lantern jars, and three suspicious stalls.",
        ),
        Turn(
            "Player",
            "Ilyra asks the spice seller why one stall has no prices.",
        ),
        Turn(
            "DM",
            "Ruling target: insight. Wisdom (Insight) can read the seller's "
            "fear before Ilyra spends coin. A success reveals leverage; a "
            "failure makes the merchant clam up.",
        ),
        Turn(
            "Player",
            "She keeps her tone friendly and watches the seller's hands.",
        ),
        Turn(
            "DM",
            "Open roll: {ROLL_1}. Success. The seller taps twice near a tray "
            "of smoked salt whenever the unpriced stall is mentioned.",
        ),
        Turn(
            "Player",
            "Ilyra buys the smoked salt and asks what else travels with it.",
        ),
        Turn(
            "DM",
            "The merchant offers three concrete options: a stormproof cloak, a "
            "sealed courier box, and a cracked mirror charm that reflects "
            "doors which are behind you.",
        ),
        Turn(
            "Player",
            "Ilyra wants an inventory board before choosing, because she has "
            "limited coin and one attunement slot reserved.",
        ),
        Turn(
            "DM",
            "Visual saved: merchant inventory. Known prices and visible "
            "qualities are shown; hidden properties are not implied.",
        ),
        Turn(
            "Player",
            "She bargains for the courier box by offering news from the road.",
        ),
        Turn(
            "DM",
            "Ruling target: persuasion. Charisma (Persuasion) fits a sincere "
            "trade. The seller wants proof that Ilyra is not working for the "
            "caravan thieves.",
        ),
        Turn(
            "Player",
            "Ilyra shows her signet but keeps her family name out of it.",
        ),
        Turn(
            "DM",
            "Open roll: {ROLL_2}. Failure with a soft landing. The price does "
            "not drop, but the seller reveals the box was ordered by someone "
            "using Ilyra's old family crest.",
        ),
        Turn(
            "Player",
            "Ilyra buys the box anyway and asks for the stall owner's name.",
        ),
        Turn(
            "DM",
            "The name is Voss Merrow. The market clock advances to 1/4: Voss "
            "has heard someone is asking about the caravan.",
        ),
        Turn(
            "Player",
            "Ilyra wants a portrait-style visual of Voss before meeting him, "
            "based only on what witnesses describe.",
        ),
        Turn(
            "DM",
            "Visual saved: Voss Merrow witness portrait. It is marked as "
            "rumor-based so later corrections can update continuity.",
        ),
        Turn(
            "Player",
            "She ends by choosing between opening the box now, following Voss, "
            "or using the mirror charm near the market gate.",
        ),
        Turn(
            "DM",
            "Session closes with commerce, social pressure, and a concrete "
            "purchase that matters. The next scene starts with Ilyra holding "
            "the sealed courier box.",
        ),
    ]
    return Scenario(
        slug="saltglass-market",
        title="Saltglass Market Alpha",
        mode="social commerce",
        tone="bright intrigue with practical stakes",
        boundaries="no graphic gore, no coercive romance",
        hero_name="Ilyra Vale",
        hero_concept="quick-witted half-elf envoy",
        premise="A market visit becomes a social puzzle when a sealed courier "
        "box points back to the hero's own family crest.",
        next_choice="open the courier box, follow Voss, or test the mirror charm",
        meaningful_choice_count=5,
        rules_queries=["insight", "persuasion"],
        roll_expressions=["d20+3", "d20+5"],
        random_seed=31,
        continuity_anchors=[
            "blue saltglass awnings that ring in the wind",
            "Ilyra's covered family signet",
            "sealed courier box with old family crest",
            "rumor-based Voss Merrow portrait",
        ],
        fun_targets=[
            "Make shopping feel like play, not a menu dump.",
            "Use price and inventory visuals to support decisions.",
            "Let a failed social roll create information instead of a dead end.",
            "Preserve rumor uncertainty for later correction.",
        ],
        watch_risks=[
            "Merchant scenes can become too transactional.",
            "Inventory diagrams must avoid inventing hidden mechanics.",
        ],
        turns=turns,
        visual_beats=[
            VisualBeat(
                1,
                "location",
                "Saltglass Market",
                original_visual_prompt(
                    "open-air fantasy market under blue glass awnings, lantern "
                    "jars, smoked salt trays, and suspicious unpriced stall",
                    "establish a commerce scene with social clues",
                    "colorful grounded fantasy market, clear readable staging",
                ),
            ),
            VisualBeat(
                2,
                "merchant",
                "Saltglass Merchant Board",
                original_visual_prompt(
                    "merchant display with stormproof cloak, sealed courier "
                    "box, cracked mirror charm, coin piles, and visible quality "
                    "tags represented without readable text",
                    "help the player compare purchases",
                    "organized tabletop prop board, no exact readable prices",
                ),
            ),
            VisualBeat(
                2,
                "item",
                "Sealed Courier Box",
                original_visual_prompt(
                    "small black courier box sealed with pale wax and an old "
                    "family crest, brass corners, travel scuffs",
                    "persistent purchased clue",
                    "isolated prop view on blue market cloth",
                ),
            ),
            VisualBeat(
                3,
                "character",
                "Voss Merrow Witness Portrait",
                original_visual_prompt(
                    "rumor-based portrait of a neat merchant with silver rings, "
                    "narrow smile, and salt-stained green coat",
                    "mark an uncertain NPC description for later correction",
                    "painted witness-board portrait, slightly incomplete edges",
                ),
            ),
            VisualBeat(
                3,
                "inventory",
                "Ilyra Travel Inventory",
                original_visual_prompt(
                    "organized adventurer inventory board with rapier, travel "
                    "satchel, smoked salt, sealed courier box, and covered "
                    "signet pouch",
                    "show carried gear and new purchase clearly",
                    "top-down inventory diagram, clean grouping, no readable text",
                ),
            ),
        ],
    )


def build_rootbound_vault_scenario() -> Scenario:
    turns = [
        Turn(
            "DM",
            "The vault door is a living root lattice. It breathes in the dark "
            "and opens slightly whenever the party stops speaking.",
        ),
        Turn(
            "Player",
            "Tamsin asks for a map view before entering. She wants to know "
            "which exits are visible and which areas remain unknown.",
        ),
        Turn(
            "DM",
            "Visual saved: Rootbound Vault Fog Map. Only the entry chamber, "
            "root door, water channel, and two visible exits are shown.",
        ),
        Turn(
            "Player",
            "Tamsin moves quietly to the water channel and checks whether the "
            "roots react to vibration.",
        ),
        Turn(
            "DM",
            "Ruling target: stealth. Dexterity (Stealth) matters because sound "
            "and vibration may wake the door. A failure costs position, not "
            "instant combat.",
        ),
        Turn(
            "Player",
            "She wraps the metal buckles on her pack and steps on wet moss.",
        ),
        Turn(
            "DM",
            "Open roll: {ROLL_1}. Success. The roots twitch toward metal but "
            "ignore soft pressure on moss.",
        ),
        Turn(
            "Player",
            "Tamsin marks that on the map and offers the door a drop of water "
            "instead of blood.",
        ),
        Turn(
            "DM",
            "The door drinks the water and reveals a hollow containing a seed "
            "of green fire. The table gets a clear choice: take it, speak to "
            "it, or leave it as a ward.",
        ),
        Turn(
            "Player",
            "She speaks first. If it answers, she wants to know what it guards.",
        ),
        Turn(
            "DM",
            "Ruling target: arcana. Intelligence (Arcana) can interpret the "
            "seed's magical pressure without touching it.",
        ),
        Turn(
            "Player",
            "Tamsin studies heat, shadow, and the root patterns around the "
            "seed.",
        ),
        Turn(
            "DM",
            "Open roll: {ROLL_2}. Partial success. The seed guards a memory of "
            "the vault's builder, but touching it wakes the bramble sentinel.",
        ),
        Turn(
            "Player",
            "She asks for a creature visual before deciding whether to risk "
            "waking it.",
        ),
        Turn(
            "DM",
            "Visual saved: Bramble Sentinel. It shows branch armor, ember eyes, "
            "and a cracked stone mask, but no stat block or hidden weakness.",
        ),
        Turn(
            "Player",
            "Tamsin tries to wedge her mirror under the root without touching "
            "the seed.",
        ),
        Turn(
            "DM",
            "This is a tool-assisted Dexterity check. The consequence is loud "
            "root movement if she fails.",
        ),
        Turn(
            "Player",
            "She commits. If it wakes the sentinel, she wants a route to flee, "
            "not a forced fight.",
        ),
        Turn(
            "DM",
            "Open roll: {ROLL_3}. Failure. The mirror slips, roots scrape "
            "stone, and the sentinel wakes. The map updates with the safe moss "
            "path and the blocked metal-grate path.",
        ),
        Turn(
            "Player",
            "Tamsin chooses flight over combat and spends her action to pull "
            "chalk across the safe path for later.",
        ),
        Turn(
            "DM",
            "Visual saved: chase scene. The sentinel is close enough to matter "
            "but not close enough to remove agency. Vault clock advances to "
            "2/6.",
        ),
        Turn(
            "Player",
            "She ends at the water channel with the seed still in place. Next "
            "time she can parley, distract the sentinel, or retreat and return "
            "with wooden tools.",
        ),
        Turn(
            "DM",
            "Session closes with a map update, a creature anchor, and a clear "
            "non-combat path. No unexplored chamber is revealed early.",
        ),
    ]
    return Scenario(
        slug="rootbound-vault",
        title="Rootbound Vault Alpha",
        mode="dungeon pressure",
        tone="tense exploration with fair danger",
        boundaries="no graphic gore, no body horror",
        hero_name="Tamsin Reed",
        hero_concept="careful halfling delver",
        premise="A living vault tests whether the player can read space, "
        "avoid spoilers, and choose between treasure, knowledge, and safety.",
        next_choice=(
            "parley with the sentinel, distract it, or retreat for wooden tools"
        ),
        meaningful_choice_count=5,
        rules_queries=["stealth", "arcana", "dexterity checks"],
        roll_expressions=["d20+6", "d20+3", "d20+4"],
        random_seed=35,
        continuity_anchors=[
            "root lattice door that reacts to metal",
            "green fire seed inside the hollow",
            "bramble sentinel with ember eyes and cracked stone mask",
            "fog map showing safe moss path and blocked metal grate",
        ],
        fun_targets=[
            "Make dungeon mapping useful at the table.",
            "Offer non-combat choices even when a creature wakes.",
            "Keep failed rolls active instead of punitive.",
            "Protect fog-of-war secrets.",
        ],
        watch_risks=[
            "Dungeon pressure can become puzzle-box opacity.",
            "Creature visuals must not imply hidden stat information.",
        ],
        turns=turns,
        visual_beats=[
            VisualBeat(
                1,
                "map",
                "Rootbound Vault Fog Map",
                original_visual_prompt(
                    "fog-of-war dungeon map with entry chamber, living root "
                    "door, water channel, two visible exits, safe moss path, "
                    "and blank unexplored areas",
                    "support exploration without revealing secrets",
                    "top-down parchment map, restrained labels, hidden rooms obscured",
                ),
            ),
            VisualBeat(
                1,
                "location",
                "Living Root Door",
                original_visual_prompt(
                    "vault door made from breathing root lattice, wet moss, "
                    "black stone, and tiny green fire leaking through cracks",
                    "anchor the dungeon's central pressure",
                    "painterly fantasy realism, eerie but readable",
                ),
            ),
            VisualBeat(
                2,
                "item",
                "Green Fire Seed",
                original_visual_prompt(
                    "small seed of green fire nested inside root hollow, "
                    "lighting wet bark and old stone without burning them",
                    "persistent magical object and temptation",
                    "macro fantasy prop, high detail, no text",
                ),
            ),
            VisualBeat(
                3,
                "creature",
                "Bramble Sentinel",
                original_visual_prompt(
                    "humanoid sentinel of braided brambles with ember eyes and "
                    "a cracked stone mask, rising from a root-filled vault",
                    "make the threat understandable without a stat block",
                    "dramatic creature concept art, no gore",
                ),
            ),
            VisualBeat(
                3,
                "scene",
                "Moss Path Chase",
                original_visual_prompt(
                    "small delver marking a moss path with chalk while a "
                    "bramble sentinel pushes through roots behind her",
                    "recap the failed roll and fair escape route",
                    "dynamic action scene, tense but not grim",
                ),
            ),
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run long-form Questforge alpha playtests."
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--date", dest="date_text")
    return parser


def parse_date(date_text: str | None) -> date | None:
    if date_text is None:
        return None
    return date.fromisoformat(date_text)


def main(arguments: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parsed_arguments = build_parser().parse_args(arguments)
    result = run_alpha_playtests(
        output_dir=parsed_arguments.output_dir,
        session_date=parse_date(parsed_arguments.date_text),
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
