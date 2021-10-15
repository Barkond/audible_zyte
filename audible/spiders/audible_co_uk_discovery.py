import re
import scrapy
from urllib.parse import urljoin


class AudibleCoUkDiscoverySpider(scrapy.Spider):
    name = 'audible_co_uk_discovery'
    allowed_domains = ['www.audible.co.uk']
    zyte_smartproxy_enabled = False
    zyte_smartproxy_apikey = 'ca2b385de83d4668a02d499d936999be'

    def start_requests(self):
        url = 'https://www.audible.co.uk/categories'
        yield scrapy.Request(url=url, callback=self.parse)

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

            if product.css('li.bc-list-item.narratorLabel'):
                narrators = []
                for narrator in product.css('li.bc-list-item.narratorLabel a'):
                    narrator_name = narrator.css('::text').get()
                    if narrator_name:
                        narrators.append(narrator_name.strip())
                item['narrators'] = narrators

            product_duration = product.css('li.bc-list-item.bc-list-item.runtimeLabel span::text').get()
            if product_duration:
                t_minute = re.findall(r'(\d+) min', product_duration)
                t_hour = re.findall(r'(\d+) hr', product_duration)
                if t_hour and t_minute:
                    hour = t_hour[0]
                    minute = t_minute[0]
                    item['duration'] = f'{hour}:{minute}'
                elif t_hour:
                    hour = t_hour[0]
                    item['duration'] = f'{hour}:00'
                elif t_minute:
                    item['duration'] = t_minute[0]

            breadcrumps = []
            for bc in response.css('ul.bc-list.bc-spacing-none li.bc-list-item a'):
                bc_name = ''.join(bc.css('::text').getall())
                bc_url = bc.css('::attr(href)').get()
                if bc_name and bc_url:
                    breadcrumps.append({'name': bc_name.strip(),
                                        'url': urljoin(response.url, bc_url)})
            last_bc = {}
            last_bc_name = response.css('div.bc-box.bc-box-padding-none ul.bc-list li.bc-list-item span::text').get()
            if last_bc_name:
                last_bc['name'] = last_bc_name.strip()
            last_bc_url = response.xpath('//link[@rel="canonical"]/@href').get()
            if last_bc_url:
                last_bc['url'] = w3lib.url.url_query_cleaner(last_bc_url, ('node',))  # NOQA
            if last_bc:
                breadcrumps.append(last_bc)
            item['breadcrumps'] = breadcrumps

            price = product.css('div.adblBuyBoxPrice > p.buybox-regular-price > span:last-child::text').re_first(
                r'(\d+\.\d+)')
            currency = product.css('div.adblBuyBoxPrice > p.buybox-regular-price > span:last-child::text').re_first(
                r'^\s+(.)')
            if price:
                item['buy_price'] = price
            if currency == '£':
                item['currency'] = 'GBP'

            yield item

            next_page = response.css('span.bc-button.bc-button-secondary.nextButton a::attr(href)').get()
            if response.css('span.bc-button.bc-button-secondary.nextButton.bc-button-disabled'):
                pass
            else:
                yield scrapy.Request(url=urljoin(response.url, next_page), callback=self.parse_product_list)
