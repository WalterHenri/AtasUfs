# model/__init__.py
from .database import db, configure_database
from .entities.ata import Ata
from .entities.user import User
from .entities.chat_prompt import ChatPrompt
from .schemas.ata_schema import AtaCreateSchema, AtaResponseSchema
from .schemas.chat_schema import ChatPromptCreateSchema, ChatPromptResponseSchema

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