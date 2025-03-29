from app import app
import logging
from process_african_diseases import process_african_diseases

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Process African diseases data on startup
    logger.info("Processing African diseases data on startup...")
    success = process_african_diseases()
    if success:
        logger.info("Successfully processed African diseases data!")
    else:
        logger.error("Failed to process African diseases data on startup.")
    
    # Start the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)
