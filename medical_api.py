import os
import json
import logging
import requests
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalResourceAPI:
    """Class to interact with external medical resources and APIs"""
    
    def __init__(self):
        """Initialize the MedicalResourceAPI with necessary configurations"""
        # Base URL for the medical information API
        self.health_api_url = "https://clinicaltables.nlm.nih.gov/api/conditions/v3/search"
        self.treatment_api_url = "https://clinicaltables.nlm.nih.gov/api/conditions/v3/search"
        
        # Alternative APIs for backup use
        self.medline_api_url = "https://wsearch.nlm.nih.gov/ws/query"
        
        # The maximum number of results to return
        self.max_results = 3
    
    def search_medical_condition(self, symptoms: List[str]) -> Dict:
        """
        Search for medical conditions based on symptoms using various medical resources
        
        Args:
            symptoms: List of symptoms experienced by the user
        
        Returns:
            Dictionary containing potential conditions and information
        """
        try:
            # Query health API with symptoms
            symptom_query = " ".join(symptoms)
            health_results = self._query_health_api(symptom_query)
            
            # If no results from the primary API, try the medline API as backup
            if not health_results.get("conditions"):
                medline_results = self._query_medline_api(symptom_query)
                if medline_results:
                    health_results["conditions"].extend(medline_results)
            
            # Add disclaimer
            health_results["disclaimer"] = (
                "Information provided comes from reputable medical resources. "
                "This is not a definitive diagnosis. Please consult a healthcare professional."
            )
            
            return health_results
        
        except Exception as e:
            logger.error(f"Error searching medical conditions: {str(e)}")
            return {
                "conditions": [],
                "disclaimer": "Unable to retrieve external medical information. Please consult with a healthcare professional for accurate diagnosis."
            }
    
    def _query_health_api(self, query: str) -> Dict:
        """
        Query the health API for condition information
        
        Args:
            query: The symptom or condition to search for
            
        Returns:
            Dictionary with the response information
        """
        try:
            params = {
                "terms": query,
                "maxList": self.max_results,
                "df": "consumer_name,definition"
            }
            
            response = requests.get(self.health_api_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Format the response
                conditions = []
                
                # Data structure: [count, "", ["name1", "name2"], [["definition1"], ["definition2"]]]
                if len(data) >= 4 and isinstance(data[2], list) and isinstance(data[3], list):
                    for i, name in enumerate(data[2]):
                        if i < len(data[3]) and data[3][i]:
                            description = data[3][i][0] if data[3][i] else "No description available"
                            conditions.append({
                                "name": name,
                                "description": description,
                                "source": "National Library of Medicine"
                            })
                
                return {"conditions": conditions}
            else:
                logger.warning(f"Health API returned status code {response.status_code}")
                return {"conditions": []}
        
        except Exception as e:
            logger.error(f"Error querying health API: {str(e)}")
            return {"conditions": []}
    
    def _query_medline_api(self, query: str) -> List[Dict]:
        """
        Query the MedlinePlus API for medical information
        
        Args:
            query: The symptom or condition to search for
            
        Returns:
            List of condition information dictionaries
        """
        try:
            params = {
                "db": "healthTopics",
                "term": f"{query} symptoms treatment",
                "retmax": self.max_results
            }
            
            response = requests.get(self.medline_api_url, params=params, timeout=5)
            
            if response.status_code == 200:
                # Parse XML response (simplified for this implementation)
                # In a real implementation, would use proper XML parsing
                results = []
                response_text = response.text
                
                # Extract document sections using simple text markers
                # This is simplified logic - real implementation would use proper XML parsing
                sections = response_text.split("<document>")[1:]
                
                for section in sections[:self.max_results]:
                    try:
                        title = section.split("<content name=\"title\">")[1].split("</content>")[0].strip()
                        snippet = section.split("<content name=\"snippet\">")[1].split("</content>")[0].strip()
                        
                        results.append({
                            "name": title,
                            "description": snippet,
                            "source": "MedlinePlus"
                        })
                    except IndexError:
                        continue
                
                return results
            else:
                logger.warning(f"Medline API returned status code {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error querying Medline API: {str(e)}")
            return []
    
    def get_treatment_recommendations(self, condition: str) -> Dict:
        """
        Get treatment recommendations for a specific condition
        
        Args:
            condition: The medical condition to get treatment information for
            
        Returns:
            Dictionary containing treatment information
        """
        try:
            # Query the treatment API with the condition
            params = {
                "terms": f"{condition} treatment",
                "maxList": 1,
                "df": "consumer_name,definition"
            }
            
            response = requests.get(self.treatment_api_url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract treatment information
                if len(data) >= 4 and isinstance(data[3], list) and data[3]:
                    treatment_info = data[3][0][0] if data[3][0] else "No specific treatment information available."
                    return {
                        "condition": condition,
                        "treatment": treatment_info,
                        "source": "National Library of Medicine",
                        "disclaimer": "Always consult with a healthcare professional before starting any treatment."
                    }
            
            # If no results or error, return default message
            return {
                "condition": condition,
                "treatment": "No specific treatment information found. Please consult with a healthcare professional.",
                "source": "Not available",
                "disclaimer": "Always consult with a healthcare professional before starting any treatment."
            }
            
        except Exception as e:
            logger.error(f"Error getting treatment recommendations: {str(e)}")
            return {
                "condition": condition,
                "treatment": "Unable to retrieve treatment information. Please consult with a healthcare professional.",
                "source": "Not available",
                "disclaimer": "Always consult with a healthcare professional before starting any treatment."
            }


# For testing
if __name__ == "__main__":
    api = MedicalResourceAPI()
    results = api.search_medical_condition(["fever", "cough", "headache"])
    print(json.dumps(results, indent=2))