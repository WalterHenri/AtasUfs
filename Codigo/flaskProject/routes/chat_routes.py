from flask import Blueprint, render_template, request, jsonify, session, current_app
from service import ChatService, AtaService
from model.schemas import ChatPromptCreateSchema, ChatPromptResponseSchema
import uuid
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/', methods=['GET', 'POST'])
def chat_ata():
    if not hasattr(chat_bp, 'ata_service'):
        # Esta é uma forma de inicializar. Para apps maiores, considere factories ou injeção de dependência no __init__.py do app.
        chat_bp.ata_service = AtaService()
        chat_bp.chat_service = ChatService(chat_bp.ata_service)

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or 'pergunta' not in data:
                return jsonify({"error": "Pergunta não fornecida."}), 400

            logger.info(f"Dados recebidos para chat: {data}")

            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())

            current_session_id_str = session['session_id']
            try:
                current_session_id_uuid = uuid.UUID(current_session_id_str)
            except ValueError:
                logger.error(f"Invalid session_id in Flask session: {current_session_id_str}. Generating new one.")
                session['session_id'] = str(uuid.uuid4())
                current_session_id_uuid = uuid.UUID(session['session_id'])

            prompt_data = ChatPromptCreateSchema(
                pergunta=data['pergunta'],
                sessao_id=current_session_id_uuid
            )

            # MODIFICADO: Lista de modelos e padrão atualizados
            default_model = "gemini-1.5-flash" # Novo padrão
            valid_models = [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "ollama/deepseek-r1:1.5b"
                # Adicione outros modelos Ollama aqui se configurados
            ]
            selected_model = data.get('modelo_selecionado', default_model)
            if not selected_model or selected_model not in valid_models:
                logger.warning(f"Modelo selecionado inválido '{selected_model}', usando '{default_model}'.")
                selected_model = default_model

            logger.info(f"Processando pergunta com modelo: {selected_model}")
            response_schema = chat_bp.chat_service.generate_response(prompt_data, selected_model)

            logger.info(f"Resposta gerada: {response_schema.resposta[:100]}...")
            return response_schema.model_dump(mode='json'), 200

        except ConnectionError as ce:
            logger.error(f"Erro de conexão no endpoint de chat: {str(ce)}")
            return jsonify({"error": f"Erro de conexão com o modelo: {str(ce)}"}), 503
        except ValueError as ve: # Erros de configuração do ChatService (ex: API key, modelo não encontrado)
            logger.error(f"Erro de configuração no endpoint de chat: {str(ve)}")
            return jsonify({"error": f"Erro de configuração: {str(ve)}"}), 400 # Bad Request para erros de config
        except RuntimeError as rte: # Erros de execução do ChatService, incluindo o relançado 404
            logger.error(f"Erro de execução no endpoint de chat: {str(rte)}")
            # Mapear o erro 404 para uma mensagem mais amigável, se necessário, ou deixar como está
            if "is not found for API version" in str(rte) or "Call ListModels" in str(rte):
                 return jsonify({"error": f"O modelo selecionado não foi encontrado ou não está disponível. Verifique a configuração. Detalhes: {str(rte)}"}), 500
            return jsonify({"error": f"Ocorreu um erro interno: {str(rte)}"}), 500
        except Exception as e:
            logger.error(f"Erro inesperado no endpoint de chat: {type(e).__name__} - {str(e)}")
            return jsonify({"error": f"Ocorreu um erro interno inesperado: {str(e)}"}), 500

    chat_history_dtos = []
    if 'session_id' in session:
        try:
            session_uuid = uuid.UUID(session['session_id'])
            if hasattr(chat_bp, 'chat_service'): # Garante que o serviço está inicializado
                chat_history_dtos = chat_bp.chat_service.get_chat_history(session_uuid)
            else: # Fallback ou log de erro se o serviço não estiver pronto
                logger.error("ChatService não inicializado para buscar histórico.")
        except ValueError:
            logger.warning(f"Invalid session_id format in session: {session['session_id']}")
            session.pop('session_id', None)
        except Exception as e:
            logger.error(f"Error fetching chat history: {e}")

    return render_template('chat.html', chat_history=chat_history_dtos)