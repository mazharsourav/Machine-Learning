import gzip
import json
import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

import scrapy
import trafilatura
from scrapy.exceptions import CloseSpider
from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor

from news_crawler.items import NewsCrawlerItem
from news_crawler.sites import site_of

# trafilatura warns about every non-article page it can't read, which is expected here
logging.getLogger('trafilatura').setLevel(logging.ERROR)

# Pages that are never news articles, so there is no point downloading them
SKIP_LINKS = [
    r'/(login|signin|sign-in|signup|register|account|subscribe|newsletters?)(/|\?|$)',
    r'/(privacy|terms|cookies|contact|about|careers|jobs|help|faq)(/|\?|$)',
    r'/(live|live-blog|video|videos|gallery|galleries|podcasts?|audio)(/|\?|$)',
    # Shopping deals, e.g. NBC News's /select/shopping/ section
    r'/(select|shopping|deals)(/|\?|$)',
]

# URL parts that say nothing about an article's topic, e.g. bbc.com/news/articles/...
GENERIC_SECTIONS = {'news', 'article', 'articles', 'story', 'stories', 'post', 'amp'}

# Pages with less text than this are teasers or listings rather than articles
MIN_WORDS = 150

# The Bengali block of Unicode: every Bangla letter, vowel sign and digit is in it
BANGLA_CHARACTERS = re.compile(r'[ঀ-৿]')

# Where the byline is on sites whose page labels name the wrong author. Samakal's JSON-LD
# credits every article's headline as its author, so its byline is read from the page instead.
BYLINES = {
    'samakal.com': 'div.writter p::text',
}


