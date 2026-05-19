from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import ArrayType, StringType

spark = SparkSession.builder.appName("CatKnowledgePipeline").getOrCreate()

def extract_facts(text):
    import spacy
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(text)

    results = []

    for token in doc:
        if token.pos_ == "ADJ":
            head = token.head
            if head.pos_ in ["NOUN", "PROPN"]:
                results.append(f"ATTR:{head.text}={token.text}")

    for ent in doc.ents:
        if ent.label_ == "GPE":
            results.append(f"GPE:{ent.text}")

    return results

extract_udf = udf(extract_facts, ArrayType(StringType()))

df = spark.read.json("hdfs:///raw/Maine_Coon/wikipediaapi/Maine_Coon.json")

df2 = df.withColumn("facts", extract_udf(col("payload")))

df2.select("facts") \
   .write \
   .mode("overwrite") \
   .json("hdfs:///processed/cats/Maine_Coon/")