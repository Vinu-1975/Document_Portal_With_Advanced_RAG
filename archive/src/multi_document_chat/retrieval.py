import sys
import os
from operator import itemgetter
from typing import Optional, List

from altair.utils.html import INLINE_HTML_TEMPLATE
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS

from utils.model_loader import ModelLoader
from exception.custom_exception_archive import DocumentPortalException
from logger.custom_logger import CustomLogger
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType

class ConversationalRAG:
    def __init__(self, session_id: str = None, retriever = None):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.llm = self._load_llm()
            self.contextualize_prompt: ChatPromptTemplate = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt: ChatPromptTemplate = PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]
            if not retriever:
                raise ValueError("Retriever cannot be None")
            self.retriever = retriever
            self._build_lcel_chain()
            self.log.info("ConversationalRAG initialized with session_id: %s", self.session_id)

        except Exception as e:
            self.log.error(f"Error in ConversationalRAG __init__: {e}")
            raise DocumentPortalException("Error in ConversationalRAG __init__", sys)

    def load_retriever_from_faiss(self, index_path: str = None):
        """
        Load a FAISS vectorstore from disk and convert to retriever.
        """
        try:
            embeddings = ModelLoader().load_embedding()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"FAISS index not found in dir: {index_path}")

            vectorstore = FAISS.load_local(
                index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )

            self.retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
            self.log.info("Retriever loaded from FAISS index: %s", index_path)
            # self._build_lcel_chain()
            return self.retriever



        except Exception as e:
            self.log.error(f"Error in load_retriever_from_faiss: {e}")
            raise DocumentPortalException("Error in load_retriever_from_faiss", sys)

    def invoke(self, user_input: str, chat_history: Optional[List[BaseMessage]] = None)->str:
        try:
            chat_history = chat_history or []
            payload = {"input":user_input, "chat_history":chat_history}
            answer = self.chain.invoke(payload)
            if not answer:
                self.log.warning("No answer generated for user input: %s", user_input)
                return "no answer guaranteed"
            self.log.info("Answer generated for user input via CHAIN: %s", user_input[:150])
            return answer


        except Exception as e:
            self.log.error(f"Error in invoke: {e}")
            raise DocumentPortalException("Error in invoke", sys)
    def _load_llm(self):
        try:
            llm = ModelLoader().load_llm()
            if not llm:
                raise ValueError("LLm cannot be loaded")
            self.log.info("LLM loaded successfully")
            return llm

        except Exception as e:
            self.log.error(f"Error in _load_llm: {e}")
            raise DocumentPortalException("Error in _load_llm", sys)


    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    def _build_lcel_chain(self):
        try:
            # 1. rewrite question using chat history
            question_rewriter = (
                {"input": itemgetter("input"),"chat_history": itemgetter("chat_history")}
                | self.contextualize_prompt
                | self.llm
                | StrOutputParser()
            )
            # 2 . retrieve docs for rewritten question
            retrieve_docs = question_rewriter | self.retriever | self._format_docs
            # 3. Feed context + original input + chat history with answer prompt
            self.chain = (
                {
                    "context": retrieve_docs,
                    "input": itemgetter("input"),
                    "chat_history": itemgetter("chat_history"),

                }
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )

            self.log.info("LCEL chain built successfully")


        except Exception as e:
            self.log.error(f"Error in _build_lcel_chain: {e}")
            raise DocumentPortalException("Error in _build_lcel_chain", sys)
