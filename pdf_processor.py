import os
import logging
import json
import PyPDF2
import re
from pathlib import Path
import nltk

# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PDFMedicalProcessor:
    def __init__(self, pdf_dir="attached_assets", single_pdf_path=None):
        """Initialize the PDF processor with PDF directory path or single PDF path"""
        self.pdf_dir = pdf_dir
        self.single_pdf_path = single_pdf_path
        self.medical_data = {
            "symptoms": {},
            "conditions": {},
            "symptom_related_questions": {}
        }
        self.knowledge_base = {}
        
        # Load any existing medical data first
        self.load_existing_medical_data()
        
        # Process PDFs and enhance the knowledge base
        if single_pdf_path:
            # Process a single PDF file
            self.extract_medical_knowledge(single_pdf_path)
        else:
            # Process all PDFs in the directory
            self.process_pdfs()
        
        # Save the combined knowledge
        self.save_enhanced_medical_data()
    
    def load_existing_medical_data(self):
        """Load existing medical data if available"""
        try:
            data_path = Path(__file__).parent / "static" / "data" / "medical_data.json"
            if data_path.exists():
                with open(data_path, 'r') as file:
                    self.medical_data = json.load(file)
                    logger.info("Loaded existing medical data")
        except Exception as e:
            logger.error(f"Error loading existing medical data: {str(e)}")
    
    def process_pdfs(self):
        """Process all PDF files in the directory"""
        if not os.path.exists(self.pdf_dir):
            logger.warning(f"PDF directory {self.pdf_dir} doesn't exist")
            return
        
        for filename in os.listdir(self.pdf_dir):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_dir, filename)
                self.extract_medical_knowledge(pdf_path)
    
    def extract_medical_knowledge(self, pdf_path):
        """Extract medical knowledge from a PDF file"""
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                text = ""
                for page_num in range(len(reader.pages)):
                    text += reader.pages[page_num].extract_text() + "\n"
                
                # Process the extracted text to find symptoms, conditions, and relationships
                self.process_medical_text(text)
                
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
    
    def process_medical_text(self, text):
        """Process extracted text to identify medical information"""
        # Extract chapter headings and content
        chapters = self.extract_chapters(text)
        
        # Process each chapter to extract symptom-disease relationships
        for chapter_title, chapter_content in chapters.items():
            self.analyze_chapter(chapter_title, chapter_content)
            
        # Find symptom-condition relationships
        self.extract_symptom_condition_relationships(text)
    
    def extract_chapters(self, text):
        """Extract chapters from the text"""
        chapters = {}
        
        # Look for chapter headings using common patterns
        chapter_patterns = [
            r'Chapter\s+\d+\.?\s+([A-Z][^\n]+)',
            r'CHAPTER\s+\d+\.?\s+([A-Z][^\n]+)',
            r'\d+\s*-\s*([A-Z][^\n]+)'
        ]
        
        # Find all possible chapter matches
        all_matches = []
        for pattern in chapter_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                all_matches.append((match.start(), match.group(1).strip()))
        
        # Sort by position in text
        all_matches.sort()
        
        # Extract chapter content
        for i in range(len(all_matches)):
            start_pos = all_matches[i][0]
            chapter_title = all_matches[i][1]
            
            # Find the end of this chapter (start of next chapter or end of text)
            if i < len(all_matches) - 1:
                end_pos = all_matches[i+1][0]
            else:
                end_pos = len(text)
            
            # Extract chapter content
            chapter_content = text[start_pos:end_pos]
            chapters[chapter_title] = chapter_content
        
        return chapters
    
    def analyze_chapter(self, chapter_title, chapter_content):
        """Analyze chapter content to extract medical knowledge"""
        # Map of common symptom phrases
        symptom_phrases = [
            "symptoms include", "symptoms are", "symptoms may include",
            "common symptoms", "typical symptoms", "presenting symptoms",
            "characterized by", "presents with", "signs and symptoms",
            "clinical features"
        ]
        
        # Look for symptom descriptions
        for phrase in symptom_phrases:
            pattern = f"{phrase}[^.]*\\."
            matches = re.finditer(pattern, chapter_content, re.IGNORECASE)
            
            for match in matches:
                symptom_text = match.group(0)
                
                # Extract condition from chapter title or nearby context
                condition = self.extract_condition(chapter_title, chapter_content)
                
                # Extract symptoms from symptom text
                symptoms = self.extract_symptoms(symptom_text)
                
                # Add to knowledge base
                if condition and symptoms:
                    if condition not in self.knowledge_base:
                        self.knowledge_base[condition] = {
                            "symptoms": [],
                            "treatment": []
                        }
                    
                    # Add unique symptoms
                    self.knowledge_base[condition]["symptoms"].extend(
                        [s for s in symptoms if s not in self.knowledge_base[condition]["symptoms"]]
                    )
                    
                    # Update our medical data structure
                    for symptom in symptoms:
                        if symptom not in self.medical_data["symptoms"]:
                            self.medical_data["symptoms"][symptom] = []
                        
                        if condition not in self.medical_data["symptoms"][symptom]:
                            self.medical_data["symptoms"][symptom].append(condition)
    
    def extract_condition(self, chapter_title, chapter_content):
        """Extract the medical condition from chapter title or content"""
        # Try to extract from chapter title first
        potential_conditions = [
            "headache", "migraine", "fever", "cold", "flu", "bronchitis", 
            "pneumonia", "asthma", "diabetes", "hypertension", "arthritis",
            "depression", "anxiety", "insomnia", "allergies", "sinusitis",
            "gastritis", "ulcer", "colitis", "hepatitis", "nephritis",
            "dermatitis", "eczema", "psoriasis", "anemia", "leukemia",
            "cancer", "tumor", "fracture", "sprain", "strain",
            "concussion", "epilepsy", "stroke", "heart attack", "heart failure",
            # Add common diseases
            "malaria", "typhoid fever", "typhoid", "cholera", "yellow fever",
            "tuberculosis", "tb", "hiv/aids", "aids", "ebola", "dengue fever",
            "schistosomiasis", "bilharzia", "trypanosomiasis", "sleeping sickness",
            "meningitis", "leishmaniasis", "filariasis", "river blindness",
            "guinea worm", "dracunculiasis", "trachoma"
        ]
        
        # Check if any known condition is in the title
        for condition in potential_conditions:
            if condition.lower() in chapter_title.lower():
                return condition.title()
        
        # Otherwise extract from first few sentences
        first_paragraph = " ".join(chapter_content.split(".")[:3])
        
        for condition in potential_conditions:
            if condition.lower() in first_paragraph.lower():
                return condition.title()
        
        # If nothing found, return the chapter title as fallback
        return chapter_title
    
    def extract_symptoms(self, symptom_text):
        """Extract symptoms from symptom text"""
        # Common symptoms to look for
        common_symptoms = [
            "headache", "fever", "cough", "fatigue", "pain", "nausea",
            "vomiting", "diarrhea", "constipation", "rash", "swelling",
            "dizziness", "weakness", "numbness", "tingling", "shortness of breath",
            "chest pain", "abdominal pain", "back pain", "joint pain", "muscle pain",
            "sore throat", "runny nose", "congestion", "sneezing", "sweating",
            "chills", "insomnia", "loss of appetite", "weight loss", "weight gain",
            # Symptoms specific to common tropical diseases
            "high fever", "intermittent fever", "cyclic fever", "recurrent fever", 
            "night sweats", "shivering", "rigors", "jaundice", "enlarged spleen",
            "enlarged liver", "splenomegaly", "hepatomegaly", "anemia", "malaise",
            "bloody diarrhea", "bloody stool", "dehydration", "confusion",
            "night sweats", "persistent cough", "coughing up blood", "hemoptysis",
            "skin rash", "rose spots", "abdominal tenderness", "body aches", "myalgia"
        ]
        
        found_symptoms = []
        
        # Look for common symptoms in the text
        for symptom in common_symptoms:
            if re.search(r'\b' + symptom + r'\b', symptom_text.lower()):
                found_symptoms.append(symptom)
        
        return found_symptoms
    
    def extract_symptom_condition_relationships(self, text):
        """Extract relationships between symptoms and conditions"""
        # Common symptoms to look for
        common_symptoms = [
            "headache", "fever", "cough", "fatigue", "pain", "nausea",
            "vomiting", "diarrhea", "constipation", "rash", "swelling",
            "dizziness", "weakness", "numbness", "tingling", "shortness of breath",
            "chest pain", "abdominal pain", "back pain", "joint pain", "muscle pain",
            "sore throat", "runny nose", "congestion", "sneezing", "sweating",
            "chills", "insomnia", "loss of appetite", "weight loss", "weight gain",
            # Symptoms specific to common tropical diseases
            "high fever", "intermittent fever", "cyclic fever", "recurrent fever", 
            "night sweats", "shivering", "rigors", "jaundice", "enlarged spleen",
            "enlarged liver", "splenomegaly", "hepatomegaly", "anemia", "malaise",
            "bloody diarrhea", "bloody stool", "dehydration", "confusion",
            "night sweats", "persistent cough", "coughing up blood", "hemoptysis",
            "skin rash", "rose spots", "abdominal tenderness", "body aches", "myalgia"
        ]
        
        # Common conditions to look for
        common_conditions = [
            "common cold", "flu", "influenza", "bronchitis", "pneumonia", 
            "sinusitis", "migraine", "tension headache", "gastritis", 
            "gastroenteritis", "irritable bowel syndrome", "ulcer", 
            "hypertension", "hypotension", "anemia", "diabetes", 
            "hypothyroidism", "hyperthyroidism", "arthritis", "osteoporosis",
            "asthma", "copd", "emphysema", "allergies", "eczema", 
            "psoriasis", "dermatitis", "anxiety", "depression", "insomnia",
            # Common diseases around the world
            "malaria", "typhoid fever", "typhoid", "yellow fever", "cholera",
            "tuberculosis", "tb", "hiv", "aids", "ebola", "dengue fever",
            "schistosomiasis", "bilharzia", "trypanosomiasis", "sleeping sickness",
            "meningitis", "hepatitis", "leishmaniasis", "kala-azar", "filariasis",
            "river blindness", "onchocerciasis", "guinea worm", "dracunculiasis"
        ]
        
        # Find paragraphs that contain both symptoms and conditions
        for symptom in common_symptoms:
            symptom_pattern = r'\b' + symptom + r'\b'
            symptom_matches = list(re.finditer(symptom_pattern, text.lower()))
            
            for match in symptom_matches:
                # Get surrounding context (200 chars before and after)
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end]
                
                # Check if any conditions appear in this context
                for condition in common_conditions:
                    condition_pattern = r'\b' + condition + r'\b'
                    if re.search(condition_pattern, context.lower()):
                        # We found a relationship between symptom and condition
                        if symptom not in self.medical_data["symptoms"]:
                            self.medical_data["symptoms"][symptom] = []
                            
                        condition_title = " ".join(word.capitalize() for word in condition.split())
                        
                        if condition_title not in self.medical_data["symptoms"][symptom]:
                            self.medical_data["symptoms"][symptom].append(condition_title)
                        
                        # Also add to conditions if not present
                        if condition_title not in self.medical_data["conditions"]:
                            self.medical_data["conditions"][condition_title] = ["consult healthcare provider"]
    
    def save_enhanced_medical_data(self):
        """Save the enhanced medical data to JSON file"""
        try:
            data_path = Path(__file__).parent / "static" / "data" / "medical_data.json"
            
            # Ensure the data directory exists
            os.makedirs(data_path.parent, exist_ok=True)
            
            # Write the enhanced data
            with open(data_path, 'w') as file:
                json.dump(self.medical_data, file, indent=2)
                logger.info(f"Enhanced medical data saved to {data_path}")
        except Exception as e:
            logger.error(f"Error saving enhanced medical data: {str(e)}")


# Helper function to process PDFs and enhance medical data
def enhance_medical_knowledge():
    """Process PDFs and enhance the medical knowledge base"""
    processor = PDFMedicalProcessor()
    return processor.medical_data


if __name__ == "__main__":
    # Run the processor
    enhance_medical_knowledge()