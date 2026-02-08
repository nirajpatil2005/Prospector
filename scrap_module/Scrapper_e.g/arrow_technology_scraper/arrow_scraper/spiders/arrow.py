import scrapy
from arrow_scraper.items import PageItem
from urllib.parse import urlparse


class ArrowSpider(scrapy.Spider):
    name = "arrow"
    allowed_domains = ["arrowtechnologies.com"]
    start_urls = ["https://arrowtechnologies.com/"]

    def parse(self, response):
        item = PageItem()

        item["page_type"] = "home"
        item["url"] = response.url
        item["title"] = response.css("title::text").get()
        item["meta_description"] = response.css(
            'meta[name="description"]::attr(content)'
        ).get()
        item["h1"] = response.css("h1::text").get()
        item["h2"] = response.css("h2::text").getall()
        item["paragraphs"] = response.css("p::text").getall()
        item["emails"] = response.css('a[href^="mailto:"]::attr(href)').getall()
        item["phones"] = response.css('a[href^="tel:"]::attr(href)').getall()

        yield item

        # Follow internal links safely
        for link in response.css("a::attr(href)").getall():
            if not link:
                continue

            link = link.strip()

            # 🚫 Ignore invalid schemes
            if link.startswith((
                "#",
                "javascript:",
                "mailto:",
                "tel:",
                "whatsapp:",
                "ftp:"
            )):
                continue

            yield response.follow(
                link,
                callback=self.parse_internal,
                dont_filter=True
            )

    def parse_internal(self, response):
        # Restrict to same domain
        if urlparse(response.url).netloc not in self.allowed_domains:
            return

        item = PageItem()

        item["page_type"] = "internal"
        item["url"] = response.url
        item["title"] = response.css("title::text").get()
        item["meta_description"] = response.css(
            'meta[name="description"]::attr(content)'
        ).get()
        item["h1"] = response.css("h1::text").get()
        item["h2"] = response.css("h2::text").getall()
        item["paragraphs"] = response.css("p::text").getall()
        item["emails"] = response.css('a[href^="mailto:"]::attr(href)').getall()
        item["phones"] = response.css('a[href^="tel:"]::attr(href)').getall()

        yield item
