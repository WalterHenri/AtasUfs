from flask import Blueprint, render_template, request, jsonify
from service import ChatService, AtaService
from model.schemas import ChatPromptCreateSchema
import uuid

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/<int:ata_id>', methods=['GET', 'POST'])
def chat_ata(ata_id):
    ata_service = AtaService()
    chat_service = ChatService(ata_service)

    if request.method == 'POST':
        try:
            session_id = request.cookies.get('session_id', str(uuid.uuid4()))

            prompt_data = ChatPromptCreateSchema(
                ata_id=ata_id,
                pergunta=request.json['pergunta'],
                sessao_id=session_id
            )

            response = chat_service.generate_response(prompt_data)
            return jsonify({
                "resposta": response.resposta,
                "session_id": session_id
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    ata = chat_service.ata_service.get_ata_by_id(ata_id)
    return render_template('chat.html', ata=ata)