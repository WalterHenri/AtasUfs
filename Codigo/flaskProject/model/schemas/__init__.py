# model/schemas/__init__.py
from .ata_schema import AtaCreateSchema, AtaResponseSchema
from .chat_schema import ChatPromptCreateSchema, ChatPromptResponseSchema

__all__ = [
    'AtaCreateSchema',
    'AtaResponseSchema',
    'ChatPromptCreateSchema',
    'ChatPromptResponseSchema'
]