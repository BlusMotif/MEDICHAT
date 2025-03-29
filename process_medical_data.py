import json
import os
import logging
from typing import Dict, List, Optional

from text_processor import MedicalTextProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_medical_text():
    """
    Process medical data from text file and integrate with medical knowledge base
    """
    # Ensure directories exist
    os.makedirs('static/data', exist_ok=True)
    
    # Set file paths
    text_file_path = 'resources/medical_data/Common_Diseases_Symptoms_Treatment.txt'
    if not os.path.exists(text_file_path):
        text_file_path = 'attached_assets/Common_Diseases_Symptoms_Treatment.txt'
    
    output_json_path = 'static/data/medical_data.json'
    
    # Process the text file
    try:
        processor = MedicalTextProcessor(text_file_path)
        disease_data = processor.process_text_file()
        
        # Convert to the format expected by the chatbot
        medical_data = {"conditions": []}
        
        for disease_name, disease_info in disease_data.items():
            condition = {
                "name": disease_name,
                "symptoms": disease_info.get("symptoms", []),
                "treatment": disease_info.get("treatment", "Please consult a healthcare provider for treatment options."),
                "description": disease_info.get("description", ""),
                "confidence": 0.8  # Default confidence value
            }
            medical_data["conditions"].append(condition)
        
        # Save the processed data
        with open(output_json_path, 'w') as f:
            json.dump(medical_data, f, indent=2)
        
        logger.info(f"Processed {len(medical_data['conditions'])} diseases from text file")
        logger.info(f"Saved medical data directly to medical_data.json")
        
        # Save regional specific data (for backward compatibility)
        regional_output_path = 'static/data/regional_diseases.json'
        processor.save_to_json(regional_output_path)
        
        return medical_data
    
    except Exception as e:
        logger.error(f"Error processing medical text: {str(e)}")
        # Return an empty dataset as fallback
        return {"conditions": []}

if __name__ == "__main__":
    process_medical_text()