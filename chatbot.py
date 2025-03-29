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
            "Has anyone around you experienced similar symptoms?"
        ]
        
        # Disclaimer messages
        self.disclaimer = (
            "IMPORTANT: This is only a preliminary assessment based on the symptoms you've described. "
            "It is not a medical diagnosis. Please consult with a healthcare professional for proper diagnosis and treatment."
        )

    def load_medical_data(self):
        """Load the medical knowledge base from JSON file"""
        try:
            data_path = Path(__file__).parent / "static" / "data" / "medical_data.json"
            
            # If file doesn't exist yet (during development)
            if not data_path.exists():
                # Use sample data
                medical_data = {
                    "symptoms": {
                        "headache": ["Tension headache", "Migraine", "Sinusitis", "Dehydration", "Eye strain"],
                        "fever": ["Common cold", "Flu", "COVID-19", "Infection", "Inflammation"],
                        "cough": ["Common cold", "Bronchitis", "Asthma", "COVID-19", "Allergies"],
                        "sore throat": ["Strep throat", "Common cold", "Tonsillitis", "Allergies", "Acid reflux"],
                        "runny nose": ["Common cold", "Allergies", "Sinusitis", "Flu"],
                        "fatigue": ["Anemia", "Depression", "Sleep disorder", "Thyroid issues", "Infection"],
                        "nausea": ["Food poisoning", "Stomach flu", "Migraine", "Pregnancy", "Motion sickness"],
                        "dizziness": ["Low blood pressure", "Inner ear issues", "Anemia", "Dehydration", "Anxiety"],
                        "chest pain": ["Heartburn", "Anxiety", "Muscle strain", "Asthma", "Heart issues"],
                        "shortness of breath": ["Asthma", "Anxiety", "COVID-19", "Heart issues", "Pneumonia"],
                        "back pain": ["Muscle strain", "Herniated disc", "Arthritis", "Kidney infection", "Poor posture"],
                        "abdominal pain": ["Gastritis", "Food poisoning", "Irritable bowel syndrome", "Appendicitis", "Menstrual cramps"],
                        "diarrhea": ["Food poisoning", "Irritable bowel syndrome", "Infection", "Food intolerance", "Medication side effect"],
                        "constipation": ["Dehydration", "Low fiber diet", "Medication side effect", "Irritable bowel syndrome", "Thyroid issues"],
                        "rash": ["Allergic reaction", "Eczema", "Psoriasis", "Contact dermatitis", "Fungal infection"],
                        "joint pain": ["Arthritis", "Injury", "Gout", "Lupus", "Bursitis"],
                        "vomiting": ["Food poisoning", "Stomach flu", "Migraine", "Pregnancy", "Motion sickness"],
                        "muscle pain": ["Strain", "Overuse", "Fibromyalgia", "Infection", "Medication side effect"],
                        "ear pain": ["Ear infection", "Sinus infection", "Tooth infection", "Temporomandibular joint disorder", "Water in ear"],
                        "eye pain": ["Conjunctivitis", "Dry eye", "Foreign object", "Glaucoma", "Migraine"]
                    },
                    "conditions": {
                        "Common cold": ["rest", "fluids", "over-the-counter pain relievers", "decongestants"],
                        "Flu": ["rest", "fluids", "antiviral medications", "fever reducers"],
                        "COVID-19": ["isolation", "rest", "fluids", "consult healthcare provider"],
                        "Migraine": ["rest", "dark quiet room", "pain relievers", "prescription medications"],
                        "Allergies": ["antihistamines", "avoid allergens", "nasal sprays", "consult allergist"],
                        "Sinusitis": ["saline nasal irrigation", "decongestants", "pain relievers", "antibiotics if bacterial"],
                        "Tension headache": ["stress management", "pain relievers", "rest", "massage"],
                        "Asthma": ["inhalers", "avoid triggers", "breathing exercises", "medical follow-up"],
                        "Food poisoning": ["hydration", "bland diet", "rest", "probiotics"],
                        "Irritable bowel syndrome": ["dietary changes", "stress management", "fiber supplements", "medications"]
                    },
                    "symptom_related_questions": {
                        "headache": ["Is the headache on one side or both?", "Is it pulsating or a constant pressure?", "Does light or noise make it worse?"],
                        "fever": ["What's your temperature?", "Do you have chills or sweating?", "How long have you had the fever?"],
                        "cough": ["Is it a dry cough or producing mucus?", "When did it start?", "Is it worse at night?"],
                        "abdominal pain": ["Where exactly is the pain?", "Is it sharp or dull?", "Does it come and go or is it constant?"]
                    }
                }
                return medical_data
            
            with open(data_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading medical data: {str(e)}")
            # Return a minimal fallback dataset
            return {
                "symptoms": {
                    "headache": ["Tension headache", "Migraine"],
                    "fever": ["Common cold", "Flu"],
                    "cough": ["Common cold", "Bronchitis"]
                },
                "conditions": {
                    "Common cold": ["rest", "fluids"],
                    "Tension headache": ["rest", "pain relievers"]
                }
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
        
        # Find conditions that match the symptoms
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
        
        # Get top 3 conditions
        top_conditions = sorted_conditions[:3]
        
        # Generate diagnosis response
        response = "Based on the symptoms you've described, here are some possible conditions to consider:\n\n"
        
        for condition, _ in top_conditions:
            response += f"• {condition}\n"
            if condition in self.medical_data["conditions"]:
                response += "  Possible self-care steps include: " + ", ".join(self.medical_data["conditions"][condition]) + "\n\n"
            else:
                response += "\n"
                
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
                return "For more detailed information about these conditions, please consult with a healthcare professional. They can provide personalized advice based on your medical history and a proper examination. " + self.disclaimer
            
            # Default response in diagnosis stage
            return "Based on the symptoms you've shared, I've provided my best assessment. Is there anything specific you'd like to know about these potential conditions? You can also say 'restart' to begin a new consultation."
        
        # Default response if no other condition is met
        return "I'm not sure I understand. Could you please clarify or rephrase your question? You can describe your symptoms or ask for a diagnosis if we've already discussed your symptoms."

    def reset_conversation(self):
        """Reset the conversation state"""
        self.conversation_state = {
            "collected_symptoms": set(),
            "confirmed_symptoms": set(),
            "stage": "greeting",
            "current_question": None
        }
