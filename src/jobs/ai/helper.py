import math
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import ollama
import chromadb
import os
from typing import Dict, List
from django.conf import settings
from jobs.models import JobPost
from users.models import User

class JobMatcher:    
    def __init__(self):
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-large"
        )

        # Initialize ChromaDB
        CHROMA_PATH = os.path.join(settings.BASE_DIR, 'db_chroma')
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)

        try:
            self.jobs_collection = self.client.get_collection(
                "jobs", 
                embedding_function=self.embeddings.embed_documents
            )
        except :
            self.jobs_collection = self.client.create_collection(
                "jobs",
                embedding_function=self.embeddings.embed_documents,
                metadata={"hnsw:space": "cosine"}
            )
            print("Created new ChromaDB collection: jobs")

        # Initialize ChatGPT model
        self.llm = ChatOpenAI(
            temperature=0.7,
            model_name="gpt-4o-mini",
            openai_api_key=settings.OPENAI_API_KEY
        )