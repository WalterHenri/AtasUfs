# model/schemas/chat_schema.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class ChatPromptCreateSchema(BaseModel):
    user_id: Optional[int] = None
    pergunta: str = Field(..., min_length=1, max_length=2000) # Adjusted min_length
    sessao_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    # modelo_llm is removed from here; it will be passed as a separate parameter to the service

    @field_validator('pergunta')
    def pergunta_non_empty(cls, v):
        if not v.strip():
            raise ValueError("Pergunta não pode ser vazia")
        return v.strip()

class ChatPromptResponseSchema(BaseModel): # No longer inherits from CreateSchema directly for this field
    id: int
    user_id: Optional[int] = None
    pergunta: str
    resposta: str
    modelo_llm: str # Model that was used for the response
    tokens_utilizados: Optional[int] = None
    data_interacao: datetime
    sessao_id: uuid.UUID
    interaction_metadata: Optional[Dict[str, Any]] = None # Changed from Optional[dict]

    class Config:
        from_attributes = True # Updated from orm_mode for Pydantic v2
        json_encoders = { # Kept for compatibility, though Pydantic v2 handles UUID/datetime well
            uuid.UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }