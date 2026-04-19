import os
import glob
import re
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET_NAME = os.getenv("BQ_DATASET_NAME", "claude_economic_index")

if not GCP_PROJECT_ID:
    print("Cannot find GCP_PROJECT_ID, please check your .env")
    exit(1)

client = bigquery.Client(project=GCP_PROJECT_ID)
dataset_ref = f"{GCP_PROJECT_ID}.{BQ_DATASET_NAME}"

def compile_and_run(sql_path, materialization):
    table_name = os.path.basename(sql_path).replace(".sql", "")
    with open(sql_path, 'r') as f:
        sql = f.read()

    # Strip jinja config block
    sql = re.sub(r'\{\{\s*config\([^\}]+\)\s*\}\}', '', sql)
    
    # Replace source macro
    sql = re.sub(r"\{\{\s*source\('staging_raw',\s*'([^']+)'\)\s*\}\}", rf"`{dataset_ref}.\1`", sql)
    
    # Replace ref macro
    sql = re.sub(r"\{\{\s*ref\('([^']+)'\)\s*\}\}", rf"`{dataset_ref}.\1`", sql)

    if materialization == "table":
        final_sql = f"CREATE OR REPLACE TABLE `{dataset_ref}.{table_name}` AS\n{sql}"
    else:
        final_sql = f"CREATE OR REPLACE VIEW `{dataset_ref}.{table_name}` AS\n{sql}"

    print(f"Executing {materialization} creation for {table_name}...")
    job = client.query(final_sql)
    job.result()
    print(f"Successfully created {table_name}.")

print("Running pure Python fallback DBT runner...")
# Compile Silver first (dependency)
compile_and_run("pipeline/dbt/models/silver/silver_aei.sql", "view")

# Compile Gold Tables
gold_files = glob.glob("pipeline/dbt/models/gold/*.sql")
for gold in gold_files:
    compile_and_run(gold, "table")

print("All transformations complete.")
