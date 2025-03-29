import json
import os
import logging
import random
from typing import List, Dict, Set, Any, Optional, Tuple

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DoctorChatbot:
    def __init__(self):
        """Initialize the Doctor Chatbot with necessary resources"""
        # Download required NLTK packages
        try:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
            nltk.download('punkt_tab')  # This includes punkt tokenizer models
            logger.info("Downloaded required NLTK resources")
        except Exception as e:
            logger.error(f"Error downloading NLTK resources: {str(e)}")
        
        # Initialize NLP tools
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Conversation state
        self.conversation_state = {
            "greeting_shown": False,
            "symptoms": set(),
            "confirmed_symptoms": set(),
            "rejected_symptoms": set(),
            "diagnoses": [],
            "follow_up_questions_asked": 0,
            "diagnosis_provided": False,
            "current_condition": None
        }
        
        # Greeting messages
        self.greeting_messages = [
            "Hello! I'm Medi Chat, your personal medical assistant. I can help identify possible health conditions based on your symptoms. Please describe at least 3 symptoms you're experiencing.",
            "Hi there! Welcome to Medi Chat. I'm here to help with your health concerns. Please tell me at least 3 symptoms you're experiencing so I can assist better.",
            "Welcome to Medi Chat! I'm designed to help identify potential health conditions. For the most accurate assessment, please describe at least 3 symptoms you're experiencing."
        ]
        
        # Follow-up questions to gather more symptoms
        self.follow_up_questions = [
            "Could you describe any other symptoms you're experiencing?",
            "When did your symptoms begin?",
            "Are you experiencing any pain? If yes, where and how would you describe it?",
            "Have you noticed any changes in your appetite or weight recently?",
            "Are you having any difficulties with sleep?",
            "Any fever, chills, or sweating?",
            "Have you been feeling unusually tired or fatigued?",
            "Have you noticed any changes in your bowel movements or urination?",
            "Any dizziness, headaches, or issues with balance?",
            "Have you experienced these symptoms before?"
        ]
        
        # Load medical knowledge base
        self.medical_data = self.load_medical_data()
        
        # Create an index of symptoms to conditions for efficient lookup
        self.symptom_to_conditions = {}
        self._build_symptom_index()
    
    def load_medical_data(self):
        """Load the medical knowledge base from JSON file or process the text file directly"""
        medical_data_file = 'static/data/medical_data.json'
        
        if os.path.exists(medical_data_file):
            try:
                with open(medical_data_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Successfully loaded medical data from {medical_data_file}")
                return data
            except Exception as e:
                logger.error(f"Error loading medical data from JSON: {str(e)}")
        
        # If JSON file doesn't exist or there's an error, process the text file directly
        logger.info("Processing medical text file directly.")
        from process_medical_data import process_medical_text
        process_medical_text()
        
        # Try loading the JSON file again after processing
        try:
            with open(medical_data_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error loading processed medical data: {str(e)}")
            # Return basic medical data as fallback
            return self._get_basic_medical_data()
    
    def _get_basic_medical_data(self):
        """Return a basic dataset focused on common diseases"""
        return {
            "conditions": [
                {
                    "name": "Common Cold",
                    "symptoms": ["runny nose", "sneezing", "sore throat", "cough", "congestion"],
                    "treatment": "Rest, hydration, over-the-counter cold medications.",
                    "confidence": 0.9
                },
                {
                    "name": "Influenza (Flu)",
                    "symptoms": ["fever", "body aches", "fatigue", "headache", "cough", "sore throat"],
                    "treatment": "Rest, hydration, antiviral medications if prescribed.",
                    "confidence": 0.85
                },
                {
                    "name": "Migraine",
                    "symptoms": ["severe headache", "nausea", "sensitivity to light", "sensitivity to sound"],
                    "treatment": "Pain relievers, rest in a dark quiet room, prescription medications.",
                    "confidence": 0.8
                }
            ]
        }
    
    def _build_symptom_index(self):
        """Build an index that maps symptoms to conditions"""
        for condition in self.medical_data.get("conditions", []):
            condition_name = condition.get("name", "")
            for symptom in condition.get("symptoms", []):
                # Store both original form and lemmatized form
                lemma_symptom = " ".join([self.lemmatizer.lemmatize(word) for word in symptom.lower().split()])
                
                if symptom not in self.symptom_to_conditions:
                    self.symptom_to_conditions[symptom] = []
                if lemma_symptom not in self.symptom_to_conditions:
                    self.symptom_to_conditions[lemma_symptom] = []
                
                self.symptom_to_conditions[symptom].append(condition_name)
                self.symptom_to_conditions[lemma_symptom].append(condition_name)
    
    def extract_symptoms(self, user_input):
        """Extract symptoms from user input"""
        # Tokenize and lemmatize the input
        tokens = word_tokenize(user_input.lower())
        lemmatized_tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        lemmatized_input = " ".join(lemmatized_tokens)
        
        # Simple approach: Check if common symptom phrases are in the input
        potential_symptoms = set()
        
        # Check for symptoms in the knowledge base
        for symptom in self.symptom_to_conditions.keys():
            if symptom.lower() in lemmatized_input.lower() or symptom.lower() in user_input.lower():
                potential_symptoms.add(symptom)
        
        # If no symptoms were found using the knowledge base, try to extract based on user input
        if not potential_symptoms:
            # Extract noun phrases as potential symptoms (simplified)
            ngrams = []
            for i in range(1, 4):  # Check 1-grams, 2-grams, and 3-grams
                for j in range(len(tokens) - i + 1):
                    ngram = " ".join(tokens[j:j+i])
                    if not all(token in self.stop_words for token in ngram.split()):
                        ngrams.append(ngram)
            
            # Filter ngrams that might be symptoms (very simplified)
            symptom_indicators = ["pain", "ache", "sore", "hurt", "discomfort", "fever", 
                                 "cough", "dizz", "nause", "vomit", "rash", "swelling", 
                                 "tired", "fatigue", "weak", "sick", "ill", "sweating"]
            
            for ngram in ngrams:
                for indicator in symptom_indicators:
                    if indicator in ngram and ngram not in self.conversation_state["rejected_symptoms"]:
                        potential_symptoms.add(ngram)
                        break
        
        return potential_symptoms
    
    def get_follow_up_question(self):
        """Get a follow-up question based on collected symptoms"""
        # If we already have some symptoms, ask a follow-up based on those
        if self.conversation_state["symptoms"]:
            # If we don't have enough symptoms yet, encourage more symptom reporting
            if len(self.conversation_state["confirmed_symptoms"]) < 3:
                remaining = 3 - len(self.conversation_state["confirmed_symptoms"])
                return f"I need {remaining} more {'symptoms' if remaining > 1 else 'symptom'} to provide a better assessment. What else are you experiencing?"
            
            # Otherwise, ask a general follow-up question
            self.conversation_state["follow_up_questions_asked"] += 1
            if self.conversation_state["follow_up_questions_asked"] <= 3:
                return random.choice(self.follow_up_questions)
        
        # Default follow-up if no symptoms yet
        return "Could you describe your symptoms in more detail?"
    
    def get_diagnosis(self):
        """Generate a diagnosis based on confirmed symptoms"""
        # Check if we have enough symptoms
        if len(self.conversation_state["confirmed_symptoms"]) < 3:
            remaining = 3 - len(self.conversation_state["confirmed_symptoms"])
            return f"I need at least {remaining} more {'symptoms' if remaining > 1 else 'symptom'} to provide an accurate assessment."
        
        # Count conditions that match each symptom
        condition_matches = {}
        
        for symptom in self.conversation_state["confirmed_symptoms"]:
            # Find conditions that match this symptom
            matching_conditions = self.symptom_to_conditions.get(symptom, [])
            matching_conditions.extend(self.symptom_to_conditions.get(symptom.lower(), []))
            
            # Update the count for each matching condition
            for condition in matching_conditions:
                if condition not in condition_matches:
                    condition_matches[condition] = 0
                condition_matches[condition] += 1
        
        # Sort conditions by number of matching symptoms
        sorted_conditions = sorted(condition_matches.items(), key=lambda x: x[1], reverse=True)
        
        # If no conditions match, return a generic message
        if not sorted_conditions:
            return "Based on the symptoms you've described, I don't have enough information to suggest a specific condition. Please consult a healthcare professional for proper diagnosis."
        
        # Get detailed information for the top 2 matching conditions
        detailed_conditions = []
        for condition_name, match_count in sorted_conditions[:2]:
            # Find the condition details
            condition_details = None
            for condition in self.medical_data.get("conditions", []):
                if condition.get("name") == condition_name:
                    condition_details = condition
                    break
            
            if condition_details:
                # Calculate match percentage
                condition_symptom_count = len(condition_details.get("symptoms", []))
                if condition_symptom_count > 0:
                    match_percentage = (match_count / condition_symptom_count) * 100
                else:
                    match_percentage = 0
                
                # Determine confidence level
                confidence_level = ""
                if match_percentage >= 70:
                    confidence_level = "High Sickness"
                elif match_percentage >= 40:
                    confidence_level = "Moderate Sickness"
                else:
                    confidence_level = "Possible Sickness"
                
                # Add to detailed conditions
                detailed_conditions.append({
                    "name": condition_name,
                    "confidence": confidence_level,
                    "treatment": condition_details.get("treatment", "Please consult a healthcare provider for treatment options."),
                    "match_percentage": match_percentage
                })
        
        # Format the response
        if detailed_conditions:
            response = "Based on the symptoms you've described, here are potential conditions:<br><br>"
            
            for idx, condition in enumerate(detailed_conditions):
                response += f"<strong>{idx+1}. {condition['name']}</strong> ({condition['confidence']})<br>"
                response += f"<em>Treatment:</em> {condition['treatment']}<br><br>"
            
            response += "<strong>Medical Disclaimer:</strong> This information is for educational purposes only and should not replace professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment."
            
            # Store the diagnoses for reference
            self.conversation_state["diagnoses"] = detailed_conditions
            self.conversation_state["diagnosis_provided"] = True
            
            return response
        else:
            return "Based on your symptoms, I couldn't identify a specific condition. Please consult a healthcare professional for a proper diagnosis."
    
    def process_input(self, user_input):
        """Process user input and return appropriate response"""
        # Check for conversation reset
        if "reset" in user_input.lower() or "start over" in user_input.lower() or "new conversation" in user_input.lower():
            self.reset_conversation()
            return random.choice(self.greeting_messages)
        
        # Show greeting on first interaction
        if not self.conversation_state["greeting_shown"]:
            self.conversation_state["greeting_shown"] = True
            return random.choice(self.greeting_messages)
        
        # Extract symptoms from user input
        new_symptoms = self.extract_symptoms(user_input)
        
        # If symptoms were found, acknowledge them and add to our list
        if new_symptoms:
            # Add new symptoms to our tracking sets
            for symptom in new_symptoms:
                if symptom not in self.conversation_state["rejected_symptoms"]:
                    self.conversation_state["symptoms"].add(symptom)
                    self.conversation_state["confirmed_symptoms"].add(symptom)
            
            # If we now have enough symptoms, provide a diagnosis
            if len(self.conversation_state["confirmed_symptoms"]) >= 3 and not self.conversation_state["diagnosis_provided"]:
                return self.get_diagnosis()
            
            # Otherwise acknowledge the symptoms and ask a follow-up
            if len(self.conversation_state["confirmed_symptoms"]) < 3:
                symptom_list = ", ".join(list(new_symptoms))
                remaining = 3 - len(self.conversation_state["confirmed_symptoms"])
                return f"I've noted your symptom(s): {symptom_list}. I need {remaining} more {'symptoms' if remaining > 1 else 'symptom'} to provide a better assessment. What else are you experiencing?"
            else:
                # We have enough symptoms but want more information
                return self.get_follow_up_question()
        
        # If user is asking for a diagnosis and we have enough symptoms
        diagnosis_keywords = ["diagnosis", "what do i have", "what is wrong", "what could it be", "tell me what", "my condition"]
        if any(keyword in user_input.lower() for keyword in diagnosis_keywords) and len(self.conversation_state["confirmed_symptoms"]) >= 3:
            return self.get_diagnosis()
        
        # If user is asking about treatment for a condition
        treatment_keywords = ["treatment", "how to treat", "what should i do", "remedy", "medicine", "cure"]
        if any(keyword in user_input.lower() for keyword in treatment_keywords) and self.conversation_state["diagnoses"]:
            # Get the most likely condition
            if self.conversation_state["diagnoses"]:
                condition = self.conversation_state["diagnoses"][0]["name"]
                return self.get_treatment_info(condition)
        
        # If user is asking a medical question but we don't have enough symptoms
        medical_question_keywords = ["diagnosis", "what do i have", "what is wrong", "what could it be"]
        if any(keyword in user_input.lower() for keyword in medical_question_keywords) and len(self.conversation_state["confirmed_symptoms"]) < 3:
            remaining = 3 - len(self.conversation_state["confirmed_symptoms"])
            return f"I need at least {remaining} more {'symptoms' if remaining > 1 else 'symptom'} to provide an accurate assessment. Please describe more symptoms you're experiencing."
        
        # Default: ask a follow-up question to gather more information
        return self.get_follow_up_question()
    
    def get_treatment_info(self, condition):
        """Get detailed treatment information for a specific condition"""
        # Look up the condition in our medical data
        for cond in self.medical_data.get("conditions", []):
            if cond["name"].lower() == condition.lower():
                treatment = cond.get("treatment", "Please consult a healthcare provider for treatment options.")
                return f"<strong>Treatment for {condition}:</strong><br>{treatment}<br><br><strong>Medical Disclaimer:</strong> This information is for educational purposes only and should not replace professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment."
        
        # If condition not found
        return f"I don't have detailed treatment information for {condition}. Please consult a healthcare professional for appropriate treatment options."
    
    def reset_conversation(self):
        """Reset the conversation state"""
        self.conversation_state = {
            "greeting_shown": False,
            "symptoms": set(),
            "confirmed_symptoms": set(),
            "rejected_symptoms": set(),
            "diagnoses": [],
            "follow_up_questions_asked": 0,
            "diagnosis_provided": False,
            "current_condition": None
        }