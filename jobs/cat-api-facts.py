from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import explode

INPUT = "/raw/cat-api/breeds.json"
OUTPUT = "/processed/cats/cat-api_knowledge"

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.json("hdfs://" + INPUT).select(explode('payload').alias('breed')).select('breed.*')

fact_rows = []
for row in df.collect():
    character_list_str:str = row['temperament']
    character_list = character_list_str.split(", ")
    character_facts = ", CHARACTER:".join(character_list)
    fact_rows.append(Row(extracted_facts=f'ORIGIN:{row["origin"]}, {character_facts}', source_file='hdfs://nn:9000/raw/cat-api/breeds.json', title=row['name']))

df2 = spark.createDataFrame(fact_rows)
df2.write.mode('overwrite').json(f"hdfs://{OUTPUT}")