"""Shows what's in the database: writes sample_articles.json and updates the stats in README.md.

Run it from this folder (the one with scrapy.cfg) after crawling:
    python report.py
"""
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from news_crawler.settings import SQLITE_PATH
from news_crawler.sites import site_of

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FILE = ROOT / "sample_articles.json"
README_FILE = ROOT / "README.md"

SAMPLE_SIZE = 20
# The sample only shows the start of each article's text. It is committed to a public
# repo, and the full articles belong to their publishers. The database keeps the full text.
SAMPLE_TEXT_LENGTH = 300

LANGUAGE_NAMES = {"en": "English", "bn": "Bangla"}


def words(article):
    return len((article["text"] or "").split())


def language(code):
    """e.g. "en-GB" -> "English". Codes not in LANGUAGE_NAMES are shown as they are."""
    if not code:
        return "unknown"
    base = code.split("-")[0].lower()
    return LANGUAGE_NAMES.get(base, base)


def pick_sample(articles):
    """The newest articles, taking one from each site in turn so every site is shown,
    starting with the Bangla sites."""
    # One group per site and language, since e.g. bdnews24.com has a Bangla and an English
    # edition, and bbc.com has BBC News Bangla and BBC News
    by_edition = defaultdict(list)
    for article in articles:  # already newest first
        by_edition[(site_of(article["link"]), article["language"])].append(article)
    edition_order = sorted(by_edition, key=lambda e: e[1] != "bn")

    sample = []
    while len(sample) < SAMPLE_SIZE and any(by_edition.values()):
        for edition in edition_order:
            if by_edition[edition] and len(sample) < SAMPLE_SIZE:
                sample.append(dict(by_edition[edition].pop(0)))

    for article in sample:
        if article["text"] and len(article["text"]) > SAMPLE_TEXT_LENGTH:
            article["text"] = article["text"][:SAMPLE_TEXT_LENGTH].rstrip() + "…"
    return sample


def language_order(name):
    """Sort key: Bangla first, then English, then any other languages."""
    return (name != "Bangla", name != "English", name)


def stats_markdown(articles):
    by_language = defaultdict(list)
    # One row per site and language, since e.g. bdnews24.com has a Bangla and an English edition
    by_edition = defaultdict(list)
    for article in articles:
        by_language[language(article["language"])].append(article)
        by_edition[(site_of(article["link"]), language(article["language"]))].append(article)

    totals = [
        f"**{len(by_language[name]):,} {name} articles** ({sum(words(a) for a in by_language[name]):,} words)"
        for name in sorted(by_language, key=language_order)
    ]
    totals = totals[0] if len(totals) == 1 else ", ".join(totals[:-1]) + " and " + totals[-1]
    shares = " · ".join(f"{name} {len(by_language[name]) / len(articles):.0%}" for name in sorted(by_language, key=language_order))
    first_day = min(a["scraped_at"] for a in articles)[:10]
    last_day = max(a["scraped_at"] for a in articles)[:10]

    lines = [
        f"{totals} from {len(by_edition)} news sites, collected {first_day} to {last_day} (UTC).",
        "",
        f"Languages: {shares}",
        "",
        "| Site | Language | Articles | Avg. words |",
        "|---|---|---:|---:|",
    ]
    for (site, lang), edition in sorted(by_edition.items(), key=lambda e: (language_order(e[0][1]), -len(e[1]))):
        avg_words = sum(words(a) for a in edition) / len(edition)
        lines.append(f"| {site} | {lang} | {len(edition):,} | {avg_words:,.0f} |")
    lines += ["", "_Generated from the database by `report.py`._"]
    return "\n".join(lines)


def update_readme(stats):
    readme = README_FILE.read_text(encoding="utf-8")
    pattern = r"(<!-- STATS:START -->).*?(<!-- STATS:END -->)"
    if not re.search(pattern, readme, flags=re.DOTALL):
        print(f"No <!-- STATS:START --> / <!-- STATS:END --> markers in {README_FILE}, so it wasn't updated.")
        return
    readme = re.sub(pattern, lambda m: f"{m[1]}\n{stats}\n{m[2]}", readme, flags=re.DOTALL)
    README_FILE.write_text(readme, encoding="utf-8")
    print(f"Updated the stats in {README_FILE}")


def main():
    if not Path(SQLITE_PATH).exists():
        print(f"No database at {SQLITE_PATH} yet. Crawl a site first, e.g.: scrapy crawl news -a url=https://www.bbc.com")
        return

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    articles = [dict(row) for row in conn.execute("SELECT * FROM articles ORDER BY scraped_at DESC")]
    conn.close()
    if not articles:
        print("The database is empty. Crawl a site first.")
        return

    sample = pick_sample(articles)
    SAMPLE_FILE.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(sample)} articles to {SAMPLE_FILE}")

    stats = stats_markdown(articles)
    update_readme(stats)
    print()
    print(stats)


if __name__ == "__main__":
    main()
