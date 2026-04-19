{{ config(materialized='table') }}

WITH aggregated AS (
    SELECT
        REPLACE(cluster_name, '::value', '') AS onet_task,
        MAX(CASE WHEN facet = 'onet_task::human_education_years' AND variable = 'onet_task_human_education_years_mean' THEN metric_value END) AS human_education_years_mean,
        MAX(CASE WHEN facet = 'onet_task::ai_education_years' AND variable = 'onet_task_ai_education_years_mean' THEN metric_value END) AS ai_education_years_mean,
        MAX(CASE WHEN facet = 'onet_task' AND variable = 'onet_task_pct' THEN metric_value END) AS task_usage_pct
    FROM {{ ref('silver_aei') }}
    WHERE facet IN ('onet_task::human_education_years', 'onet_task::ai_education_years', 'onet_task')
    GROUP BY 1
)
SELECT 
    onet_task,
    human_education_years_mean,
    ai_education_years_mean,
    (ai_education_years_mean - human_education_years_mean) AS ai_vs_human_delta,
    CASE 
        WHEN (ai_education_years_mean - human_education_years_mean) > 1 THEN 'AI exceeds'
        WHEN (ai_education_years_mean - human_education_years_mean) < -1 THEN 'Human exceeds'
        ELSE 'Comparable'
    END AS education_comparison,
    task_usage_pct
FROM aggregated
WHERE human_education_years_mean IS NOT NULL
  AND ai_education_years_mean IS NOT NULL
