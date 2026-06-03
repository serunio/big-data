from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
import psycopg2


INPUT_PATH = "hdfs:///processed/cats/{final_extracted_knowledge,cat-api_knowledge}/*.json"

DB_CONFIG = {
    "host": "postgres",
    "database": "cats_knowledge",
    "user": "cats",
    "password": "cats"
}


def detect_source(hdfs_path: str, explicit_source: str = None) -> str:
    if explicit_source and str(explicit_source).strip():
        return str(explicit_source).strip().lower()

    if not hdfs_path:
        return "unknown"

    path = hdfs_path.lower()

    markers = [
        "/data/raw/",
        "/raw/data/",
        "cat-api/",
        "/raw/"
    ]

    for marker in markers:
        if marker in path:
            after = path.split(marker, 1)[1]
            parts = [p for p in after.split("/") if p]

            if parts:
                source_name = parts[0].replace(".json", "")
                return parts[0].strip().lower()

    return "unknown"

    
def extract_breed(facts):
    if not facts:
        return None

    for fact in facts:
        if fact.startswith("BREED:"):
            return fact.split(":", 1)[1].strip()

    return None


def parse_fact(raw_fact: str):
    if not raw_fact or ":" not in raw_fact:
        return None

    prefix, value = raw_fact.split(":", 1)
    prefix = prefix.strip().upper()
    value = value.strip()

    if prefix == "BREED":
        return None

    if prefix == "FEATURE":
        if "=" in value:
            key, val = value.split("=", 1)
            fact_type = f"feature_{key.strip().lower()}"
            fact_value = val.strip()
        else:
            fact_type = "feature"
            fact_value = value
    else:
        fact_type = prefix.lower()
        fact_value = value

    if not fact_value:
        return None

    return fact_type, fact_value


def row_to_candidate_facts(row):
    facts = row["extracted_facts"] or []
    hdfs_path = row["source_file"]

    explicit_source = None
    if "source" in row.asDict():
        explicit_source = row["source"]

    source = detect_source(hdfs_path, explicit_source)
    breed = extract_breed(facts)

    if not breed:
        return []

    result = []

    for raw_fact in facts:
        parsed = parse_fact(raw_fact)

        if parsed is None:
            continue

        fact_type, fact_value = parsed

        result.append((
            breed,
            fact_type,
            fact_value,
            source,
            hdfs_path
        ))

    return result

def truncate_candidate_facts():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("TRUNCATE TABLE candidate_facts RESTART IDENTITY;")

    conn.commit()
    cur.close()
    conn.close()


def insert_partition(rows):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    sql = """
        INSERT INTO candidate_facts (
            breed,
            fact_type,
            fact_value,
            source,
            hdfs_path
        )
        VALUES (%s, %s, %s, %s, %s);
    """

    batch = []

    for row in rows:
        batch.append((
            row["breed"],
            row["fact_type"],
            row["fact_value"],
            row["source"],
            row["hdfs_path"]
        ))

    if batch:
        cur.executemany(sql, batch)
        conn.commit()

    cur.close()
    conn.close()


def main():
    spark = SparkSession.builder \
        .appName("LoadCandidateFactsToPostgres") \
        .getOrCreate()

    df = spark.read.json(INPUT_PATH)

    parsed_rdd = df.rdd.flatMap(row_to_candidate_facts)

    schema = StructType([
        StructField("breed", StringType(), False),
        StructField("fact_type", StringType(), False),
        StructField("fact_value", StringType(), False),
        StructField("source", StringType(), True),
        StructField("hdfs_path", StringType(), True),
    ])

    candidate_df = spark.createDataFrame(parsed_rdd, schema)

    candidate_df = candidate_df.dropDuplicates([
        "breed",
        "fact_type",
        "fact_value",
        "source",
        "hdfs_path"
    ])

    print("Przykładowe rekordy do zapisania:")
    candidate_df.show(20, truncate=False)

    print(f"Liczba rekordów: {candidate_df.count()}")

    truncate_candidate_facts()

    candidate_df.foreachPartition(insert_partition)

    print("Zapisano candidate_facts do PostgreSQL.")

    spark.stop()


if __name__ == "__main__":
    main()
