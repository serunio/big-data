from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, regexp_extract, sum

INPUT = "/processed/pubmed/article_list"
OUTPUT = "/processed/pubmed/breed_popularity"

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.parquet("hdfs://" + INPUT)

df2 = df.withColumn("count", regexp_extract("payload", r"<Count>(\d+)</Count>", 1).cast("int")) \
        .select("breed", "count").groupBy("breed").agg(sum("count").alias("count")) \
        .withColumn("source", lit(INPUT))

df2.show()

df2.write.mode("overwrite").parquet("hdfs://" + OUTPUT)

spark.stop()