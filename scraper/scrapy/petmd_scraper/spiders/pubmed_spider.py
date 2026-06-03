import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import PurePosixPath

import scrapy
from hdfs import InsecureClient


class PubMedHDFSSpider(scrapy.Spider):
    name = "pubmed_spider"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.1,        
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.1,
        "AUTOTHROTTLE_MAX_DELAY": 1,
        "RETRY_TIMES": 3,
        "COOKIES_ENABLED": False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.logger.info("=== start of init entered ===")


        hdfs_url = kwargs.get("hdfs_url", "http://nn:9870")
        hdfs_user = kwargs.get("hdfs_user", "hadoop")
        self.client = InsecureClient(hdfs_url, user=hdfs_user)

        self.api_key = os.getenv("NLM_API_KEY")
        if not self.api_key:
            raise ValueError("NLM_API_KEY environment variable not set")

        self.input_base = "/raw/pubmed/article_list"
        self.output_base = "/raw/pubmed/articles"
        
    def iter_json_files(self, base_path):
        try:
            entries = self.client.list(base_path)
        except Exception as e:
            self.logger.error("Failed listing %s: %s", base_path, e)
            return

        for entry in entries:
            full_path = str(PurePosixPath(base_path) / entry)

            try:
                status = self.client.status(full_path)
            except Exception as e:
                self.logger.error("Status error %s: %s", full_path, e)
                continue

            if status["type"] == "DIRECTORY":
                yield from self.iter_json_files(full_path)

            elif status["type"] == "FILE" and entry.endswith(".json"):
                yield full_path

    async def start(self):
        json_files = list(self.iter_json_files(self.input_base))

        self.logger.info("Found %d JSON files", len(json_files))

        for full_path in json_files:
            breed_group = PurePosixPath(full_path).parent.name

            self.logger.info(
                "Processing JSON: %s (breed: %s)",
                full_path,
                breed_group,
            )

            try:
                with self.client.read(full_path, encoding="utf-8") as reader:
                    record = json.load(reader)
            except Exception as e:
                self.logger.error("Read error %s: %s", full_path, e)
                continue

            xml_payload = record.get("payload")

            if not xml_payload:
                continue

            try:
                root = ET.fromstring(xml_payload)

                id_list = root.find(".//IdList")

                if id_list is None:
                    continue

                pmids = [
                    el.text.strip()
                    for el in id_list.findall("Id")
                    if el.text
                ]

            except ET.ParseError:
                continue

            for pmid in pmids:
                url = (
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
                    f"efetch.fcgi?db=pubmed&id={pmid}"
                    f"&retmode=xml&api_key={self.api_key}"
                )

                yield scrapy.Request(
                    url,
                    callback=self.save_article,
                    meta={
                        "breed_group": breed_group,
                        "pmid": pmid,
                        "fetch_start": datetime.now().isoformat(),
                    },
                    dont_filter=True,
                )

    def save_article(self, response):
        breed_group = response.meta["breed_group"]
        pmid = response.meta["pmid"]
        fetch_start = response.meta["fetch_start"]

        output_dir = PurePosixPath(self.output_base) / breed_group
        output_file = output_dir / f"{pmid}.json"
        
        self.client.makedirs(str(output_dir), permission="755")

        record = {
            "url": response.url,
            "fetched_at": fetch_start,
            "content_type": "xml",
            "payload": response.text,
        }

        try:
            with self.client.write(str(output_file), overwrite=True, encoding="utf-8") as writer:
                writer.write(json.dumps(record, ensure_ascii=False))
                self.logger.info(f"Saved {pmid} to {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to write {output_file}: {e}")

    def closed(self, reason):
        self.logger.info(f"Spider finished: {reason}")