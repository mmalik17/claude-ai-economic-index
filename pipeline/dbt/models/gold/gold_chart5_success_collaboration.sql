{{ config(materialized='table') }}

WITH collab AS (
    SELECT cluster_name AS onet_task, variable as collab_type, metric_value AS collab_pct
    FROM {{ ref('silver_aei') }}
    WHERE facet = 'onet_task::collaboration'
      AND variable like 'collaboration_pct%'
),
success AS (
    SELECT cluster_name AS onet_task, variable as success_type, metric_value AS success_pct
    FROM {{ ref('silver_aei') }}
    WHERE facet = 'onet_task::task_success'
      AND variable like 'task_success_pct%'
)
SELECT 
    REPLACE(c.collab_type, 'collaboration_pct_','') AS collaboration_pattern,
    REPLACE(s.success_type, 'task_success_pct_','') AS task_success_status,
    AVG(s.success_pct) as avg_task_success_pct,
    AVG(c.collab_pct) as avg_collaboration_pct,
    COUNT(DISTINCT c.onet_task) as task_count
FROM collab c
JOIN success s ON c.onet_task = s.onet_task
GROUP BY 1, 2
