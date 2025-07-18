import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import webbrowser
import sys
from polyword.services.ocr import OCRService
from polyword.services.translate import TranslationService
from polyword.services.storage import StorageService
from polyword.services.chatgpt import ChatGPTService
from polyword.processor import PDFProcessor

from dotenv import load_dotenv
load_dotenv()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class PolyWordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PolyWord")
        self.root.geometry("800x600")
        
        # Set up credentials
        credentials_path = resource_path('gcpkey.json')
        if not os.path.exists(credentials_path):
            messagebox.showerror("Error", f"Credentials file not found at: {credentials_path}")
            root.destroy()
            return
            
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        # Initialize services
        self.ocr_service = OCRService()
        self.translation_service = TranslationService()
        self.storage_service = StorageService()
        self.chatgpt_service = ChatGPTService()
        self.processor = PDFProcessor(
            self.ocr_service,
            self.translation_service,
            self.storage_service,
            self.chatgpt_service
        )
        
        # Initialize variables
        self.selected_file = None
        self.processing_results = {}
        self.bucket_name = 'polyword-bucket'
        self.output_prefix = 'results'
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File selection
        ttk.Label(main_frame, text="Select PDF File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_label = ttk.Label(main_frame, text="No file selected")
        self.file_label.grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)
        
        # Upload button
        self.upload_btn = ttk.Button(main_frame, text="Upload", command=self.upload_file, state=tk.DISABLED)
        self.upload_btn.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Processing Results", padding="5")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Results list
        self.results_list = ttk.Treeview(results_frame, columns=("Type", "Status"), show="headings")
        self.results_list.heading("Type", text="File Type")
        self.results_list.heading("Status", text="Status")
        self.results_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Download button
        self.download_btn = ttk.Button(results_frame, text="Download Selected", command=self.download_selected, state=tk.DISABLED)
        self.download_btn.grid(row=1, column=0, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=Path(file_path).name)
            self.upload_btn.config(state=tk.NORMAL)
    
    def upload_file(self):
        if not self.selected_file:
            return
        
        self.upload_btn.config(state=tk.DISABLED)
        self.progress.start()
        
        def process_file():
            try:
                # Upload file to GCS
                dest_blob_name = f"{self.output_prefix}/{Path(self.selected_file).name}"
                gcs_uri = self.storage_service.upload_pdf_to_gcs(
                    self.selected_file,
                    self.bucket_name,
                    dest_blob_name
                )
                
                # Process the file
                results = self.processor.process_pdf(
                    gcs_uri,
                    self.bucket_name,
                    self.output_prefix,
                    'en'  # Default to English
                )
                
                self.processing_results = results
                
                # Update UI in the main thread
                self.root.after(0, self.update_results_ui)
                
            except Exception as error:
                error_msg = str(error)
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            finally:
                self.root.after(0, self.progress.stop)
                self.root.after(0, lambda: self.upload_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=process_file, daemon=True).start()
    
    def update_results_ui(self):
        # Clear existing items
        for item in self.results_list.get_children():
            self.results_list.delete(item)
        
        # Add new results
        for key, uri in self.processing_results.items():
            file_type = key.replace('_uri', '').replace('_', ' ').title()
            if 'pdf' in key.lower():
                file_type = "PDF Document"
            self.results_list.insert("", tk.END, values=(file_type, "Ready"), tags=(uri,))
        
        self.download_btn.config(state=tk.NORMAL)
    
    def download_selected(self):
        selected_items = self.results_list.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select files to download")
            return
        
        download_dir = filedialog.askdirectory()
        if not download_dir:
            return
        
        def download_files():
            try:
                for item in selected_items:
                    uri = self.results_list.item(item)['tags'][0]
                    file_name = uri.split('/')[-1]
                    local_path = os.path.join(download_dir, file_name)
                    
                    # Download from GCS
                    bucket_name = uri.split('/')[2]
                    blob_name = '/'.join(uri.split('/')[3:])
                    bucket = self.storage_service.client.get_bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    blob.download_to_filename(local_path)
                
                self.root.after(0, lambda: messagebox.showinfo("Success", "Files downloaded successfully"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        threading.Thread(target=download_files, daemon=True).start()

def main():
    root = tk.Tk()
    app = PolyWordApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 