import os
import uuid
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from polyword.services.ocr import OCRService
from polyword.services.translate import TranslationService
from polyword.services.storage import StorageService
from polyword.services.chatgpt import ChatGPTService
from polyword.processor import PDFProcessor

# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcpkey.json'

app = FastAPI(title="PolyWord API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/", StaticFiles(directory="polyword/static"), name="static")

# Initialize services
ocr_service = OCRService()
translation_service = TranslationService()
storage_service = StorageService()
chatgpt_service = ChatGPTService()
processor = PDFProcessor(ocr_service, translation_service, storage_service, chatgpt_service)

@app.get("/")
async def read_root():
    return {"message": "Welcome to PolyWord API"}

@app.post("/upload")
async def upload_file(file: UploadFile):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create a unique filename
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = f"/tmp/{unique_filename}"
    
    try:
        # Save the uploaded file temporarily
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Upload to GCS
        input_bucket = 'polyword-bucket'
        output_prefix = 'uploads'
        gcs_path = f"{output_prefix}/{unique_filename}"
        pdf_uri = storage_service.upload_pdf_to_gcs(temp_path, input_bucket, gcs_path)
        
        # Process the PDF
        result = processor.process_pdf(
            pdf_uri,
            input_bucket,
            output_prefix,
            'en'  # Default to English
        )
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "message": "File processed successfully",
            "original_text": result['original_text_uri'],
            "translated_text": result['translated_text_uri'],
            "refined_text": result['refined_text_uri']
        }
        
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    try:
        bucket = storage_service.client.get_bucket('polyword-bucket')
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the file content
        content = blob.download_as_bytes()
        
        # Determine content type
        content_type = "application/octet-stream"
        if file_path.endswith('.txt'):
            content_type = "text/plain"
        elif file_path.endswith('.pdf'):
            content_type = "application/pdf"
        
        return JSONResponse(
            content={
                "content": content.decode('utf-8'),
                "filename": os.path.basename(file_path)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 