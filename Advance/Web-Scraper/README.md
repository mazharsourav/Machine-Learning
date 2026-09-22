# Bangla News Crawler

**বাংলা সংবাদ থেকে তৈরি মেশিন লার্নিং ডেটাসেট** · a machine learning dataset made from Bangla news

**Bangla + English:** a bilingual dataset of Bangladeshi news, Bangla first.

A Scrapy crawler that collects articles from Bangladeshi news sites, in Bangla and in English, and builds them into a clean, growing, duplicate-free dataset for training AI models. It also collects English articles from a few international news sites (BBC News, The Guardian and NBC News).

## Why this matters

Bangla is spoken by more than 230 million people, most of them in Bangladesh and India. Yet in AI it is a *low-resource* language: there is far less clean, labelled, up-to-date Bangla text to train models on than there is for English. That gap is a big part of why search, translation, spam filtering, fake-news detection and chatbots work less well in Bangla.

Bangladeshi newspapers publish professionally edited Bangla on every topic, every day. This project turns that into a dataset anyone can build and keep growing on their own machine. One command collects the latest articles from 10 Bangla news sites, and each run adds only what's new.

### Why English too

Bangladesh also has a strong English-language press. Its articles cover the same events, on the same days, as the Bangla press, so together the two form a **bilingual dataset of the same news in two languages**. That's something a Bangla-only or English-only dataset can't offer.

The English articles are written independently, not translated from the Bangla ones. That makes this a *comparable* corpus rather than a parallel one: well suited to cross-lingual search, bilingual models and comparing coverage, but not a ready-made set of translation pairs.

## Dataset

<!-- STATS:START -->
**839 Bangla articles** (381,362 words) and **664 English articles** (380,611 words) from 17 news sites, collected 2026-09-21 to 2026-09-22 (UTC).

Languages: Bangla 56% · English 44%

| Site | Language | Articles | Avg. words |
|---|---|---:|---:|
| dhakapost.com | Bangla | 100 | 348 |
| banglatribune.com | Bangla | 100 | 364 |
| ittefaq.com.bd | Bangla | 100 | 321 |
| bdnews24.com | Bangla | 100 | 406 |
| samakal.com | Bangla | 100 | 453 |
| prothomalo.com | Bangla | 100 | 689 |
| ajkerpatrika.com | Bangla | 100 | 520 |
| risingbd.com | Bangla | 100 | 383 |
| kalerkantho.com | Bangla | 27 | 643 |
| bbc.com | Bangla | 12 | 1,298 |
| bbc.com | English | 100 | 440 |
| theguardian.com | English | 100 | 797 |
| tbsnews.net | English | 100 | 525 |
| thedailystar.net | English | 100 | 442 |
| dhakatribune.com | English | 100 | 461 |
| bdnews24.com | English | 91 | 599 |
| nbcnews.com | English | 73 | 817 |

_Generated from the database by `report.py`._
<!-- STATS:END -->

A sample of the output is in [sample_articles.json](sample_articles.json). The sample shows only the start of each article's text; the database stores the full text.

The database itself isn't in this repository, since the articles belong to their publishers. Run the crawler to build your own copy (see [Usage](#usage)).

## What you can build with it

| Task | Data |
|---|---|
| Bangla news topic classification | `text` → `category` |
| Bangla headline generation, summarization | `text` → `title` or `summary` |
| Bangla language models, word embeddings | `text` |
| Cross-lingual search, bilingual embeddings | Bangla and English articles about the same events, on the same days |
| Comparing how the Bangla and English press cover a story | `text`, `source`, `date`, `language` |
| Misinformation research, as a reference set of published news | `text`, `source`, `date` |

## Built for Bangla and Bangladeshi news sites

The crawler was tested on 20 Bangladeshi news sites. These are the problems that testing turned up, and how the crawler handles them:

