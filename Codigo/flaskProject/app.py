from flask import Flask, redirect, url_for
from model.database import configure_database
from routes.ata_routes import ata_bp
from routes.chat_routes import chat_bp
from service import AtaService, ChatService

app = Flask(__name__)
app.secret_key = 'ufs@2024'
app.config['UPLOAD_FOLDER'] = './uploads'

configure_database(app)

ata_service = AtaService()  # Adicionar inicialização
chat_service = ChatService(ata_service)  # Passar o serviço correto

app.register_blueprint(ata_bp)
app.register_blueprint(chat_bp)

@app.route('/')
def home():
    return redirect(url_for('ata.list_atas'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)