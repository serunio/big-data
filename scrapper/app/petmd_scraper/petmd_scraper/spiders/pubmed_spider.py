import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import PurePosixPath

import scrapy
from hdfs import InsecureClient


class PubMedHDFSSpider(scrapy.Spider):
    name = "pubmed_hdfs"

    custom_settings = {
        "DOWNLOAD_DELAY": 0.1,        
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.1,
        "AUTOTHROTTLE_MAX_DELAY": 1,
        "USER_AGENT": "Mozilla/5.0 (compatible; PubMedHDFS/1.0; +mailto:dciaszczyk@gmail.com)",
        "RETRY_TIMES": 3,
        "COOKIES_ENABLED": False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hdfs_url = kwargs.get("hdfs_url", "http://nn:9870")
        hdfs_user = kwargs.get("hdfs_user", "hadoop")
        self.client = InsecureClient(hdfs_url, user=hdfs_user)

        self.api_key = os.getenv("NLM_API_KEY")
        if not self.api_key:
            raise ValueError("NLM_API_KEY environment variable not set")

        self.input_base = "/raw/pubmed/article_list"
        self.output_base = "/raw/pubmed/articles"

    def start_requests(self):
        for status in self.client.walk(self.input_base):
            dir_path, _, files = status
            for file_name in files:
                if not file_name.endswith(".json"):
                    continue

                full_file_path = PurePosixPath(dir_path) / file_name
                breed_group = PurePosixPath(dir_path).name

                try:
                    with self.client.read(str(full_file_path), encoding="utf-8") as reader:
                        record = json.load(reader)
                except (json.JSONDecodeError, Exception) as e:
                    self.logger.error(f"Error reading {full_file_path}: {e}")
                    continue

                xml_payload = record.get("payload")
                if not xml_payload:
                    continue

                try:
                    root = ET.fromstring(xml_payload)
                    id_list = root.find(".//IdList")
                    if id_list is None:
                        continue
                    pmids = [id_elem.text.strip() for id_elem in id_list.findall("Id") if id_elem.text]
                except ET.ParseError:
                    self.logger.error(f"XML parse error in {full_file_path}")
                    continue

                for pmid in pmids:
                    url = (
                        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
                        f"db=pubmed&id={pmid}&retmode=xml&api_key={self.api_key}"
                    )
                    yield scrapy.Request(
                        url,
                        callback=self.save_article,
                        meta={"breed_group": breed_group, "pmid": pmid, "fetch_start": datetime.now().isoformat()},
                        dont_filter=True,  
                    )

    def save_article(self, response):
        breed_group = response.meta["breed_group"]
        pmid = response.meta["pmid"]
        fetch_start = response.meta["fetch_start"]

        output_dir = PurePosixPath(self.output_base) / breed_group
        output_file = output_dir / f"{pmid}.xml"

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