{{ config(materialized='table') }}

-- Aggregating Time Saved metrics
SELECT 
    cluster_name AS task_group,
    MAX(CASE WHEN facet = 'onet_task::human_only_time' AND variable LIKE '%_mean' THEN metric_value END) as human_only_time_mean,
    MAX(CASE WHEN facet = 'onet_task::human_with_ai_time' AND variable LIKE '%_mean' THEN metric_value END) as human_with_ai_time_mean
FROM {{ ref('silver_aei') }}
WHERE facet IN ('onet_task::human_only_time', 'onet_task::human_with_ai_time')
GROUP BY task_group
HAVING human_only_time_mean IS NOT NULL AND human_with_ai_time_mean IS NOT NULL
