from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("test").getOrCreate()

df = spark.read.text("hdfs://nn:9000/input")

df.show()

df.write.mode("overwrite").text("hdfs://nn:9000/output")

spark.stop()