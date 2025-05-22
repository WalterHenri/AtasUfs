from ..database import db
from sqlalchemy.dialects.postgresql import ARRAY

class Ata(db.Model):
    __tablename__ = 'atas'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    caminho_arquivo = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), 
                          onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f"<Ata {self.titulo} ({self.data_reuniao})>"

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "caminho_arquivo": self.caminho_arquivo,
            "created_at": self.created_at.isoformat()
        }