from news_crawler.sites import INTERNATIONAL_SITES
from news_crawler.spiders.news_spider import NewsSpider


class InternationalNewsSpider(NewsSpider):
    """Crawls all the international English-language news sites listed in news_crawler/sites.py in one go.

    Usage:
        scrapy crawl international
        scrapy crawl international -a limit=50

    Works like the english spider: without -a url it crawls every site in INTERNATIONAL_SITES,
    the limit applies to each site separately, and only English articles are kept.
    """

    name = 'international'

    def __init__(self, url=None, language='en', mode='sitemap', **kwargs):
        super().__init__(url=url or ','.join(INTERNATIONAL_SITES.values()), language=language, mode=mode, **kwargs)
