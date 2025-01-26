from model import ChatPrompt, db
from model.schemas import ChatPromptCreateSchema, ChatPromptResponseSchema
from langchain.chains import RetrievalQA
import uuid
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM  # Novo pacote específico
import os  # Adicionar se faltando


class ChatService:
    def __init__(self, ata_service, model_name: str = "llama2"):
        self.ata_service = ata_service
        self.model_name = model_name
        self.llm = OllamaLLM(model=model_name)

    def _get_qa_chain(self, ata_id: int):
        """Cria corrente QA para uma ATA específica"""
        ata = self.ata_service.get_ata_by_id(ata_id)

        embeddings = OllamaEmbeddings(model="llama2")
        vector_store = Chroma(
            persist_directory=os.path.join(self.ata_service.vector_store_path, "atas"),
            embedding_function=embeddings
        )

        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever()
        )

    def generate_response(self, prompt_data: ChatPromptCreateSchema) -> ChatPromptResponseSchema:
        """Gera resposta para uma pergunta usando LLM"""
        try:
            # Obtém corrente QA
            qa_chain = self._get_qa_chain(prompt_data.ata_id)

            # Executa a consulta
            result = qa_chain.run(prompt_data.pergunta)

            # Registra a interação
            new_prompt = ChatPrompt(
                ata_id=prompt_data.ata_id,
                user_id=prompt_data.user_id,
                pergunta=prompt_data.pergunta,
                resposta=result["result"],
                modelo_llm=self.model_name,
                tokens_utilizados=result.get("tokens_used", None),
                sessao_id=prompt_data.sessao_id
            )

            db.session.add(new_prompt)
            db.session.commit()

            return ChatPromptResponseSchema(
                id=new_prompt.id,
                **prompt_data.dict(),
                resposta=new_prompt.resposta,
                tokens_utilizados=new_prompt.tokens_utilizados,
                data_interacao=new_prompt.data_interacao
            )

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Erro ao gerar resposta: {str(e)}")

    def get_chat_history(self, session_id: uuid.UUID) -> list:
        """Busca histórico de conversa por sessão"""
        return ChatPrompt.query.filter_by(sessao_id=session_id).order_by(ChatPrompt.data_interacao.asc()).all()