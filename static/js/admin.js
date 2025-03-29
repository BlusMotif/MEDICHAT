document.addEventListener('DOMContentLoaded', function() {
    // African Diseases Text Processing Elements
    const processAfricanDiseasesBtn = document.getElementById('processAfricanDiseasesBtn');
    const africanDiseasesStatus = document.getElementById('africanDiseasesStatus');
    const africanDiseasesComplete = document.getElementById('africanDiseasesComplete');
    const africanDiseasesError = document.getElementById('africanDiseasesError');
    const africanDiseasesErrorMessage = document.getElementById('africanDiseasesErrorMessage');
    const africanDiseasesStatusText = document.getElementById('africanDiseasesStatusText');
    
    // Statistics Elements
    const symptomCount = document.getElementById('symptomCount');
    const conditionCount = document.getElementById('conditionCount');
    
    // Update knowledge base status when modal opens
    document.getElementById('adminModal').addEventListener('shown.bs.modal', function() {
        updateKnowledgeBaseStats();
    });
    
    // Process African Diseases button
    processAfricanDiseasesBtn.addEventListener('click', function() {
        startAfricanDiseasesProcessing();
    });
    
    // Start African Diseases text processing
    function startAfricanDiseasesProcessing() {
        // Reset UI
        processAfricanDiseasesBtn.disabled = true;
        africanDiseasesStatus.classList.remove('d-none');
        africanDiseasesComplete.classList.add('d-none');
        africanDiseasesError.classList.add('d-none');
        
        // Call API to start processing
        fetch('/process_african_diseases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'started') {
                // Start checking status
                africanDiseasesStatusText.textContent = 'Processing started...';
                checkAfricanDiseasesStatus();
            } else if (data.status === 'already_running') {
                // Already running, start checking status
                africanDiseasesStatusText.textContent = 'Processing already in progress...';
                checkAfricanDiseasesStatus();
            } else {
                // Error
                showAfricanDiseasesError('Failed to start African diseases text processing');
            }
        })
        .catch(error => {
            showAfricanDiseasesError('Error: ' + error.message);
        });
    }
    
    // Check African Diseases text processing status
    function checkAfricanDiseasesStatus() {
        fetch('/african_diseases_status')
            .then(response => response.json())
            .then(data => {
                // Update status message if provided
                if (data.message) {
                    africanDiseasesStatusText.textContent = data.message;
                }
                
                // Check if still running
                if (data.is_running) {
                    // Check again in 2 seconds
                    setTimeout(checkAfricanDiseasesStatus, 2000);
                } else {
                    // Processing complete
                    if (data.completed) {
                        showAfricanDiseasesComplete();
                    } else {
                        // Show error message
                        showAfricanDiseasesError(data.message || 'Processing failed');
                    }
                }
            })
            .catch(error => {
                showAfricanDiseasesError('Error checking status: ' + error.message);
            });
    }
    
    // Show African diseases processing complete
    function showAfricanDiseasesComplete() {
        africanDiseasesStatus.classList.add('d-none');
        africanDiseasesComplete.classList.remove('d-none');
        processAfricanDiseasesBtn.disabled = false;
        
        // Update knowledge base stats
        updateKnowledgeBaseStats();
    }
    
    // Show African diseases processing error
    function showAfricanDiseasesError(message) {
        africanDiseasesStatus.classList.add('d-none');
        africanDiseasesError.classList.remove('d-none');
        africanDiseasesErrorMessage.textContent = message;
        processAfricanDiseasesBtn.disabled = false;
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