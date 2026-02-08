import scrapy
from urllib.parse import urlparse


class AccionFullSpider(scrapy.Spider):
    name = "accion_full"
    allowed_domains = ["accionlabs.com"]
    start_urls = ["https://www.accionlabs.com/"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0",
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "LOG_LEVEL": "INFO",
        "DEPTH_LIMIT": 4
    }

    VALID_PATH_KEYWORDS = [
        "about",
        "leadership",
        "insights",
        "news",
        "press",
        "case",
        "industry",
        "service",
        "career"
    ]

    def parse(self, response):
        yield self.extract_page(response, page_type="home")

        for link in self.extract_links(response):
            yield response.follow(link, self.parse_internal)

    def parse_internal(self, response):
        yield self.extract_page(response, page_type="internal")

        for link in self.extract_links(response):
            yield response.follow(link, self.parse_internal)

    def extract_page(self, response, page_type):
        return {
            "page_type": page_type,
            "url": response.url,
            "title": response.css("title::text").get(),
            "meta_description": response.css(
                'meta[name="description"]::attr(content)'
            ).get(),
            "h1": response.css("h1::text").get(),
            "h2": response.css("h2::text").getall(),
            "paragraphs": [
                p.strip()
                for p in response.css("p::text").getall()
                if p.strip()
            ]
        }

    def extract_links(self, response):
        links = []
        for href in response.css("a::attr(href)").getall():
            if not href:
                continue

            href = href.strip().lower()

            if href.startswith((
                "#",
                "javascript:",
                "mailto:",
                "tel:",
                "whatsapp:",
                "linkedin.com",
                "twitter.com",
                "facebook.com"
            )):
                continue

            parsed = urlparse(href)
            path = parsed.path.lower()

            # only follow meaningful business pages
            if any(key in path for key in self.VALID_PATH_KEYWORDS):
                links.append(href)

        return set(links)
