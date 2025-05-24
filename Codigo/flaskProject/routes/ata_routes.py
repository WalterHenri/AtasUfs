# Codigo/flaskProject/routes/ata_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from model.database import db
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
    if not hasattr(ata_bp, 'ata_service'):
        ata_bp.ata_service = AtaService()

    chat_service = ChatService(ata_bp.ata_service)

    if request.method == 'POST':
        file_path_for_cleanup = None
        try:
            # Validação 1: Verificar se o arquivo foi enviado
            if 'file' not in request.files:
                flash('Nenhum arquivo enviado.', 'warning')
                return redirect(request.url)

            file = request.files['file']

            # Validação 2: Verificar se o nome do arquivo é válido
            if file.filename == '':
                flash('Arquivo não selecionado.', 'warning')
                return redirect(request.url)

            titulo = request.form.get('titulo', '').strip()
            if not titulo:
                flash('O título da reunião é obrigatório.', 'danger')
                return redirect(request.url)

            # Validação 3: Sanitizar nome do arquivo
            original_filename = file.filename
            filename = secure_filename(original_filename)
            if not filename:  # secure_filename might return empty if original_filename is just dots, etc.
                flash(f'Nome de arquivo inválido: {original_filename}', 'danger')
                return redirect(request.url)

            # Validação 5: Verificar extensão do arquivo
            allowed_extensions = {'pdf', 'txt'}
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            if file_ext not in allowed_extensions:
                flash(f'Formato de arquivo inválido ({file_ext}). Use PDF ou TXT.', 'danger')
                return redirect(request.url)

            upload_dir = current_app.config.get('UPLOAD_FOLDER', './uploads')  # Get from app config
            os.makedirs(upload_dir, exist_ok=True)  # Ensure upload folder exists

            file_path = os.path.join(upload_dir, filename)
            file_path_for_cleanup = file_path  # Assign for potential cleanup

            # Validação 4: Verificar duplicidade de arquivo (antes de salvar)
            if os.path.exists(file_path):
                flash(f'Já existe um arquivo com o nome "{filename}". Renomeie o arquivo ou envie um novo.', 'danger')
                return redirect(request.url)

            file.save(file_path)
            logger.info(f"Arquivo '{filename}' salvo em '{file_path}'.")

            # O campo 'conteudo' em AtaCreateSchema não é mais preenchido diretamente com ""
            # Ele será populado pelo AtaService a partir do conteúdo processado do arquivo.
            ata_data = AtaCreateSchema(
                titulo=titulo,
                conteudo="",  # Será preenchido pelo service
                caminho_arquivo=file_path  # O service usará este caminho para ler e processar
            )

            # Use the service instance
            ata_bp.ata_service.create_ata(ata_data, file_path)  # Pass file_path for processing
            flash('ATA cadastrada e processada com sucesso!', 'success')
            return redirect(url_for('ata.list_atas'))

        except ValueError as ve:  # Catch validation errors from service (e.g., empty doc, embedding fail)
            db.session.rollback()
            logger.error(f"Erro de validação ao cadastrar ATA: {str(ve)}")
            flash(f'Erro de validação ao cadastrar ATA: {str(ve)}', 'danger')
            if file_path_for_cleanup and os.path.exists(
                    file_path_for_cleanup) and "Falha na geração de embeddings" not in str(ve):
                # Only remove if it's not already handled by the service for embedding failures
                # os.remove(file_path_for_cleanup)
                logger.info(
                    f"Arquivo {file_path_for_cleanup} não removido automaticamente após erro de validação, verificar.")
            return redirect(request.url)
        except RuntimeError as rte:  # Catch runtime errors from service (more general)
            db.session.rollback()
            logger.error(f"Erro de execução ao cadastrar ATA: {str(rte)}")
            flash(f'Erro de execução ao cadastrar ATA: {str(rte)}', 'danger')
            # Service might handle file cleanup on its own errors; double-check logic if needed
            return redirect(request.url)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao cadastrar ATA: {type(e).__name__} - {str(e)}")
            # import traceback
            # logger.error(traceback.format_exc())
            flash(f'Erro inesperado ao cadastrar ATA: {str(e)}', 'danger')
            if file_path_for_cleanup and os.path.exists(file_path_for_cleanup):
                # Generic error, might be good to clean up the saved file if something went wrong after save but before DB commit
                # os.remove(file_path_for_cleanup)
                logger.info(
                    f"Arquivo {file_path_for_cleanup} não removido automaticamente após erro inesperado, verificar.")
            return redirect(request.url)
    conversations = chat_service.get_conversations()
    return render_template('upload_ata.html', conversations=conversations)


