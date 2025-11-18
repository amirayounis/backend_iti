import openai
from django.conf import settings

class ConversationService:
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    @staticmethod
    def conversation():
        
        result =ConversationService.client.conversations.create(
            metadata={"topic": "interview"})
        # result is binary audio
        return result.id  
    @staticmethod
    def add_item(conversation_id,user_response):
        result =ConversationService.client.conversations.create(
            conversation_id
            ,items=[{"role": "user",
                    "content": user_response
                    ,"type": "message"}])
        return result
    @staticmethod
    def get_conversation(conversation_id):
        items = ConversationService.client.conversations.items.list(conversation_id)
        return items.data