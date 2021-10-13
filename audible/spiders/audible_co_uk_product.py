import scrapy


class AudibleCoUkProductSpider(scrapy.Spider):
    name = 'audible_co_uk_product'
    allowed_domains = ['audible.co.uk']
    start_urls = ['http://audible.co.uk/']

    def parse(self, response):
        pass
