from polyword.services.ocr import OCRService
from polyword.services.translate import TranslationService
from polyword.services.storage import StorageService
from polyword.services.chatgpt import ChatGPTService
from markdown_pdf import MarkdownPdf, Section
import tempfile
import os

class PDFProcessor:
    def __init__(
        self,
        ocr_service: OCRService,
        translation_service: TranslationService,
        storage_service: StorageService,
        chatgpt_service: ChatGPTService
    ):
        self.ocr = ocr_service
        self.translator = translation_service
        self.storage = storage_service
        self.chatgpt = chatgpt_service

    def process_pdf(
        self,
        pdf_uri: str,
        output_bucket: str,
        output_prefix: str,
        target_language: str
    ) -> dict:
        # Step 1: OCR
        json_output_uri = f'gs://{output_bucket}/{output_prefix}/'
        self.ocr.async_detect_document(pdf_uri, json_output_uri)

        # Step 2: Extract text
        extracted_text = self.ocr.extract_text_from_results(
            self.storage, output_bucket, output_prefix
        )
        original_uri = self.storage.save_text(
            output_bucket,
            f"{output_prefix}/original_text.txt",
            extracted_text
        )

        # Step 3: Translate
        translated_text = self.translator.translate_text(
            extracted_text, target_language
        )
        translated_uri = self.storage.save_text(
            output_bucket,
            f"{output_prefix}/translated_text_{target_language}.txt",
            translated_text
        )

        # Step 4: Refine
        refined_text = self.chatgpt.refine_text(translated_text)
        refined_uri = self.storage.save_text(
            output_bucket,
            f"{output_prefix}/refined_text_{target_language}.txt",
            refined_text
        )

        # Step 5: Convert refined text to PDF
        pdf_uri = self._convert_to_pdf(
            refined_text,
            output_bucket,
            f"{output_prefix}/refined_text_{target_language}.pdf"
        )

        return {
            'original_text_uri': original_uri,
            'translated_text_uri': translated_uri,
            'refined_text_uri': refined_uri,
            'refined_pdf_uri': pdf_uri
        }

    def _convert_to_pdf(self, markdown_text: str, bucket_name: str, dest_blob_name: str) -> str:
        """Convert markdown text to PDF and upload to GCS."""
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            # Initialize PDF converter
            pdf = MarkdownPdf(toc_level=2, optimize=True)
            
            # Add metadata
            pdf.meta["title"] = "Refined Document"
            pdf.meta["author"] = "PolyWord"
            
            # Add the markdown content as a section
            pdf.add_section(Section(markdown_text))
            
            # Save to temporary file
            pdf.save(temp_pdf.name)
            
            # Upload to GCS
            gcs_uri = self.storage.upload_pdf_to_gcs(
                temp_pdf.name,
                bucket_name,
                dest_blob_name
            )
            
            # Clean up temporary file
            os.unlink(temp_pdf.name)
            
            return gcs_uri