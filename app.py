import os
import logging
import threading
from flask import Flask, render_template, request, jsonify
from chatbot import DoctorChatbot
from pdf_processor import PDFMedicalProcessor
from text_processor import AfricanDiseaseTextProcessor
from process_african_diseases import process_african_diseases

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Initialize chatbot
chatbot = DoctorChatbot()

# Flag to check if PDF processing is running
pdf_processing_status = {
    "is_running": False,
    "progress": 0,
    "total_pdfs": 0,
    "processed_pdfs": 0
}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    """Process user message and return chatbot response"""
    try:
        user_message = request.json.get('message', '')
        logger.debug(f"Received user message: {user_message}")
        
        # Allow empty messages (for initial greeting)
        response = chatbot.process_input(user_message)
        logger.debug(f"Generated response: {response}")
        
        return jsonify({"response": response})
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return jsonify({"error": "An error occurred while processing your message. Please try again."}), 500

def process_pdfs_background():
    """Process PDFs in a background thread to avoid timeouts"""
    global pdf_processing_status
    
    try:
        # Get list of PDF files
        pdf_dir = "attached_assets"
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        
        pdf_processing_status["total_pdfs"] = len(pdf_files)
        pdf_processing_status["processed_pdfs"] = 0
        
        for pdf_file in pdf_files:
            # Process single PDF
            pdf_path = os.path.join(pdf_dir, pdf_file)
            logger.info(f"Processing PDF: {pdf_path}")
            
            try:
                # Process a single PDF file
                processor = PDFMedicalProcessor(single_pdf_path=pdf_path)
                # Update chatbot with new medical data
                chatbot.medical_data = processor.medical_data
                
                # Update progress
                pdf_processing_status["processed_pdfs"] += 1
                pdf_processing_status["progress"] = int((pdf_processing_status["processed_pdfs"] / pdf_processing_status["total_pdfs"]) * 100)
                
                logger.info(f"Processed {pdf_file} successfully")
            except Exception as e:
                logger.error(f"Error processing PDF {pdf_file}: {str(e)}")
        
        logger.info("PDF processing completed")
    except Exception as e:
        logger.error(f"Error in PDF processing thread: {str(e)}")
    finally:
        # Mark processing as complete
        pdf_processing_status["is_running"] = False

@app.route('/process_pdfs', methods=['POST'])
def process_pdfs():
    """Start PDF processing in background"""
    global pdf_processing_status
    
    if pdf_processing_status["is_running"]:
        return jsonify({
            "status": "already_running",
            "progress": pdf_processing_status["progress"],
            "message": "PDF processing is already running"
        })
    
    # Reset status and start processing
    pdf_processing_status["is_running"] = True
    pdf_processing_status["progress"] = 0
    pdf_processing_status["processed_pdfs"] = 0
    pdf_processing_status["total_pdfs"] = 0
    
    # Start processing in background thread
    thread = threading.Thread(target=process_pdfs_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "message": "PDF processing started in background"
    })

@app.route('/pdf_processing_status', methods=['GET'])
def get_pdf_processing_status():
    """Get the current status of PDF processing"""
    return jsonify(pdf_processing_status)

# Status for tracking African diseases text processing
text_processing_status = {
    "is_running": False,
    "completed": False,
    "message": ""
}

def process_african_diseases_background():
    """Process African diseases text file in background to avoid timeouts"""
    global text_processing_status
    
    try:
        logger.info("Starting to process African diseases text file")
        text_processing_status["message"] = "Processing African diseases text file..."
        
        # Process the African diseases text file
        success = process_african_diseases()
        
        if success:
            text_processing_status["message"] = "Successfully processed African diseases text file"
            text_processing_status["completed"] = True
            
            # Reload medical data in chatbot to include new information
            chatbot.medical_data = chatbot.load_medical_data()
            logger.info("Chatbot medical data reloaded with African diseases information")
        else:
            text_processing_status["message"] = "Error processing African diseases text file"
            
        logger.info("African diseases text processing completed")
    except Exception as e:
        logger.error(f"Error in African diseases text processing thread: {str(e)}")
        text_processing_status["message"] = f"Error processing: {str(e)}"
    finally:
        # Mark processing as complete
        text_processing_status["is_running"] = False

@app.route('/process_african_diseases', methods=['POST'])
def start_process_african_diseases():
    """Start processing African diseases text file in background"""
    global text_processing_status
    
    if text_processing_status["is_running"]:
        return jsonify({
            "status": "already_running",
            "message": "African diseases text processing is already running"
        })
    
    # Reset status and start processing
    text_processing_status["is_running"] = True
    text_processing_status["completed"] = False
    text_processing_status["message"] = "Starting African diseases text processing..."
    
    # Start processing in background thread
    thread = threading.Thread(target=process_african_diseases_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "message": "African diseases text processing started in background"
    })

@app.route('/african_diseases_status', methods=['GET'])
def get_african_diseases_status():
    """Get the current status of African diseases text processing"""
    return jsonify(text_processing_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
