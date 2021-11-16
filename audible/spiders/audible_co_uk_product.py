import json
import re
import scrapy
from urllib.parse import urljoin

RAW_PRODUCT_IDS = """B004EVK3HG
,B004FJHGE0
,B004HJBZV8
,B004S7OIOU
,B004ZGYFQA
,B0064DYOUE
,B007KBKVEW
,B007W5BSX4
,B004ELYQIS
,B004EXITL6
"""


class AudibleCoUkProductSpider(scrapy.Spider):
    name = 'audible_co_uk_product'
    allowed_domains = ['www.audible.co.uk']
    start_urls = ['https://httpbin.org/ip']

    def parse(self, response):  # NOQA
        product_ids = RAW_PRODUCT_IDS.split(',')
        for product_id in product_ids:
            split_id = product_id.strip()
            item_url = urljoin('https://www.audible.co.uk/pd/', split_id)
            yield scrapy.Request(url=item_url, callback=self.parse_product)

    def parse_product(self, response):
        audiobook_data, product_data = None, None
        for script in response.xpath('//div[@id=\'bottom-0\']/script'):
            if script.xpath("./self::*[contains(text(),"
                            "'\"@type\": \"Audiobook\"')]/text()"):
                audiobook_data = json.loads(script.xpath("./text()").get())[0]
            elif script.xpath("./self::*[contains(text(),"
                              "'\"@type\": \"Product\"')]/text()"):
                product_data = json.loads(script.xpath("./text()").get())[0]
        if not audiobook_data or not product_data:
            self.logger.error(f'No script data found for {response.url}')
            return

        item = {
            "url": response.url,
            'title_name': audiobook_data.get('name', ''),
            'no_reviews': audiobook_data.get('aggregateRating'
                                             '', {}).get('ratingCount', 0)
        }

        if audiobook_data.get('publisher'):
            item['publisher'] = audiobook_data['publisher']
        if audiobook_data.get('inLanguage'):
            item['lang'] = audiobook_data['inLanguage']
        if audiobook_data.get('datePublished'):
            item['publication_date'] = audiobook_data['datePublished']
        if audiobook_data.get('datePublished'):
            item['publication_date'] = audiobook_data['datePublished']
        if audiobook_data.get('aggregateRating', {}).get('ratingValue'):
            item['avg_review_score'] = audiobook_data['aggregateRating'
                                                      '']['ratingValue'][:4]
        if audiobook_data.get('offers').get('highPrice'):
            item['buy_price'] = audiobook_data['offers']['highPrice']
        if product_data.get('productID'):
            item['asin'] = product_data['productID']
        if product_data.get('sku'):
            item['sku'] = product_data['sku']

        authors = []
        if audiobook_data.get('author'):
            for author in audiobook_data.get('author', []):
                authors.append(author['name'])
            item['authors'] = authors

        narrators = []
        if audiobook_data.get('readBy'):
            for narrator in audiobook_data.get('readBy', []):
                narrators.append(narrator['name'])
            item['narrators'] = narrators

        item_duration = audiobook_data.get('duration')
        if item_duration:
            t_minute = re.findall(r'(\d+)M', item_duration)
            t_hour = re.findall(r'(\d+)H', item_duration)
            if t_hour and t_minute:
                hour = t_hour[0]
                minute = t_minute[0]
                item['duration'] = f'{hour}:{minute}'
            elif t_hour:
                hour = t_hour[0]
                item['duration'] = f'{hour}:00'
            elif t_minute:
                item['duration'] = t_minute[0]

        av = re.findall(r'(\w+)$', audiobook_data['offers']['availability'])
        if av:
            if av[0] == 'InStock':
                item['available'] = True
            else:
                item['available'] = False

        yield item
