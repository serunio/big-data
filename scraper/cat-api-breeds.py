import requests
from datetime import datetime
from hdfs import InsecureClient
import json

OUTPUT = "/raw/cat-api/breeds.json"

client = InsecureClient("http://nn:9870", user="hadoop")

url = 'https://api.thecatapi.com/v1/breeds'
r = requests.get(url)
r.raise_for_status()
payload = r.json()

record = {
    "url": url,
    "fetched_at": datetime.now().isoformat(),
    "content_type": "json",
    "payload": payload
    }

with client.write(OUTPUT, encoding="utf-8") as w:
    w.write(json.dumps(record))