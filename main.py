from app import app
import logging
from process_medical_data import process_medical_text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Process medical data on startup
    logger.info("Processing medical data on startup...")
    success = process_medical_text()
    if success:
        logger.info("Successfully processed medical data!")
    else:
        logger.error("Failed to process medical data on startup.")
    
    # Start the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)
