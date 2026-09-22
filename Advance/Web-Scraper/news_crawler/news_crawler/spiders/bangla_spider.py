from news_crawler.sites import BANGLA_SITES
from news_crawler.spiders.news_spider import NewsSpider


class BanglaNewsSpider(NewsSpider):
    """Crawls all the Bangla news sites listed in news_crawler/sites.py in one go.

    Usage:
        scrapy crawl bangla
        scrapy crawl bangla -a limit=50

    It takes the same options as the news spider, with different defaults:
      - url: every site in BANGLA_SITES. The limit applies to each site separately.
      - language=bn: only Bangla articles are kept. Some sites mix in English pages,
        e.g. Ajker Patrika's English edition, or BBC News Bangla's links to BBC in English.
      - mode=sitemap: sitemaps give cleaner results than following links on these sites,
        even for a section like bbc.com/bengali. A site whose sitemap fails is still
        crawled by following links.
    """

    name = 'bangla'

    def __init__(self, url=None, language='bn', mode='sitemap', **kwargs):
        super().__init__(url=url or ','.join(BANGLA_SITES.values()), language=language, mode=mode, **kwargs)