class NewsSpider(scrapy.Spider):
    """Crawls news articles from any site.

    Usage:
        scrapy crawl news -a url=https://www.bbc.com -O headlines.json

    Options, each passed with -a:
        url    the site or page to crawl. Separate several with commas, and put the
               whole option in quotes: -a "url=https://a.com,https://b.com"
        mode   auto (default), sitemap or links. "auto" reads the site's sitemap when
               url is a homepage, and collects the articles linked from url otherwise.
        days   only take sitemap articles from the last N days (default 2, 0 = any age)
        limit  stop after this many articles from each site (default 100, 0 = no limit)
        depth  in links mode, how many clicks from url to look for articles (default 1)
        language  only keep articles in this language, e.g. bn for Bangla (default: keep all)
    """

    name = 'news'

    def __init__(self, url=None, mode='auto', days=2, limit=100, depth=1, language=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not url:
            raise ValueError('Tell the spider which site to crawl, e.g.: scrapy crawl news -a url=https://www.bbc.com')
        if mode not in ('auto', 'sitemap', 'links'):
            raise ValueError('mode must be auto, sitemap or links')

        urls = [u.strip() for u in url.split(',') if u.strip()]
        self.start_urls = [u if '://' in u else 'https://' + u for u in urls]
        # Without "www." subdomains are allowed too, e.g. edition.cnn.com when crawling www.cnn.com
        self.allowed_domains = sorted({urlparse(u).hostname.removeprefix('www.') for u in self.start_urls})

        self.mode = mode
        self.oldest = datetime.now(timezone.utc) - timedelta(days=float(days)) if float(days) > 0 else None
        self.limit = int(limit)
        self.depth = int(depth)
        self.language = language
        self.article_links = set()
        # Articles found per site, so each site gets its own limit and a big site can't crowd out the rest
        self.sites = {site_of(u) for u in self.start_urls}
        self.site_counts = Counter()
        # Only follow links on the same site, not to its other subdomains like jobs.example.com
        self.link_extractor = LinkExtractor(allow_domains=[urlparse(u).hostname for u in self.start_urls], deny=SKIP_LINKS)

    async def start(self):
        for url in self.start_urls:
            is_homepage = urlparse(url).path in ('', '/')
            if self.mode == 'sitemap' or (self.mode == 'auto' and is_homepage):
                yield scrapy.Request(
                    urljoin(url, '/robots.txt'),
                    callback=self.parse_robots,
                    errback=self.fall_back_to_links,
                    cb_kwargs={'start_url': url},
                )
            else:
                yield scrapy.Request(url, callback=self.parse_start)

    # --- Finding articles through the site's sitemap ---

    def parse_robots(self, response, start_url):
        sitemaps = [
            urljoin(response.url, line.split(':', 1)[1].strip())
            for line in response.text.splitlines()
            if line.strip().lower().startswith('sitemap:')
        ]
        # Ignore sitemaps on other sites: Naya Diganta's robots.txt points to an unrelated demo site
        sitemaps = [s for s in sitemaps if site_of(s) == site_of(start_url)]
        if not sitemaps:
            self.logger.info(f'No sitemap found for {start_url}, following links instead')
            yield scrapy.Request(start_url, callback=self.parse_start)
            return

        # A news sitemap only lists recent articles, so use it instead of the full-site ones when there is one
        news_sitemaps = [s for s in sitemaps if 'news' in urlparse(s).path.rsplit('/', 1)[-1].lower()]
        for sitemap in news_sitemaps or sitemaps:
            yield scrapy.Request(sitemap, callback=self.parse_sitemap, errback=self.fall_back_to_links, cb_kwargs={'start_url': start_url})

    def fall_back_to_links(self, failure):
        """Called when robots.txt or a sitemap can't be read, e.g. it's blocked (403) or the server
        is down (502): collect the articles linked from the start page instead."""
        if self.site_is_full(failure.request.url):  # skipped on purpose by SkipFullSitesMiddleware
            return
        start_url = failure.request.cb_kwargs['start_url']
        self.logger.info(f'Could not read {failure.request.url}, following links from {start_url} instead')
        # If several sitemaps fail, Scrapy's duplicate filter makes sure the start page is only crawled once
        yield scrapy.Request(start_url, callback=self.parse_start)

    def parse_sitemap(self, response, start_url):
        body = response.body
        if body[:2] == b'\x1f\x8b':  # gzip-compressed sitemap (.xml.gz)
            body = gzip.decompress(body)
        sitemap = scrapy.Selector(body=body, type='xml')
        sitemap.remove_namespaces()

        if not sitemap.xpath('//sitemap | //url'):
            # Not a sitemap after all, e.g. New Age's redirects to an error page: follow links instead
            self.logger.info(f'{response.url} lists no pages, following links from {start_url} instead')
            yield scrapy.Request(start_url, callback=self.parse_start)
            return

        # A sitemap index lists more sitemaps
        for entry in sitemap.xpath('//sitemap'):
            url = entry.xpath('loc/text()').get()
            if url and self.is_recent(entry.xpath('lastmod/text()').get()):
                yield scrapy.Request(url.strip(), callback=self.parse_sitemap, errback=self.fall_back_to_links, cb_kwargs={'start_url': start_url})

        # A regular sitemap lists pages. Only pages on the site and section the crawl started
        # at are taken: for bbc.com/bengali only /bengali/... pages, and for prothomalo.com
        # not the pages of its other subdomains, like nagorik.prothomalo.com.
        start = urlparse(start_url)
        for entry in sitemap.xpath('//url'):
            url = (entry.xpath('loc/text()').get() or '').strip()
            date = entry.xpath('news/publication_date/text()').get() or entry.xpath('lastmod/text()').get()
            page = urlparse(url)
            in_section = (
                (page.hostname or '').removeprefix('www.') == start.hostname.removeprefix('www.')
                and page.path.startswith(start.path.rstrip('/') + '/')
            )
            if in_section and self.is_recent(date) and not any(re.search(p, url) for p in SKIP_LINKS):
                # level=depth: don't follow links from these pages; priority=1: fetch them before more sitemaps
                yield scrapy.Request(url, callback=self.parse_page, cb_kwargs={'level': self.depth}, priority=1)

    def is_recent(self, date_text):
        """True if the date is within the last `days` days, or is missing or unreadable."""
        if self.oldest is None or not date_text:
            return True
        try:
            date = datetime.fromisoformat(date_text.strip())
        except ValueError:
            return True
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return date >= self.oldest

    # --- Finding articles by following links ---

    def parse_start(self, response):
        """The page given with -a url, e.g. a homepage or section page: collect the articles it links to."""
        yield from self.follow_links(response, level=1)

    def follow_links(self, response, level):
        for link in self.link_extractor.extract_links(response):
            # Longer URLs are more likely to be articles, so fetch them first
            yield scrapy.Request(link.url, callback=self.parse_page, cb_kwargs={'level': level}, priority=len(link.url))

    # --- Reading an article ---

    def parse_page(self, response, level):
        if not isinstance(response, TextResponse):  # images, PDFs and other files
            return
        if self.site_is_full(response.url):
            return

        doc = trafilatura.bare_extraction(response.text, url=response.url, with_metadata=True, include_comments=False)
        date = response.css('meta[property="article:published_time"]::attr(content)').get() or (doc.date if doc else None)

        if doc and self.looks_like_article(doc, date, response):
            item = self.make_item(doc, date, response)
            if self.language and item['language'] != self.language:
                return
            if item['link'] not in self.article_links:
                self.article_links.add(item['link'])
                self.site_counts[site_of(response.url)] += 1
                yield item
                if self.limit and all(self.site_counts[site] >= self.limit for site in self.sites):
                    raise CloseSpider(f'reached the limit of {self.limit} articles from each site')
        elif level < self.depth:
            # Not an article (e.g. a section page), so look for articles among its links
            yield from self.follow_links(response, level + 1)

    def site_is_full(self, url):
        """True once the site this URL belongs to has `limit` articles. Also used by SkipFullSitesMiddleware."""
        return bool(self.limit) and self.site_counts[site_of(url)] >= self.limit

    def looks_like_article(self, doc, date, response):
        # Most news sites label what kind of page it is. The schema.org label is the most
        # precise: NewsArticle, Article, BlogPosting, ... for articles, and WebPage,
        # VideoObject, LiveBlogPosting, ... for other pages. Pages without one usually have
        # og:type: "article" for articles, "website" for homepages, "video.other" for videos.
        # (Sites don't always follow the standard: The Daily Star's articles say og:type "News".)
        types = schema_types(response)
        og_type = response.css('meta[property="og:type"]::attr(content)').get()
        if types:
            if not any(t.endswith('Article') or t == 'BlogPosting' for t in types):
                return False
        elif og_type and 'article' not in og_type.lower():
            return False
        return bool(doc.title and date and doc.text and len(doc.text.split()) >= MIN_WORDS)

    def make_item(self, doc, date, response):
        # The page's canonical URL drops tracking parameters, so the same article isn't saved twice
        canonical = doc.url if doc.url and urlparse(doc.url).path not in ('', '/') else None

        item = NewsCrawlerItem()
        item['title'] = doc.title
        item['link'] = canonical or response.url
        item['date'] = date
        # trafilatura's author is wrong in two cases: on sites whose labels name the wrong author
        # (see BYLINES), and on pages that credit only an organization, where it takes whatever is
        # where a byline usually goes: on BBC News, the "Share" and "Save" buttons
        item['author'] = site_byline(response) or organization_author(response) or doc.author
        item['category'] = doc.categories[0] if doc.categories else category_from_url(item['link'])
        item['source'] = doc.sitename or urlparse(response.url).hostname
        item['language'] = detect_language(doc.text, response.xpath('/html/@lang').get())
        item['summary'] = doc.description or doc.text.split('\n')[0]
        item['text'] = doc.text
        return item


def detect_language(text, declared):
    """The article's language code, e.g. "bn" or "en".

    Bangla is detected from the text itself: if most of its letters are Bangla script, it's
    Bangla. That's more reliable than the page's own label, which some sites leave out or get
    wrong. Other languages come from the label, shortened from e.g. "en-GB" to "en".
    """
    letters = [c for c in text if c.isalpha()]
    bangla_letters = sum(1 for c in letters if BANGLA_CHARACTERS.match(c))
    if letters and bangla_letters / len(letters) > 0.5:
        return 'bn'

    declared = declared.split('-')[0].lower() if declared else None
    # A page labelled Bangla whose text isn't: better unknown than wrong
    return None if declared == 'bn' else declared


def site_byline(response):
    """The byline shown on the page, for sites listed in BYLINES, e.g. "সমকাল প্রতিবেদক". None otherwise."""
    selector = BYLINES.get(site_of(response.url))
    if not selector:
        return None
    # Some bylines start with an invisible zero-width space
    names = [text.replace('\u200b', '').strip() for text in response.css(selector).getall()]
    return '; '.join(name for name in names if name) or None


def json_ld_entries(response):
    """Every object in the page's JSON-LD blocks, including those in lists and @graph."""
    def walk(data):
        if isinstance(data, list):
            for entry in data:
                yield from walk(entry)
        elif isinstance(data, dict):
            yield data
            yield from walk(data.get('@graph'))

    for block in response.css('script[type="application/ld+json"]::text').getall():
        try:
            yield from walk(json.loads(block))
        except ValueError:
            pass


def schema_types(response):
    """The schema.org types a page declares in its JSON-LD blocks, e.g. {'NewsArticle', 'WebPage'}."""
    types = set()
    for entry in json_ld_entries(response):
        declared = entry.get('@type')
        if isinstance(declared, str):
            types.add(declared)
        elif isinstance(declared, list):
            types.update(t for t in declared if isinstance(t, str))
    return types


def organization_author(response):
    """The organization the page's JSON-LD credits as the author, when it credits no person,
    e.g. "BBC News" for a BBC article without a named reporter. None otherwise."""
    people, organizations = [], []
    for entry in json_ld_entries(response):
        authors = entry.get('author')
        for author in authors if isinstance(authors, list) else [authors]:
            if isinstance(author, dict) and 'Organization' in str(author.get('@type')):
                organizations.append(author.get('name'))
            elif author:
                people.append(author)
    return organizations[0] if organizations and not people else None


def category_from_url(url):
    """Guess the section from the URL, e.g. /health/health-news/some-story -> health."""
    segments = [s for s in urlparse(url).path.split('/') if s]
    for segment in segments[:-1]:  # the last one is the article's own name
        if not segment.isdigit() and segment.lower() not in GENERIC_SECTIONS:
            return segment
    return None
