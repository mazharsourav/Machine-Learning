"""The news sites this crawler is tested on, and a helper for telling sites apart."""
import tldextract

# Bangla-language news sites that `scrapy crawl bangla` crawls. Each was tested on 2026-09-22
# and returned real Bangla articles. A site can stop working if it changes its layout or starts
# blocking crawlers; test one on its own with: scrapy crawl news -a url=<its url> -a limit=5
BANGLA_SITES = {
    'Prothom Alo': 'https://www.prothomalo.com',
    'Kaler Kantho': 'https://www.kalerkantho.com',
    'Samakal': 'https://samakal.com',
    'Ittefaq': 'https://www.ittefaq.com.bd',
    'Bangla Tribune': 'https://www.banglatribune.com',
    'bdnews24.com Bangla': 'https://bangla.bdnews24.com',
    'Ajker Patrika': 'https://www.ajkerpatrika.com',
    'Dhaka Post': 'https://www.dhakapost.com',
    'Rising BD': 'https://www.risingbd.com',
    'BBC News Bangla': 'https://www.bbc.com/bengali',
}

# English-language Bangladeshi news sites that `scrapy crawl english` crawls, tested the same way.
# (New Age worked in testing, but its whole site showed "Account Suspended" a few hours later.
# It's kept in the list: while it's down, crawls just find nothing there and move on.)
ENGLISH_SITES = {
    'The Daily Star': 'https://www.thedailystar.net',
    'Dhaka Tribune': 'https://www.dhakatribune.com',
    'The Business Standard': 'https://www.tbsnews.net',
    'New Age': 'https://www.newagebd.net',
    'bdnews24.com': 'https://bdnews24.com',
}

# International English-language news sites that `scrapy crawl international` crawls, tested the same way.
# BBC News starts at /news so only its English news pages are taken, not BBC News Bangla or
# BBC's other language services, which share bbc.com.
INTERNATIONAL_SITES = {
    'BBC News': 'https://www.bbc.com/news',
    'The Guardian': 'https://www.theguardian.com',
    'NBC News': 'https://www.nbcnews.com',
}

# Tested on 2026-09-22 and left out:
#   Jugantor, Jago News 24   block crawlers (HTTP 403 on the homepage)
#   Bangladesh Pratidin      its sitemap links to pages that don't exist (HTTP 404)
#   Somoy News               its homepage is built with JavaScript, so it has no links to follow
#   Naya Diganta             its pages aren't labelled, so section pages can't be told apart from articles


def site_of(url):
    """The site a URL belongs to, e.g. https://nagorik.prothomalo.com/x -> prothomalo.com"""
    return tldextract.extract(url).top_domain_under_public_suffix
