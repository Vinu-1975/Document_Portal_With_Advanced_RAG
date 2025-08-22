import sys
from pathlib import Path
import fitz
from logger.custom_logger import CustomLogger
from exception.custom_exception_archive import DocumentPortalException
from datetime import datetime
import uuid

class DocumentIngestion:
    """
    Handle saving, reading and combining of PDFs for comparison with session-based versioning.
    """
    def __init__(self, base_dir:str = "data\\document_compare", session_id=None):
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir)
        self.session_id = session_id or f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.session_path = self.base_dir / self.session_id
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.log.info(f"DocumentIngestion initialized", session = str(self.session_id))

    def save_uploaded_file(self,reference_file,actual_file):
        """
        Saves the uploaded file to the specified path.
        """
        try:
            ref_path = self.base_dir / reference_file.name
            act_path = self.base_dir / actual_file.name

            if not reference_file.name.endswith(".pdf") or not actual_file.name.endswith(".pdf"):
                raise ValueError("Only PDFs are allowed")
            
            with open(ref_path,"wb") as f:
                f.write(reference_file.getbuffer())
            with open(act_path,"wb") as f:
                f.write(actual_file.getbuffer())

            self.log.info("Files saved successfully",reference=str(ref_path), actual=str(act_path))
            return ref_path, act_path

        except Exception as e:
            self.log.error(f"Error in save_uploaded_file: {e}")
            raise DocumentPortalException("Error in save_uploaded_file", sys)


    
    def read_pdf(self, pdf_path: Path)->str:
        """
        Reads the PDF file and extract text from each page
        """
        try:
            with fitz.open(pdf_path)as doc:
                if doc.is_encrypted:
                    raise ValueError(f"PDF is encrypted : {pdf_path.name}")
                all_text = []
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()

                    if text.strip():
                        all_text.append(f"\n --- Page {page_num + 1} ---\n{text}")
                self.log.info("PDF read successfully", file=str(pdf_path),pages=len(all_text))
                return "\n".join(all_text)
        except Exception as e:
            self.log.error(f"Error in read_pdf: {e}")
            raise DocumentPortalException("Error in read_pdf", sys)


    def combine_documents(self)->str:
        try:
            content_dict = {}
            doc_parts = []

            for filename in sorted(self.base_dir.iterdir()):
                if filename.is_file() and filename.suffix == ".pdf":
                    content_dict[filename.name] = self.read_pdf(filename)
            for filename, content in content_dict.items():
                doc_parts.append(f"Document: {filename}\n{content}\n")
            return "\n".join(doc_parts)
        except Exception as e:
            self.log.error(f"Error in combine_documents: {e}")
            raise DocumentPortalException("Error in combine_documents", sys)


    def clean_old_sessions(self, keep_latest: int = 3):
        """
        Optional method to delete older session folders, keeping only the latest N.
        """
        try:
            session_folders = sorted(
                [f for f in self.base_dir.iterdir() if f.is_dir()],
                reverse=True
            )
            for folder in session_folders[keep_latest]:
                for file in folder.iterdir():
                    file.unlink()
                folder.rmdir()
                self.log.info("Old session folder deleted", folder = str(folder))

        except Exception as e:
            self.log.error(f"Error in clean_old_sessions: {e}")
            raise DocumentPortalException("Error in clean_old_sessions", sys)


