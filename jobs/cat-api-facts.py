from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import explode

INPUT = "/raw/cat-api/breeds.json"
OUTPUT = "/processed/cats/cat-api_knowledge"

spark = SparkSession.builder.appName("CattaBase").getOrCreate()

df = spark.read.json("hdfs://" + INPUT).select(explode('payload').alias('breed')).select('breed.*')

fact_rows = []
for row in df.collect():
    facts = []

    if row["name"]:
        facts.append(f"BREED:{row['name']}")
    
    if row["origin"]:
        facts.append(f"ORIGIN:{row['origin']}")
        
    if row['temperament']:
        character_list = row['temperament'].split(", ")
        for character in character_list:
            facts.append(f"CHARACTER:{character.strip()}")
            
    fact_rows.append(Row(
        extracted_facts=facts, 
        source_file='hdfs://nn:9000/raw/cat-api/breeds.json', 
        title=row['name']
    ))

df2 = spark.createDataFrame(fact_rows)
df2.write.mode('overwrite').json(f"hdfs://{OUTPUT}")
