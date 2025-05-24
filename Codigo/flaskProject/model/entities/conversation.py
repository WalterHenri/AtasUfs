# model/entities/conversation.py
import uuid
from ..database import db

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.dialects.postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    prompts = db.relationship('ChatPrompt', backref='conversation', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation {self.title}>"