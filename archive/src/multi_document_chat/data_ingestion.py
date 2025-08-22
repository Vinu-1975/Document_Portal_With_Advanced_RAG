
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from utils.model_loader import ModelLoader 
from logger.custom_logger import CustomLogger
from exception.custom_exception_archive import DocumentPortalException

class DocumentIngestor:
    SUPPORTED_FILE_TYPES = {".pdf", ".docx", ".txt", ".md"}

    def __init__(
        self,
        temp_dir: str = "data/multi_document_chat",
        faiss_dir: str = "faiss_index",
        session_id: str | None = None,
    ):
        try:
            self.log = CustomLogger().get_logger(__name__)

            #base dir
            self.temp_dir = Path(temp_dir)
            self.faiss_dir = Path(faiss_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)

            #sessionized path
            self.session_id = session_id or f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            self.session_temp_dir = self.temp_dir / self.session_id
            self.session_temp_dir.mkdir(parents=True, exist_ok=True)
            self.session_faiss_dir = self.faiss_dir / self.session_id
            self.session_faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()
            self.log.info(
                "DocumentIngestor initialized",
                temp_path=str(self.session_temp_dir),
                faiss_path=str(self.session_faiss_dir),
            )


        except Exception as e:
            self.log.error(f"Error in DocumentIngestor __init__: {e}")
            raise DocumentPortalException("Error in DocumentIngestor __init__", sys)

    def ingest_files(self, uploaded_files):

        try:
            documents = []
            for uploaded_file in uploaded_files:
                ext = Path(uploaded_file.name).suffix.lower()
                if ext not in self.SUPPORTED_FILE_TYPES:
                    self.log.warning(f"Unsupported file type: {ext}")
                    continue
                unique_filename = f"{uuid.uuid4().hex[:8]}{ext}"
                temp_path = self.session_temp_dir / unique_filename

                with open(temp_path,"wb") as f:
                    f.write(uploaded_file.read())
                self.log.info("File saved for ingestion", filename=uploaded_file.name, path=str(temp_path), session_id = self.session_id)

                if ext == ".pdf":
                    loader = PyPDFLoader(str(temp_path))
                elif ext == ".docx":
                    loader = Docx2txtLoader(str(temp_path))
                else:
                    loader = TextLoader(str(temp_path))
                docs = loader.load()
                documents.extend(docs)
                if not documents:
                    raise DocumentPortalException("No valid documents loaded for ingestion", sys)

                self.log.info("All documents loaded", count=len(documents))
            return self._create_retriever(documents)


        except Exception as e:
            self.log.error(f"Error in ingest_files: {e}")
            raise DocumentPortalException("Error in ingest_files", sys)

    def _create_retriever(self, documents):
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=300
            )
            split_docs = splitter.split_documents(documents)
            self.log.info("Documents split into chunks", count=len(split_docs))
            embeddings = self.model_loader.load_embedding()
            vectorstore = FAISS.from_documents(
                split_docs, embeddings
            )
            vectorstore.save_local(str(self.session_faiss_dir))
            self.log.info("Retriever created and saved", session_id=self.session_id, count=len(split_docs))

            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={'k': 5})

            self.log.info("Retriever created", session_id=self.session_id)

            return retriever

        except Exception as e:
            self.log.error(f"Error in _create_retriever: {e}")
            raise DocumentPortalException("Error in _create_retriever", sys)