- **Pages labelled with the wrong language.** Ajker Patrika's English edition is labelled as Bangla. The crawler detects Bangla from the text itself: if most letters are in the Bengali Unicode block (U+0980–U+09FF), the article is Bangla. The Bangla data contains only Bangla, and the English data only English.
- **The same word stored two ways.** Letters like ড় and য় can be typed as one Unicode character or as two (ড + ়). They look identical, but a computer sees বাড়ি typed one way and বাড়ি typed the other way as different words. Every text is normalized to one form (Unicode NFC), so a model sees one word.
- **Non-standard page labels.** The Daily Star labels its articles `og:type="News"` instead of `"article"`. The crawler checks the more precise schema.org label (`NewsArticle`) first.
- **Wrong author labels.** Samakal's page labels (JSON-LD) name each article's headline as its author. For Samakal, the crawler reads the byline shown on the page instead, e.g. সমকাল প্রতিবেদক.
- **Blocked, broken or misconfigured sitemaps.** Kaler Kantho blocks some of its sitemaps (403), bdnews24's was down (502), New Age's redirects to an error page, and Naya Diganta's robots.txt points to another website. The crawler ignores sitemaps on other sites and falls back to following links from the homepage.
- **Pages built with JavaScript.** Prothom Alo's section pages load their article lists with JavaScript, which a crawler can't see. Its sitemap is used instead.
- **Shared domains.** BBC News Bangla shares bbc.com with BBC's other language services, so only pages under `/bengali` are taken, and for BBC News in English only pages under `/news`. bdnews24.com runs its Bangla and English editions on the same domain, and they're kept apart by language.
- **Opening the data in Excel.** Excel shows Bangla in a CSV file as garbled characters unless the file is saved as UTF-8 with a BOM (`utf-8-sig`). The CSV examples under [Usage](#usage) and [Working with the data](#working-with-the-data) save it that way.

## News sites

Tested on 2026-09-22. The lists are in [sites.py](news_crawler/news_crawler/sites.py).

**Bangla, crawled by `scrapy crawl bangla`:** Prothom Alo, Kaler Kantho, Samakal, Ittefaq, Bangla Tribune, bdnews24.com Bangla, Ajker Patrika, Dhaka Post, Rising BD, BBC News Bangla.

**English, crawled by `scrapy crawl english`:** The Daily Star, Dhaka Tribune, The Business Standard, New Age, bdnews24.com.

**International English, crawled by `scrapy crawl international`:** BBC News, The Guardian, NBC News.

**Not supported:**

| Site | Why |
|---|---|
| Jugantor, Jago News 24 | They block crawlers (HTTP 403 on the homepage) |
| Bangladesh Pratidin | Its sitemap links to pages that don't exist (HTTP 404) |
| Somoy News | Its homepage is built with JavaScript, so there are no links to follow |
| Naya Diganta | Its pages aren't labelled, so section pages can't be told apart from articles |

Any other news site can be crawled with `scrapy crawl news -a url=...`.

## Setup

Requires Python 3.11 or newer (tested on 3.12). This project is the `Advance/Web-Scraper` folder of the [Machine-Learning](https://github.com/mazharsourav/Machine-Learning) repository.

```bash
git clone https://github.com/mazharsourav/Machine-Learning.git
cd Machine-Learning/Advance/Web-Scraper
python -m venv venv
venv\Scripts\activate            # Windows
source venv/bin/activate         # macOS / Linux
pip install -r requirements.txt
```

## Usage

Run from the `news_crawler` folder (the one containing `scrapy.cfg`):

```bash
scrapy crawl bangla                    # all 10 Bangla sites, up to 100 new articles from each
scrapy crawl english                   # all 5 English-language Bangladeshi sites
scrapy crawl international             # BBC News, The Guardian and NBC News
scrapy crawl bangla -a limit=20        # a quicker run
scrapy crawl news -a url=https://www.aljazeera.com    # any other news site
```

Articles are saved to `news_crawler/news.db`. Add `-O latest.json` to also save the current run to a file. For a CSV file that shows Bangla correctly in Excel, add `-O latest.csv -s FEED_EXPORT_ENCODING=utf-8-sig`.

Then refresh the sample file and the stats above:

```bash
python report.py
```

On Windows, [collect.bat](news_crawler/collect.bat) runs all three crawls and `report.py` in one go. Double-click it once a day, or schedule it with Task Scheduler, to keep the dataset growing.

| Option | What it does | Default |
|---|---|---|
| `-a url=...` | Site or section page to crawl. For several, quote it: `-a "url=https://a.com,https://b.com"` | `news`: required<br>`bangla`, `english`, `international`: their sites |
| `-a limit=50` | Stop after this many articles from each site (`0` = no limit) | 100 |
| `-a language=bn` | Only keep articles in this language | `news`: keep all<br>`bangla`: `bn`<br>`english`, `international`: `en` |
| `-a days=7` | How far back to go in a sitemap (`0` = any age) | 2 |
| `-a mode=links` | `auto`, `sitemap` or `links`. `auto` uses the sitemap for homepages and links for other pages | `news`: auto<br>`bangla`, `english`, `international`: sitemap |
| `-a depth=2` | In links mode, also look through section pages linked from the start page | 1 |

## Working with the data

With pandas installed (`pip install pandas`):

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("news_crawler/news.db")

# Bangla articles from the last week, newest first
bangla = pd.read_sql("""
    SELECT title, source, category, date, text
    FROM articles
    WHERE language = 'bn' AND scraped_at >= date('now', '-7 days')
    ORDER BY date DESC
""", conn)

# Bangla and English side by side: how many articles each language has per day
per_day = pd.read_sql("""
    SELECT substr(date, 1, 10) AS day, language, COUNT(*) AS articles
    FROM articles
    GROUP BY day, language
    ORDER BY day
""", conn)

# Export for Excel ("utf-8-sig" makes Excel show Bangla correctly)
bangla.to_csv("bangla_articles.csv", index=False, encoding="utf-8-sig")
```

Columns: `link` (primary key), `title`, `date`, `author`, `category`, `source`, `language` (`bn` or `en`), `summary`, `text`, `scraped_at`.

## How it works

```
url ──► robots.txt ──► news sitemap ─────────┐
  │    (no sitemap, or it fails)             ├──► article page ──► is it an article? ──► extract ──► clean ──► SQLite
  └────────────────────► links on the page ──┘                     (schema.org, og:type,           (NFC,
                                                                     date, 150+ words)              spaces)
```

| File | Role |
|---|---|
| [news_spider.py](news_crawler/news_crawler/spiders/news_spider.py) | Finds articles (sitemap or links), checks they're articles, extracts their content and detects the language |
| [bangla_spider.py](news_crawler/news_crawler/spiders/bangla_spider.py) | Crawls all the Bangla sites at once, keeping only Bangla articles |
| [english_spider.py](news_crawler/news_crawler/spiders/english_spider.py) | Crawls all the English-language Bangladeshi sites at once, keeping only English articles |
| [international_spider.py](news_crawler/news_crawler/spiders/international_spider.py) | Crawls all the international sites at once, keeping only English articles |
| [sites.py](news_crawler/news_crawler/sites.py) | The tested Bangla, English and international news sites |
| [pipelines.py](news_crawler/news_crawler/pipelines.py) | Normalizes Unicode and whitespace, then saves to SQLite, skipping duplicates |
| [middlewares.py](news_crawler/news_crawler/middlewares.py) | Stops downloading from a site once it has enough articles |
| [settings.py](news_crawler/news_crawler/settings.py) | Politeness, caching and database settings |
| [report.py](news_crawler/report.py) | Writes `sample_articles.json` and the stats in this README |
| [collect.bat](news_crawler/collect.bat) | Runs all three crawls and `report.py` in one go (Windows) |

## Limitations

- Sites that block crawlers, or build their pages with JavaScript, can't be crawled (see *Not supported* above). A site can also stop working if it changes its layout.
- `category` comes from each site's own labels or URLs, so it's in Bangla on some sites (খেলা) and English on others (sports). Map categories to a shared set before training a classifier across sites. BBC News articles have no category: their URLs (`/news/articles/<id>`) don't name a section.
- `date` is in whatever precision the site gives: some give the exact time, others only the day.
- The Bangla and English articles aren't matched to each other. Pairing articles about the same story (e.g. by date and shared names) is a possible next step.

## Responsible use

This project is for personal research and learning. It obeys each site's robots.txt, identifies itself, and waits between requests. Respect each site's terms of use, and don't republish the articles you collect: they belong to their publishers.
