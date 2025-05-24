from model import Ata, db
from model.schemas import AtaCreateSchema, AtaResponseSchema
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
import logging

logger = logging.getLogger(__name__)


class AtaService:
    def __init__(self, vector_store_path: str = "./vector_store"):
        self.vector_store_path = vector_store_path
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    def _validate_document(self, file_path: str):
        """Valida se o arquivo tem conteúdo legível"""
        try:
            if os.path.getsize(file_path) == 0:
                raise ValueError("Arquivo vazio")
        except Exception as e:
            logger.error(f"Erro na validação do arquivo {file_path}: {str(e)}")
            raise

    def _process_document(self, file_path: str):
        """Processa documentos com tratamento de erros"""
        try:
            self._validate_document(file_path)

            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith(".txt"):
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                raise ValueError("Formato de arquivo não suportado. Use PDF ou TXT.")

            documents = loader.load()

            if not documents:
                raise ValueError("Documento não contém texto processável")

            valid_docs = [doc for doc in documents if doc.page_content and doc.page_content.strip()]

            if not valid_docs:
                raise ValueError("Documento não contém conteúdo textual válido após o carregamento.")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400,
                chunk_overlap=0
            )
            chunks = text_splitter.split_documents(valid_docs)

            if not chunks:
                raise ValueError("Nenhum chunk válido gerado. Verifique o conteúdo do documento.")

            return chunks

        except Exception as e:
            logger.error(f"Erro no processamento do documento {file_path}: {str(e)}")
            if os.path.exists(file_path) and "uploads" in file_path:
                logger.info(f"Arquivo {file_path} problemático não removido automaticamente, verificar.")
            raise

    def create_ata(self, ata_data: AtaCreateSchema, file_path: str) -> AtaResponseSchema:
        """Cria nova ATA com verificação de embeddings usando OpenAI"""
        try:
            chunks = self._process_document(file_path)
            print("processou docs")
            vector_dir = os.path.join(self.vector_store_path, "atas")
            os.makedirs(vector_dir, exist_ok=True)

            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=vector_dir
            )

            if vector_store._collection.count() == 0:  # type: ignore
                if os.path.exists(file_path) and "uploads" in file_path:
                    try:
                        os.remove(file_path)
                        logger.info(f"Arquivo {file_path} removido pois falhou na geração de embeddings.")
                    except OSError as e:
                        logger.error(f"Erro ao remover arquivo {file_path} após falha de embedding: {e}")
                raise ValueError("Falha na geração de embeddings. Nenhum vetor foi criado.")

            new_ata = Ata(
                titulo=ata_data.titulo,
                conteudo=ata_data.titulo,
                caminho_arquivo=file_path
            )

            db.session.add(new_ata)
            db.session.commit()
            db.session.refresh(new_ata)

            return AtaResponseSchema.model_validate(new_ata)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar ata para {file_path}: {str(e)}")
            raise RuntimeError(f"Erro ao criar ata: {str(e)}")

    def get_ata_by_id(self, ata_id: int) -> Ata:
        """Busca uma ATA pelo ID"""
        ata = db.session.get(Ata, ata_id)
        if not ata:
            raise ValueError("ATA não encontrada")
        return ata

    def search_atas(self, query: str) -> list:
        """Busca semântica nas ATAs usando vector store com OpenAI embeddings"""
        vector_store = Chroma( # Sem from_documents aqui, apenas carregando
            persist_directory=os.path.join(self.vector_store_path, "atas"),
            embedding_function=self.embeddings
        )
        return vector_store.similarity_search(query, k=3)