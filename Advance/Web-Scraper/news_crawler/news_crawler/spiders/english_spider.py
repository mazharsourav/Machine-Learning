from news_crawler.sites import ENGLISH_SITES
from news_crawler.spiders.news_spider import NewsSpider


class EnglishNewsSpider(NewsSpider):
    """Crawls all the English-language Bangladeshi news sites listed in news_crawler/sites.py in one go.

    Usage:
        scrapy crawl english
        scrapy crawl english -a limit=50

    Works like the bangla spider: without -a url it crawls every site in ENGLISH_SITES,
    the limit applies to each site separately, and only English articles are kept.
    """

    name = 'english'

    def __init__(self, url=None, language='en', mode='sitemap', **kwargs):
        super().__init__(url=url or ','.join(ENGLISH_SITES.values()), language=language, mode=mode, **kwargs)
