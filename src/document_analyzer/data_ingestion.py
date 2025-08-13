import os
import fitz  # a wrapper on top of pypdf
import uuid  # to create unique id(s) universally [Universal Unique ID]
from datetime import datetime
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
import sys


class DocumentHandler:
    """
    Handles pdf saving and reading operations.
    Automatically logs all actions and support session-based organization
    """

    def __init__(self, data_dir=None, session_id=None):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.data_dir = data_dir or os.getenv(
                "DATA_STORAGE_PATH", os.path.join(os.getcwd(), "data", "document_analysis")
            )
            self.session_id = session_id or f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{(uuid.uuid4().hex[:8])}"

            self.session_path = os.path.join(self.data_dir,self.session_id)
            os.makedirs(self.session_path,exist_ok=True)

            self.log.info("PDFHandler initialized", session_id=session_id,session_path = self.session_path)
        except Exception as e:
            self.log.error("Error initializing PDFHandler",error = str(e))
            raise DocumentPortalException("Failed to initialize PDFHandler", e) from e



    def save_pdf(self, uploaded_file):
        """
        Saves the pdf file to the session directory.
        Returns the unique file name.
        """
        try:
            filename = os.path.basename(uploaded_file.name)
            if not filename.lower().endswith('.pdf'):
                raise DocumentPortalException("Uploaded file is not a PDF", sys)
            save_path = os.path.join(self.session_path,filename)
            with open(save_path,'wb')as f:
                f.write(uploaded_file.getbuffer())
            self.log.info("PDF saved successfully", file = filename, save_path = save_path, session_id = self.session_id)
            return save_path

        except Exception as e:
            self.log.error("Error saving PDF", error=str(e))
            raise DocumentPortalException("Failed to save PDF", e) from e


    def read_pdf(self, pdf_path):
        """
        Reads the pdf file from the session directory.
        Returns the pdf file content.
        """
        try:
            text_chunks = []
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc,start = 1):
                    text_chunks.append(f"\n--- Page {page_num} ---\n{page.get_text()}")
            text = "\n".join(text_chunks)
            self.log.info("PDF read successfully",pdf_path = pdf_path, session_id = self.session_id)
            return text
        except Exception as e:
            self.log.error("Error reading PDF", error=str(e))
            raise DocumentPortalException("Failed to read PDF", e) from e

if __name__ == "__main__":
    from pathlib import Path # creates a system compatible path
    from io import BytesIO

    pdf_path = r"D:\\Gen AI\\LLMOPS\\P1_DOCUMENT_PORTAL\\data\\document_analysis\\NIPS-2017-attention-is-all-you-need-Paper.pdf"

    class DummyFile:
        def __init__(self,file_path):
            self.name = Path(file_path).name
            self.file_path = file_path
        def getbuffer(self):
            return open(self.file_path,'rb').read()

    dummy_file = DummyFile(pdf_path)
    handler = DocumentHandler()

    try:
        saved_path = handler.save_pdf(dummy_file)
        print(saved_path)

        content = handler.read_pdf(saved_path)
        print(content[:500])
    except Exception as e:
       print(f"Error: {e}")




    # print(f"Session ID: {handler.session_id}")
    # print(f"Session Path: {handler.session_path}")

