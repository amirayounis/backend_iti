import json
import os
import openai
from django.conf import settings
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import CharacterTextSplitter
from jobs.models import FreelancerProfile, Skill

def read_file_content(file_path):
    """Read content from PDF or DOCX files"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            return ' '.join([page.page_content for page in pages])
        elif file_extension in ['.docx', '.doc']:
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
            return ' '.join([doc.page_content for doc in documents])
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")

def parse_cv(file_path):
    """
    Parse CV using OpenAI to extract relevant information and update FreelancerProfile
    Returns a dictionary containing extracted information
    """
    try:
        # api key past again --------------------------
        # Set OpenAI API key
        if not OPENAI_API_KEY:
            raise Exception("OpenAI API key is not configured")
        openai.api_key = OPENAI_API_KEY

        # Read the content of the CV
        cv_content = read_file_content(file_path)
        
        # Split text into manageable chunks if it's too long
        text_splitter = CharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(cv_content)
        
        # Prepare the system message
        system_message = """You are an expert CV analyzer. Extract the following information from the CV:
        1. Skills (technical and professional skills, return as a list)
        2. Years of Experience (return as a integer)
        3. Hourly Rate (estimate based on experience and skills, return as a number)
        4. Preferred Job Type (one of: full_time, part_time, contract, temporary)
        5. Categories of Expertise (one of: web_development, graphic_design, content_writing, digital_marketing, data_analysis, customer_service, other)
        6. Portfolio Website (if mentioned)
        7. LinkedIn Profile (if mentioned)
        8. GitHub Profile (if mentioned)        
        Format the response as a JSON object with these exact keys:
        {
            "skills": ["skill1", "skill2", ...],
            "experience_years": intger,
            "hourly_rate": .2f decimal,
            "job_type": "job_type_value",
            "category": "category_value",
            "portfolio_website": "url or empty string",
            "linkedin_profile": "url or empty string",
            "github_profile": "url or empty string"
        }"""
        
        # Initialize OpenAI client with API key from settings
        openai.api_key = settings.OPENAI_API_KEY
        
        # Process each chunk and combine results
        combined_analysis = {}
        for chunk in chunks:
            response = openai.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content":[ {"type":"input_text", "text": system_message}]},
                    {"role": "user", "content": [ {"type":"input_text", "text": chunk}]}
                ],
                temperature=0.3
            )
            
            # Parse the response and update combined analysis
            try:
                json_text = response.output[0].content[0].text.strip()
                # Try to find the JSON object in the text
                start_idx = json_text.find('{')
                end_idx = json_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_text = json_text[start_idx:end_idx]
                    combined_analysis = json.loads(json_text)
                    # print("888888888888888888")
                    # print(combined_analysis)
                else:
                    # print(f"No valid JSON object found in response: {json_text}")
                    continue
            except json.JSONDecodeError as e:
                # print(f"Error parsing JSON response: {str(e)}\nResponse text: {json_text}")
                continue
            except Exception as e:
                # print(f"Unexpected error processing response: {str(e)}")
                continue
      
        return combined_analysis
        
    except Exception as e:
        raise Exception(f"Error parsing CV: {str(e)}")