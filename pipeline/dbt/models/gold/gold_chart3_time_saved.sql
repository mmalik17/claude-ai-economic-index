{{ config(materialized='table') }}

WITH aggregated AS (
    SELECT
        REPLACE(cluster_name, '::value', '') AS onet_task,
        MAX(CASE WHEN facet = 'onet_task::human_with_ai_time' AND variable = 'onet_task_human_with_ai_time_mean' THEN metric_value END) AS human_only_time_hrs,
        MAX(CASE WHEN facet = 'onet_task::human_only_time' AND variable = 'onet_task_human_only_time_mean' THEN metric_value END) AS human_with_ai_time_hrs,
        MAX(CASE WHEN facet = 'onet_task' AND variable = 'onet_task_pct' THEN metric_value END) AS task_usage_pct
    FROM {{ ref('silver_aei') }}
    WHERE facet IN ('onet_task::human_only_time', 'onet_task::human_with_ai_time', 'onet_task')
    GROUP BY 1
)
SELECT 
    onet_task,
    human_only_time_hrs,
    human_with_ai_time_hrs,
    (human_only_time_hrs - human_with_ai_time_hrs) AS time_saved_hrs,
    ((human_only_time_hrs - human_with_ai_time_hrs) / NULLIF(human_only_time_hrs, 0)) * 100 AS pct_time_saved,
    task_usage_pct
FROM aggregated
WHERE human_only_time_hrs IS NOT NULL
  AND human_with_ai_time_hrs IS NOT NULL
