import streamlit as st
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    dbname="cats_knowledge",
    user="cats",
    password="cats",
    host="postgres",
    port=5432
)

st.title("Cat Facts Search")

query = st.text_input("Search facts")

if query:
    cur = conn.cursor()
    cur.execute("""
        SELECT breed, fact_type, fact_value, source_list, mentions_count, final_score
        FROM final_facts,
            to_tsquery('simple', %s) query
        WHERE search_vector @@ query
        ORDER BY final_score DESC, ts_rank(search_vector, query) DESC;
    """, (query.replace(" ", " & "),))

    rows = cur.fetchall()

    
    df = pd.DataFrame(rows, columns=[
        "breed", "fact type", "fact value", "sources", "mentions", "score"
    ])

    st.dataframe(df, use_container_width=True)