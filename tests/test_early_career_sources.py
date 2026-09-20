import json
from pathlib import Path


SOURCES_PATH = Path(__file__).parents[1] / "early_career_sources.json"


def test_early_career_sources_are_complete_and_unique():
    sources = json.loads(SOURCES_PATH.read_text())["sources"]

    assert len(sources) >= 8
    assert len({source["url"] for source in sources}) == len(sources)
    for source in sources:
        assert {"name", "company", "category", "url", "cadence", "focus"} <= source.keys()
        assert source["url"].startswith("https://")
