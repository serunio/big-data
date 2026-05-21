#!/bin/bash
set -e  

cd /app/petmd_scraper
scrapy crawl petmd_breeds &
scrapy crawl petmd_conditions &
python /app/scrape_wikipedia.py & 
wait

echo "Scrapeowanie zakończone"
# tail -f /dev/null