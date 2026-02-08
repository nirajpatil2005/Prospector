# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# import scrapy


# class ArrowScraperItem(scrapy.Item):
#     # define the fields for your item here like:
#     # name = scrapy.Field()
#     pass


import scrapy


class PageItem(scrapy.Item):
    page_type = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    meta_description = scrapy.Field()
    h1 = scrapy.Field()
    h2 = scrapy.Field()
    paragraphs = scrapy.Field()
    emails = scrapy.Field()
    phones = scrapy.Field()
