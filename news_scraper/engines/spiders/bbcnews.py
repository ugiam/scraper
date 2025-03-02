import scrapy
from datetime import datetime, timedelta
from scrapy.exceptions import CloseSpider
import json
import re

def utf8_to_ascii(s: str, ws=re.compile('\s+', flags=re.M)) -> str:
    s = s.encode("utf8")
    s = s.decode("ascii", errors="replace")
    s = s.replace(u"\ufffd", " ")
    s = ws.sub(" ", s)
    return s.strip()

class BbcNewsSpider(scrapy.Spider):
    name = "bbcnews"
    allowed_domain = [
        "https://www.bbc.com/news",
    ]
    base_url = "https://www.bbc.com/news"

    def __init__(self, start_date=None, end_date=None, hourly=True, *args, **kwargs):
        super(BbcNewsSpider, self).__init__(*args, **kwargs)

        self.start_date = start_date  
        self.end_date = end_date  

        self.hourly = True  

        if self.start_date != None and self.end_date != None:
            self.start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
            self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
            if self.start_date >= self.end_date:
                raise scrapy.exceptions.CloseSpider(
                    reason="Start date must be lower than end date"
                )

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def changemonth(self, date):
        months = {
            "01": "January",
            "02": "February",
            "03": "March",
            "04": "April",
            "05": "May",
            "06": "June",
            "07": "Jule",
            "08": "Agustus",
            "09": "September",
            "10": "October",
            "11": "November",
            "12": "December",
        }
        _date = date.isoformat().split("T")[0].split("-")
        date = []
        for month in _date:
            if month in months:
                month = months[month]
            date.append(month)
        tgl = "{} {}, {}".format(date[2], date[1], date[0])
        return tgl

    def start_requests(self):
        _ranged = [
            self.base_url,
        ]

        if self.start_date != None and self.end_date != None:
            print(self.start_date)
            first_date = self.changemonth(self.start_date)
            second_date = self.changemonth(self.end_date)
            _ranged = []

            for date in self.daterange(
                self.start_date, self.end_date + timedelta(days=1)
            ):
                _ranged.append(
                    "{}?daterange={} - {}".format(
                        self.base_url, first_date, second_date
                    )
                )

        for url in _ranged:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        link_1= response.css(" div.sc-93223220-0.sc-b38350e4-2.cmkdDu.QUMNJ >  div > div>a::attr(href)").extract()
        link_2 = response.css(" div.sc-93223220-0.biogCF > div > div > a::attr(href)").extract()
        link = link_1+link_2
        for article_url in link:
            url = "https://www.bbc.com" + article_url
            yield scrapy.Request(
                response.urljoin("{}?page=all&single=1   ".format(article_url)),
                callback=self.parse_article_page,
            )

        next_link = response.css("div.paging__item").css("a")
        next_page = next_link.css("::attr(href)").extract()[-1]
        if next_page.split("&")[-1].split("=")[-1] == "6":
            next_page = None
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    def parse_article_page(self, response):
        item = {
            "source": "BBC News",
            "type": "article",
            "slug": response.request.url,
        }

        # Get category
        item["category"] = []
        breadcrumb = response.css(
            " span.ssrcss-1mstwv3-LinkTextContainer.eis6szr1 ::text"
        ).extract()
        if breadcrumb:
            item["category"] = breadcrumb[0]

        # # Get title
        item["title"] = ""
        title = response.css(
            " article > div > h1.sc-518485e5-0.bWszMR::text"
        ).extract_first()
        if title:
            item["title"] = title.replace("\t", "").replace("\r", "").replace("\n", "").strip()
        else:
            raise CloseSpider("Get no title")

        # Get author
        item["author"] = ""
        item["news_date"] = ""
        author = response.css('head > script[type="application/ld+json"]::text').getall()[0]
        if author:
            data  = json.loads(author)
            authors = data.get("author", [])
            names = [author["name"] for author in authors if "name" in author][0]
            names = [name.strip() for name in names.replace(" & ", ", ").split(", ")]
            item["author"] = names

            published_date = data.get("dateModified")
            published_date = published_date.split(".")[0].replace("T"," ")
            published_date = datetime.strptime(published_date, "%Y-%m-%d %H:%M:%S") + timedelta(hours=7)
            item["news_date"] = published_date
        else:
            raise CloseSpider("Get no author")

        # # Get media url
        item["media"] = []
        media = response.css(
            " article > figure > div > div > img::attr(src)"
        ).extract()

        if media: 
            media = [url for url in media if url != '/bbcx/grey-placeholder.png']
            item["media"] = list(set(media))

        # # Get tags
        item["tags"] = response.css(
            "div.sc-4b0aaa-0.dGavUm > div > a::text"
        ).extract()

        # Get raw content
        content = response.css( "p.sc-eb7bd5f6-0.fYAfXe ::text" ).extract()
        string = " ".join(content)
        if string == "":
            raise CloseSpider("There's no content")
        item["contentRaw"] = utf8_to_ascii(string)
        print(item["contentRaw"])

        # Get Created Date
        item["createdAt"] = datetime.now()

        if datetime.now().hour - item["news_date"].hour > 1:
            raise CloseSpider("get only and hour from now")
        print(item['slug'])
        yield item
