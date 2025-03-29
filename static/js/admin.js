document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const processPdfsBtn = document.getElementById('processPdfsBtn');
    const pdfProcessingStatus = document.getElementById('pdfProcessingStatus');
    const pdfProcessingComplete = document.getElementById('pdfProcessingComplete');
    const pdfProcessingError = document.getElementById('pdfProcessingError');
    const pdfErrorMessage = document.getElementById('pdfErrorMessage');
    const pdfProgressBar = document.getElementById('pdfProgressBar');
    const pdfStatusText = document.getElementById('pdfStatusText');
    const symptomCount = document.getElementById('symptomCount');
    const conditionCount = document.getElementById('conditionCount');
    
    // Update knowledge base status when modal opens
    document.getElementById('adminModal').addEventListener('shown.bs.modal', function() {
        updateKnowledgeBaseStats();
    });
    
    // Process PDFs button
    processPdfsBtn.addEventListener('click', function() {
        startPdfProcessing();
    });
    
    // Start PDF processing
    function startPdfProcessing() {
        // Reset UI
        processPdfsBtn.disabled = true;
        pdfProcessingStatus.classList.remove('d-none');
        pdfProcessingComplete.classList.add('d-none');
        pdfProcessingError.classList.add('d-none');
        
        // Call API to start processing
        fetch('/process_pdfs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'started') {
                // Start checking status
                pdfStatusText.textContent = 'Processing started...';
                checkPdfProcessingStatus();
            } else if (data.status === 'already_running') {
                // Already running, start checking status
                pdfStatusText.textContent = 'Processing already in progress...';
                updateProgressBar(data.progress);
                checkPdfProcessingStatus();
            } else {
                // Error
                showProcessingError('Failed to start PDF processing');
            }
        })
        .catch(error => {
            showProcessingError('Error: ' + error.message);
        });
    }
    
    // Check PDF processing status
    function checkPdfProcessingStatus() {
        fetch('/pdf_processing_status')
            .then(response => response.json())
            .then(data => {
                // Update progress
                updateProgressBar(data.progress);
                
                if (data.processed_pdfs > 0) {
                    pdfStatusText.textContent = `Processed ${data.processed_pdfs} of ${data.total_pdfs} PDFs (${data.progress}%)`;
                }
                
                // Check if still running
                if (data.is_running) {
                    // Check again in 2 seconds
                    setTimeout(checkPdfProcessingStatus, 2000);
                } else {
                    // Processing complete
                    if (data.progress === 100) {
                        showProcessingComplete();
                    } else {
                        // Only mark as error if it stopped but didn't reach 100%
                        if (data.processed_pdfs > 0) {
                            showProcessingError(`Processing stopped at ${data.progress}%. ${data.processed_pdfs} of ${data.total_pdfs} PDFs processed.`);
                        } else {
                            showProcessingError('Processing failed to start properly');
                        }
                    }
                }
            })
            .catch(error => {
                showProcessingError('Error checking status: ' + error.message);
            });
    }
    
    // Update progress bar
    function updateProgressBar(progress) {
        pdfProgressBar.style.width = progress + '%';
        pdfProgressBar.textContent = progress + '%';
        pdfProgressBar.setAttribute('aria-valuenow', progress);
    }
    
    // Show processing complete
    function showProcessingComplete() {
        pdfProcessingStatus.classList.add('d-none');
        pdfProcessingComplete.classList.remove('d-none');
        processPdfsBtn.disabled = false;
        
        // Update knowledge base stats
        updateKnowledgeBaseStats();
    }
    
    // Show processing error
    function showProcessingError(message) {
        pdfProcessingStatus.classList.add('d-none');
        pdfProcessingError.classList.remove('d-none');
        pdfErrorMessage.textContent = message;
        processPdfsBtn.disabled = false;
    }
    
    // Update knowledge base stats
    function updateKnowledgeBaseStats() {
        // Fetch current medical data to show stats
        fetch('/static/data/medical_data.json')
            .then(response => response.json())
            .then(data => {
                symptomCount.textContent = Object.keys(data.symptoms).length;
                conditionCount.textContent = Object.keys(data.conditions).length;
            })
            .catch(error => {
                symptomCount.textContent = 'Error loading';
                conditionCount.textContent = 'Error loading';
                console.error('Error loading medical data:', error);
            });
    }
});