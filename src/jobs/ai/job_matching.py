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

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY
                              ,model="text-embedding-3-large")

# Initialize ChromaDB
CHROMA_PATH = os.path.join(settings.BASE_DIR, 'db_chroma')
client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    jobs_collection = client.get_collection("jobs", embedding_function=embeddings.embed_documents)
except :
    jobs_collection = client.get_collection(
        "jobs"    )
    print("Created new ChromaDB collection: jobs")

# Initialize ChatGPT model
llm = ChatOpenAI(
    temperature=0.7,
    model_name="gpt-4o-mini",
    openai_api_key=settings.OPENAI_API_KEY
)

# Prompt templates
SKILLS_ANALYSIS_TEMPLATE = """
Analyze the following job description and extract or suggest relevant skills:

Job Description:
{job_description}

Please provide:
1. A list of technical skills required
2. A list of soft skills required
3. Any additional skills that would be beneficial
4. Estimated years of experience needed
5. Recommended experience level (Junior/Mid/Senior)

Format the response as a JSON object with the following structure:
{
    "technical_skills": [],
    "soft_skills": [],
    "additional_skills": [],
    "estimated_experience_years": "X-Y years",
    "experience_level": "Junior/Mid/Senior"
}
"""

skills_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        input_variables=["job_description"],
        template=SKILLS_ANALYSIS_TEMPLATE
    )
)
CHROMA_PATH2 = os.path.join(settings.BASE_DIR, 'chroma_db')
client2 = chromadb.PersistentClient(path=CHROMA_PATH2)
# ✅ Define a callable embedding function for Chroma
def ollama_embedder(texts):
    """Generate embeddings for a list of texts using Ollama."""
    embeddings = []
    for t in texts:
        response = ollama.embeddings(model="mxbai-embed-large", prompt=t)
        embeddings.append(response["embedding"])
    return embeddings
try:
    jobs_collection2 = client2.get_collection("jobs")
except :
    jobs_collection2 = client2.create_collection("jobs", embedding_function=ollama_embedder)
def store_job_embedding_with_ollama(job_id: int, description: str) -> None:
    """Store job description in the vector database using Ollama."""
    vector = ollama.embeddings(model="mxbai-embed-large",prompt=description)["embedding"]
    # Store in ChromaDB
    print("Created new ChromaDB collection: jobs")
    jobs_collection2.add(
        documents=[description],
        metadatas=[{"job_id": str(job_id)}],
        ids=[str(job_id)],
        embeddings=[vector]
    )
def store_job_embedding(job_id: int, description: str) -> None:
    """Store job description in the vector database."""
    vector = embeddings.embed_documents([description])[0]
    # Store in ChromaDB
    jobs_collection.add(
        documents=[description],
        metadatas=[{"job_id": str(job_id)}],
        ids=[str(job_id)],
        embeddings=[vector]
    )
def remove_job_embedding(job_id: int) -> None:
    """Remove job description from the vector database."""
    jobs_collection.delete(ids=[str(job_id)])


def generate_job_criteria(job_description: str) -> Dict:
    """Generate AI criteria for a job posting."""
    try:
        # Generate skills analysis using LangChain
        analysis = skills_chain.run(job_description=job_description)
        
        # Convert string response to dictionary (assuming proper JSON response)
        import json
        criteria = json.loads(analysis)
        
        # Format the response
        return {
            'suggested_skills': {
                'technical': criteria['technical_skills'],
                'soft': criteria['soft_skills'],
                'additional': criteria['additional_skills']
            },
            'estimated_experience': criteria['estimated_experience_years'],
            'recommended_experience_level': criteria['experience_level']
        }
    except Exception as e:
        print(f"Error generating job criteria: {str(e)}")
        return {
            'suggested_skills': {'technical': [], 'soft': [], 'additional': []},
            'estimated_experience': '0-1 years',
            'recommended_experience_level': 'Junior'
        }

def get_matches_jops(query: str, n_results: int = 5) -> List[Dict]:
    # Embed the freelancer's profile query
        print("Query for job matching:", query)
        query_vector = embeddings.embed_query(query)

        # Query the vector DB
        results = jobs_collection.query(
            query_embeddings=[query_vector],
            n_results=4
        )
def get_matches_jops_ollama(query: str, n_results: int = 5) -> List[Dict]:
    # Embed the freelancer's profile query
        print("------------------------------")
        print("Query for job matching:", query)
        query_vector = ollama.embeddings(model="mxbai-embed-large", prompt=query)["embedding"]
        # Query the vector DB
        results = jobs_collection2.query(
            query_embeddings=[query_vector],
            n_results=4
        )
        # Get job IDs from metadata
        matched_ids = [r["job_id"] for r in results["metadatas"][0]]
        print("Matched Job IDs:", matched_ids)
        matched_jobs = JobPost.objects.filter(id__in=matched_ids).values()
        for job in matched_jobs:
            job["client_name"] = User.objects.get(id=job['client_id']).username
            job['skills'] = [skill.name for skill in JobPost.objects.get(id=job['id']).required_skills.all()]
            distance = results['distances'][0][matched_ids.index(str(job['id']))] if 'distances' in results else None
            alpha=0.01
            similarity = math.exp(-alpha * distance)
            job['match_score'] = similarity
            print("Job Match Score:", job['match_score'])
        # print("Matched Jobs:", matched_jobs)
        return matched_jobs

def find_matching_jobs(freelancer_skills: List[str], 
                      experience_years: int,
                      n_results: int = 5) -> List[Dict]:
    """Find matching jobs for a freelancer based on skills and experience."""
    # Create a query string from freelancer skills
    query = ", ".join(freelancer_skills)
    
    # Search in ChromaDB
    results = jobs_collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Format and return results
    matches = []
    for idx, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        matches.append({
            'job_id': metadata['job_id'],
            'title': metadata['title'],
            'relevance_score': results['distances'][0][idx] if 'distances' in results else None
        })
    
    return matches