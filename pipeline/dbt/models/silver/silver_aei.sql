{{ config(materialized='view') }}

-- We filter the dataset down to only the facets required for the dashboard
-- to improve performance and narrow the dataset width.

SELECT
    geo_id,
    geography,
    date_start,
    date_end,
    platform_and_product,
    facet,
    level,
    variable,
    cluster_name,
    SAFE_CAST(value AS FLOAT64) as metric_value
FROM {{ source('staging_raw', 'aei_raw_claude_ai') }}
