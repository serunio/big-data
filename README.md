# big-data

### Build

```
./start.sh
```

Tworzy dzielone woluminy i uruchamia compose. żadnego pierdolenia się z macvlanem. Do tego na nn uruchamia dfs i yarna.

stop.sh je kładzie.

### Wejście do namenode

Przez Docker:

```
sudo docker exec -it --user hadoop nn bash
```

### wystawione porty

8088 - yarn
9870 - hadoop ui
9000 - do komunikacji z hdfs z hosta

### scripts

[crawl_example.py](scripts/crawl_example.py) pobiera z api Wikipedii stronę o jednej z ras i zapisuje jej tekst w hdfs.  
Wywołujemy z hosta:

```
sudo docker exec -it spark python3 /scripts/script.py
```

lub

```
./script.sh script.py
```

### spark jobs

Przed uruchomieniem joba trzeba na namenode uruchomić hdfs `start-dfs.sh`  (uruchamia sie sam w skrypcie build)
Potem z hosta:

```
sudo docker exec -it spark spark-submit /jobs/job.py
```

lub

```
./spark.sh job.py
```

Wyniki na namenode:

```
hdfs dfs -ls /output
```

[nlp_example.py](jobs/nlp_example.py) zawiera prostą przykładową analizę nlp. Wyciąda z tekstu pary przymiotnik-rzeczownik (potencjalny opis rasy) oraz nazwy krajów/miast (potencjalne pochodzenie)

# scrapeowanie

Wikipedia:
~1200 artykułów

petmd: choroby i rasy

```
sudo docker exec -it --user scrapper scrapper scrape.sh
```

można pogrzebać w ustawieniach scrapy zmniejszyć opóźnienie trochę

# hdfs

```
sudo docker exec -it --user hadoop nn bash
```
