import os
from google.cloud import storage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "your-gcs-bucket-name")

DATASET_DIR = "dataset"
FILES_TO_UPLOAD = [
    "aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv",
    "job_exposure.csv",
    "task_penetration.csv",
    "country_info.csv"
]

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    # We skip bucket.reload() or create_bucket here since the service account may lack
    # `storage.buckets.get` or `storage.buckets.create` permissions.
    # It will just attempt the upload directly.

    print(f"Uploading {source_file_name} to {destination_blob_name}...")
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} successfully uploaded to {destination_blob_name}.")

def main():
    if not os.path.exists(DATASET_DIR):
        print(f"Dataset directory '{DATASET_DIR}' not found relative to script.")
        return

    for file_name in FILES_TO_UPLOAD:
        source_path = os.path.join(DATASET_DIR, file_name)
        if os.path.exists(source_path):
            # We preserve the original filenames inside GCS in a specific folder
            destination = f"claude_economic_index/{file_name}"
            upload_blob(GCS_BUCKET_NAME, source_path, destination)
        else:
            print(f"Warning: File {source_path} not found locally.")

if __name__ == "__main__":
    main()
