from pyspark.sql import SparkSession
from pyspark.sql.functions import concat_ws
from hdfs import InsecureClient

INPUT = "/processed/cat-api/breeds/*"
OUTPUT = "/processed/cat-api/breed-names.txt"
    
client = InsecureClient("http://nn:9870", user="hadoop")

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.parquet("hdfs://" + INPUT)

rows = df.select(concat_ws(", ", "name", "alt_names").alias("all_names")).collect()
strings = [row["all_names"] for row in rows]
result = "\n".join(strings)


with client.write(OUTPUT, encoding="utf-8") as w:
    w.write(result)

spark.stop()