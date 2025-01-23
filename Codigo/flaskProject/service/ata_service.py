from model import Ata, db
from model.schemas import AtaCreateSchema, AtaResponseSchema
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
import os


class AtaService:
    def __init__(self, vector_store_path: str = "./vector_store"):
        self.vector_store_path = vector_store_path

    def _process_document(self, file_path: str):
        """Processa documentos PDF ou texto e retorna chunks"""
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)

        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        return text_splitter.split_documents(documents)

    def create_ata(self, ata_data: AtaCreateSchema, file_path: str) -> AtaResponseSchema:
        """Cria uma nova ATA e processa seu conteúdo"""
        try:
            # Processa o documento
            chunks = self._process_document(file_path)

            # Cria embeddings e armazena no ChromaDB
            embeddings = OllamaEmbeddings(model="llama2")
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=os.path.join(self.vector_store_path, "atas")
            )
            vector_store.persist()

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

            return AtaResponseSchema(**new_ata.to_dict())

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
        embeddings = OllamaEmbeddings(model="llama2")
        vector_store = Chroma(
            persist_directory=os.path.join(self.vector_store_path, "atas"),
            embedding_function=embeddings
        )

        return vector_store.similarity_search(query, k=3)