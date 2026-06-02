from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, current_timestamp, lit
from datetime import datetime

INPUT = "/raw/cat-api/breeds.json"
OUTPUT = "/processed/cat-api/breeds"

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.json("hdfs://" + INPUT)

df2 = df.select(explode("payload").alias("breed"))

df2.select("breed.*") \
    .withColumn("generated_at", current_timestamp()) \
    .withColumn("source", lit(INPUT)) \
    .write.mode("overwrite").parquet("hdfs://" + OUTPUT)

spark.stop()