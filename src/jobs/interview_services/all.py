from langchain import init_chat_model
from langchain_core.runnables import RunnableSequence
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
speech_to_text = init_chat_model("whisper-1")      
moderation = init_chat_model("moderation-latest")            
chat_llm = init_chat_model("gpt-4.1")   
text_to_speech = init_chat_model("tts-1")     

# --- Build pipeline ---
voice_chat_pipeline = (
    speech_to_text
    | moderation
    | (lambda text: HumanMessage(content=text))
    | chat_llm
    | moderation
    | text_to_speech
)

llm = init_chat_model("gpt-4.1")

# --- Template for structured reports ---
report_prompt = ChatPromptTemplate.from_messages([
    ("system", ""),
    ("human", "Generate a detailed report from the following data:\n{data}")
])

report_chain = (
    (lambda data: {"data": data})
    | report_prompt
    | llm
)