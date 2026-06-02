from pyspark.sql import SparkSession
from pyspark.sql.functions import concat_ws
from hdfs import InsecureClient
from datetime import datetime
import json

INPUT = "/processed/cat-api/breeds/*"
OUTPUT = "/processed/cat-api/breed-names.json"
    
client = InsecureClient("http://nn:9870", user="hadoop")

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.parquet("hdfs://" + INPUT)

rows = df.select(concat_ws(", ", "name", "alt_names").alias("all_names")).collect()
strings = [row["all_names"] for row in rows]
result = "\n".join(strings)

record = {
    "source": INPUT,
    "generated_at": datetime.now().isoformat(),
    "content_type": "txt",
    "payload": result
    }


with client.write(OUTPUT, encoding="utf-8", overwrite=True) as w:
    w.write(json.dumps(record))

spark.stop()