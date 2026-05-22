from pyspark.sql import SparkSession
from pyspark.sql.functions import explode

INPUT = "/raw/cat-api/breeds.json"
OUTPUT = "/processed/cat-api/breeds"

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.json("hdfs://" + INPUT)

df2 = df.select(explode("payload").alias("breed"))

df2.select("breed.*").write.mode("overwrite").parquet("hdfs://" + OUTPUT)

spark.stop()