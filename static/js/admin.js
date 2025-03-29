document.addEventListener('DOMContentLoaded', function() {
    // Medical Text Processing Elements
    const processAfricanDiseasesBtn = document.getElementById('processAfricanDiseasesBtn');
    const africanDiseasesStatus = document.getElementById('africanDiseasesStatus');
    const africanDiseasesComplete = document.getElementById('africanDiseasesComplete');
    const africanDiseasesError = document.getElementById('africanDiseasesError');
    const africanDiseasesErrorMessage = document.getElementById('africanDiseasesErrorMessage');
    const africanDiseasesStatusText = document.getElementById('africanDiseasesStatusText');
    
    // Statistics Elements
    const symptomCount = document.getElementById('symptomCount');
    const conditionCount = document.getElementById('conditionCount');
    const africanDiseaseCount = document.getElementById('africanDiseaseCount');
    
    // Update knowledge base status when modal opens
    document.getElementById('adminModal').addEventListener('shown.bs.modal', function() {
        updateKnowledgeBaseStats();
    });
    
    // Process Medical Text button
    processAfricanDiseasesBtn.addEventListener('click', function() {
        startMedicalTextProcessing();
    });
    
    // Start Medical Text processing
    function startMedicalTextProcessing() {
        // Reset UI
        processAfricanDiseasesBtn.disabled = true;
        africanDiseasesStatus.classList.remove('d-none');
        africanDiseasesComplete.classList.add('d-none');
        africanDiseasesError.classList.add('d-none');
        
        // Call API to start processing
        fetch('/process_medical_data', {
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
                checkMedicalTextStatus();
            } else if (data.status === 'already_running') {
                // Already running, start checking status
                africanDiseasesStatusText.textContent = 'Processing already in progress...';
                checkMedicalTextStatus();
            } else {
                // Error
                showProcessingError('Failed to start medical text processing');
            }
        })
        .catch(error => {
            showProcessingError('Error: ' + error.message);
        });
    }
    
    // Check Medical Text processing status
    function checkMedicalTextStatus() {
        fetch('/medical_data_status')
            .then(response => response.json())
            .then(data => {
                // Update status message if provided
                if (data.message) {
                    africanDiseasesStatusText.textContent = data.message;
                }
                
                // Check if still running
                if (data.is_running) {
                    // Check again in 2 seconds
                    setTimeout(checkMedicalTextStatus, 2000);
                } else {
                    // Processing complete
                    if (data.completed) {
                        showProcessingComplete();
                    } else {
                        // Show error message
                        showProcessingError(data.message || 'Processing failed');
                    }
                }
            })
            .catch(error => {
                showProcessingError('Error checking status: ' + error.message);
            });
    }
    
    // Show text processing complete
    function showProcessingComplete() {
        africanDiseasesStatus.classList.add('d-none');
        africanDiseasesComplete.classList.remove('d-none');
        processAfricanDiseasesBtn.disabled = false;
        
        // Update knowledge base stats
        updateKnowledgeBaseStats();
    }
    
    // Show text processing error
    function showProcessingError(message) {
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
                let totalSymptoms = 0;
                let totalConditions = 0;
                let regionalDiseases = 0;
                
                // Count symptoms (they might be in different data structures)
                if (data.symptoms) {
                    totalSymptoms += Object.keys(data.symptoms).length;
                }
                
                // Count conditions/diseases
                if (data.conditions) {
                    totalConditions += Object.keys(data.conditions).length;
                }
                
                // Count regional diseases specifically
                if (data.diseases) {
                    regionalDiseases = Object.keys(data.diseases).length;
                    totalConditions += regionalDiseases;
                    
                    // Also count their symptoms
                    Object.values(data.diseases).forEach(disease => {
                        if (disease.symptoms && Array.isArray(disease.symptoms)) {
                            totalSymptoms += disease.symptoms.length;
                        }
                    });
                }
                
                symptomCount.textContent = totalSymptoms;
                conditionCount.textContent = totalConditions;
                africanDiseaseCount.textContent = regionalDiseases;
            })
            .catch(error => {
                symptomCount.textContent = 'Error loading';
                conditionCount.textContent = 'Error loading';
                africanDiseaseCount.textContent = 'Error loading';
                console.error('Error loading medical data:', error);
            });
    }
});