# Claude AI Economic Index — Dashboard

This repository contains an end-to-end data engineering pipeline and interactive dashboard visualizing **Claude AI's economic impact and usage patterns** across the global economy. The project leverages Anthropic's Economic Index (AEI) dataset (week of Feb 5–12, 2026).

---

# Project Overview

## Problem Background
1.  **Geographic Inequality**: Global AI adoption is rapidly evolving, but which regions are leading? There is a lack of granular visibility into whether AI usage is concentrated in tech hubs or being adopted democratically across developing regions.
2.  **The Productivity Dividend**: Does AI actually save time? While anecdotal evidence suggests high efficiency, researchers need empirical data to identify which specific O*NET occupational tasks see the most significant time reductions.
3.  **The Skill Shift**: As AI demonstrates high-level knowledge, the educational requirements for "knowledge work" are changing. We need to understand the gap between the education a human needs for a task versus the knowledge demonstrated by AI.

## Project Objective
1.  **Map Global Adoption**: Quantify and visualize Claude's usage share at both national and subnational (state/province) levels to identify global AI hotspots.
2.  **Validate Productivity Gains**: Analyze and compare the time taken for tasks with and without AI assistance to pinpoint the high-impact efficiency gains across industries.
3.  **Assess Skill Democratization**: Compare human education requirements against AI-demonstrated knowledge to evaluate how Claude amplifiers professional expertise and democratizes complex skills.

## Important Files
- `dashboard/app.py`: The Main Streamlit application serving the dashboard.
- `pipeline/bruin/pipeline.yml`: The orchestration DAG defining the ingestion and transformation flow.
- `pipeline/dbt/`: The transformation logic layer (Staging, Silver, and Gold models).
- `Dockerfile` & `docker-compose.yml`: Full containerization for reproducible deployment.

---

# Architecture and Tech Stack

## Architecture Diagram 
[https://github.com/mmalik17/claude-ai-economic-index/blob/main/image/Data%20Pipeline%20Architecture.jpg](https://github.com/mmalik17/claude-ai-economic-index/blob/main/image/Data%20Pipeline%20Architecture.jpg?raw=true)


## Tech Stack Explanation
| Component | Tool | Function |
|---|---|---|
| **Orchestration** | [Bruin](https://getbruin.com) | Manages the end-to-end pipeline (Ingestion -> GCS -> BigQuery -> dbt). |
| **Transformation** | [dbt](https://getdbt.com) | SQL-based transformation for Silver (cleansing) and Gold (marts) layers. |
| **Data Lake** | **Google Cloud Storage** | Stores raw CSV data as the landing zone (Bronze layer). |
| **Data Warehouse**| **BigQuery** | Central storage and compute for analytical processing and dashboard queries. |
| **Visualization** | **Streamlit** | Multi-page interactive UI for data exploration. |
| **Infrastructure** | **Docker Compose** | Orchestrates the entire stack for one-click cross-platform deployment. |

## Project Structure
```text
.
├── dashboard
│   └── app.py                  # Streamlit Dashboard UI
├── dataset
│   ├── aei_raw_claude_ai...csv # Main AEI usage dataset
│   ├── job_exposure.csv       # Task-to-Job mapping
│   ├── task_penetration.csv  # AI penetration rates
│   └── country_info.csv       # Geographic metadata (join key)
├── pipeline
│   ├── bruin
│   │   └── pipeline.yml       # Orchestration DAG
│   ├── dbt                    # Transformation layer
│   └── scripts                # Ingestion & Utility scripts
├── Dockerfile                  # Container build config
├── docker-compose.yml          # Service orchestration
├── requirements.txt            # Python dependencies
└── .env.example                # Environment template
```

## Data Source
All files are located in the `/dataset` folder.
- **Source**: Anthropic Economic Index (AEI) - Feb 2026 Release.
- **Key Columns**:
  - `geo_id`: ISO country or region code.
  - `usage_pct`: Percentage of global/regional AI conversations.
  - `onet_task`: Standardized O*NET work task descriptions.
  - `human_only_time_mean`: Baseline hours required by a human.
  - `ai_education_years_mean`: Equivalent knowledge level demonstrated by AI.

---

# Transformation Layer (DBT)

The transformation logic is implemented in `dbt-bigquery`, split into a layered architecture:

```text
pipeline/dbt/models/
├── gold
│   ├── gold_chart1_world_heatmap.sql   # Map data
│   ├── gold_chart2_state_drilldown.sql # Subnational metrics
│   ├── gold_chart3_time_saved.sql      # Productivity stats
│   └── gold_chart4_education_scatter.sql # Skill gap analysis
├── silver
│   └── silver_aei.sql                  # Normalized/Cleaned main table
└── staging
    └── sources.yml                     # Inbound BigQuery references
```

---

# Storage Layer

- **Google Cloud Storage (Data Lake)**: Uses `pipeline/scripts/upload_to_gcs.py` to push raw CSV files into an organized bucket structure.
- **Google BigQuery (Data Warehouse)**:
  - **Raw Schema**: Initial load of GCS data.
  - **Silver Schema**: Optimized, cleaned, and joined (e.g., joining AEI with `country_info`).
  - **Gold Schema**: Specific "Datamart" tables optimized for dashboard performance.

---

# Visualization Layer (Streamlit Dashboard)

The dashboard is accessible on port `8501` and features **three analytical pages** optimized for high-density, single-viewport performance:
1.  **Geographic Analysis**: Treemaps chart and reordered metric cards that show Claude's usage share at both national and subnational (state/province) levels to identify global AI hotspots.
2.  **Time & Productivity**: Horizontal grouped visualizations of "time saved" dividends across task types.
3.  **Education & Skills**: Tabbed horizontal bar charts analyzing "Education Delta" leads and a searchable 3,000+ task data hub.

---

# Quick Start / How to Run Project

### Prerequisites
1.  **Docker Desktop** (latest version).
2.  **GCP Service Account**: A JSON key with `Storage Admin` and `BigQuery Admin` permissions.

### Setup Steps
1.  **Clone this repository**.
2.  **Place your GCP Key**: Rename your JSON key to `zoomcamp-2026-privatekey.json` and place it in the root directory.
3.  **Configure Environment**:
    ```bash
    cp .env.example .env
    ```
    Update the `GCP_PROJECT_ID` and other variables in `.env`.
4.  **Launch the Project**:
    ```bash
    docker-compose up --build
    ```

The dashboard will be available at [http://localhost:8501](http://localhost:8501).

---

# Evaluation Criteria

The project is designed to align with the **Data Engineering Zoomcamp 2026** evaluation criteria:

| Criteria | Status | Implementation Detail |
|---|---|---|
| **Problem Description** | ✅ Compliant | Clear problem statements and objectives for all focus areas. |
| **Cloud** | ✅ Compliant | Fully integrated with Google Cloud (GCS & BigQuery). |
| **Data Ingestion** | ✅ Compliant | End-to-end DAG using **Bruin** for orchestrating GCS uploads and BQ loading. |
| **Data Warehouse** | ✅ Compliant | Layered architecture in BigQuery (Raw -> Silver -> Gold). |
| **Transformations** | ✅ Compliant | Comprehensive **dbt** project with staging and analytical models. |
| **Dashboard** | ✅ Compliant | 3-page interactive Streamlit app with multiple chart types. |
| **Reproducibility** | ✅ Compliant | Fully containerized with Docker; detailed Quick Start instructions. |
| **Clean Code** | ✅ Compliant | Used environment variables for credentials and optimized (.dockerignore). |
