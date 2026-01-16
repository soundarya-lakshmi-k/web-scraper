1. Introduction

This project implements a scalable web scraping system to extract public marriage record data from the MOMS portal while respecting platform constraints.

2. Search Strategy

A three-level hierarchical narrowing strategy ensures search results never exceed the 30-record limit:

First Name → Last Name → Middle Name

Date range is set wide (1900-2026) for all searches.

3. Technology Stack

Python 3.10+

Playwright (Async Browser Automation)

Pandas (CSV structuring)

Logging & Retry Handling

4. Code Overview

MomsScraper class handles full workflow

search_phase() → URL collection

profile_phase() → full data extraction

Async execution for speed and stability

5. Running Instructions
git clone <repo>
cd moms-scraper
pip install -r requirements.txt
playwright install
python scraper.py

6. Notes & Limitations

Selectors are assumed based on typical ASPX forms; may need adjustment after inspection

Respect robots.txt and legal permissions

Proxy rotation recommended for scale

⭐ Optional Enhancements (Already Architected)

✅ Retry logic
✅ Delay injection
✅ Proxy support
✅ Headless toggle
✅ CAPTCHA-safe design

If you want, I can also:

Convert this into production-grade crawler

Add proxy rotation

Add resume-from-checkpoint

Add# web-scraper
