import scrapy
from datetime import datetime, timedelta
import re
import os
from scrapy.exceptions import CloseSpider
from bs4 import BeautifulSoup as bs


class VivaSpider(scrapy.Spider):
    name = "viva"
    allowed_domain = [
        "viva.co.id",
    ]

    base_url = "https://www.viva.co.id/indeks"

    def __init__(self, start_date=None, end_date=None, hourly=True, *args, **kwargs):
        super(VivaSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date  
        self.end_date = end_date 

        self.hourly = True  # False #True per jam

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

    def start_requests(self):
        _ranged = [
            self.base_url,
        ]

        if self.start_date != None and self.end_date != None:
            _ranged = []

            for date in self.daterange(
                self.start_date, self.end_date + timedelta(days=1)
            ):
                _ranged.append(
                    "{}/all/all/{}".format(
                        self.base_url,
                        f"{date.year}/{date.month}/{date.day}",
                    )
                )

        for url in _ranged:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for article_url in response.css(
            "div.article-list-info.content_center a.article-list-title::attr(href)"
        ).extract()[0:-2]:
            yield scrapy.Request(
                response.urljoin("{}?page=all&single=1   ".format(article_url)),
                callback=self.parse_article_page,
            )

    def parse_article_page(self, response):
        item = {
            "source": "Viva",
            "type": "article",
            "slug": response.request.url,
        }

        # Get category
        breadcrumb = response.css(
            "div.main-content-top ul.breadcrumb li a.breadcrumb-step.content_center div::text"
        ).extract()
        item["category"] = breadcrumb

        # Get title
        title = response.css(
            "div.main-content-top h1.main-content-title::text"
        ).extract_first()
        item["title"] = None
        if title:
            item["title"] = title.replace("\t", "").replace("\r", "").replace("\n", "")
        else:
            raise CloseSpider("Get no title")

        # Get author
        author = response.css("div.main-content-author ul li a::text").extract_first()
        item["author"] = None
        if author:
            item["author"] = author.replace("\n", "")
        else:
            raise CloseSpider("Get no author")

        # Get date (String)
        monthChanger = {
            "Januari": "January",
            "January": "January",
            "Jan": "January",
            "Februari": "February",
            "February": "February",
            "Feb": "February",
            "Maret": "March",
            "March": "March",
            "Mar": "March",
            "April": "April",
            "Apr": "April",
            "Mei": "May",
            "May": "May",
            "May": "May",
            "Juni": "June",
            "Jun": "June",
            "June": "June",
            "Juli": "July",
            "July": "July",
            "Jul": "July",
            "Agustus": "August",
            "August": "August",
            "Aug": "August",
            "September": "September",
            "Sep": "September",
            "Oktober": "October",
            "October": "October",
            "Oct": "October",
            "November": "November",
            "Nov": "November",
            "Desember": "December",
            "December": "December",
            "Des": "December",
        }
        date = response.css(
            "div.main-content-top div.main-content-date::text"
        ).extract_first()
        if date:
            date = date.replace("WIB", "").replace("| ", "").split(", ")[1].split("-")
            date = " ".join(date)
            date = date.replace(
                re.search("[A-Za-z]+", date).group(0),
                monthChanger[re.search("[A-Za-z]+", date).group(0)],
            )
            date = date.strip()
            item["news_date"] = datetime.strptime(date, "%d %B %Y %H:%M")

        # Get media url
        item["media"] = response.css(
            "div.main-content-image div.mci-frame picture img::attr(src)"
        ).extract()

        # Get tags
        item["tags"] = []
        tags = response.css(
            "div.topic-list-container a::text").extract()
        if tags:
            tags = [ tag.replace("\n","").strip() for tag in tags if tag.replace("\n","").strip() != '' ]
            item["tags"] = tags

        # Get raw content
        content = response.css("div.main-content-detail").get()
        soup = bs(content)
        list_content = []
        for strings in soup.find_all("p"):
            list_content.append(strings.text)
        string = " ".join(list_content)
        string = re.sub("\n|\t|\r|\xa0|\u201d|\u201c|\u2013", "", string)
        string = re.sub(" +", " ", string)
        item["contentRaw"] = string.strip()
        if item["contentRaw"] == "":
            raise CloseSpider("get no content")

        item["createdAt"] = datetime.now()

        # stop berita diatas 1 jam dari sekarang
        if datetime.now().hour - item["news_date"].hour > 1:
            raise CloseSpider("get only and hour from now")
        print(item['slug'])
        yield item
