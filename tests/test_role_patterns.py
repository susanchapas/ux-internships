"""Regression coverage for role and early-career matching configuration."""

import json
import re
from pathlib import Path


CONFIG_PATH = Path(__file__).parents[1] / "config.json"


def _patterns():
    with CONFIG_PATH.open() as config_file:
        return json.load(config_file)


def test_requested_design_disciplines_match_titles_and_descriptions():
    config = _patterns()
    title_pattern = re.compile("|".join(config["title_include"]), re.I)
    description_pattern = re.compile(config["description_include"], re.I)
    examples = [
        "A11y Design Intern",
        "Assistive Technology Designer",
        "Design Engineer",
        "Mixed-Methods Researcher",
        "Spatial Computing Designer",
        "Human-AI Interaction Designer",
        "UX Architect",
    ]

    for example in examples:
        assert title_pattern.search(example), example
        assert description_pattern.search(example), example


def test_early_career_modifiers_match_in_both_title_orders():
    config = _patterns()
    design_then_modifier = re.compile(config["title_include"][2], re.I)
    modifier_then_design = re.compile(config["title_include"][3], re.I)
    early_career_pattern = re.compile(config["early_career_include"], re.I)
    modifiers = [
        "Summer Analyst",
        "Undergraduate",
        "Master's",
        "Early Talent",
        "Future Leader",
        "New Graduate",
        "Recent Grad",
        "Pathways",
        "Entry-Level",
        "Cooperative Education",
    ]

    for modifier in modifiers:
        assert design_then_modifier.search(f"Product Designer, {modifier}"), modifier
        assert modifier_then_design.search(f"{modifier} Product Designer"), modifier
        assert early_career_pattern.search(modifier), modifier
