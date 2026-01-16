"""
MOMS Vital Records Web Scraper
Author: Soundarya Lakshmi K
Tech: Playwright (Async)
"""

import asyncio
import string
import csv
import logging
from itertools import product
from typing import List, Dict

from playwright.async_api import async_playwright, Page, TimeoutError

# ---------------- CONFIG ---------------- #

BASE_URL = "https://moms.mn.gov/"
OUTPUT_FILE = "moms.csv"

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

ALPHABETS = list(string.ascii_uppercase)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- SCRAPER CLASS ---------------- #

class MomsScraper:
    def __init__(self):
        self.profile_urls = set()
        self.results = []

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()

            await page.goto(BASE_URL, timeout=60000, wait_until='domcontentloaded')
            await page.wait_for_timeout(5000)  # Wait for Cloudflare

            # Save page content for inspection
            with open("page_content.html", "w", encoding="utf-8") as f:
                f.write(await page.content())

            await self.search_phase(page)
            await self.profile_phase(page)

            await browser.close()
            self.save_csv()

    # ---------------- SEARCH PHASE ---------------- #

    async def search_phase(self, page: Page):
        logging.info("Starting search phase")

        for fname in ALPHABETS:
            count = await self.perform_search(page, fname=fname)

            if count > 30:
                for lname in ALPHABETS:
                    count = await self.perform_search(page, fname=fname, lname=lname)

                    if count > 30:
                        for mname in ALPHABETS:
                            count = await self.perform_search(
                                page, fname=fname, lname=lname, mname=mname
                            )

    async def perform_search(self, page: Page, **filters) -> int:
        """
        Perform a search and collect profile URLs.
        Returns number of results.
        """

        await self.fill_search_form(page, filters)
        await page.wait_for_timeout(1500)

        result_count = await self.get_result_count(page)

        if result_count <= 30:
            urls = await self.extract_profile_urls(page)
            self.profile_urls.update(urls)

        return result_count

    async def fill_search_form(self, page: Page, filters: Dict):
        """
        Abstracted form filling.
        Selectors must be updated based on actual site inspection.
        """

        # Wait for form to load
        await page.wait_for_selector("input[id='ctl00_ContentPlaceHolder1_txtLastName']", timeout=60000)

        if "fname" in filters:
            await page.fill("input[id='ctl00_ContentPlaceHolder1_txtFirstName']", filters["fname"])
        if "lname" in filters:
            await page.fill("input[id='ctl00_ContentPlaceHolder1_txtLastName']", filters["lname"])
        if "mname" in filters:
            await page.fill("input[id='ctl00_ContentPlaceHolder1_txtMiddleName']", filters["mname"])

        # Set wide date range
        await page.fill("input[id='ctl00_ContentPlaceHolder1_txtDateFrom']", "01/01/1900")
        await page.fill("input[id='ctl00_ContentPlaceHolder1_txtDateTo']", "12/31/2026")

        await page.click("input[id='ctl00_ContentPlaceHolder1_btnSearch']")

    async def get_result_count(self, page: Page) -> int:
        """
        Reads result count from UI
        """

        try:
            text = await page.inner_text("body")
            # Assume it says "X results found" or similar
            import re
            match = re.search(r'(\d+) results?', text, re.IGNORECASE)
            if match:
                return int(match.group(1))
            return 0
        except Exception:
            return 0

    async def extract_profile_urls(self, page: Page) -> List[str]:
        # Assume results have links to certificate or profile
        links = await page.query_selector_all("a[href*='Certificate']")
        urls = []
        for link in links:
            href = await link.get_attribute("href")
            if href:
                urls.append(href if href.startswith('http') else BASE_URL + href)
        return urls

    # ---------------- PROFILE PHASE ---------------- #

    async def profile_phase(self, page: Page):
        logging.info(f"Scraping {len(self.profile_urls)} profiles")

        for url in self.profile_urls:
            try:
                await page.goto(url, timeout=60000)
                data = await self.scrape_profile(page)
                self.results.append(data)
            except TimeoutError:
                logging.warning(f"Timeout while loading {url}")

    async def scrape_profile(self, page: Page) -> Dict:
        """
        Scrape all available fields from a profile page
        """

        def safe_text(selector):
            try:
                return page.inner_text(selector)
            except:
                return ""

        return {
            "Applicant 1": await safe_text("#applicant1"),
            "Applicant 2": await safe_text("#applicant2"),
            "Certificate Number": await safe_text("#certificate"),
            "Date Filed": await safe_text("#dateFiled"),
            "County": await safe_text("#county"),
            "Profile URL": page.url
        }

    # ---------------- OUTPUT ---------------- #

    def save_csv(self):
        if not self.results:
            logging.warning("No data to save")
            return

        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
            writer.writeheader()
            writer.writerows(self.results)

        logging.info(f"Saved data to {OUTPUT_FILE}")


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    scraper = MomsScraper()
    asyncio.run(scraper.run())