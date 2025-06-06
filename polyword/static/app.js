document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const uploadButton = document.getElementById('upload-button');
    const uploadSection = document.getElementById('upload-section');
    const processingStatus = document.getElementById('processing-status');
    const resultsSection = document.getElementById('results-section');
    const dropZone = document.querySelector('.border-dashed');

    let selectedFile = null;
    let processingResults = null;

    // Handle file selection
    fileInput.addEventListener('change', (e) => {
        selectedFile = e.target.files[0];
        if (selectedFile) {
            fileName.textContent = selectedFile.name;
            fileInfo.classList.remove('hidden');
            uploadButton.classList.remove('hidden');
        }
    });

    // Handle drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('drag-over');
    }

    function unhighlight(e) {
        dropZone.classList.remove('drag-over');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        selectedFile = files[0];
        if (selectedFile) {
            fileName.textContent = selectedFile.name;
            fileInfo.classList.remove('hidden');
            uploadButton.classList.remove('hidden');
        }
    }

    // Handle file upload
    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('file', selectedFile);

        // Show processing status
        uploadSection.classList.add('hidden');
        processingStatus.classList.remove('hidden');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            processingResults = await response.json();
            
            // Show results
            processingStatus.classList.add('hidden');
            resultsSection.classList.remove('hidden');
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing your file. Please try again.');
            processingStatus.classList.add('hidden');
            uploadSection.classList.remove('hidden');
        }
    });

    // Handle downloads
    document.querySelectorAll('.download-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const type = button.dataset.type;
            let filePath;

            switch (type) {
                case 'original':
                    filePath = processingResults.original_text.split('gs://polyword-bucket/')[1];
                    break;
                case 'translated':
                    filePath = processingResults.translated_text.split('gs://polyword-bucket/')[1];
                    break;
                case 'refined':
                    filePath = processingResults.refined_text.split('gs://polyword-bucket/')[1];
                    break;
            }

            try {
                const response = await fetch(`/download/${filePath}`);
                if (!response.ok) throw new Error('Download failed');
                
                const data = await response.json();
                
                // Create and trigger download
                const blob = new Blob([data.content], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while downloading the file. Please try again.');
            }
        });
    });
}); 