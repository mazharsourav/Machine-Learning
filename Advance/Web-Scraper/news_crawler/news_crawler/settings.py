# Scrapy settings for news_crawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from pathlib import Path

BOT_NAME = "news_crawler"

SPIDER_MODULES = ["news_crawler.spiders"]
NEWSPIDER_MODULE = "news_crawler.spiders"

ADDONS = {}

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 1

DOWNLOAD_DELAY_JITTER = 0.5

# Tells sites who is crawling them. Adding a way to contact you (a URL or email)
# is good practice. Some sites block crawlers; if one returns 403 errors, that's why.
USER_AGENT = "news_crawler/1.0 (personal research project)"

# Lower numbers run first: clean each article up, then save it
ITEM_PIPELINES = {
    'news_crawler.pipelines.NewsCrawlerPipeline': 300,
    'news_crawler.pipelines.SQLitePipeline': 400,
}

# Lower numbers run first, so this skips requests before any other work is done on them
DOWNLOADER_MIDDLEWARES = {
    'news_crawler.middlewares.SkipFullSitesMiddleware': 50,
}

# The database articles are saved to: news.db, next to scrapy.cfg,
# whichever folder the crawl is started from
SQLITE_PATH = str(Path(__file__).resolve().parent.parent / "news.db")

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

LOG_LEVEL = "INFO"

# Keep downloaded pages for an hour (in the .scrapy/httpcache folder), so re-running
# the crawler while you change the code is instant and doesn't re-download everything.
# Runs more than an hour apart always get fresh pages. Set to False to turn it off.
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"
# Don't cache errors, so they are retried on the next run
HTTPCACHE_IGNORE_HTTP_CODES = [403, 429, 500, 502, 503, 504]

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
