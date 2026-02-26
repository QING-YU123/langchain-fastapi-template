from langchain_openai import ChatOpenAI
from app.core.config import settings

def get_chat_model() -> ChatOpenAI:
    """实例化并返回第三方大模型"""
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base,
        model=settings.model_name,
        temperature=0.7,
    )