from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.llms.builder import get_chat_model

# 1. 定义提示词模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个幽默的 AI 助手。请用一两句话简短回答，并带点冷幽默。"),
    ("user", "请谈谈关于 {topic} 的看法。")
])

# 2. 获取模型实例
model = get_chat_model()

# 3. 组装 LCEL 链
simple_chat_chain = prompt | model | StrOutputParser()