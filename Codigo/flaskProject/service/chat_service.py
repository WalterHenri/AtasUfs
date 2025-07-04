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

# Novas importações para Busca Híbrida e Reranking
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.documents import Document  # Adicionado

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

        # Inicializar CrossEncoder para Reranking
        try:
            self.cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("CrossEncoder para reranking inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao inicializar CrossEncoder: {e}. Reranking pode não funcionar.", exc_info=True)
            self.cross_encoder = None

        # Inicializar BM25Retriever (para busca por palavras-chave)
        self.bm25_retriever = None
        try:
            # Busca todos os documentos (chunks) do vector store (Chroma)

            all_docs_for_bm25 = self.ata_service.get_all_docs_from_vectorstore()

            if all_docs_for_bm25 and not (len(all_docs_for_bm25) == 1 and all_docs_for_bm25[0].page_content == "empty"):
                self.bm25_retriever = BM25Retriever.from_documents(
                    documents=all_docs_for_bm25,
                    k=20  # BM25 também buscará k=20 documentos para o ensemble
                )
                logger.info(f"BM25Retriever inicializado com {len(all_docs_for_bm25)} documentos.")
            else:
                logger.warning(
                    "BM25Retriever não pôde ser inicializado (nenhum documento). Busca por palavra-chave será desabilitada.")
        except Exception as e:
            logger.error(f"Falha ao inicializar BM25Retriever: {e}. Busca por palavra-chave pode ser desabilitada.",
                         exc_info=True)
            self.bm25_retriever = None

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
        vector_store_path = self.ata_service.chroma_persistence_dir  # Usar o mesmo path

        # Carregar ChromaDB para busca vetorial (densa)
        chroma_vectorstore = Chroma(
            persist_directory=vector_store_path,
            embedding_function=self.embeddings
        )

        if chroma_vectorstore._collection.count() == 0:
            logger.warning(
                f"Chroma collection em {vector_store_path} está vazia. Busca vetorial pode não encontrar documentos.")

        chroma_retriever = chroma_vectorstore.as_retriever(search_kwargs={"k": 20})  # k=20 para busca densa

        # Configurar EnsembleRetriever para busca híbrida
        # Ponderar os resultados: 60% vetorial, 40% BM25 (ajustar conforme necessário)
        if self.bm25_retriever and chroma_vectorstore._collection.count() > 0:
            logger.info("Configurando EnsembleRetriever (Híbrido: Chroma + BM25).")
            base_retriever = EnsembleRetriever(
                retrievers=[self.bm25_retriever, chroma_retriever],
                weights=[0.4, 0.6]  # Ajuste estes pesos conforme os resultados
            )
        elif chroma_vectorstore._collection.count() > 0:
            logger.info("Configurando apenas ChromaRetriever (BM25 não disponível ou Chroma vazio).")
            base_retriever = chroma_retriever
        elif self.bm25_retriever:  # Chroma vazio, mas BM25 disponível (improvável se BM25 usa dados do Chroma)
            logger.info("Configurando apenas BM25Retriever (Chroma vazio).")
            base_retriever = self.bm25_retriever
        else:
            logger.error("Nenhum retriever base (Chroma ou BM25) pôde ser configurado. A busca falhará.")

            # Cria um retriever que não retorna nada para evitar falha na construção da cadeia
            # É melhor ter um tratamento de erro mais robusto aqui.
            class EmptyRetriever:
                def get_relevant_documents(self, query): return []

                async def aget_relevant_documents(self, query): return []

            base_retriever = EmptyRetriever()

        # Configurar Reranker
        final_retriever = base_retriever  # Default se o reranker não estiver disponível
        if self.cross_encoder:
            reranker_compressor = CrossEncoderReranker(model=self.cross_encoder, top_n=5)  # Seleciona top 5 chunks
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=reranker_compressor,
                base_retriever=base_retriever  # O base_retriever já é o ensemble (híbrido) ou o Chroma/BM25
            )
            final_retriever = compression_retriever
            logger.info("Reranking configurado sobre o retriever base.")
        else:
            logger.warning("CrossEncoder não inicializado. Reranking será pulado. Usando retriever base diretamente.")

        prompt_template_str = """
        Você é um assessor pedagógico da UFS, amigável e prestativo. Sua principal função é auxiliar com informações institucionais baseadas no material fornecido.

        Analise a "Pergunta do usuário" abaixo:

        1.  Se a pergunta for uma saudação (como "oi", "olá", "bom dia"), uma despedida, ou uma conversa casual que claramente não busca informações específicas sobre atas, documentos ou processos da UFS, responda de forma cordial e apropriada à conversa, sem se basear estritamente no "Contexto institucional".
        2.  Se a pergunta parecer ser uma consulta sobre informações institucionais, atas, documentos, ou procedimentos da UFS, siga estas diretrizes:
            a. Utilize APENAS as informações contidas no "Contexto institucional" abaixo para formular sua resposta.
            b. Se a informação solicitada não estiver presente no "Contexto institucional", responda explicitamente que a informação não foi encontrada no material disponível. Não tente adivinhar ou buscar informações fora do contexto fornecido.
            c. Apresente a resposta de forma clara e objetiva.

        Contexto institucional (material de referência para consultas específicas sobre a UFS):
        {context}

        Pergunta do usuário:
        {question}

        Sua resposta:
        """
        prompt = PromptTemplate(
            template=prompt_template_str,
            input_variables=["context", "question"]
        )
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=final_retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )


    def get_or_create_conversation(self, user_id: int, conversation_id: uuid.UUID = None,
                                   first_prompt: str = "") -> Conversation:
        """Busca uma conversa existente do usuário ou cria uma nova se o ID não for fornecido."""
        if conversation_id:
            conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
            if conversation:
                return conversation
            else:
                logger.warning(f"Conversation ID {conversation_id} not found for user {user_id}. Creating new one.")
                pass

        title = (first_prompt[:75] + '...') if len(first_prompt) > 75 else first_prompt
        if not title:  # Se o primeiro prompt for vazio ou None
            title = "Nova Conversa"

        new_conversation = Conversation(
            id=uuid.uuid4(),  # Gera um novo UUID se não for encontrado
            title=title,
            user_id=user_id
        )
        db.session.add(new_conversation)
        return new_conversation

    def generate_response(self, user_id: int, prompt_data: ChatPromptCreateSchema,
                          selected_model_identifier: str) -> ChatPromptResponseSchema:
        try:
            api_model_name = self.google_model_map.get(selected_model_identifier, selected_model_identifier)
            if selected_model_identifier in self.google_model_map and not os.getenv("GOOGLE_API_KEY"):
                raise ValueError(f"Google API Key não configurada para o modelo {api_model_name}.")
            if not os.getenv("OPENAI_API_KEY"):  #
                raise ValueError("OpenAI API Key não configurada para os embeddings.")

            conversation = self.get_or_create_conversation(
                user_id=user_id,
                conversation_id=prompt_data.conversation_id,
                first_prompt=prompt_data.pergunta
            )

            if conversation not in db.session:
                db.session.add(conversation)

            qa_chain = self._get_qa_chain(selected_model_identifier)
            result = qa_chain.invoke({"query": prompt_data.pergunta})
            resposta_text = result.get("result", "Não foi possível gerar uma resposta.")
            source_documents = result.get("source_documents", []) # Para debug ou mostrar fontes
            print(source_documents)

            new_prompt = ChatPrompt(
                conversation_id=conversation.id,
                user_id=user_id,
                pergunta=prompt_data.pergunta,
                resposta=resposta_text,
                modelo_llm=selected_model_identifier,  # Salva o modelo selecionado pelo usuário
            )

            db.session.add(new_prompt)
            db.session.commit()  # Commit da conversa e do novo prompt
            db.session.refresh(new_prompt)  # Garante que temos o ID e outros campos gerados pelo DB

            return ChatPromptResponseSchema.from_orm(new_prompt)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro detalhado ao gerar resposta para user {user_id}: {type(e).__name__} - {str(e)}",
                         exc_info=True)
            raise RuntimeError(f"Erro ao gerar resposta: {str(e)}")

    def get_conversations(self, user_id: int) -> list[ConversationResponseSchema]:
        """Busca todas as conversas do usuário especificado."""
        conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.updated_at.desc()).all()
        return [ConversationResponseSchema.from_orm(c) for c in conversations]

    def get_chat_history(self, user_id: int, conversation_id: uuid.UUID) -> list[ChatPromptResponseSchema]:
        """Busca histórico de uma conversa específica, verificando se pertence ao usuário."""
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            logger.warning(
                f"User {user_id} tentou acessar a conversa {conversation_id} que não lhe pertence ou não existe.")
            return []  # Retorna lista vazia se não encontrar ou não pertencer ao usuário

        history_orm = ChatPrompt.query.filter_by(conversation_id=conversation_id, user_id=user_id).order_by(
            ChatPrompt.data_interacao.asc()).all()
        return [ChatPromptResponseSchema.from_orm(item) for item in history_orm]