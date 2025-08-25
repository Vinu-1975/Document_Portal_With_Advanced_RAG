import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Dict, Any

import fitz
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.vectorstores import FAISS

from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

log = CustomLogger().get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

def load_documents(paths: Iterable[Path])-> List[Document]:
    """Load docs using appropriate loader based on extension."""
    docs: List[Document] = []
    try:
        for p in paths:
            ext = p.suffix.lower()
            if ext == ".pdf":
                loader = PyPDFLoader(str(p))
            elif ext == ".docx":
                loader = Docx2txtLoader(str(p))
            elif ext == ".txt":
                loader = TextLoader(str(p),  encoding="utf-8")
            else:
                log.warning(f"Unsupported file type: {ext}")
                continue
            docs.extend(loader.load())
        log.info(f"Documents loaded: {len(docs)}")
        return docs
    except Exception as e:
        log.error("Error loading documents", error=str(e))
        raise DocumentPortalException("Error loading documents", e) from e



def concat_for_analysis(docs: List[Document])->str:
    parts = []
    for d in docs:
        src = d.metadata.get('source') or d.metadata.get('file_path') or "unknown"
        parts.append(f"\n==== SOURCE: {src} ====\n{d.page_content}")
    return "\n".join(parts)


def concat_for_comparison(ref_docs: List[Document], act_docs: List[Document])-> str:
    left = concat_for_analysis(ref_docs)
    right = concat_for_analysis(act_docs)
    return f"<<REFERENCE_DOCUMENTS>>\n{left}\n<<ACTUAL_DOCUMENTS>>\n{right}"