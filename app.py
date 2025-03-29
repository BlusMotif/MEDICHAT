import os
import logging
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from chatbot import DoctorChatbot
from text_processor import MedicalTextProcessor
from process_african_diseases import process_african_diseases
from models import db, User, MedicalHistory
from forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database with the app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user from database using user_id"""
    return User.query.get(int(user_id))

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin_exists = User.query.filter_by(username='admin').first()
    if not admin_exists:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('adminpassword')
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created successfully")

# Initialize chatbot
chatbot = DoctorChatbot()

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        
        # Safely handle the next page redirect - make sure it's relative to our app
        if not next_page or next_page.startswith('//') or '://' in next_page:
            next_page = url_for('index')
            
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)
        
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html', title='Register', form=form)


@app.route('/profile')
@login_required
def profile():
    """Display user profile"""
    # Fetch user's medical history
    history = MedicalHistory.query.filter_by(user_id=current_user.id).order_by(MedicalHistory.timestamp.desc()).all()
    return render_template('profile.html', title='Profile', history=history)


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
        
        # If user is authenticated, save this conversation to their history
        if current_user.is_authenticated:
            # Save chat history
            conversation_data = {
                "user_message": user_message,
                "bot_response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            history_entry = MedicalHistory(
                user_id=current_user.id,
                conversation_data=conversation_data
            )
            
            db.session.add(history_entry)
            db.session.commit()
            logger.debug(f"Saved chat history for user {current_user.username}")
        
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
        success = process_african_diseases()  # Using existing function for compatibility
        
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

@app.route('/process_african_diseases', methods=['POST'])
def start_process_african_diseases():
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

@app.route('/african_diseases_status', methods=['GET'])
def get_african_diseases_status():
    """Get the current status of medical text processing"""
    return jsonify(text_processing_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
