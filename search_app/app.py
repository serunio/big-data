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
        SELECT breed, fact_type, fact_value, source_list, final_score,
            ts_rank(search_vector, query) AS rank
        FROM final_facts,
            to_tsquery('simple', %s) query
        WHERE search_vector @@ query
        ORDER BY rank DESC, final_score DESC;
    """, (query.replace(" ", " & "),))

    rows = cur.fetchall()

    
    df = pd.DataFrame(rows, columns=[
        "breed", "fact_type", "fact_value", "sources", "final_score", "rank"
    ])

    st.dataframe(df, use_container_width=True)