import json
import re
import os
import logging
import random
from pathlib import Path
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from typing import Dict, List, Set, Optional
from medical_api import MedicalResourceAPI

# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Download NLTK resources if not already present
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('punkt_tab')
    logger.info("Downloaded required NLTK resources")

class DoctorChatbot:
    def __init__(self):
        """Initialize the Doctor Chatbot with necessary resources"""

        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Initialize medical API for external references
        self.medical_api = MedicalResourceAPI()
        
        # Load medical data
        self.medical_data = self.load_medical_data()
        
        # Track conversation state
        self.conversation_state = {
            "collected_symptoms": set(),
            "confirmed_symptoms": set(),
            "stage": "greeting",  # greeting, collecting_symptoms, diagnosis, follow_up
            "current_question": None
        }
        
        # Greeting messages
        self.greetings = [
            "Hello! I'm Dr. Bot, a virtual assistant that can help identify potential health issues based on your symptoms. What symptoms are you experiencing?",
            "Hi there! I'm Dr. Bot, your virtual medical assistant. Please describe any symptoms you're experiencing so I can try to help.",
            "Welcome! I'm Dr. Bot, here to assist with preliminary medical advice. What symptoms are you having today?"
        ]
        
        # Follow-up questions
        self.follow_up_questions = [
            "How long have you been experiencing these symptoms?",
            "Are you experiencing any pain? If so, can you rate it from 1-10?",
            "Have you taken any medications for these symptoms?",
            "Do you have any known allergies or medical conditions?",
            "Have you had any fever or chills?",
            "Has anyone around you experienced similar symptoms?",
            "Have you traveled to any tropical or subtropical regions recently?",
            "Have you noticed any pattern to your fever, like coming and going every few days?",
            "Have you been exposed to mosquitoes or other insects recently?",
            "Is anyone else in your household or community experiencing similar symptoms?",
            "Have you had any vaccinations for tropical diseases like yellow fever or typhoid?",
            "Do you have access to clean drinking water?",
            "Have you been near any stagnant water sources recently?"
        ]
        
        # Disclaimer messages
        self.disclaimer = (
            "IMPORTANT: This is only a preliminary assessment based on the symptoms you've described. "
            "It is not a medical diagnosis. Please consult with a healthcare professional for proper diagnosis and treatment."
        )

    def load_medical_data(self):
        """Load the medical knowledge base from JSON file"""
        try:
            # First, try to use the african diseases JSON file if it exists
            data_path = Path(__file__).parent / "static" / "data" / "african_diseases.json"
            
            # If African diseases file doesn't exist, look for general medical data
            if not data_path.exists():
                # Try the general medical data file
                data_path = Path(__file__).parent / "static" / "data" / "medical_data.json"
            
            # If no files exist yet, process the African diseases text file
            if not data_path.exists():
                logger.info("No knowledge base found. Processing African diseases text file.")
                # Import required module only when needed
                from process_african_diseases import process_african_diseases
                process_african_diseases()
                
                # Check if file was created
                if not data_path.exists():
                    logger.warning("Failed to process African diseases. Using basic knowledge base.")
                    # Use basic African disease data
                    return self._get_basic_african_disease_data()
            
            # Load the data from file
            with open(data_path, 'r') as file:
                return json.load(file)
            
        except Exception as e:
            logger.error(f"Error loading medical data: {str(e)}")
            # Return a basic dataset focused on African diseases
            return self._get_basic_african_disease_data()
            
    def _get_basic_african_disease_data(self):
        """Return a basic dataset focused on common African diseases"""
        return {
            "symptoms": {
                "high fever": ["MALARIA", "TYPHOID FEVER", "YELLOW FEVER", "DENGUE FEVER"],
                "fever": ["MALARIA", "TYPHOID FEVER", "CHOLERA", "HEPATITIS B", "YELLOW FEVER"],
                "chills": ["MALARIA", "TYPHOID FEVER", "YELLOW FEVER"],
                "headache": ["MALARIA", "TYPHOID FEVER", "MENINGITIS"],
                "sweating": ["MALARIA", "YELLOW FEVER"],
                "nausea": ["MALARIA", "TYPHOID FEVER", "CHOLERA", "HEPATITIS B"],
                "vomiting": ["MALARIA", "TYPHOID FEVER", "CHOLERA", "YELLOW FEVER"],
                "fatigue": ["MALARIA", "TYPHOID FEVER", "HEPATITIS B", "HIV/AIDS"],
                "abdominal pain": ["TYPHOID FEVER", "CHOLERA", "HEPATITIS B"],
                "diarrhea": ["TYPHOID FEVER", "CHOLERA", "HIV/AIDS"],
                "rash": ["TYPHOID FEVER", "MEASLES", "HIV/AIDS"],
                "jaundice": ["HEPATITIS B", "YELLOW FEVER", "MALARIA"],
                "muscle pain": ["MALARIA", "DENGUE FEVER", "LASSA FEVER"],
                "stiff neck": ["MENINGITIS"],
                "cough": ["TUBERCULOSIS", "PNEUMONIA", "INFLUENZA"],
                "weight loss": ["TUBERCULOSIS", "HIV/AIDS"]
            },
            "conditions": {
                "MALARIA": ["Antimalarial drugs (Artemisinin-based Combination Therapy - ACT)", "supportive care for fever and dehydration", "seek immediate medical attention"],
                "TYPHOID FEVER": ["Antibiotics (Ciprofloxacin, Azithromycin)", "hydration therapy", "seek medical care immediately"],
                "CHOLERA": ["Oral Rehydration Therapy (ORT)", "intravenous fluids", "antibiotics (Doxycycline, Azithromycin)"],
                "TUBERCULOSIS": ["6-month course of antibiotics (Rifampin, Isoniazid, Ethambutol, Pyrazinamide)", "medical monitoring"],
                "HEPATITIS B": ["Antiviral medications (Tenofovir, Entecavir)", "liver monitoring", "supportive therapy"],
                "YELLOW FEVER": ["Supportive care (fluids, pain relievers, rest)", "seek immediate medical attention", "preventable by vaccination"],
                "MENINGITIS": ["Antibiotics for bacterial meningitis", "antiviral treatment for viral meningitis", "corticosteroids to reduce inflammation"],
                "MEASLES": ["Supportive care (fluids, fever reducers, vitamin A supplements)", "preventable by vaccination"],
                "HIV/AIDS": ["Antiretroviral therapy (ART) to manage the virus and prevent complications", "regular medical follow-up"]
            },
            "symptom_related_questions": {
                "high fever": ["Does your fever come and go in cycles?", "Do you have chills before the fever starts?", "Have you been in a malaria-endemic area recently?"],
                "fever": ["How long have you had the fever?", "Is it constant or does it come and go?", "Have you traveled recently to tropical areas?"],
                "jaundice": ["Have you noticed yellowing of your eyes or skin?", "Have you had any changes in urine color?", "Do you have any pain in your abdomen?"],
                "rash": ["Where is the rash located on your body?", "Is the rash itchy or painful?", "Did the rash appear after taking any medication?"],
                "diarrhea": ["How severe is the diarrhea?", "Is there any blood in your stool?", "Have you been drinking clean water?"],
                "cough": ["Is it a productive cough with sputum?", "How long have you been coughing?", "Have you coughed up any blood?"],
                "abdominal pain": ["Where exactly is the pain located?", "Is the pain constant or does it come and go?", "Does it get worse after eating?"],
                "headache": ["Is the headache severe?", "Does it get worse when you move?", "Do you have any sensitivity to light?"],
                "stiff neck": ["Can you touch your chin to your chest?", "Do you have a severe headache with the stiff neck?", "Do you have fever along with the stiff neck?"]
            },
            "diseases": {}
        }

    def extract_symptoms(self, user_input):
        """Extract symptoms from user input"""
        # Tokenize and lemmatize input
        words = word_tokenize(user_input.lower())
        lemmatized_words = [self.lemmatizer.lemmatize(word) for word in words if word not in self.stop_words]
        
        # Extract matched symptoms
        potential_symptoms = []
        for symptom in self.medical_data["symptoms"].keys():
            # Check for exact matches
            if symptom in user_input.lower():
                potential_symptoms.append(symptom)
                continue
                
            # Check for partial matches with compound symptoms (e.g., "sore throat")
            symptom_parts = symptom.split()
            if len(symptom_parts) > 1:
                match_count = sum(1 for part in symptom_parts if part in user_input.lower())
                if match_count / len(symptom_parts) >= 0.5:  # At least half the words match
                    potential_symptoms.append(symptom)
                    
        return potential_symptoms

    def get_follow_up_question(self):
        """Get a follow-up question based on collected symptoms"""
        # If we have specific follow-up questions for a symptom, use those
        for symptom in self.conversation_state["collected_symptoms"]:
            if symptom in self.medical_data.get("symptom_related_questions", {}):
                questions = self.medical_data["symptom_related_questions"][symptom]
                return random.choice(questions)
        
        # Otherwise use general follow-up questions
        return random.choice(self.follow_up_questions)

    def get_diagnosis(self):
        """Generate a diagnosis based on confirmed symptoms"""
        if not self.conversation_state["confirmed_symptoms"]:
            return "I need more information about your symptoms to provide a helpful assessment."
        
        # Find conditions that match the symptoms in our local database
        potential_conditions = {}
        
        for symptom in self.conversation_state["confirmed_symptoms"]:
            if symptom in self.medical_data["symptoms"]:
                conditions = self.medical_data["symptoms"][symptom]
                for condition in conditions:
                    potential_conditions[condition] = potential_conditions.get(condition, 0) + 1
        
        # Sort conditions by frequency
        sorted_conditions = sorted(potential_conditions.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_conditions:
            return "Based on the symptoms you've described, I don't have enough information to suggest a potential cause. Please consult with a healthcare professional."
        
        # Get top 3 conditions from local database
        top_conditions = sorted_conditions[:3]
        
        # Generate diagnosis response
        response = "Based on the symptoms you've described, here are some possible conditions to consider:\n\n"
        
        for condition, _ in top_conditions:
            response += f"• {condition}\n"
            if condition in self.medical_data["conditions"]:
                response += "  Possible self-care steps include: " + ", ".join(self.medical_data["conditions"][condition]) + "\n\n"
            else:
                response += "\n"
                
        # Also check external medical resources for additional information
        try:
            # Convert set to list for API
            symptom_list = list(self.conversation_state["confirmed_symptoms"])
            external_data = self.medical_api.search_medical_condition(symptom_list)
            
            if external_data and external_data.get("conditions"):
                response += "\nAdditional information from medical references:\n\n"
                
                for condition_info in external_data["conditions"]:
                    response += f"• {condition_info['name']}\n"
                    if condition_info.get('description'):
                        response += f"  {condition_info['description']}\n"
                    if condition_info.get('source'):
                        response += f"  Source: {condition_info['source']}\n\n"
                
                # Add the external API disclaimer if available
                if external_data.get("disclaimer"):
                    response += f"\n{external_data['disclaimer']}\n"
        except Exception as e:
            logger.error(f"Error getting external medical information: {str(e)}")
            # Continue without external data if there's an error
        
        response += "\n" + self.disclaimer
        
        return response

    def process_input(self, user_input):
        """Process user input and return appropriate response"""
        # Handle greetings
        if self.conversation_state["stage"] == "greeting":
            self.conversation_state["stage"] = "collecting_symptoms"
            return random.choice(self.greetings)
        
        # Check for conversation ending or restart
        if re.search(r'\b(goodbye|bye|thank you|thanks)\b', user_input.lower()):
            self.reset_conversation()
            return "I'm glad I could help. Remember, this is not a substitute for professional medical advice. Take care and consult a healthcare provider for proper diagnosis and treatment. Type anything to start a new conversation."
        
        # Check for restart request
        if re.search(r'\b(restart|start over|new conversation)\b', user_input.lower()):
            self.reset_conversation()
            return "Let's start over. " + random.choice(self.greetings)
        
        # Collecting symptoms stage
        if self.conversation_state["stage"] == "collecting_symptoms":
            extracted_symptoms = self.extract_symptoms(user_input)
            
            if extracted_symptoms:
                self.conversation_state["collected_symptoms"].update(extracted_symptoms)
                self.conversation_state["confirmed_symptoms"].update(extracted_symptoms)
                
                symptoms_text = ", ".join(extracted_symptoms)
                follow_up = self.get_follow_up_question()
                
                if len(self.conversation_state["confirmed_symptoms"]) >= 3:
                    self.conversation_state["stage"] = "diagnosis"
                    return f"I've identified these symptoms: {symptoms_text}. {follow_up} Or if you feel I have enough information, just say 'diagnose'."
                else:
                    return f"I see you're experiencing {symptoms_text}. {follow_up} Please mention any other symptoms you're experiencing."
            
            # Check if user wants a diagnosis with the symptoms collected so far
            if re.search(r'\b(diagnose|diagnosis|what do i have|what is it)\b', user_input.lower()):
                if self.conversation_state["confirmed_symptoms"]:
                    self.conversation_state["stage"] = "diagnosis"
                    return self.get_diagnosis()
                else:
                    return "I don't have enough information yet. Could you please describe your symptoms?"
            
            # No symptoms detected in the response
            return "I didn't recognize specific symptoms in your message. Could you please mention your symptoms more clearly? For example: headache, fever, cough, etc."
        
        # Diagnosis stage
        if self.conversation_state["stage"] == "diagnosis":
            # Check if user is adding more symptoms
            new_symptoms = self.extract_symptoms(user_input)
            if new_symptoms:
                self.conversation_state["confirmed_symptoms"].update(new_symptoms)
                symptoms_text = ", ".join(new_symptoms)
                return f"I've added these additional symptoms: {symptoms_text}. " + self.get_diagnosis()
            
            # Check if user is asking for more information or clarification
            if re.search(r'\b(more info|more information|tell me more|additional info|explain|clarify)\b', user_input.lower()):
                # Get potential conditions from symptoms (similar to get_diagnosis)
                potential_conditions = {}
                for symptom in self.conversation_state["confirmed_symptoms"]:
                    if symptom in self.medical_data["symptoms"]:
                        conditions = self.medical_data["symptoms"][symptom]
                        for condition in conditions:
                            potential_conditions[condition] = potential_conditions.get(condition, 0) + 1
                
                # Try to get information about specific conditions mentioned in user input
                for condition in potential_conditions.keys():
                    if condition.lower() in user_input.lower():
                        return self.get_treatment_info(condition)
                
                # Check if user is asking about a specific disease that wasn't in our diagnosis
                # Common diseases to check for
                specific_diseases = [
                    "malaria", "typhoid", "dengue", "cholera", "tuberculosis", "tb", 
                    "covid", "flu", "influenza", "pneumonia", "bronchitis", "asthma",
                    "diabetes", "hypertension", "cancer", "hiv", "aids"
                ]
                
                for disease in specific_diseases:
                    if disease in user_input.lower():
                        return self.get_treatment_info(disease.title())
                
                return "For more detailed information about these conditions, please consult with a healthcare professional. They can provide personalized advice based on your medical history and a proper examination. " + self.disclaimer
            
            # Default response in diagnosis stage
            return "Based on the symptoms you've shared, I've provided my best assessment. Is there anything specific you'd like to know about these potential conditions? You can also say 'restart' to begin a new consultation."
        
        # Default response if no other condition is met
        return "I'm not sure I understand. Could you please clarify or rephrase your question? You can describe your symptoms or ask for a diagnosis if we've already discussed your symptoms."

    def get_treatment_info(self, condition):
        """Get detailed treatment information for a specific condition"""
        response = f"Here's more information about {condition}:\n\n"
        
        # Try to get information from our local database
        if condition in self.medical_data["conditions"]:
            response += f"Recommended self-care steps include: {', '.join(self.medical_data['conditions'][condition])}\n\n"
        
        # Try to get additional information from external sources
        try:
            treatment_info = self.medical_api.get_treatment_recommendations(condition)
            
            if treatment_info:
                if treatment_info.get('treatment'):
                    response += f"Additional treatment information:\n{treatment_info['treatment']}\n\n"
                
                if treatment_info.get('source'):
                    response += f"Source: {treatment_info['source']}\n"
                
                if treatment_info.get('disclaimer'):
                    response += f"\n{treatment_info['disclaimer']}\n"
        except Exception as e:
            logger.error(f"Error getting treatment information: {str(e)}")
            # Continue without external data if there's an error
        
        response += "\n" + self.disclaimer
        return response
    
    def reset_conversation(self):
        """Reset the conversation state"""
        self.conversation_state = {
            "collected_symptoms": set(),
            "confirmed_symptoms": set(),
            "stage": "greeting",
            "current_question": None
        }
