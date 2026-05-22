CREATE TABLE IF NOT EXISTS candidate_facts (  --output z nlp
    id SERIAL PRIMARY KEY,
    breed TEXT NOT NULL,        --rasa
    fact_type TEXT NOT NULL,    --kategoria informacji
    fact_value TEXT NOT NULL,   --treść informacji
    source TEXT,                --źródło: wikipedia/reddit/...
    hdfs_path TEXT              --ścieżka do jsona z którego stworzono fakt
);

CREATE TABLE IF NOT EXISTS source_weights (   
    source TEXT PRIMARY KEY,    --źródło: wikipedia/reddit/...
    weight DOUBLE PRECISION     --jakaś subiektywna waga wiarygodnosci danego źródła
);

CREATE TABLE IF NOT EXISTS final_facts (  --output po czyszczeniu i agregacji
    id SERIAL PRIMARY KEY,
    breed TEXT NOT NULL,
    fact_type TEXT NOT NULL,
    fact_value TEXT NOT NULL,
    mentions_count INTEGER NOT NULL,  --ile wystąpień
    sources_count INTEGER NOT NULL,   --w ilu źródłach  
    source_list TEXT,                 --lista źródeł zawierających fakt
    final_score DOUBLE PRECISION,     --końcowy wskaźnik wiarygodności wyliczany na podstawie źródeł i ich wag
    search_vector tsvector,           --wektor do pełnotekstowego wyszukiwania
    UNIQUE (breed, fact_type, fact_value)
);

CREATE INDEX idx_final_facts_search
ON final_facts
USING GIN(search_vector);