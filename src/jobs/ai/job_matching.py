import math
from unittest import result
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
from jobs.ai.draft_proposal import draft_proposal
from jobs.models import FreelancerProfile, JobPost, Proposalai
from users.models import User
from . import services as ai_s
import numpy as np



def store_job_embedding(job_id: int, description: str) -> None:
    """Store job description in the vector database."""
    vector = ai_s.embeddings.embed_documents([description])[0]
    # Store in ChromaDB
    ai_s.jobs_collection.add(
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
        # Generate skills analysis using LangChain (using invoke instead of deprecated run)
        result = ai_s.skills_chain.invoke({"job_description": job_description})
        
        # Convert string response to dictionary (assuming proper JSON response)
        import json
        
        # Extract the text from the result
        if isinstance(result, dict) and 'text' in result:
            analysis_text = result['text']
        elif isinstance(result, str):
            analysis_text = result
        else:
            analysis_text = str(result)
        
        criteria = json.loads(analysis_text)
        
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

def get_matches_jobs(query: str, top_k: int = 20, n_results: int = 10, current_user=None) -> List[Dict]:
    """
    Get top n_results jobs for a freelancer using hybrid scoring:
    combined embedding similarity + reranker score.
    """
    # -----------------------
    # 1️⃣ Vector Search
    # -----------------------
    query_vector = ai_s.embeddings.embed_query(query)

    results = ai_s.jobs_collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "distances"]
    )

    docs = results["documents"][0]
    ids = results["ids"][0]
    distances = results["distances"][0]

    if not docs:
        return []

    # -----------------------
    # 2️⃣ Compute embedding similarity (1 - cosine distance)
    # -----------------------
    embedding_scores = [1 - d for d in distances]  # normalize to similarity 0–1

    # -----------------------
    # 3️⃣ Rerank top-k using BGE CrossEncoder
    # -----------------------
    rerank_inputs = [(query, doc) for doc in docs]
    rerank_scores = ai_s.reranker.predict(rerank_inputs)

    # -----------------------
    # 4️⃣ Normalize rerank scores to 0–1
    # -----------------------
    min_score, max_score = np.min(rerank_scores), np.max(rerank_scores)
    if max_score - min_score > 0:
        rerank_scores_norm = [(s - min_score) / (max_score - min_score) for s in rerank_scores]
    else:
        rerank_scores_norm = [0.0] * len(rerank_scores)

    # -----------------------
    # 5️⃣ Combine embedding + rerank scores
    # -----------------------
    combined_scores = [
        0.6 * emb + 0.4 * rerank
        for emb, rerank in zip(embedding_scores, rerank_scores_norm)
    ]

    # -----------------------
    # 6️⃣ Build job objects
    # -----------------------
    combined = list(zip(ids, docs, embedding_scores, rerank_scores_norm, combined_scores))
    combined.sort(key=lambda x: x[4], reverse=True)  # sort by combined_score descending

    final_results = []
    for job_id, doc, emb_score, rerank_score, combined_score in combined[:n_results]:
        try:
            job = JobPost.objects.get(id=int(job_id))
            # # Get current user from request
            # current_user = None
            # print(request)
            # if request is not None and hasattr(request, "user"):
            #     if request.user.is_authenticated:
            #         current_user = request.user
            
            # # Try to get freelancer profile if user is authenticated
            # if current_user:

            #     try:
            #         print(f"Fetching freelancer profile for user {current_user}")
            #         freelancer = FreelancerProfile.objects.get(user=current_user)
            #         draft_proposal(job, freelancer)
            #     except FreelancerProfile.DoesNotExist:
            #         print(f"No freelancer profile for user {current_user}")
            
            final_results.append({
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "budget": str(job.budget),
                "location": job.location,
                "job_type": job.job_type,
                "experience_level": job.experience_level,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "client_name": job.client.username,
                "required_skills": [s.name for s in job.required_skills.all()],
                "match_score": float(combined_score),
                "proposal_status": Proposalai.objects.filter(job=job).values('status').first().get('status') if Proposalai.objects.filter(job=job).exists() else None,
            })
        except Exception as e:
            print(f"Error processing job {job_id}: {str(e)}")
            continue
    
    # print("Final Results:", final_results)
    return final_results


    
  