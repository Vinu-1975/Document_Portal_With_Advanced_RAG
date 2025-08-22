import os
import sys
from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception_archive import DocumentPortalException
from model.models import *
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from prompt.prompt_library import PROMPT_REGISTRY


class DocumentAnalyzer:
    """
    Analyzes the document using a pre-trained model.
    Automatically logs all actions and support session-based organization.
    """

    def __init__(self) -> None:
        self.log = CustomLogger().get_logger(__name__)
        try:
            self.loader = ModelLoader()
            self.llm = self.loader.load_llm()

            self.parser = JsonOutputParser(pydantic_object=Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(
                parser=self.parser, llm=self.llm
            )

            self.prompt = PROMPT_REGISTRY["document_analysis"]

            self.log.info("DocumentAnalyzer initialized successfully")

        except Exception as e:
            self.log.error(f"Error initializing Document Analyzer:{e}")
            raise DocumentPortalException("Error in DocumentAnalyzer init", sys)

    def analyze_document(self, document_text: str) -> dict:
        """
        Analyzes the document's text and extract structured metadata and summary
        """
        try:
            chain = self.prompt | self.llm | self.fixing_parser
            self.log.info("Metadata analysis chain initialized")

            response = chain.invoke(
                {
                    "format_instructions": self.parser.get_format_instructions(),
                    "document_text": document_text,
                }
            )
            self.log.info("Metadata extraction successful",keys = list(response.keys()))
            return response
        except Exception as e:
            self.log.error(f"Error in analyze_document:{e}")
            raise DocumentPortalException("Error in analyze_document", sys)
