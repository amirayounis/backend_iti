from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv

def extract_skills_from_file(file_path: str) -> list:
    """
    Extracts skills from a file using LangChain and an LLM.

    Args:
        file_path (str): Path to the file to upload.
        openai_api_key (str): OpenAI API key.

    Returns:
        list: Extracted skills.
    """
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    # Define prompt template
    prompt = PromptTemplate(
        input_variables=["resume_text"],
        template="Extract a list of professional skills from the following resume:\n\n{resume_text}\n\nSkills:"        
    )

    # Initialize LLM
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = OpenAI(openai_api_key=openai_api_key, temperature=0)

    # Create chain
    chain = LLMChain(llm=llm, prompt=prompt)

    # Run chain
    result = chain.run(resume_text=file_content)

    # Parse skills (assuming comma or newline separated)
    skills = [skill.strip() for skill in result.replace('\n', ',').split(',') if skill.strip()]
    return skills