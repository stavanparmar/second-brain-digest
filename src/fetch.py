from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

try:
    import praw
except ImportError:  # pragma: no cover
    praw = None

from src.config import ROOT, load_sources

RAW_ITEMS_PATH = ROOT / "raw_items.json"


def _normalize_rss_entry(feed_name: str, entry) -> dict | None:
    """Convert a feedparser entry into the pipeline's item format.

    Entries without a title or link, and entries older than one day, are
    ignored so downstream stages only process useful recent content.

    Args:
        feed_name: Display name of the RSS feed.
        entry: Feedparser entry object to normalize.

    Returns:
        A normalized item dictionary, or ``None`` when the entry is invalid or
        outside the one-day freshness window.
    """
    title = getattr(entry, "title", "Untitled")
    link = getattr(entry, "link", "")
    summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
    published = getattr(entry, "published_parsed", None)

    if not title or not link:
        return None

    if published:
        try:
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        except TypeError:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    if datetime.now(timezone.utc) - dt > timedelta(days=1):
        return None

    return {
        "title": title,
        "url": link,
        "source": feed_name,
        "published": dt.isoformat(),
        "raw_text": summary,
    }


def fetch_rss_feeds(feeds: list[dict]) -> list[dict]:
    """Fetch and normalize recent entries from configured RSS feeds.

    Args:
        feeds: Feed definitions containing ``url`` and optional ``name`` keys.

    Returns:
        Normalized items collected from feeds that can be reached. Individual
        feed failures are logged and do not stop the remaining fetches.
    """
    items: list[dict] = []
    for feed in feeds:
        url = feed.get("url")
        name = feed.get("name", "RSS Feed")
        if not url:
            continue
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries:
                item = _normalize_rss_entry(name, entry)
                if item:
                    items.append(item)
        except Exception as exc:  # pragma: no cover - network issues should not crash the run
            print(f"Unable to fetch RSS feed {name}: {exc}")
    return items


def fetch_subreddit_posts(subreddits: list[dict]) -> list[dict]:
    """Fetch top posts from configured subreddits when Reddit is available.

    Args:
        subreddits: Definitions containing ``name`` and optional ``limit``.

    Returns:
        Normalized Reddit items, or an empty list when PRAW or credentials are
        unavailable. Individual subreddit failures are logged and skipped.
    """
    if praw is None:
        return []

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        return []

    items: list[dict] = []
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=os.getenv("REDDIT_USER_AGENT", "second-brain-digest"),
    )

    for subreddit in subreddits:
        name = subreddit.get("name")
        limit = int(subreddit.get("limit", 5))
        if not name:
            continue
        try:
            for post in reddit.subreddit(name).top(time_filter="day", limit=limit):
                if not getattr(post, "title", None):
                    continue
                items.append(
                    {
                        "title": post.title,
                        "url": post.url,
                        "source": f"r/{name}",
                        "published": datetime.now(timezone.utc).isoformat(),
                        "raw_text": post.selftext or post.title,
                    }
                )
        except Exception as exc:  # pragma: no cover - network or auth problems should be graceful
            print(f"Unable to fetch subreddit {name}: {exc}")
    return items


def main() -> list[dict]:
    """Fetch all configured sources and persist the raw item collection.

    Returns:
        The list written to ``raw_items.json``.
    """
    sources = load_sources()
    items = fetch_rss_feeds(sources.get("rss_feeds", []))
    items.extend(fetch_subreddit_posts(sources.get("subreddits", [])))
    with open(RAW_ITEMS_PATH, "w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2, ensure_ascii=False)
    print(f"Saved {len(items)} items to {RAW_ITEMS_PATH}")
    return items


if __name__ == "__main__":
    main()
