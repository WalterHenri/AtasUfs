# model/schemas/chat_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


class ConversationResponseSchema(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatPromptCreateSchema(BaseModel):
    pergunta: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[uuid.UUID] = None  # ID da conversa existente, ou None para criar uma nova


class ChatPromptResponseSchema(BaseModel):
    id: int
    conversation_id: uuid.UUID
    pergunta: str
    resposta: str
    modelo_llm: str
    data_interacao: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }