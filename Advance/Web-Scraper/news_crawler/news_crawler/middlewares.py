# Downloader middlewares sit between the spider and the internet: every request
# passes through them before it is downloaded.
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/downloader-middleware.html

from scrapy.exceptions import IgnoreRequest


class SkipFullSitesMiddleware:
    """Drops waiting requests for sites that already have `limit` articles.

    A site's sitemap can list hundreds of pages, all queued at the start. Without
    this, the crawl would keep downloading them after the site reached its limit,
    only for the spider to throw them away.
    """

    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request):
        site_is_full = getattr(self.crawler.spider, "site_is_full", None)
        if site_is_full and site_is_full(request.url):
            raise IgnoreRequest(f"Already have enough articles from this site: {request.url}")
        return None
