# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import logging
import sqlite3
import unicodedata

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class NewsCrawlerPipeline:
    def process_item(self, item):
        adapter = ItemAdapter(item)

        # Some Bangla letters can be typed as different Unicode sequences, e.g. ড় as one
        # character or as ড followed by the nukta sign ়. They look identical, but a computer
        # sees different words. NFC normalization stores every word the same way.
        for field in ("title", "summary", "author", "category", "text"):
            if adapter.get(field):
                adapter[field] = unicodedata.normalize("NFC", adapter[field])

        # Collapse extra spaces and line breaks in the short fields.
        # "text" keeps its line breaks, since they separate paragraphs.
        for field in ("title", "summary", "author", "category"):
            if adapter.get(field):
                adapter[field] = " ".join(adapter[field].split())

        return item


class SQLitePipeline:
    """Saves articles to an SQLite database. The link is the primary key,
    so an article saved in an earlier run is skipped instead of duplicated."""

    def __init__(self, path):
        self.path = path

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get("SQLITE_PATH"))

    def open_spider(self):
        # Runs once when the crawl starts: open the database file (it's created if missing)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                link       TEXT PRIMARY KEY,
                title      TEXT,
                date       TEXT,
                author     TEXT,
                category   TEXT,
                source     TEXT,
                language   TEXT,
                summary    TEXT,
                text       TEXT,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.new = 0
        self.already_saved = 0

    def process_item(self, item):
        # Runs once per article: save it, or skip it if the link is already saved
        a = ItemAdapter(item)
        cursor = self.conn.execute(
            """INSERT OR IGNORE INTO articles
               (link, title, date, author, category, source, language, summary, text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (a.get("link"), a.get("title"), a.get("date"), a.get("author"), a.get("category"),
             a.get("source"), a.get("language"), a.get("summary"), a.get("text")),
        )
        self.conn.commit()
        if cursor.rowcount:
            self.new += 1
        else:
            self.already_saved += 1
        return item

    def close_spider(self):
        # Runs once when the crawl ends
        self.conn.close()
        logger.info(f"Saved {self.new} new articles to {self.path} ({self.already_saved} were already there)")
