# Codigo/flaskProject/service/ata_service.py
from model import Ata, db
from model.schemas import AtaCreateSchema, AtaResponseSchema  # [cite: 19]
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document  # Import Document
import os
import logging

logger = logging.getLogger(__name__)


class AtaService:
    def __init__(self, vector_store_path: str = "./vector_store"):
        self.vector_store_path = vector_store_path
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.chroma_persistence_dir = os.path.join(self.vector_store_path, "atas")

    def _validate_document(self, file_path: str):
        """Valida se o arquivo tem conteúdo legível"""
        try:
            if os.path.getsize(file_path) == 0:
                raise ValueError("Arquivo vazio")
        except Exception as e:
            logger.error(f"Erro na validação do arquivo {file_path}: {str(e)}")
            raise

    def _process_document(self, file_path: str):
        """Processa documentos com tratamento de erros e chunking customizado"""
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

            # Separadores customizados em ordem de prioridade
            custom_separators = [
                r"(?m)^\s*\d{1,2}\)\s",  # Listas numeradas: 1) ..., 20) ...
                r"(?m)^\s*(?:X{0,3}(?:IX|IV|V|V?I{1,3})|L?X{0,3}(?:IX|IV|V|V?I{1,3}))\.\s",
                # Romanos: I., V., X., XX. etc.
                r"(?m)^\s*Item \d{1,2}\.\s",  # Listas de Itens: Item 1., Item 2. ...
                "\n\n",  # Separador padrão: Parágrafos
                "\n",  # Separador padrão: Linhas
                " ",  # Separador padrão: Espaços
                ""  # Separador padrão: Caracteres
            ]

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=200,
                separators=custom_separators,
                keep_separator=True  # Mantém o separador no início do chunk seguinte (geralmente útil)
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
            logger.info(f"Processou {len(chunks)} chunks para o arquivo {file_path}")

            vector_dir = self.chroma_persistence_dir  # Usar o atributo da classe
            os.makedirs(vector_dir, exist_ok=True)

            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=vector_dir
            )

            if vector_store._collection.count() == 0:
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
        # Este método é para uma busca direta, pode ou não ser o usado pelo ChatService agora.
        # O ChatService irá construir seu próprio retriever.
        vector_store = Chroma(
            persist_directory=self.chroma_persistence_dir,
            embedding_function=self.embeddings
        )
        return vector_store.similarity_search(query, k=3)  # k=3 é o default aqui

    def get_all_docs_from_vectorstore(self) -> list[Document]:
        """
        Busca todos os documentos (chunks) diretamente do ChromaDB.
        Usado para inicializar o BM25Retriever.
        """
        try:
            # Certifique-se que o diretório de persistência existe
            if not os.path.exists(self.chroma_persistence_dir) or not os.listdir(self.chroma_persistence_dir):
                logger.warning(
                    f"Diretório do Chroma ({self.chroma_persistence_dir}) não existe ou está vazio. Nenhum documento para BM25.")
                return [Document(page_content="empty", metadata={"source": "dummy"})]

            # Carrega o ChromaDB do diretório persistido
            chroma_instance_for_reading = Chroma(
                persist_directory=self.chroma_persistence_dir,
                embedding_function=self.embeddings  # Necessário para carregar corretamente
            )

            if chroma_instance_for_reading._collection.count() == 0:
                logger.warning("Chroma collection está vazia. Nenhum documento para BM25.")
                return [Document(page_content="empty", metadata={"source": "dummy"})]

            # Fetch all documents. Pode ser intensivo em memória para coleções muito grandes.
            retrieved_docs_dict = chroma_instance_for_reading.get(include=["documents", "metadatas"])

            langchain_documents = []
            if retrieved_docs_dict and retrieved_docs_dict.get("ids"):
                num_docs = len(retrieved_docs_dict["ids"])
                docs_content_list = retrieved_docs_dict.get("documents")
                metadatas_list = retrieved_docs_dict.get("metadatas")

                for i in range(num_docs):
                    content = docs_content_list[i] if docs_content_list and i < len(docs_content_list) else ""
                    metadata = metadatas_list[i] if metadatas_list and i < len(metadatas_list) else {}
                    # Adicionar uma verificação para garantir que metadados não sejam None
                    if metadata is None:
                        metadata = {"source": "unknown"}  # ou algum valor padrão
                    elif not isinstance(metadata, dict):
                        metadata = {"original_metadata": str(metadata)}

                    langchain_documents.append(Document(page_content=content, metadata=metadata))

            if not langchain_documents:
                logger.warning("Nenhum documento recuperado do Chroma para BM25, embora a coleção não esteja vazia.")
                return [Document(page_content="empty", metadata={"source": "dummy"})]

            logger.info(f"Buscados {len(langchain_documents)} documentos do Chroma para BM25.")
            return langchain_documents

        except Exception as e:
            logger.error(f"Erro ao buscar documentos do Chroma para BM25: {e}", exc_info=True)
            return [Document(page_content="empty", metadata={"source": "dummy"})]  # Fallback