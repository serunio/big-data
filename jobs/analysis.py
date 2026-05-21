import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://cats:cats@localhost:5432/cats_knowledge")

df = pd.read_sql("SELECT * FROM candidate_facts", engine)
weights = pd.read_sql("SELECT * FROM source_weights", engine)
df = df.dropna(subset=["breed", "fact_type", "fact_value"])
df["breed"]      = df["breed"].str.strip().str.title()
df["fact_type"]  = df["fact_type"].str.strip().str.upper()
df["fact_value"] = df["fact_value"].str.strip().str.lower()
df["source"]     = df["source"].str.strip().str.lower().fillna("unknown")
df = df.drop_duplicates(subset=["breed", "fact_type", "fact_value", "source"])

