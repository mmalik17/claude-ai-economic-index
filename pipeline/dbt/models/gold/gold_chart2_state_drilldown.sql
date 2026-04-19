{{ config(materialized='table') }}

SELECT
    a.geo_id,
    SUBSTR(a.geo_id, 1, 2) as country_code,
    SUBSTR(a.geo_id, 4, length(a.geo_id)) as region_code,
    a.metric_value as usage_pct,
    c.country_name,
    a.date_start,
    a.date_end
FROM {{ ref('silver_aei') }} a
LEFT JOIN {{ source('staging_raw', 'country_info') }} c
    ON SUBSTR(a.geo_id, 1, 2) = c.iso2
WHERE a.facet = 'country-state'
  AND a.variable = 'usage_pct'
