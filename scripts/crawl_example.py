import requests
from bs4 import BeautifulSoup
from datetime import datetime
from hdfs import InsecureClient
import json
import wikipediaapi

client = InsecureClient("http://nn:9870", user="hadoop")

# def fetch(url):
#     r = requests.get(url, timeout=10)
#     r.raise_for_status()
#     return r.text

# def crawl(url):
#     html = fetch(url)

#     record = {
#         "url": url,
#         "fetched_at": datetime.now().isoformat(),
#         "content_type": "html",
#         "payload": html
#     }

#     path = f"/raw/web/{url.replace('https://','').replace('/','_')}.json"

#     with client.write(path, encoding="utf-8") as w:
#         w.write(json.dumps(record))

# crawl("https://en.wikipedia.org/api/rest_v1/page/html/Maine_Coon")

wiki = wikipediaapi.Wikipedia(user_agent='CataBase', language='en')
def wiki_get(name):
    payload = wiki.page(name).text
    record = {
    "url": f'https://en.wikipedia.org/api/rest_v1/page/html/{name}',
    "fetched_at": datetime.now().isoformat(),
    "content_type": "text",
    "payload": payload
    }
    path = f"/raw/{name}/wikipediaapi/{name}.json"

    with client.write(path, encoding="utf-8") as w:
        w.write(json.dumps(record))

wiki_get('Maine_Coon')