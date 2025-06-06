from google.cloud import storage

class StorageService:
    def __init__(self, storage_client=None):
        self.client = storage_client or storage.Client()

    def list_blobs(self, bucket_name: str, prefix: str):
        """Lists all blobs in the bucket that begin with the prefix."""
        bucket = self.client.get_bucket(bucket_name)
        return bucket.list_blobs(prefix=prefix)

    def download_blob_content(self, blob) -> str:
        """Downloads a blob's content as a string."""
        return blob.download_as_string().decode('utf-8')

    def save_text(self, bucket_name: str, file_name: str, content: str) -> str:
        """Saves text content to a file in GCS and returns the GCS URI."""
        bucket = self.client.get_bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_string(content)
        print(f'Saved to gs://{bucket_name}/{file_name}')
        return f'gs://{bucket_name}/{file_name}'

    def upload_pdf_to_gcs(self, local_pdf_path: str, bucket_name: str, dest_blob_name: str) -> str:
        """Uploads a local PDF to GCS and returns the GCS URI."""
        bucket = self.client.get_bucket(bucket_name)
        blob = bucket.blob(dest_blob_name)
        blob.upload_from_filename(local_pdf_path)
        return f'gs://{bucket_name}/{dest_blob_name}'