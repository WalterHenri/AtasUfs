# model/__init__.py
from model.database import db, configure_database
from model.entities.ata import Ata
from model.entities.user import User
from model.entities.chat_prompt import ChatPrompt
from model.schemas.ata_schema import AtaCreateSchema, AtaResponseSchema
from model.schemas.chat_schema import ChatPromptCreateSchema, ChatPromptResponseSchema

__all__ = [
    'db',
    'configure_database',
    'Ata',
    'User',
    'ChatPrompt',
    'AtaCreateSchema',
    'AtaResponseSchema',
    'ChatPromptCreateSchema',
    'ChatPromptResponseSchema'
]