import scrapy
from lottery.items import LotteryItem

class LotterySpider(scrapy.Spider):
    name = "nswLotterySpider";
    allowed_domains = ['nswlotteries.com.au', 'tatts.com'];
    start_urls = ['https://tatts.com/nswlotteries/results/latest-results',];

    def parse(self, response):
        sel = scrapy.Selector(response);        
        lottoItems = [];
        for ln in sel.xpath("//tr/td/div[@class='resultNumberWrapperDiv']"):
    	    item = LotteryItem();
            # ./ is relative to previous xpath
            item['winningNum'] = ln.xpath('.//span/text()').extract();
    	    print item['winningNum'];
            lottoItems.append(item);

        return lottoItems