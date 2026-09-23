from src.config import load_sources


def test_load_sources_returns_expected_structure():
    sources = load_sources()

    assert isinstance(sources, dict)
    assert "rss_feeds" in sources
    assert "subreddits" in sources
    assert any(feed["name"] == "Hacker News" for feed in sources["rss_feeds"])
    assert any(sub["name"] == "MachineLearning" for sub in sources["subreddits"])
