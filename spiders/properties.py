import scrapy
from scrapy.http import FormRequest, Request
import sqlite3
import os

class PropertiesSpider(scrapy.Spider):
    name = "foxtons-spider"
    start_urls = [
        f"https://www.foxtons.co.uk/properties-to-rent/london?travel_%7Bn%7D_mode=public_transport&travel_%7Bn%7D_travel_time=45&order_by=latest&bedrooms_from={n}&bedrooms_to={n}"
        for n in range(1, 5)
    ]
    download_delay = 1
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
    property_ids = []

    def __init__(self):
        self.con = sqlite3.connect("sqlite3/foxtons.db")
        self.cur = self.con.cursor()

    def start_requests(self):
        login_url = "https://www.foxtons.co.uk/auth/enter/?mode=login"
        return [FormRequest(
            login_url,
            formdata=dict(email=os.environ["FOXTONS_EMAIL"], password=os.environ["FOXTONS_PASSWORD"]),
            callback=self.logged_in,
        )]

    def logged_in(self, *a):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        for property_ in response.css(".property_wrapper"):
            link = property_.xpath(".//h6/a")
            href = "https://www.foxtons.co.uk" + link.xpath("./@href").get()
            id = property_.xpath("./../@id").get()
            address = f"{''.join([t.get() for t in link.css('::text')])}".replace("'", "''")

            if id in self.property_ids:
                continue

            self.cur.execute(f"""
                INSERT INTO properties VALUES
                    ('{address}', '{href}', '{id}')
            """)

            yield dict(
                address=address,
                link=href,
                id=id,
            )

    def closed(self, *a):
        self.con.commit()
