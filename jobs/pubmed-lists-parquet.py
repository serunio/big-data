from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_replace, regexp_extract, input_file_name

INPUT = "/raw/pubmed/article_list"
OUTPUT = "/processed/pubmed/article_list"

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.json("hdfs://" + INPUT + "/*/*.json")

df2 = df.withColumn("breed", regexp_extract(input_file_name(), r"/raw/pubmed/article_list/([^/]+)/", 1)) \
        .withColumn("breed", regexp_replace("breed", r"%20", r" ")) \

df2.write.mode("overwrite").parquet("hdfs://" + OUTPUT)

spark.stop()