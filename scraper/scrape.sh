#!/bin/bash
set -e  

cd /app/petmd_scraper
#python /app/cat-api-breeds.py &
#python /app/scrape_wikipedia.py & 
#python /app/pubmed-lists.py &
#scrapy crawl petmd_breeds &
#scrapy crawl petmd_conditions &
#scrapy crawl pubmed_spider &
wait

echo "Scrapeowanie zakończone"
# tail -f /dev/null