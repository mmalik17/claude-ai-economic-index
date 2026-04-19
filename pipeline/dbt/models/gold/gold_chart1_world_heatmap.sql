{{ config(materialized='table') }}

SELECT
    a.geo_id,
    c.country_name,
    c.continent_name,
    c.population,
    a.metric_value as usage_pct,
    a.date_start,
    a.date_end
FROM {{ ref('silver_aei') }} a
LEFT JOIN {{ source('staging_raw', 'country_info') }} c
    ON a.geo_id = c.iso2
WHERE a.facet = 'country'
  AND a.variable = 'usage_pct'
