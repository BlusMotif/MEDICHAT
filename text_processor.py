import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalTextProcessor:
    """Process text files containing information about medical conditions and diseases"""
    
    def __init__(self, text_file_path: str):
        """
        Initialize the text processor with the path to the text file
        
        Args:
            text_file_path: Path to the text file containing disease information
        """
        self.text_file_path = text_file_path
        self.disease_data = {
            "diseases": {},
            "symptoms": {},
            "diagnosis_methods": {},
            "treatments": {}
        }
    
    def process_text_file(self) -> Dict:
        """
        Process the text file and extract disease information
        
        Returns:
            Dictionary containing structured disease information
        """
        try:
            if not os.path.exists(self.text_file_path):
                logger.error(f"Text file not found: {self.text_file_path}")
                return self.disease_data
            
            with open(self.text_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Extract disease sections using regex
            disease_pattern = r'## \d+\. ([A-Z\s()/-]+)\n- \*\*Symptoms\*\*: (.*?)\n- \*\*Diagnosis\*\*: (.*?)\n- \*\*Treatment\*\*: (.*?)(?:\n\n|\n##|\Z)'
            disease_matches = re.findall(disease_pattern, content, re.DOTALL)
            
            for match in disease_matches:
                disease_name = match[0].strip()
                symptoms_text = match[1].strip()
                diagnosis_text = match[2].strip()
                treatment_text = match[3].strip()
                
                # Process symptoms into a list
                symptoms = [s.strip() for s in re.split(r',|\.', symptoms_text) if s.strip()]
                
                # Add to disease data
                self.disease_data["diseases"][disease_name] = {
                    "symptoms": symptoms,
                    "diagnosis": diagnosis_text,
                    "treatment": treatment_text
                }
                
                # Create symptom to disease mapping
                for symptom in symptoms:
                    symptom = symptom.lower()
                    if symptom not in self.disease_data["symptoms"]:
                        self.disease_data["symptoms"][symptom] = []
                    if disease_name not in self.disease_data["symptoms"][symptom]:
                        self.disease_data["symptoms"][symptom].append(disease_name)
                
                # Add diagnosis methods
                self.disease_data["diagnosis_methods"][disease_name] = diagnosis_text
                
                # Add treatments
                self.disease_data["treatments"][disease_name] = treatment_text
            
            logger.info(f"Successfully processed {len(self.disease_data['diseases'])} diseases from text file")
            return self.disease_data
            
        except Exception as e:
            logger.error(f"Error processing text file: {str(e)}")
            return self.disease_data
    
    def save_to_json(self, output_path: Optional[str] = None) -> bool:
        """
        Save the processed disease data to a JSON file
        
        Args:
            output_path: Path to save the JSON file (optional)
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            if not output_path:
                # Use default path in static/data directory
                default_path = Path(__file__).parent / "static" / "data" / "medical_data.json"
                output_path = str(default_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(self.disease_data, file, indent=4)
            
            logger.info(f"Successfully saved disease data to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving disease data to JSON: {str(e)}")
            return False
    
    def merge_with_existing_medical_data(self, existing_data_path: str) -> Dict:
        """
        Merge the processed disease data with existing medical data
        
        Args:
            existing_data_path: Path to existing medical data JSON file
            
        Returns:
            Dictionary containing merged medical data
        """
        try:
            if not os.path.exists(existing_data_path):
                logger.warning(f"Existing data file not found: {existing_data_path}")
                return self.disease_data
            
            with open(existing_data_path, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
            
            # Merge symptoms
            for symptom, diseases in self.disease_data["symptoms"].items():
                if symptom in existing_data["symptoms"]:
                    # Add new diseases to existing symptom
                    for disease in diseases:
                        if disease not in existing_data["symptoms"][symptom]:
                            existing_data["symptoms"][symptom].append(disease)
                else:
                    # Add new symptom
                    existing_data["symptoms"][symptom] = diseases
            
            # Merge conditions/diseases
            for disease, info in self.disease_data["diseases"].items():
                if disease in existing_data.get("conditions", {}):
                    # Update existing disease with new information
                    existing_data["conditions"][disease].extend([info["treatment"]])
                else:
                    # Add new disease
                    existing_data["conditions"][disease] = [info["treatment"]]
            
            # Add symptom related questions if not present in existing data
            if "symptom_related_questions" not in existing_data:
                existing_data["symptom_related_questions"] = {}
            
            # Add specific questions for common disease symptoms
            existing_data["symptom_related_questions"]["high fever"] = [
                "Does your fever come and go in cycles?",
                "Do you have chills before the fever starts?",
                "Have you been in an area with endemic diseases recently?"
            ]
            
            existing_data["symptom_related_questions"]["jaundice"] = [
                "Have you noticed yellowing of your eyes or skin?",
                "Have you had any changes in urine color?",
                "Do you have any pain in your abdomen?"
            ]
            
            existing_data["symptom_related_questions"]["rash"] = [
                "Where is the rash located on your body?",
                "Is the rash itchy or painful?",
                "Did the rash appear after taking any medication?"
            ]
            
            logger.info("Successfully merged disease data with existing medical data")
            return existing_data
            
        except Exception as e:
            logger.error(f"Error merging with existing medical data: {str(e)}")
            return self.disease_data

# For testing
if __name__ == "__main__":
    processor = MedicalTextProcessor("attached_assets/Common_Diseases_Symptoms_Treatment.txt")
    processor.process_text_file()
    processor.save_to_json()