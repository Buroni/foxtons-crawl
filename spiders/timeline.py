import scrapy
from datetime import datetime
from scrapy.http import FormRequest, Request
import sqlite3
import re
import os


class TimelineSpider(scrapy.Spider):
    name = "scheduled-foxtons-spider"
    download_delay = 0.2
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    property_ids = []

    def __init__(self):
        self.con = sqlite3.connect("/Users/jake/oss/foxtons-crawl/sqlite3/foxtons.db")
        self.cur = self.con.cursor()

    def start_requests(self):
        login_url = "https://www.foxtons.co.uk/auth/enter/?mode=login"
        return [FormRequest(
            login_url,
            formdata=dict(email=os.environ["FOXTONS_EMAIL"], password=os.environ["FOXTONS_PASSWORD"]),
            callback=self.logged_in,
        )]

    def logged_in(self, *a):
        response = self.cur.execute("SELECT url, id FROM properties").fetchall()
        for property_ in response:
            yield Request(url=property_[0], callback=self.parse, meta=dict(id=property_[1]))

    def parse(self, response):
        is_reduced = len(response.css(".recently_reduced")) > 0
        price_pcm = re.sub("[£,]", "", response.css(".per_month").xpath("./data/text()").get())

        self.cur.execute(f"""
            INSERT INTO timeline VALUES
                ({float(price_pcm)}, '{response.meta["id"]}', {"1" if is_reduced else "0"}, '{datetime.now().isoformat()}')
        """)

        yield dict(
            is_reduced=is_reduced,
            price_pcm=price_pcm,
            id=response.meta["id"],
        )

    def closed(self, *a):
        self.con.commit()
