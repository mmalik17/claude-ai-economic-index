import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "your-gcs-bucket-name")
BQ_DATASET_NAME = os.getenv("BQ_DATASET_NAME", "claude_economic_index")

TABLES_TO_LOAD = {
    "aei_raw_claude_ai": "claude_economic_index/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv",
    "job_exposure": "claude_economic_index/job_exposure.csv",
    "task_penetration": "claude_economic_index/task_penetration.csv",
    "country_info": "claude_economic_index/country_info.csv"
}

def create_dataset_if_not_exists(client, dataset_id):
    try:
        client.get_dataset(dataset_id)
        print(f"Dataset {dataset_id} already exists.")
    except Exception:
        print(f"Dataset {dataset_id} is not found. Creating it...")
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {dataset_id}.")

def load_csv_to_bq(client, table_id, gcs_uri):
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
    )
    print(f"Starting load job for {table_id} from {gcs_uri}...")
    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    
    # Waits for the job to complete
    load_job.result()
    destination_table = client.get_table(table_id)
    print(f"Loaded {destination_table.num_rows} rows into {table_id}.")

def main():
    client = bigquery.Client(project=GCP_PROJECT_ID)
    dataset_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_NAME}"
    
    create_dataset_if_not_exists(client, dataset_id)
    
    for table_name, gcs_path in TABLES_TO_LOAD.items():
        table_id = f"{dataset_id}.{table_name}"
        gcs_uri = f"gs://{GCS_BUCKET_NAME}/{gcs_path}"
        load_csv_to_bq(client, table_id, gcs_uri)

if __name__ == "__main__":
    main()
