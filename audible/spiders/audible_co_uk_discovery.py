import scrapy
from urllib.parse import urljoin


class AudibleCoUkDiscoverySpider(scrapy.Spider):
    name = 'audible_co_uk_discovery'
    allowed_domains = ['www.audible.co.uk']
    zyte_smartproxy_enabled = False
    zyte_smartproxy_apikey = 'ca2b385de83d4668a02d499d936999be'

    def start_requests(self):
        url = 'https://www.audible.co.uk/search?node=19393888031'
        yield scrapy.Request(url=url, callback=self.parse_product_list)

    def parse(self, response):  # NOQA
        for top_category in response.css('.bc-row-responsive.bc-spacing-medium h2 a'):
            yield scrapy.Request(url=urljoin(response.url, top_category.css('::attr(href)')),
                                 callback=self.parse_categories)

    def parse_categories(self, response):
        for category in response.css('.bc-row-responsive.subCategoriesContainer div'):
            if category.css('a'):
                yield scrapy.Request(url=urljoin(response.url, category.css('a::attr(href)').get()),
                                     callback=self.parse_categories)
            yield scrapy.Request(
                url=urljoin(response.url, response.css('.bc-col-responsive.bc-text-right.bc-col-4 a::attr(href)')),
                callback=self.parse_product_list)

    def parse_product_list(self, response):  # NOQA
        for product in response.css('div.adbl-impression-container li.bc-list-item.productListItem'):
            item = {
                'publication_date': product.css('li.bc-list-item.releaseDateLabel span::text').re_first(
                    r'(\d{2}-\d{2}-\d{2})'),
                'lang': product.css('li.bc-list-item.languageLabel span::text').re_first(r'(\w*)\s*$')
            }
            name = product.css('h3 a::text').get()
            item_url = product.css('h3 a::attr(href)').get()
            if name and item_url:
                item['name'] = name.strip()
                item['url'] = urljoin(response.url, item_url)

            if product.css('li.bc-list-item.ratingsLabel span.bc-text.bc-pub-offscreen'):
                item['avg_review_score'] = float(product.css(
                    'li.bc-list-item.ratingsLabel span.bc-text.bc-pub-offscreen::text').re_first(r'^(\d\.\d|\d)', '0'))
            item_reviews_count = product.css(
                'li.bc-list-item.ratingsLabel span.bc-text.bc-size-small::text').re_first(r'(\d+\,\d+|\d)', '0')
            if item_reviews_count:
                item_reviews_count = item_reviews_count.replace(',', '')
                item['no_reviews'] = int(item_reviews_count)

            if product.css('li.bc-list-item.subtitle'):
                subtitle = product.css('li.bc-list-item.subtitle span::text').get()
                item['subtitle'] = subtitle.strip()

            if product.css('li.bc-list-item.authorLabel'):
                authors = []
                for author in product.css('li.bc-list-item.authorLabel a'):
                    author_name = author.css('::text').get()
                    if author_name:
                        authors.append(author_name.strip())
                item['authors'] = authors
