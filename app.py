import os
import logging
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from chatbot import DoctorChatbot
from process_medical_data import process_medical_text

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Initialize chatbot
chatbot = DoctorChatbot()

# Main routes
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

# Status for tracking medical text processing
text_processing_status = {
    "is_running": False,
    "completed": False,
    "message": ""
}

def process_medical_text_background():
    """Process medical text file in background to avoid timeouts"""
    global text_processing_status
    
    try:
        logger.info("Starting to process medical text file")
        text_processing_status["message"] = "Processing medical text file..."
        
        # Process the medical text file
        success = process_medical_text()
        
        if success:
            text_processing_status["message"] = "Successfully processed medical text file"
            text_processing_status["completed"] = True
            
            # Reload medical data in chatbot to include new information
            chatbot.medical_data = chatbot.load_medical_data()
            logger.info("Chatbot medical data reloaded with updated medical information")
        else:
            text_processing_status["message"] = "Error processing medical text file"
            
        logger.info("Medical text processing completed")
    except Exception as e:
        logger.error(f"Error in medical text processing thread: {str(e)}")
        text_processing_status["message"] = f"Error processing: {str(e)}"
    finally:
        # Mark processing as complete
        text_processing_status["is_running"] = False

@app.route('/process_medical_data', methods=['POST'])
def start_process_medical_data():
    """Start processing medical text file in background"""
    global text_processing_status
    
    if text_processing_status["is_running"]:
        return jsonify({
            "status": "already_running",
            "message": "Medical text processing is already running"
        })
    
    # Reset status and start processing
    text_processing_status["is_running"] = True
    text_processing_status["completed"] = False
    text_processing_status["message"] = "Starting medical text processing..."
    
    # Start processing in background thread
    thread = threading.Thread(target=process_medical_text_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "message": "Medical text processing started in background"
    })

@app.route('/medical_data_status', methods=['GET'])
def get_medical_data_status():
    """Get the current status of medical text processing"""
    return jsonify(text_processing_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
