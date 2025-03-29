import os
import logging
from pathlib import Path
from text_processor import AfricanDiseaseTextProcessor
from chatbot import DoctorChatbot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_african_diseases():
    """
    Process African diseases from text file and integrate with medical knowledge base
    """
    try:
        # Path to the text file
        text_file_path = os.path.join("attached_assets", "Africa_Common_Diseases_Symptoms_Treatment (1).txt")
        
        # Create processor and process the text file
        processor = AfricanDiseaseTextProcessor(text_file_path)
        disease_data = processor.process_text_file()
        
        # Create directories if they don't exist
        os.makedirs(os.path.join("static", "data"), exist_ok=True)
        
        # Save directly to medical_data.json (not to a separate file)
        medical_data_path = os.path.join("static", "data", "medical_data.json")
        with open(medical_data_path, 'w', encoding='utf-8') as file:
            import json
            json.dump(disease_data, file, indent=4)
        
        logger.info(f"Processed {len(disease_data['diseases'])} African diseases from text file")
        logger.info(f"Saved African disease data directly to medical_data.json")
        
        # Also save to african_diseases.json for backup
        african_data_path = os.path.join("static", "data", "african_diseases.json")
        processor.save_to_json(african_data_path)
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing African diseases: {str(e)}")
        return False

if __name__ == "__main__":
    process_african_diseases()