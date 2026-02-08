# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface


class CleanPipeline:
    def process_item(self, item, spider):
        for field in ["paragraphs", "h2"]:
            if field in item and item[field]:
                item[field] = [
                    text.strip()
                    for text in item[field]
                    if text and text.strip()
                ]
        return item
