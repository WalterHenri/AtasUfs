from ..database import db
from sqlalchemy.dialects.postgresql import UUID


class ChatPrompt(db.Model):
    __tablename__ = 'chat_prompts'

    id = db.Column(db.Integer, primary_key=True)
    # Substitui sessao_id por uma Foreign Key para a tabela Conversations
    conversation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversations.id'), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pergunta = db.Column(db.Text, nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    modelo_llm = db.Column(db.String(50), default='llama2')
    tokens_utilizados = db.Column(db.Integer)
    data_interacao = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<ChatPrompt {self.id} for Conversation {self.conversation_id}>"