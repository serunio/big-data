import sys
import re
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, input_file_name
from pyspark.sql.types import ArrayType, StringType

BREED_DICTIONARY_PATH = "/processed/cat-api/breed-names.txt"
WIKIPEDIA_INPUT_PATH = "/raw/wikipedia/cat_articles/*.json"
PETMD_CONDITIONS_PATH = "/raw/petmd/conditions/*.json"
PETMD_BREEDS_PATH     = "/raw/petmd/breeds/*.json"
OUTPUT_PATH = "/processed/cats/final_extracted_knowledge"

_nlp_model = None
_broadcasted_patterns = None


def init_nlp_pipeline(local_patterns):
    global _nlp_model
    import spacy

    nlp = spacy.load("en_core_web_sm")
    ruler = nlp.add_pipe("entity_ruler", before="ner")


    medical_patterns = [
        {"label": "DISEASE", "pattern": [{"LOWER": "hypertrophic"}, {"LOWER": "cardiomyopathy"}],
         "id": "Hypertrophic Cardiomyopathy"},
        {"label": "DISEASE", "pattern": [{"LOWER": "hcm"}], "id": "Hypertrophic Cardiomyopathy"},
        {"label": "DISEASE", "pattern": [{"LOWER": "polycystic"}, {"LOWER": "kidney"}, {"LOWER": "disease"}],
         "id": "Polycystic Kidney Disease"},
        {"label": "SYMPTOM", "pattern": [{"LOWER": "lethargy"}], "id": "Lethargy"},
        {"label": "SYMPTOM", "pattern": [{"LOWER": "vomiting"}], "id": "Vomiting"}
    ]

    all_patterns = local_patterns + medical_patterns
    ruler.add_patterns(all_patterns)
    _nlp_model = nlp


def extract_knowledge(text):
    if not text or not isinstance(text, str):
        return []
        
    if bool(re.search(r'<[^>]+>', text)):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text(separator=" ")
        
    global _nlp_model

    if _nlp_model is None:
        import spacy
        _nlp_model = spacy.load("en_core_web_sm")

    doc = _nlp_model(text)
    facts = []

    for ent in doc.ents:
        if ent.label_ in ["BREED", "DISEASE", "SYMPTOM"]:
            normalized = ent.ent_id_ if ent.ent_id_ else ent.text
            facts.append(f"{ent.label_}:{normalized}")
        elif ent.label_ == "GPE":
            facts.append(f"ORIGIN:{ent.text}")

    for token in doc:
        if token.pos_ == "ADJ" and token.dep_ == "amod":
            if token.head.lemma_ in ["fur", "coat", "ear", "tail", "body", "size", "eye"]:
                facts.append(f"FEATURE:{token.head.lemma_}={token.lower_}")

        if token.pos_ == "ADJ" and token.dep_ == "acomp":
            for child in token.head.children:
                if child.dep_ == "nsubj" and (
                        child.lemma_ in ["cat", "breed", "animal"] or child.ent_type_ == "BREED"):
                    facts.append(f"CHARACTER:{token.lower_}")

    return sorted(list(set(facts)))


def main():
    spark = SparkSession.builder \
        .appName("CatHdfsNlpPipeline") \
        .getOrCreate()

    print("Uruchamianie potoku NLP")

    print("Ladowanie slownika ras z HDFS")
    patterns = []
    try:
        df_dict = spark.read.text(f"hdfs://{BREED_DICTIONARY_PATH}")
        lines = [row.value for row in df_dict.collect()]

        for line in lines:
            if not line or not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if not parts or not parts[0]:
                continue
            official_name = parts[0]

            for synonym in set(parts):
                if synonym and synonym.strip():
                    patterns.append({
                        "label": "BREED",
                        "pattern": [{"LOWER": t} for t in synonym.lower().split()],
                        "id": official_name
                    })
        print(f"Sukces! Wygenerowano {len(patterns)} regul dla spaCy.")
    except Exception as e:
        print(f"BLAD slownika: {e}.")
        patterns.append(
            {"label": "BREED", "pattern": [{"LOWER": "maine"}, {"LOWER": "coon"}], "id": "Maine Coon"})


    init_nlp_pipeline(patterns)

    extract_knowledge_udf = udf(extract_knowledge, ArrayType(StringType()))

    paths_to_load = [
        f"hdfs://{WIKIPEDIA_INPUT_PATH}",
        f"hdfs://{PETMD_CONDITIONS_PATH}",
        f"hdfs://{PETMD_BREEDS_PATH}"
    ]

    print(f"Wczytywanie danych z HDFS")

    try:
        df_raw = spark.read.option("multiline", "true").json(paths_to_load)
    except Exception as e:
        print(f"BLAD: Brak plikow.")
        spark.stop()
        sys.exit(1)

    if "content" in df_raw.columns:
        df_unified = df_raw.withColumnRenamed("content", "text_to_process")
    else:
        print("BLAD: Brak kolumny 'content' w plikach JSON.")
        spark.stop()
        sys.exit(1)

    df_with_meta = df_unified.withColumn("source_file", input_file_name())

    print("Analiza NLP w toku...")
    df_results = df_with_meta.withColumn("extracted_facts", extract_knowledge_udf(col("text_to_process")))


    hdfs_output_path = f"hdfs://{OUTPUT_PATH}"
    print(f"Zapisywanie wynikow do HDFS: {hdfs_output_path}")

    df_results.select("title", "source_file", "extracted_facts") \
        .write \
        .mode("overwrite") \
        .json(hdfs_output_path)

    print("PROCES INTEGRACJI NLP Z HDFS ZAKONCZONY SUKCESEM!")
    spark.stop()


if __name__ == "__main__":
    main()
