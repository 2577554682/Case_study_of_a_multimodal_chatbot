from langchain_community.chat_message_histories import SQLChatMessageHistory
from env_utils import DB_URI


def get_store(session_id: str) -> SQLChatMessageHistory:
    return SQLChatMessageHistory(session_id=session_id, connection=DB_URI)


def save_message(session_id: str, role: str, content: str) -> None:
    """持久化一条消息到PostgreSQL"""
    try:
        store = get_store(session_id)
        if role == "user":
            from langchain_core.messages import HumanMessage
            store.add_message(HumanMessage(content=content))
        elif role == "assistant":
            from langchain_core.messages import AIMessage
            store.add_message(AIMessage(content=content))
    except Exception as e:
        print(f"[DB] 保存失败（不影响对话）: {e}")


def load_history(session_id: str) -> list:
    """从PostgreSQL加载历史消息，返回[{"role":"user","content":"..."},...]"""
    try:
        store = get_store(session_id)
        result = []
        for m in store.messages:
            role = "user" if m.type == "human" else "assistant"
            content = m.content if isinstance(m.content, str) else str(m.content)
            result.append({"role": role, "content": content})
        return result
    except Exception as e:
        print(f"[DB] 加载失败（从空对话开始）: {e}")
        return []
