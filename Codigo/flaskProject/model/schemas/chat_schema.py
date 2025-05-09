# model/schemas/chat_schema.py
from pydantic import BaseModel, Field, validator, field_validator
from datetime import datetime
from typing import Optional
import uuid

class ChatPromptCreateSchema(BaseModel):
    ata_id: int
    user_id: Optional[int] = None
    pergunta: str = Field(..., min_length=3, max_length=1000)
    sessao_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    modelo_llm: str = "deepseek-r1:1.5b"

    @field_validator('pergunta')
    def pergunta_non_empty(cls, v):
        if not v.strip():
            raise ValueError("Pergunta não pode ser vazia")
        return v.strip()

class ChatPromptResponseSchema(ChatPromptCreateSchema):
    id: int
    resposta: str
    tokens_utilizados: Optional[int] = None
    data_interacao: datetime
    interaction_metadata: Optional[dict] = None

    class Config:
        json_encoders = {
            uuid.UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }