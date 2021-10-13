import scrapy


class AudibleCoUkDiscoverySpider(scrapy.Spider):
    name = 'audible_co_uk_discovery'
    allowed_domains = ['audible.co.uk']
    start_urls = ['http://audible.co.uk/']

    def parse(self, response):
        pass
