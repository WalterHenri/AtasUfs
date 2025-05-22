from model import ChatPrompt, db
from model.schemas import ChatPromptCreateSchema, ChatPromptResponseSchema
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
        # Mapeamento de identificadores amigáveis para nomes de modelo da API
        self.google_model_map = {
            "gemini-1.5-pro": "gemini-1.5-pro-latest",
            "gemini-1.5-flash": "gemini-1.5-flash-latest",
            # Adicione outros modelos Gemini aqui se necessário
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
            # Usa o nome do modelo mapeado para a API do Google
            api_model_name = self.google_model_map[selected_model_identifier]
            logger.info(f"Using Google Gemini model: {api_model_name} (selected as: {selected_model_identifier})")
            if not os.getenv("GOOGLE_API_KEY"):
                raise ValueError("GOOGLE_API_KEY not found in environment variables for Gemini.")
            try:
                # MODIFICADO: Removido convert_system_message_to_human
                return ChatGoogleGenerativeAI(model=api_model_name)
            except Exception as e:
                logger.error(f"Failed to initialize Google model {api_model_name}: {e}")
                # O erro 404 específico já é tratado como RuntimeError mais abaixo,
                # mas podemos adicionar um log mais específico aqui se desejado.
                # if "is not found for API version" in str(e) or "Call ListModels" in str(e):
                #     raise ValueError(f"Modelo Gemini '{api_model_name}' não encontrado ou não suportado. Verifique o nome e a disponibilidade do modelo na sua conta Google AI. Detalhes: {str(e)}")
                raise ValueError(f"Erro ao inicializar o modelo Gemini '{api_model_name}': {str(e)}")

        else:
            logger.error(f"Unsupported model identifier: {selected_model_identifier}")
            raise ValueError(f"Modelo não suportado: {selected_model_identifier}")

    def _get_qa_chain(self, selected_model_identifier: str):
        """Cria corrente QA para uma ATA específica"""
        llm = self._get_llm(selected_model_identifier)

        vector_store_path = os.path.join(self.ata_service.vector_store_path, "atas")

        if not os.path.exists(vector_store_path) or not os.listdir(vector_store_path):
            logger.warning(f"Vector store at {vector_store_path} is empty or does not exist. Upload ATAs first.")
            # Considerar levantar um erro aqui se o RAG for essencial e o vector store não existir/estiver vazio
            # raise FileNotFoundError(f"Vector store em {vector_store_path} está vazio ou não existe. Faça o upload de ATAs primeiro.")


        # MODIFICADO: A importação do Chroma já foi alterada no topo do arquivo
        vectorstore = Chroma(
            persist_directory=vector_store_path,
            embedding_function=self.embeddings
        )

        if vectorstore._collection.count() == 0:  # type: ignore
            logger.warning(f"Chroma collection at {vector_store_path} is empty. RAG may not find relevant documents.")

        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

        prompt_template_str = """
        ## QUEM 
        Você é assessor pedagógico, x
        especialista em normativas resoluções da UFS, 
        com 10+ anos de experiência. 
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

    def generate_response(self, prompt_data: ChatPromptCreateSchema,
                          selected_model_identifier: str) -> ChatPromptResponseSchema:
        try:
            # Identificador amigável para o nome real do modelo API do Google
            api_model_name = self.google_model_map.get(selected_model_identifier, selected_model_identifier)

            if selected_model_identifier in self.google_model_map and not os.getenv("GOOGLE_API_KEY"):
                raise ValueError(f"Google API Key não configurada para o modelo {api_model_name}.")
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OpenAI API Key não configurada para os embeddings.")

            qa_chain = self._get_qa_chain(selected_model_identifier) # Passa o identificador amigável

            logger.info(
                f"Invoking QA chain for question: '{prompt_data.pergunta}' with model '{api_model_name}' (selected as '{selected_model_identifier}')")
            result = qa_chain.invoke({"query": prompt_data.pergunta})

            resposta_text = "Não foi possível gerar uma resposta."
            if isinstance(result, dict):
                resposta_text = result.get("result") or result.get("answer") or resposta_text
            else:
                resposta_text = str(result) if result else resposta_text

            logger.info(f"Generated response: '{resposta_text[:100]}...'")

            new_prompt = ChatPrompt(
                user_id=prompt_data.user_id,
                pergunta=prompt_data.pergunta,
                resposta=resposta_text,
                modelo_llm=selected_model_identifier, # Salva o identificador amigável
                sessao_id=prompt_data.sessao_id
            )

            db.session.add(new_prompt)
            db.session.commit()
            db.session.refresh(new_prompt)

            return ChatPromptResponseSchema(
                id=new_prompt.id,
                user_id=prompt_data.user_id,
                pergunta=new_prompt.pergunta,
                resposta=new_prompt.resposta,
                sessao_id=new_prompt.sessao_id,
                modelo_llm=new_prompt.modelo_llm, # Retorna o identificador amigável
                data_interacao=new_prompt.data_interacao,
                tokens_utilizados=new_prompt.tokens_utilizados,
                interaction_metadata=None
            )

        except ConnectionError as ce:
            db.session.rollback()
            logger.error(f"Connection error during response generation: {str(ce)}")
            raise RuntimeError(f"Erro de conexão com o modelo LLM: {str(ce)}")
        except ValueError as ve: # Captura erros de configuração, incluindo modelo não encontrado
            db.session.rollback()
            logger.error(f"Configuration error during response generation: {str(ve)}")
            raise RuntimeError(f"Erro de configuração: {str(ve)}") # Isso irá capturar o erro 404
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro detalhado ao gerar resposta: {type(e).__name__} - {str(e)}")
            raise RuntimeError(f"Erro ao gerar resposta: {str(e)}")

    def get_chat_history(self, session_id: uuid.UUID) -> list[ChatPromptResponseSchema]:
        """Busca histórico de conversa por sessão e formata para o schema de resposta"""
        history_orm = ChatPrompt.query.filter_by(sessao_id=session_id).order_by(ChatPrompt.data_interacao.asc()).all()
        history_dto = []
        for item in history_orm:
            history_dto.append(
                ChatPromptResponseSchema(
                    id=item.id,
                    user_id=item.user_id,
                    pergunta=item.pergunta,
                    resposta=item.resposta,
                    modelo_llm=item.modelo_llm, # Retorna o identificador amigável
                    tokens_utilizados=item.tokens_utilizados,
                    data_interacao=item.data_interacao,
                    sessao_id=item.sessao_id,
                    interaction_metadata=None
                )
            )
        return history_dto