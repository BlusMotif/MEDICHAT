import logging
from pdf_processor import enhance_medical_knowledge

# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting processing of medical PDFs...")
    enhanced_data = enhance_medical_knowledge()
    logger.info(f"Processing complete. Enhanced {len(enhanced_data['symptoms'])} symptoms and {len(enhanced_data['conditions'])} conditions.")