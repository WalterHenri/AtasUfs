# Codigo/flaskProject/routes/ata_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
# Adicione a importação do ChatService para buscar as conversas
from service import AtaService, ChatService
from model.schemas import AtaCreateSchema
from model.entities.ata import Ata
import os
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)
ata_bp = Blueprint('ata', __name__, url_prefix='/atas')


@ata_bp.route('/')
def list_atas():
    try:
        # Inicialize os serviços
        chat_service = ChatService(AtaService())

        # Busque as conversas para a sidebar
        conversations = chat_service.get_conversations()
        atas_orm = Ata.query.order_by(Ata.created_at.desc()).all()

        # Passe as conversas para o template
        return render_template('list_atas.html', atas=atas_orm, conversations=conversations)
    except Exception as e:
        logger.error(f"Erro ao listar ATAs: {e}")
        flash('Não foi possível carregar a lista de ATAs.', 'danger')
        # Passe uma lista vazia em caso de erro para não quebrar a sidebar
        return render_template('list_atas.html', atas=[], conversations=[])


@ata_bp.route('/new', methods=['GET', 'POST'])
def upload_ata():
    # Inicialize os serviços
    ata_service = AtaService()
    chat_service = ChatService(ata_service)

    if request.method == 'POST':
        # ... (a lógica do POST permanece a mesma) ...
        try:
            # Lógica de upload e criação da ATA
            # ...
            flash('ATA cadastrada e processada com sucesso!', 'success')
            return redirect(url_for('ata.list_atas'))
        except Exception as e:
            # ... (tratamento de erros permanece o mesmo) ...
            return redirect(request.url)

    # Para a requisição GET, busque e passe as conversas
    conversations = chat_service.get_conversations()
    return render_template('upload_ata.html', conversations=conversations)