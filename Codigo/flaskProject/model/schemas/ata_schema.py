from pydantic import BaseModel, validator
from datetime import date, datetime


class AtaCreateSchema(BaseModel):
    titulo: str
    data_reuniao: date
    participantes: list[str]
    conteudo: str
    caminho_arquivo: str

    @validator('titulo')
    def titulo_max_length(cls, v):
        if len(v) > 255:
            raise ValueError("Título não pode exceder 255 caracteres")
        return v

class AtaResponseSchema(BaseModel):
    id: int
    titulo: str
    data_reuniao: date
    participantes: list[str]
    conteudo: str
    caminho_arquivo: str
    created_at: datetime

    class Config:
        from_attributes = True 

