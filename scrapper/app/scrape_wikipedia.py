#!/usr/bin/env python3
import sys
import json
import time
import logging
import wikipediaapi
from hdfs import InsecureClient

WIKI_CATEGORY = "Category:WikiProject Cats articles"
HDFS_WEBHDFS_URL = "http://nn:9870"   
HDFS_USER = "hadoop"                         
HDFS_BASE_DIR = "/data/raw/wikipedia/cat_articles"       
REQUEST_DELAY = 0.01                       

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

wiki = wikipediaapi.Wikipedia(
    user_agent='WUT_BIGDATA_CATS/0.1 (github.com/serunio/big-data; dciaszczyk@gmail.com)',
    language='en'
)

try:
    hdfs_client = InsecureClient(HDFS_WEBHDFS_URL, user=HDFS_USER)
    try:
        hdfs_client.status(HDFS_BASE_DIR)
    except Exception:
        logging.info(f"Folder {HDFS_BASE_DIR} nie istnieje.")
        hdfs_client.makedirs(HDFS_BASE_DIR, permission=755)
        logging.info(f"Stworzono folder {HDFS_BASE_DIR}")
except Exception as e:
    logging.error(f"Nie udało się połączyć z {HDFS_WEBHDFS_URL}: {e}.")
    sys.exit(1)

if not hdfs_client.status(HDFS_BASE_DIR, strict=False):
    hdfs_client.makedirs(HDFS_BASE_DIR)
    logging.info(f"Stworzono folder HDFS: {HDFS_BASE_DIR}")

def get_article_text(title):
    page = wiki.page(title)
    if page.exists() and page.ns == wikipediaapi.Namespace.MAIN:
        return page.text
    else:
        logging.warning(f"Strona '{title}' nie istnieje.")
        return None

def save_article_to_hdfs(title, content):
    if content is None:
        return

    safe_title = title.replace("/", "_")
    hdfs_file_path = f"{HDFS_BASE_DIR}/{safe_title}.json"

    article_data = {
        "title": title,
        "content": content,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url": page.fullurl if 'page' in locals() else f"https://en.wikipedia.org/wiki/{title}"
    }
    json_data = json.dumps(article_data, indent=2)

    try:
        with hdfs_client.write(hdfs_file_path, overwrite=True, encoding='utf-8') as writer:
            writer.write(json_data)
        logging.info(f"Zapisano: {title} -> {hdfs_file_path}")
    except Exception as e:
        logging.error(f"Nie udało się zapisać {title} do HDFS: {e}")

def main():
    logging.info("Fetchowanie Kategorii: " + WIKI_CATEGORY)
    cat_page = wiki.page(WIKI_CATEGORY)

    if not cat_page.exists():
        logging.error(f"Kategoria '{WIKI_CATEGORY}' nie istnieje.")
        return

    members = cat_page.categorymembers
    total_members = len(members)
    logging.info(f"Znaleziono {total_members} członków w kategorii.")

    saved_count = 0
    for idx, (title, page) in enumerate(members.items(), 1):
        if page.ns == wikipediaapi.Namespace.TALK:
            article_title = title[len("Talk:"):]
            logging.info(f"[{idx}/{total_members}] Talk page: {title} -> article: {article_title}")
            content = get_article_text(article_title)
            if content:
                save_article_to_hdfs(article_title, content)
                saved_count += 1
            time.sleep(REQUEST_DELAY)
        elif page.ns == wikipediaapi.Namespace.CATEGORY_TALK:
            logging.debug(f"Pomijanie Category talk: {title}")
        else:
            logging.debug(f"pomijanie namespace ({page.ns}): {title}")

    logging.info(f"Scrapowanie zakończone. Zapisano {saved_count} artykułów.")

if __name__ == "__main__":
    main()