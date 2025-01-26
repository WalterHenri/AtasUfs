from flask import Blueprint, render_template, request, redirect, url_for, flash

from model import db
from model.entities.ata import Ata
from service import AtaService
from model.schemas import AtaCreateSchema
import os

ata_bp = Blueprint('ata', __name__, url_prefix='/atas')
ata_service = AtaService()
UPLOAD_FOLDER = './uploads'


@ata_bp.route('/')
def list_atas():
    atas = Ata.query.order_by(Ata.data_reuniao.desc()).all()
    return render_template('list_atas.html', atas=atas)


from werkzeug.utils import secure_filename
import re


@ata_bp.route('/new', methods=['GET', 'POST'])
def upload_ata():
    if request.method == 'POST':
        try:
            # Validação 1: Verificar se o arquivo foi enviado
            if 'file' not in request.files:
                flash('Nenhum arquivo enviado', 'danger')
                return redirect(request.url)

            file = request.files['file']

            # Validação 2: Verificar se o nome do arquivo é válido
            if file.filename == '':
                flash('Arquivo não selecionado', 'danger')
                return redirect(request.url)

            # Validação 3: Sanitizar nome do arquivo
            filename = secure_filename(file.filename)

            # Validação 4: Verificar duplicidade de arquivo
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                flash('Já existe um arquivo com este nome', 'danger')
                return redirect(request.url)

            # Validação 5: Verificar extensão do arquivo
            allowed_extensions = {'pdf', 'txt'}
            if '.' not in filename or filename.split('.')[-1].lower() not in allowed_extensions:
                flash('Formato de arquivo inválido. Use PDF ou TXT', 'danger')
                return redirect(request.url)

            # Validação 6: Validar participantes
            participantes = request.form.getlist('participantes')
            if not participantes:
                flash('Adicione pelo menos um participante', 'danger')
                return redirect(request.url)

            # Validar formato de emails
            email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            for email in participantes:
                if not re.match(email_regex, email):
                    flash(f'Email inválido: {email}', 'danger')
                    return redirect(request.url)

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            file.save(file_path)

            ata_data = AtaCreateSchema(
                titulo=request.form['titulo'].strip(),
                data_reuniao=request.form['data_reuniao'],
                participantes=request.form.getlist('participantes'),
                conteudo="",
                caminho_arquivo=file_path
            )

            ata_service.create_ata(ata_data, file_path)
            flash('ATA cadastrada com sucesso!', 'success')
            return redirect(url_for('ata.list_atas'))

        except Exception as e:
            db.session.rollback()
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            flash(f'Erro ao cadastrar ATA: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('upload_ata.html')