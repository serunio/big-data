INSERT INTO final_facts (
    breed,
    fact_type,
    fact_value,
    mentions_count,
    sources_count,
    source_list,
    final_score
)
WITH base AS (
    SELECT
        breed,
        fact_type,
        fact_value,
        sw.weight AS weight,
        cf.source
    FROM candidate_facts cf
    JOIN source_weights sw ON cf.source = sw.source
),

aggregated_by_source AS (
    SELECT
        breed,
        fact_type,
        fact_value,
        COUNT(*) AS mentions_count,
        source,
        weight
    FROM base
    GROUP BY breed, fact_type, fact_value, source, weight
),

final AS (
    SELECT
        breed,
        fact_type,
        fact_value,
        SUM(mentions_count) AS mentions_count,
        COUNT(DISTINCT source) AS sources_count,
        STRING_AGG(DISTINCT source, '; ') AS source_list,
        SUM(weight) * LOG(1 + SUM(mentions_count)) * LOG(1 + COUNT(DISTINCT source)) AS final_score
    FROM aggregated_by_source
    GROUP BY breed, fact_type, fact_value
)

SELECT
    breed,
    fact_type,
    fact_value,
    mentions_count,
    sources_count,
    source_list,
    final_score
FROM final;