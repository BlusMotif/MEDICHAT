import logging
import nltk
import os

# Ensure necessary directories exist
os.makedirs('static/data', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/img', exist_ok=True)
os.makedirs('resources/medical_data', exist_ok=True)

# Download NLTK resources
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    print("NLTK resources downloaded successfully!")
except Exception as e:
    print(f"Error downloading NLTK resources: {e}")

# Import and process medical text data
try:
    from process_medical_data import process_medical_text
    process_medical_text()
    print("Medical text data processed successfully!")
except Exception as e:
    print(f"Error processing medical text data: {e}")

# Import Flask application
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)