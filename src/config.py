from __future__ import annotations

from pathlib import Path

import yaml

# Resolve project-relative paths from this module so scripts work from any cwd.
ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = ROOT / "sources.yaml"


def load_sources(path: str | Path = SOURCES_PATH) -> dict:
    """Load configured RSS feeds and subreddits from a YAML file.

    Args:
        path: YAML configuration path. Defaults to the project-level
            ``sources.yaml`` file.

    Returns:
        A dictionary containing ``rss_feeds`` and ``subreddits`` lists. Invalid
        top-level YAML values produce an empty configuration.
    """
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        return {}
    rss_feeds = data.get("rss_feeds") or []
    subreddits = data.get("subreddits") or []
    return {"rss_feeds": rss_feeds, "subreddits": subreddits}
