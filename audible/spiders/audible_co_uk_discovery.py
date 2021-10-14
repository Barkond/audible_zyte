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
