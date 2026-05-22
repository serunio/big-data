import scrapy
import json
import os
from hdfs import InsecureClient

class PetmdConditionsSpider(scrapy.Spider):
    name = "petmd_conditions"
    start_urls = ["https://www.petmd.com/cat/conditions"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hdfs_client = InsecureClient('http://nn:9870', user='hadoop')

    def _ensure_directory(self, hdfs_path):
        directory = os.path.dirname(hdfs_path)
        if not self.hdfs_client.content(directory, strict=False):
            self.hdfs_client.makedirs(directory, permission=755)
            self.logger.info(f"Created HDFS directory: {directory}")

    def parse(self, response):
        script = response.css('script#__NEXT_DATA__::text').get()
        if not script:
            self.logger.error("No __NEXT_DATA__ found on %s", response.url)
            return

        data = json.loads(script)
        conditions = data.get('props', {}).get('pageProps', {}).get('data', {}).get('result', [])
        if not conditions:
            conditions = data.get('props', {}).get('pageProps', {}).get('data', {}).get('items', [])

        if not conditions:
            self.logger.error("No conditions extracted from JSON")
            return

        for condition in conditions:
            url = condition.get('url')
            if url:
                yield response.follow(url, callback=self.parse_condition)

    def parse_condition(self, response):
        filename = response.url.rstrip('/').split('/')[-1] + '.html'
        hdfs_path = f'/raw/petmd/conditions/{filename}'

        self._ensure_directory(hdfs_path)

        with self.hdfs_client.write(hdfs_path, overwrite=True) as writer:
            writer.write(response.text.encode('utf-8'))

        self.logger.info(f"Saved {response.url} to {hdfs_path}")

        yield {
            'url': response.url,
            'hdfs_path': hdfs_path,
            'condition_name': response.css('h1::text').get(),
        }