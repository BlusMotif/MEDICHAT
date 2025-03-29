import os
import json
import logging
import threading
from datetime import datetime
from io import BytesIO

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "medichat-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Import models after initializing db to avoid circular imports
with app.app_context():
    from models import User, MedicalHistory
    db.create_all()

# Import chatbot after database initialization
from chatbot import DoctorChatbot
doctor_chatbot = DoctorChatbot()

# Import forms
from forms import LoginForm, RegistrationForm

# Track medical text processing status
processing_status = {"status": "not_started", "message": "Processing not started."}

@login_manager.user_loader
def load_user(user_id):
    """Load user from database using user_id"""
    return db.session.get(User, int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form, title='Sign In')

@app.route('/logout')
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form, title='Register')

@app.route('/profile')
@login_required
def profile():
    """Display user profile"""
    medical_history = MedicalHistory.query.filter_by(user_id=current_user.id).order_by(
        MedicalHistory.timestamp.desc()).all()
    
    return render_template('profile.html', title='Profile', user=current_user, 
                          medical_history=medical_history)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', title='Medi Chat - Your Personal Medical Assistant')

@app.route('/get_response', methods=['POST'])
def get_response():
    """Process user message and return chatbot response"""
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Process the message with the chatbot
    response = doctor_chatbot.process_input(user_message)
    
    # If user is logged in, save the conversation
    if current_user.is_authenticated:
        # Create or update the conversation history
        conversation_data = {
            'user_message': user_message,
            'bot_response': response,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        medical_history = MedicalHistory(
            user_id=current_user.id,
            conversation_data=conversation_data
        )
        db.session.add(medical_history)
        db.session.commit()
    
    return jsonify({'response': response})

@app.route('/reset_conversation', methods=['POST'])
def reset_conversation():
    """Reset the chatbot conversation"""
    doctor_chatbot.reset_conversation()
    return jsonify({'status': 'success', 'message': 'Conversation reset successfully'})

def process_medical_text_background():
    """Process medical text file in background to avoid timeouts"""
    global processing_status
    try:
        processing_status = {"status": "processing", "message": "Processing medical text file..."}
        from process_medical_data import process_medical_text
        process_medical_text()
        doctor_chatbot.load_medical_data()  # Reload the data after processing
        processing_status = {"status": "completed", "message": "Medical text processing completed successfully!"}
    except Exception as e:
        processing_status = {"status": "error", "message": f"Error processing medical text: {str(e)}"}
        logger.error(f"Error in background processing: {str(e)}")

@app.route('/start_process_medical_data', methods=['POST'])
def start_process_medical_data():
    """Start processing medical text file in background"""
    global processing_status
    
    if processing_status["status"] == "processing":
        return jsonify({"status": "error", "message": "Processing already in progress"})
    
    thread = threading.Thread(target=process_medical_text_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "message": "Medical text processing started"})

@app.route('/get_medical_data_status', methods=['GET'])
def get_medical_data_status():
    """Get the current status of medical text processing"""
    global processing_status
    return jsonify(processing_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)