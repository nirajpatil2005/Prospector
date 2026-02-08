import scrapy
from urllib.parse import urlparse, urljoin


class CompanyProfileSpider(scrapy.Spider):
    name = "company_profile"

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 0.5,
        "DEPTH_LIMIT": 10,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 5,
        "LOG_LEVEL": "INFO",
        "FEEDS": {}
    }

    def __init__(self, company=None, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not company or not start_url:
            raise ValueError("company and start_url are required")

        self.company = company.lower().replace(" ", "_")
        self.start_urls = [start_url]

        parsed = urlparse(start_url)
        self.allowed_domains = [parsed.netloc]

        self.custom_settings["FEEDS"] = {
            f"data/{self.company}.json": {
                "format": "json",
                "encoding": "utf8",
                "indent": 2
            }
        }

    # -------- START --------
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    # -------- MAIN PARSE --------
    def parse(self, response):
        page_data = self.extract_page(response)
        yield page_data

        for link in self.extract_links(response):
            yield scrapy.Request(link, callback=self.parse)

    # -------- CONTENT EXTRACTION --------
    def extract_page(self, response):
        return {
            "url": response.url,
            "title": response.css("title::text").get(),
            "meta_description": response.css(
                'meta[name="description"]::attr(content)'
            ).get(),
            "headings": response.css(
                "h1::text, h2::text, h3::text"
            ).getall(),
            "text": [
                t.strip()
                for t in response.css(
                    "p::text, li::text, span::text"
                ).getall()
                if t.strip()
            ]
        }

    # -------- LINK EXTRACTION --------
    def extract_links(self, response):
        links = set()

        for href in response.css("a::attr(href)").getall():
            if not href:
                continue

            href = href.strip()

            if href.startswith((
                "#",
                "javascript:",
                "mailto:",
                "tel:",
                "whatsapp:",
                "linkedin.com",
                "twitter.com",
                "facebook.com",
                "instagram.com",
                "youtube.com"
            )):
                continue

            absolute_url = urljoin(response.url, href)
            parsed = urlparse(absolute_url)

            if parsed.netloc == self.allowed_domains[0]:
                links.add(absolute_url)

        return links
