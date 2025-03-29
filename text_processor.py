import json
import os
import re
import logging
from typing import Dict, List, Set, Optional

# Configure logging
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
        self.disease_data = {}
    
    def process_text_file(self) -> Dict:
        """
        Process the text file and extract disease information
        
        Returns:
            Dictionary containing structured disease information
        """
        try:
            with open(self.text_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Split the content by disease sections (assumption: diseases are separated by double newlines)
                disease_sections = re.split(r'\n\s*\n', content)
                
                for section in disease_sections:
                    if not section.strip():
                        continue
                    
                    # Parse the disease section
                    lines = section.strip().split('\n')
                    if not lines:
                        continue
                    
                    # First line should be the disease name
                    disease_name = lines[0].strip()
                    if not disease_name:
                        continue
                    
                    disease_info = {
                        "symptoms": [],
                        "treatment": "",
                        "description": ""
                    }
                    
                    current_section = None
                    
                    for line in lines[1:]:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Check if this is a section header
                        if line.lower().startswith("symptoms:"):
                            current_section = "symptoms"
                            # Extract symptoms from the same line if they exist
                            symptoms_text = line[len("symptoms:"):].strip()
                            if symptoms_text:
                                symptoms = [s.strip() for s in symptoms_text.split(',')]
                                disease_info["symptoms"].extend(symptoms)
                        elif line.lower().startswith("treatment:"):
                            current_section = "treatment"
                            # Extract treatment from the same line if it exists
                            treatment_text = line[len("treatment:"):].strip()
                            if treatment_text:
                                disease_info["treatment"] = treatment_text
                        elif line.lower().startswith("description:"):
                            current_section = "description"
                            # Extract description from the same line if it exists
                            description_text = line[len("description:"):].strip()
                            if description_text:
                                disease_info["description"] = description_text
                        else:
                            # Continue with the current section
                            if current_section == "symptoms":
                                # Symptoms might be comma-separated
                                symptoms = [s.strip() for s in line.split(',')]
                                disease_info["symptoms"].extend(symptoms)
                            elif current_section == "treatment":
                                disease_info["treatment"] += " " + line
                            elif current_section == "description":
                                disease_info["description"] += " " + line
                    
                    # Clean up symptoms (remove empty strings)
                    disease_info["symptoms"] = [s for s in disease_info["symptoms"] if s]
                    
                    # Add the disease to our data dictionary
                    self.disease_data[disease_name] = disease_info
            
            logger.info(f"Successfully processed {len(self.disease_data)} diseases from text file")
            return self.disease_data
            
        except Exception as e:
            logger.error(f"Error processing text file: {str(e)}")
            return {}
    
    def save_to_json(self, output_path: Optional[str] = None) -> bool:
        """
        Save the processed disease data to a JSON file
        
        Args:
            output_path: Path to save the JSON file (optional)
            
        Returns:
            Boolean indicating success or failure
        """
        if not self.disease_data:
            logger.warning("No disease data to save")
            return False
        
        try:
            # If no output path provided, use a default
            if not output_path:
                os.makedirs('static/data', exist_ok=True)
                output_path = 'static/data/diseases.json'
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(self.disease_data, file, indent=2)
            
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
                logger.warning(f"Existing data file {existing_data_path} not found")
                return self.disease_data
            
            with open(existing_data_path, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
            
            # Merge the data
            merged_data = {**existing_data, **self.disease_data}
            
            logger.info(f"Successfully merged {len(self.disease_data)} diseases with existing data")
            return merged_data
            
        except Exception as e:
            logger.error(f"Error merging with existing data: {str(e)}")
            return self.disease_data