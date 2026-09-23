from __future__ import annotations

import json
import os
from pathlib import Path

from src.config import ROOT

RAW_ITEMS_PATH = ROOT / "raw_items.json"
SUMMARY_PATH = ROOT / "summarized_items.json"


def fallback_summary(text: str) -> str:
    """Create a deterministic short summary without an external API.

    Args:
        text: Source text to normalize and truncate.

    Returns:
        Whitespace-normalized text limited to 180 characters, or a placeholder
        when no usable text is available.
    """
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return "No summary available."
    if len(cleaned) <= 180:
        return cleaned
    return cleaned[:177].rstrip() + "..."


def summarize_item(item: dict) -> dict:
    """Add an LLM summary to one item, falling back to local text trimming.

    Args:
        item: Mutable normalized item dictionary with ``raw_text`` and title
            fields.

    Returns:
        The same item dictionary with a ``summary`` field. Missing credentials
        and API failures use the deterministic fallback summary.
    """
    raw_text = item.get("raw_text") or item.get("title") or ""
    summary = fallback_summary(raw_text)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        item["summary"] = summary
        return item

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        prompt = (
            "Summarize this article in 2-3 sentences, plain and neutral tone. "
            f"Title: {item.get('title', 'Untitled')}\n\nContent: {raw_text}"
        )
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text:
            summary = text
    except Exception as exc:  # pragma: no cover - API/network failures should degrade gracefully
        print(f"Anthropic summary failed: {exc}")

    item["summary"] = summary
    return item


def main() -> list[dict]:
    """Read raw items, summarize them, and persist the summarized collection.

    Returns:
        The list written to ``summarized_items.json``.

    Raises:
        FileNotFoundError: If the fetch stage has not produced raw items.
    """
    if not RAW_ITEMS_PATH.exists():
        raise FileNotFoundError(f"Missing raw items file: {RAW_ITEMS_PATH}")

    with open(RAW_ITEMS_PATH, "r", encoding="utf-8") as handle:
        items = json.load(handle)

    summarized = [summarize_item(item) for item in items]
    with open(SUMMARY_PATH, "w", encoding="utf-8") as handle:
        json.dump(summarized, handle, indent=2, ensure_ascii=False)

    print(f"Saved {len(summarized)} summarized items to {SUMMARY_PATH}")
    return summarized


if __name__ == "__main__":
    main()
