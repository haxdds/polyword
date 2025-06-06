import json
from google.cloud import vision

class OCRService:
    def __init__(self, vision_client=None):
        self.client = vision_client or vision.ImageAnnotatorClient()

    def async_detect_document(self, gcs_source_uri: str, gcs_destination_uri: str,
                              mime_type: str = 'application/pdf', batch_size: int = 100) -> str:
        """
        Performs async document text OCR on a PDF/TIFF file in GCS.
        Returns the GCS URI where JSON output will be written.
        """
        input_config = vision.InputConfig(
            gcs_source=vision.GcsSource(uri=gcs_source_uri),
            mime_type=mime_type
        )
        output_config = vision.OutputConfig(
            gcs_destination=vision.GcsDestination(uri=gcs_destination_uri),
            batch_size=batch_size
        )
        async_request = vision.AsyncAnnotateFileRequest(
            features=[vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)],
            input_config=input_config,
            output_config=output_config
        )
        operation = self.client.async_batch_annotate_files(requests=[async_request])
        print('Waiting for the operation to finish...')
        operation.result(timeout=420)
        print('OCR operation completed')
        return gcs_destination_uri

    def extract_text_from_results(self, storage_service, bucket_name: str, prefix: str) -> str:
        """
        Reads OCR JSON outputs from GCS, concatenates all page texts, and returns as a single string.
        """
        blobs = storage_service.list_blobs(bucket_name, prefix)
        all_text = ''
        for blob in blobs:
            if not blob.name.endswith('.json'):
                continue
            content = storage_service.download_blob_content(blob)
            document = json.loads(content)
            for page in document.get('responses', []):
                if 'fullTextAnnotation' in page:
                    all_text += page['fullTextAnnotation']['text'] + '\n\n'
        return all_text