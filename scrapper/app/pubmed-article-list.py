import json

from hdfs import InsecureClient
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime

client = InsecureClient("http://nn:9870", user="hadoop")

nlp_apikey = os.getenv("NLM_API_KEY")

rows = []
with client.read("/processed/cat-api/breed-names.txt", encoding="utf-8") as reader:
    content = reader.read()
    rows = content.split("\n")

count = len(rows)
i = 1
for row in rows:
    names = row.split(", ")
    for name in names:
        if name.strip() == "":
            continue
        link_name = name.replace(" ", "+").lower()
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={link_name}+AND+cat&retmax=9999&api_key={nlp_apikey}"
        r = requests.get(url)

        try:
            r.raise_for_status()
            record = {
                "url": url,
                "fetched_at": datetime.now().isoformat(),
                "content_type": "xml",
                "payload": r.text
            }
            with client.write(f"/raw/pubmed/article_list/{names[0]}/{link_name}.json", overwrite=True, encoding="utf-8") as w:
                w.write(json.dumps(record))
        except requests.RequestException as e:
            print(f"Error fetching data for {name}: {e}")
            print(url)

        print(f"\rProcessed {i}/{count}", end="")
    i += 1