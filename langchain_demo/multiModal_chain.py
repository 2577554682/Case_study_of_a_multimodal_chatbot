from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from my_llm import multiModal_llm

prompt = ChatPromptTemplate.from_messages([
    ("system", "{system_message}"),
    MessagesPlaceholder(variable_name='chat_history'),
])

chain = prompt | multiModal_llm
