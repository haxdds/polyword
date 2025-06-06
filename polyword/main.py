import os
from polyword.services.ocr import OCRService
from polyword.services.translate import TranslationService
from polyword.services.storage import StorageService
from polyword.services.chatgpt import ChatGPTService
from polyword.processor import PDFProcessor

if __name__ == '__main__':
    # Set up credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcpkey.json'
    # Ensure OPENAI_API_KEY is set in your environment

    input_bucket = 'polyword-bucket'
    output_bucket = 'polyword-bucket'
    pdf_uri = f'gs://{input_bucket}/dzem01.pdf'
    output_prefix = 'results'
    target_language = 'en'

    # Initialize services
    ocr_service = OCRService()
    translation_service = TranslationService()
    storage_service = StorageService()
    chatgpt_service = ChatGPTService()

    # Run processing
    processor = PDFProcessor(
        ocr_service, translation_service, storage_service, chatgpt_service
    )
    result = processor.process_pdf(
        pdf_uri, output_bucket, output_prefix, target_language
    )

    print('Process completed. Results:')
    for key, uri in result.items():
        print(f"{key}: {uri}")