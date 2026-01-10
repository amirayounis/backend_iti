from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import chromadb
from chromadb.api.types import EmbeddingFunction, Embeddings
import os
from django.conf import settings
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

# Initialize OpenAI embeddings
try:
    print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY
                                  ,model="text-embedding-3-large")
    print("Initialized OpenAI embeddings successfully.")
except Exception as e:
    raise ValueError(f"--------------Failed to initialize OpenAI embeddings: {e}")
# Create a custom embedding function wrapper for ChromaDB 0.4.16+
class OpenAIEmbeddingFunction(EmbeddingFunction):
    def __call__(self, texts):
        """
        Embed a list of texts using OpenAI embeddings.
        Automatically detects query/document usage.
        """

        if isinstance(texts, str):
            texts = [texts]

        # Detect query mode (Chroma sets this flag internally)
        is_query = hasattr(self, "_query_mode") and self._query_mode

        if is_query:
            return embeddings.embed_query(texts[0])
        else:
            return embeddings.embed_documents(texts)
# Initialize the custom embedding function
embedding_function = OpenAIEmbeddingFunction()

# Initialize ChromaDB
CHROMA_PATH = os.path.join(settings.BASE_DIR, 'chroma_db')
client = chromadb.PersistentClient(path=CHROMA_PATH)
try:
    jobs_collection = client.get_collection("jobs", embedding_function=embedding_function)
except :
    jobs_collection = client.get_or_create_collection(
        "jobs"
        , embedding_function=embedding_function
        ,metadata={"hnsw:space": "cosine"})
    
    print("Created new ChromaDB collection: jobs")

# Initialize ChatGPT model
