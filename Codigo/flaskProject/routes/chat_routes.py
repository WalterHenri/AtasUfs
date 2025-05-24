# routes/chat_routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from service import ChatService, AtaService
from model.schemas import ChatPromptCreateSchema
import uuid
import logging

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


# Rota principal que redireciona para uma nova conversa
@chat_bp.route('/', methods=['GET'])
def index():
    return redirect(url_for('chat.new_chat'))


# Rota para iniciar uma nova conversa
@chat_bp.route('/new', methods=['GET'])
def new_chat():
    chat_service = ChatService(AtaService())
    conversations = chat_service.get_conversations()
    return render_template('chat.html', conversations=conversations, current_chat=None, chat_history=[])


# Rota para carregar uma conversa existente
@chat_bp.route('/<uuid:conversation_id>', methods=['GET'])
def load_chat(conversation_id):
    chat_service = ChatService(AtaService())
    conversations = chat_service.get_conversations()
    chat_history = chat_service.get_chat_history(conversation_id)
    current_chat = next((c for c in conversations if c.id == conversation_id), None)

    return render_template('chat.html', conversations=conversations, current_chat=current_chat,
                           chat_history=chat_history)


# Endpoint da API para enviar mensagens
@chat_bp.route('/message', methods=['POST'])
def post_message():
    chat_service = ChatService(AtaService())
    data = request.get_json()

    try:
        prompt_data = ChatPromptCreateSchema(
            pergunta=data.get('pergunta'),
            conversation_id=data.get('conversation_id')  # Pode ser None
        )
        selected_model = data.get('modelo_selecionado', 'gemini-1.5-flash')

        response_schema = chat_service.generate_response(prompt_data, selected_model)
        print(selected_model)

        return response_schema.model_dump(mode='json'), 200

    except Exception as e:
        logger.error(f"Erro inesperado no endpoint de mensagem: {str(e)}")
        return jsonify({"error": f"Ocorreu um erro interno: {str(e)}"}), 500