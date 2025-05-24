# Codigo/flaskProject/routes/chat_routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from pydantic import ValidationError
from service import ChatService, AtaService  # AtaService might not be directly used here anymore
from model.schemas import ChatPromptCreateSchema
import uuid
import logging
from flask_security import auth_required, current_user  # Import auth_required and current_user

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


# Helper to get chat_service instance
def get_chat_service():
    return current_app.chat_service


@chat_bp.route('/', methods=['GET'])
@auth_required()  # Protect this route
def index():
    # Redirect to new_chat which handles displaying the chat interface
    return redirect(url_for('chat.new_chat'))


@chat_bp.route('/new', methods=['GET'])
@auth_required()  # Protect this route
def new_chat():
    chat_service = get_chat_service()
    # Get conversations for the current logged-in user
    user_conversations = chat_service.get_conversations(user_id=current_user.id)
    return render_template('chat.html', conversations=user_conversations, current_chat=None, chat_history=[])


@chat_bp.route('/<uuid:conversation_id>', methods=['GET'])
@auth_required()  # Protect this route
def load_chat(conversation_id):
    chat_service = get_chat_service()
    # Get conversations for the current logged-in user
    user_conversations = chat_service.get_conversations(user_id=current_user.id)

    # Get chat history, ensuring it belongs to the current user
    chat_history = chat_service.get_chat_history(user_id=current_user.id, conversation_id=conversation_id)

    current_chat_details = None
    for conv in user_conversations:
        if conv.id == conversation_id:
            current_chat_details = conv
            break

    if not current_chat_details and chat_history:  # Should not happen if get_chat_history is strict
        logger.warning(f"User {current_user.id} accessed conversation {conversation_id} but it's not in their list.")
        # Potentially redirect or show an error if chat_history is empty due to permission check
        # For now, if history is returned, we assume it's valid.

    return render_template('chat.html',
                           conversations=user_conversations,
                           current_chat=current_chat_details,
                           chat_history=chat_history)


@chat_bp.route('/message', methods=['POST'])
@auth_required()
def post_message():
    print("oi")
    chat_service = get_chat_service()
    data = request.get_json()
    if data is None:
        print(f"Failed to decode JSON from request to /chat/message for user {current_user.id}")
        return

    try:
        pergunta = data.get('pergunta')
        if not pergunta:
            print({"error": "A pergunta não pode estar vazia."}), 400
            return

        prompt_data = ChatPromptCreateSchema(
            pergunta=pergunta,
            conversation_id=data.get('conversation_id')
        )
        selected_model = data.get('modelo_selecionado', 'gemini-1.5-flash')

        response_schema = chat_service.generate_response(
            user_id=current_user.id,
            prompt_data=prompt_data,
            selected_model_identifier=selected_model
        )

        return response_schema.model_dump(mode='json'), 200

    except ValidationError as e:
        print(f"Erro de validação Pydantic para user {current_user.id}: {e.errors()}")
        error_details = e.errors()[0]
        error_msg = f"Erro no campo '{error_details['loc'][0]}': {error_details['msg']}"
        return jsonify({"error": error_msg}), 400
    except ValueError as ve:
        print(f"Erro de valor ao postar mensagem para user {current_user.id}: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except ConnectionError as ce:
        print(f"Erro de conexão ao postar mensagem para user {current_user.id}: {str(ce)}")
        return jsonify({"error": str(ce)}), 503
    except RuntimeError as rte:
        print(f"Erro de runtime ao postar mensagem para user {current_user.id}: {str(rte)}")
        return jsonify({"error": str(rte)}), 500
    except Exception as e:
        print(f"Erro inesperado no endpoint de mensagem para user {current_user.id}: {type(e).__name__} - {str(e)}")
        return jsonify({"error": "Ocorreu um erro interno inesperado no servidor."}), 500