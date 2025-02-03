from model import ChatPrompt, db
from model.schemas import ChatPromptCreateSchema, ChatPromptResponseSchema
from langchain.chains import RetrievalQA
import uuid
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
import os
from langchain_chroma import Chroma  # ← Novo import
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


class ChatService:
    def __init__(self, ata_service, model_name: str = "deepseek-r1:1.5b"):
        self.ata_service = ata_service
        self.model_name = model_name
        self.llm = OllamaLLM(model=model_name)

    def _get_qa_chain(self, ata_id: int):
        """Cria corrente QA para uma ATA específica"""
        ata = self.ata_service.get_ata_by_id(ata_id)

        embeddings = OllamaEmbeddings(model="deepseek-r1:1.5b")
        vector_store = Chroma(
            persist_directory=os.path.join(self.ata_service.vector_store_path, "atas"),
            embedding_function=embeddings
        )

        prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="Responda com base apenas neste contexto:\n{context}\n\nPergunta: {question}"
        )

        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            chain_type_kwargs={"prompt": prompt_template}
        )

    def generate_response(self, prompt_data: ChatPromptCreateSchema) -> ChatPromptResponseSchema:
        try:
            qa_chain = self._get_qa_chain(prompt_data.ata_id)
            result = qa_chain.invoke({"query": prompt_data.pergunta})

            if isinstance(result, dict):
                resposta = result.get("result") or result.get("answer") or "Não foi possível gerar uma resposta."
            else:
                resposta = str(result)

            new_prompt = ChatPrompt(
                ata_id=prompt_data.ata_id,
                user_id=prompt_data.user_id,
                pergunta=prompt_data.pergunta,
                resposta=resposta,
                modelo_llm=self.model_name,
                sessao_id=prompt_data.sessao_id
            )

            db.session.add(new_prompt)
            db.session.commit()

            return ChatPromptResponseSchema(
                id=new_prompt.id,
                ata_id=prompt_data.ata_id,
                user_id=prompt_data.user_id,
                pergunta=prompt_data.pergunta,
                resposta=resposta,
                sessao_id=prompt_data.sessao_id,
                modelo_llm=self.model_name,
                data_interacao=new_prompt.data_interacao,
                tokens_utilizados=None,
                interaction_metadata=None
            )

        except Exception as e:
            db.session.rollback()
            print(f"Erro detalhado: {str(e)}")
            raise RuntimeError(f"Erro ao gerar resposta: {str(e)}")

    def get_chat_history(self, session_id: uuid.UUID) -> list:
        """Busca histórico de conversa por sessão"""
        return ChatPrompt.query.filter_by(sessao_id=session_id).order_by(ChatPrompt.data_interacao.asc()).all()