import sqlalchemy.dialects.postgresql

from ..database import db
from sqlalchemy.dialects.postgresql import JSONB


class ChatPrompt(db.Model):
    __tablename__ = 'chat_prompts'

    id = db.Column(db.Integer, primary_key=True)
    ata_id = db.Column(db.Integer, db.ForeignKey('atas.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pergunta = db.Column(db.Text, nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    modelo_llm = db.Column(db.String(50), default='llama2')
    tokens_utilizados = db.Column(db.Integer)
    data_interacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    sessao_id = db.Column(db.Uuid, nullable=False)

    interaction_metadata = db.Column(sqlalchemy.dialects.postgresql.TEXT)

    def log_interaction(self):
        return {
            "pergunta": self.pergunta,
            "resposta": self.resposta,
            "modelo": self.modelo_llm,
            "data": self.data_interacao.isoformat()
        }