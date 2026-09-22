@echo off
rem Collects the latest Bangla and English news articles from Bangladeshi news sites and
rem English articles from international ones, then refreshes sample_articles.json and the README stats.
rem Double-click it once a day, or schedule it with Windows Task Scheduler.

cd /d "%~dp0"
"..\venv\Scripts\scrapy.exe" crawl bangla
"..\venv\Scripts\scrapy.exe" crawl english
"..\venv\Scripts\scrapy.exe" crawl international
"..\venv\Scripts\python.exe" report.py
