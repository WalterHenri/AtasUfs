from model import Ata, db
from model.schemas import AtaCreateSchema, AtaResponseSchema
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
import os
import logging

logger = logging.getLogger(__name__)


class AtaService:
    def __init__(self, vector_store_path: str = "./vector_store"):
        self.vector_store_path = vector_store_path
        self.embeddings = OllamaEmbeddings(model="deepseek-r1:1.5b")  # Modelo fixo

    def _validate_document(self, file_path: str):
        """Valida se o arquivo tem conteúdo legível"""
        try:
            with open(file_path, 'rb') as f:
                if f.read(10) == b'':  # Verifica se o arquivo não está vazio
                    raise ValueError("Arquivo vazio")
        except Exception as e:
            logger.error(f"Erro na validação do arquivo: {str(e)}")
            raise

    def _process_document(self, file_path: str):
        """Processa documentos com tratamento de erros"""
        try:
            self._validate_document(file_path)

            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            else:
                loader = TextLoader(file_path)

            documents = loader.load()

            if not documents:
                raise ValueError("Documento não contém texto processável")

            # Filtra documentos vazios
            valid_docs = [doc for doc in documents if doc.page_content.strip()]

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(valid_docs)

            if not chunks:
                raise ValueError("Nenhum chunk válido gerado")

            return chunks

        except Exception as e:
            logger.error(f"Erro no processamento do documento: {str(e)}")
            raise

    def create_ata(self, ata_data: AtaCreateSchema, file_path: str) -> AtaResponseSchema:
        """Cria nova ATA com verificação de embeddings"""
        try:
            chunks = self._process_document(file_path)

            # Cria diretório para vetores
            vector_dir = os.path.join(self.vector_store_path, "atas")
            os.makedirs(vector_dir, exist_ok=True)

            # Gera e valida embeddings
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=vector_dir
            )

            if vector_store._collection.count() == 0:
                raise ValueError("Falha na geração de embeddings")

            # Salva no PostgreSQL
            new_ata = Ata(
                titulo=ata_data.titulo,
                data_reuniao=ata_data.data_reuniao,
                participantes=ata_data.participantes,
                conteudo=ata_data.conteudo,
                caminho_arquivo=file_path
            )

            db.session.add(new_ata)
            db.session.commit()
            db.session.refresh(new_ata)

            return AtaResponseSchema.model_validate(new_ata)

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Erro ao criar ata: {str(e)}")

    def get_ata_by_id(self, ata_id: int) -> Ata:
        """Busca uma ATA pelo ID"""
        ata = Ata.query.get(ata_id)
        if not ata:
            raise ValueError("ATA não encontrada")
        return ata

    def search_atas(self, query: str) -> list:
        """Busca semântica nas ATAs usando vector store"""
        embeddings = OllamaEmbeddings(model="deepseek-r1:1.5b")
        vector_store = Chroma(
            persist_directory=os.path.join(self.vector_store_path, "atas"),
            embedding_function=embeddings
        )

        return vector_store.similarity_search(query, k=3)