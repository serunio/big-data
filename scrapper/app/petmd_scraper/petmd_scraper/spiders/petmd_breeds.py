import scrapy
import json
import os
from hdfs import InsecureClient

class PetmdBreedsSpider(scrapy.Spider):
    name = "petmd_breeds"
    start_urls = ["https://www.petmd.com/cat/breeds"]

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
        breeds = data.get('props', {}).get('pageProps', {}).get('data', {}).get('result', [])
        if not breeds:
            self.logger.warning("No breeds found in JSON")
            return

        for breed in breeds:
            url = breed.get('url')
            if url:
                yield response.follow(url, callback=self.parse_breed)

    def parse_breed(self, response):
        filename = response.url.rstrip('/').split('/')[-1] + '.html'
        hdfs_path = f'/raw/petmd/breeds/{filename}'

        self._ensure_directory(hdfs_path)

        with self.hdfs_client.write(hdfs_path, overwrite=True) as writer:
            writer.write(response.text.encode('utf-8'))

        self.logger.info(f"Saved {response.url} to {hdfs_path}")

        yield {
            'url': response.url,
            'hdfs_path': hdfs_path,
            'breed_name': response.css('h1::text').get(),
        }