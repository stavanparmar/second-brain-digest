from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config import ROOT

SUMMARY_PATH = ROOT / "summarized_items.json"
DIGESTS_DIR = ROOT / "digests"


def build_markdown(items: list[dict]) -> str:
    """Render summarized items as a readable Markdown daily digest.

    Args:
        items: Summarized item dictionaries containing title, source, URL, and
            summary fields.

    Returns:
        Markdown text with a generated timestamp and one section per item.
    """
    lines = [
        "# Daily Digest",
        f"\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    if not items:
        lines.append("No new items were available today.")
        return "\n".join(lines) + "\n"

    for index, item in enumerate(items, start=1):
        lines.append(f"## {index}. {item.get('title', 'Untitled')}")
        lines.append(f"- Source: {item.get('source', 'Unknown')}")
        lines.append(f"- Link: {item.get('url', '#')}")
        lines.append(f"- Summary: {item.get('summary', 'No summary available.')}")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> dict:
    """Build and save the current day's Markdown and HTML digest files.

    Returns:
        A dictionary containing the generated Markdown and HTML file paths.

    Raises:
        FileNotFoundError: If the summarization stage has not produced input.
    """
    DIGESTS_DIR.mkdir(exist_ok=True)

    with open(SUMMARY_PATH, "r", encoding="utf-8") as handle:
        items = json.load(handle)

    date_tag = datetime.utcnow().strftime("%Y-%m-%d")
    markdown_path = DIGESTS_DIR / f"{date_tag}.md"
    html_path = DIGESTS_DIR / f"{date_tag}.html"

    markdown = build_markdown(items)
    markdown_path.write_text(markdown, encoding="utf-8")

    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("digest.html.j2")
    html = template.render(
        title=f"Daily Digest - {date_tag}",
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        items=items,
    )
    html_path.write_text(html, encoding="utf-8")

    print(f"Saved markdown digest to {markdown_path}")
    print(f"Saved HTML digest to {html_path}")
    return {"markdown": str(markdown_path), "html": str(html_path)}


if __name__ == "__main__":
    main()
