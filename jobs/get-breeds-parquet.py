from pyspark.sql import SparkSession
from pyspark.sql.functions import explode

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.json("hdfs:///raw/cat-api/breeds.json")

df2 = df.select(explode("payload").alias("breed"))

df2.select("breed.*").write.mode("override").parquet("hdfs:///processed/cat-api/breeds")

spark.stop()