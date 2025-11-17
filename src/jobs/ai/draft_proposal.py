import json
from typing import Optional
from django.conf import settings
from jobs.models import JobPost, Proposalai, FreelancerProfile  
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
import os

def draft_proposal(job: JobPost, freelancer: FreelancerProfile) -> Optional[Proposalai]:
    print(f"Drafting proposal for Job ID: {job.id} and Freelancer ID: {freelancer.id}")
    llm = ChatOpenAI(
        temperature=0.7,
        model_name="gpt-4o-mini",
        openai_api_key=settings.OPENAI_API_KEY,
        response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "proposal_output",
            "schema": {
                "type": "object",
                "properties": {
                    "cover_letter": {"type": "string"},
                    "proposed_rate": {"type": "string"},
                    "duration": {"type": "string"}
                },
                "required": ["cover_letter", "proposed_rate", "duration"]
            }
        }
    }
    )
    
    prompt = PromptTemplate(
        input_variables=["job_description", "freelancer_profile", "freelancer_rate"],
        template="""
        You are an expert proposal writer. 
        Given the job description and freelancer profile, draft a proposal including:
        1. A cover letter tailored to the job description.
        2. A proposed rate based on the job budget and freelancer hourly rate.
        3. expected duration in days to finish the job.
        Job Description:
        {job_description}
        Freelancer Profile:
        {freelancer_profile}
        Freelancer Hourly Rate: ${freelancer_rate}
        Provide the proposal in JSON format with keys: cover_letter, proposed_rate as float , duration as integer.
        """,
    )   
    chain = LLMChain(llm=llm, prompt=prompt)
    freelancer_profile_str = f"Name: {freelancer.user.get_full_name()}, Skills: {', '.join([skill.name for skill in freelancer.skills.all()])}, Experience: {freelancer.experience_years} years, Hourly Rate: ${freelancer.hourly_rate}"
    print("hhhhhhhhhhhh,")
    response = chain.invoke({
        "job_description": job.description,
        "freelancer_profile": freelancer_profile_str,
        "freelancer_rate": freelancer.hourly_rate
    })  
    print("kkkkkkkkkkkkkkkkkkk,")
    
    clean=response['text']
    print("output",response)
    # Parse JSON from the response text
    try:
        proposal_data = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from response: {str(e)}")
        print(f"Response text: {clean}")
        return None
    
    # save the proposal to the database
    try:
        proposalai = Proposalai.objects.create(
            job=job,
            freelancer=freelancer.user,
            cover_letter=proposal_data.get('cover_letter', ''),
            proposed_budget=float(proposal_data.get('proposed_rate', 0)),
            duration_in_days=int(proposal_data.get('duration', 0)),
            status='draft'
        )
        print(f"Proposal saved successfully: {proposalai.id}")
        return Response({
                    "data":proposalai,
                    "is_success":True
                }, status=status.HTTP_201_CREATED)    
    except Exception as e:
                print(f"Error saving proposal: {str(e)}")
                return None
    
    return proposalai