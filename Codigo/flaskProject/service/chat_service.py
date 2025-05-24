# Codigo/flaskProject/service/chat_service.py
from model.entities.chat_prompt import ChatPrompt
from model.entities.conversation import Conversation
from model.database import db
from model.schemas.chat_schema import ChatPromptCreateSchema, ChatPromptResponseSchema, ConversationResponseSchema
from langchain.chains import RetrievalQA
import uuid
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
import os
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, ata_service, default_ollama_model: str = "deepseek-r1:1.5b"):
        self.ata_service = ata_service
        self.default_ollama_model = default_ollama_model
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.google_model_map = {
            "gemma-3": "gemma-3-27b-it",
            "gemini-1.5-pro": "gemini-1.5-pro-latest",
            "gemini-1.5-flash": "gemini-1.5-flash-latest",
        }

    def _get_llm(self, selected_model_identifier: str):
        """Initializes the selected LLM."""
        if selected_model_identifier.startswith("ollama/"):
            model_name = selected_model_identifier.split("ollama/", 1)[1]
            logger.info(f"Using Ollama model: {model_name}")
            try:
                return Ollama(model=model_name)
            except Exception as e:
                logger.error(
                    f"Failed to initialize Ollama model {model_name}: {e}. Ensure Ollama is running and the model is pulled.")
                raise ConnectionError(f"Ollama model '{model_name}' not available. Check server and model status.")
        elif selected_model_identifier in self.google_model_map:
            api_model_name = self.google_model_map[selected_model_identifier]
            logger.info(f"Using Google Gemini model: {api_model_name} (selected as: {selected_model_identifier})")
            if not os.getenv("GOOGLE_API_KEY"):
                raise ValueError("GOOGLE_API_KEY not found in environment variables for Gemini.")
            try:
                return ChatGoogleGenerativeAI(model=api_model_name)
            except Exception as e:
                logger.error(f"Failed to initialize Google model {api_model_name}: {e}")
                raise ValueError(f"Erro ao inicializar o modelo Gemini '{api_model_name}': {str(e)}")
        else:
            logger.error(f"Unsupported model identifier: {selected_model_identifier}")
            raise ValueError(f"Modelo não suportado: {selected_model_identifier}")

    def _get_qa_chain(self, selected_model_identifier: str):
        llm = self._get_llm(selected_model_identifier)
        vector_store_path = os.path.join(self.ata_service.vector_store_path, "atas")

        if not os.path.exists(vector_store_path) or not os.listdir(vector_store_path):
            logger.warning(f"Vector store at {vector_store_path} is empty or does not exist. Upload ATAs first.")
            # Consider raising an error if RAG is essential and the vector store is missing/empty.
            # For now, it will proceed but might not find relevant documents.

        vectorstore = Chroma(
            persist_directory=vector_store_path,
            embedding_function=self.embeddings
        )

        if vectorstore._collection.count() == 0:
            logger.warning(f"Chroma collection at {vector_store_path} is empty. RAG may not find relevant documents.")

        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        prompt_template_str = """
        ## QUEM 
        Você é assessor pedagógico, especialista em normativas resoluções da UFS, com 10+ anos de experiência. 
        Realizações: implantação de sistemas acadêmicos, assessoria a colegiados, revisão de 150+ atas.

        ## OBJETIVO
        Seu objetivo é: responder perguntas sobre as reuniões que ocorreram

        ## CONTEXTO
        Público-alvo: Estudantes de graduação/pós, servidores técnicos, membros de colegiados.
        Estilo: Técnico-administrativo (similar a pareceres jurídicos acadêmicos).
        Tom: Preciso + Didático (8/10 formalidade).
        Escala: Precisão 9/10, Criatividade 2/10.

        ## PERGUNTAS ANTES DA RESPOSTA
        1. A pergunta envolve interpretação de alguma resolução específica?
        2. Há menção a prazos, requisitos ou procedimentos no contexto?
        3. Existem termos técnicos que precisam de desdobramento?
        4. Qual a provável intenção prática do solicitante?
        5. Há precedentes ou exceções relevantes?

        ## INSTRUÇÕES
        - Analise o contexto completo antes de responder
        - Destaque trechos-chave entre «»
        - Em caso de ambiguidade: apresente alternativas interpretativas
        - Estruture em: Resumo Executivo > Análise Detalhada > Referências
        - Se o contexto não fornecer informações suficientes para responder à pergunta, afirme explicitamente que as informações não estão disponíveis nos documentos fornecidos. Não invente respostas.

        ## AÇÃO
        Responda à seguinte consulta acadêmica sobre as atas da UFS.
        caso o contexto não ofereça informação relevante apenas diga que não sabe:

        Contexto institucional:
        {context}

        Pergunta:
        {question}

        Siga rigorosamente esta estrutura:
        [Resumo Executivo] 
        - Objetivo da consulta 
        - Conclusão inicial 

        [Análise Detalhada]
        - resposta adequada conforme a consulta
        - Contextualização histórica (se aplicável)
        - Casos análogos registrados
        - Limitações interpretativas

        [Referências]
        - documentos oficiais citados
        """
        prompt = PromptTemplate(
            template=prompt_template_str,
            input_variables=["context", "question"]
        )
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )

    def get_or_create_conversation(self, user_id: int, conversation_id: uuid.UUID = None, first_prompt: str = "") -> Conversation:
        """Busca uma conversa existente do usuário ou cria uma nova se o ID não for fornecido."""
        if conversation_id:
            # Ensure the conversation belongs to the user
            conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
            if conversation:
                return conversation
            else: # Conversation ID provided but doesn't belong to user or doesn't exist
                  # Create a new one for this user instead of erroring or using someone else's
                  logger.warning(f"Conversation ID {conversation_id} not found for user {user_id}. Creating new one.")
                  pass # Fall through to create a new one

        # Create a new conversation
        title = (first_prompt[:75] + '...') if len(first_prompt) > 75 else first_prompt
        if not title:
            title = "Nova Conversa"

        new_conversation = Conversation(
            id=uuid.uuid4(), # Generate new UUID for the conversation
            title=title,
            user_id=user_id
        )
        db.session.add(new_conversation)
        # db.session.commit() # Commit can be done after adding the prompt as well
        return new_conversation

    def generate_response(self, user_id: int, prompt_data: ChatPromptCreateSchema,
                          selected_model_identifier: str) -> ChatPromptResponseSchema:
        try:
            api_model_name = self.google_model_map.get(selected_model_identifier, selected_model_identifier)
            if selected_model_identifier in self.google_model_map and not os.getenv("GOOGLE_API_KEY"):
                raise ValueError(f"Google API Key não configurada para o modelo {api_model_name}.")
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OpenAI API Key não configurada para os embeddings.")

            # Get or create conversation, ensuring it's associated with the current user
            conversation = self.get_or_create_conversation(
                user_id=user_id,
                conversation_id=prompt_data.conversation_id,
                first_prompt=prompt_data.pergunta
            )

            qa_chain = self._get_qa_chain(selected_model_identifier)
            result = qa_chain.invoke({"query": prompt_data.pergunta})
            resposta_text = result.get("result", "Não foi possível gerar uma resposta.")

            new_prompt = ChatPrompt(
                conversation_id=conversation.id,
                user_id=user_id, # Associate prompt with the user
                pergunta=prompt_data.pergunta,
                resposta=resposta_text,
                modelo_llm=selected_model_identifier,
            )

            db.session.add(new_prompt)
            db.session.commit() # Commit conversation (if new) and new_prompt
            db.session.refresh(new_prompt) # Refresh to get ID and other defaults

            return ChatPromptResponseSchema.from_orm(new_prompt)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro detalhado ao gerar resposta para user {user_id}: {type(e).__name__} - {str(e)}")
            raise RuntimeError(f"Erro ao gerar resposta: {str(e)}")

    def get_conversations(self, user_id: int) -> list[ConversationResponseSchema]:
        """Busca todas as conversas do usuário especificado."""
        conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.updated_at.desc()).all()
        return [ConversationResponseSchema.from_orm(c) for c in conversations]

    def get_chat_history(self, user_id: int, conversation_id: uuid.UUID) -> list[ChatPromptResponseSchema]:
        """Busca histórico de uma conversa específica, verificando se pertence ao usuário."""
        # First, verify the conversation belongs to the user
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            logger.warning(f"User {user_id} attempted to access conversation {conversation_id} not belonging to them or non-existent.")
            return [] # Or raise an error: raise PermissionError("Acesso não autorizado a esta conversa.")

        history_orm = ChatPrompt.query.filter_by(conversation_id=conversation_id, user_id=user_id).order_by(
            ChatPrompt.data_interacao.asc()).all()
        return [ChatPromptResponseSchema.from_orm(item) for item in history_orm]

