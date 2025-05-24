from flask import Flask, redirect, url_for
from model.database import configure_database
from routes.ata_routes import ata_bp
from routes.chat_routes import chat_bp
from service import AtaService, ChatService
from dotenv import load_dotenv # Added
import os # Added

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'ufs@2024')
app.config['UPLOAD_FOLDER'] = './uploads'

# Ensure API keys are loaded before services are initialized
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

if not openai_api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables.")
if not google_api_key:
    # Note: Gemini might not be usable if key is missing and selected
    print("Warning: GOOGLE_API_KEY not found in environment variables.")


configure_database(app)

# Pass API keys or let services pick them up from env
ata_service = AtaService()
chat_service = ChatService(ata_service) # ChatService will pick up keys from env

app.register_blueprint(ata_bp)
app.register_blueprint(chat_bp)

@app.route('/')
def home():
    return redirect(url_for('chat.new_chat'))

if __name__ == '__main__':
    # Create necessary folders if they don't exist, as per README
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('./vector_store', exist_ok=True)
    app.run(debug=True, port=5000)