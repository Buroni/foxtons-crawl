import scrapy
from datetime import datetime
from scrapy.http import FormRequest, Request
import sqlite3
import re
import os
from dotenv import load_dotenv

load_dotenv()

os.chdir(os.path.dirname(os.path.abspath(__file__)))


class TimelineSpider(scrapy.Spider):
    name = "scheduled-foxtons-spider"
    download_delay = 0.5
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    start_urls = ["https://www.foxtons.co.uk/auth/enter/?mode=login"]

    property_ids = []

    def __init__(self):
        self.con = sqlite3.connect("../sqlite3/foxtons.db")
        self.cur = self.con.cursor()

    def parse(self, response):
        return FormRequest.from_response(
            response,
            formdata=dict(
                email=os.environ["FOXTONS_EMAIL"],
                password=os.environ["FOXTONS_PASSWORD"],
                mode="login",
                variance="default",
                remember_me="1",
            ),
            callback=self.logged_in,
            formid="auth_form",
        )

    def logged_in(self, *a):
        response = self.cur.execute("SELECT url, id FROM properties").fetchall()
        for property_ in response:
            yield Request(url=property_[0], callback=self.parse_property, meta=dict(id=property_[1]))

    def parse_property(self, response):
        is_reduced = len(response.css(".recently_reduced")) > 0
        price_pcm = re.sub("[£,]", "", response.css(".per_month").xpath("./data/text()").get())
        now = datetime.now()

        self.cur.execute(f"""
            INSERT INTO timeline VALUES
                ({float(price_pcm)}, '{response.meta["id"]}', {"1" if is_reduced else "0"}, '{now.isoformat()}', {now.timestamp()})
        """)

        yield dict(
            is_reduced=is_reduced,
            price_pcm=price_pcm,
            id=response.meta["id"],
        )

    def closed(self, *a):
        self.con.commit()
