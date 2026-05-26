import time

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_demo.multiModal_chain import chain
from langchain_demo.tools.Image_Processing import transcribe_image
from langchain_demo.tools.Voice_Processing import transcribe_audio
from langchain_demo.tools.get_last_message import get_last_user_after_assistant
from my_llm import multiModal_llm

MAX_RECENT = 8
SUMMARY_TRIGGER = 12

_file_cache = {}

_summarize_prompt = ChatPromptTemplate.from_messages([
    ("system", "回顾以下对话，用一两句话总结用户分享的每条多媒体内容及其核心结论。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "请总结上述对话的关键信息。"),
])
_summarize_chain = _summarize_prompt | multiModal_llm


def _parse_file_block(block: dict) -> tuple[str, str]:
    f = block["file"]
    return f["path"], f.get("mime_type", "")


def _upload_file(path: str, mime: str) -> dict:
    if path in _file_cache:
        return _file_cache[path]
    for attempt in range(3):
        try:
            if "audio" in mime or path.endswith(".wav"):
                block = transcribe_audio(path)
            elif "image" in mime or path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                block = transcribe_image(path)
            else:
                return {"type": "text", "text": "[不支持的文件类型]"}
            _file_cache[path] = block
            return block
        except RuntimeError as e:
            if "Rate" in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise
        except (FileNotFoundError, OSError):
            return {"type": "text", "text": "[文件已过期，无法读取]"}


def _content_to_openai(content) -> list:
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    blocks = content if isinstance(content, list) else [content]
    result = []
    for block in blocks:
        if isinstance(block, str):
            result.append({"type": "text", "text": block})
        elif isinstance(block, dict):
            t = block.get("type", "")
            if t == "text":
                result.append({"type": "text", "text": block["text"]})
            elif t == "file":
                path, mime = _parse_file_block(block)
                result.append(_upload_file(path, mime))
    return result


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    blocks = content if isinstance(content, list) else [content]
    parts = []
    for block in blocks:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            t = block.get("type", "")
            if t == "text":
                parts.append(block["text"])
            elif t == "file":
                _, mime = _parse_file_block(block)
                parts.append(
                    "[语音消息]" if "audio" in mime else
                    "[图片消息]" if "image" in mime else
                    "[文件消息]"
                )
            elif t == "audio_url":
                parts.append("[语音消息]")
            elif t == "image_url":
                parts.append("[图片消息]")
            elif t == "video_url":
                parts.append("[视频消息]")
    return " ".join(parts)


BASE_SYSTEM_MSG = "你是一个多模态AI助手，可以处理文本、音频和图像输入。"


def _compress_history(messages: list) -> tuple[str, list]:
    if len(messages) <= SUMMARY_TRIGGER:
        return BASE_SYSTEM_MSG, messages

    old = messages[:-MAX_RECENT]
    recent = messages[-MAX_RECENT:]

    try:
        summary = _summarize_chain.invoke({"history": old}).content
    except Exception:
        summary = "; ".join(
            m.content[:100] for m in old
            if m.type == "ai" and isinstance(m.content, str)
        ) or "无早期记录"

    return f"{BASE_SYSTEM_MSG}\n早期对话摘要：{summary}", recent


def submit_message(history, session_id: str = ""):
    user_message = get_last_user_after_assistant(history)

    new_content = []
    if user_message:
        for x in user_message:
            new_content.extend(_content_to_openai(x["content"]))
    if not new_content:
        history.append({"role": "assistant", "content": "没有检测到有效输入内容。"})
        return history

    new_user_msg = HumanMessage(content=new_content)
    new_start = len(history) - len(user_message) if user_message else len(history)

    chat_history = []
    for i in range(new_start):
        msg = history[i]
        role, content = msg.get("role", ""), msg.get("content", "")
        if role == "user":
            blocks = _content_to_openai(content)
            if blocks:
                chat_history.append(HumanMessage(content=blocks))
        elif role == "assistant":
            text = _content_to_text(content)
            if text:
                chat_history.append(AIMessage(content=text))

    chat_history.append(new_user_msg)
    system_message, chat_history = _compress_history(chat_history)

    if not any(m.type == "human" for m in chat_history):
        chat_history = []
        for i in range(new_start):
            msg = history[i]
            role, content = msg.get("role", ""), msg.get("content", "")
            if role == "user":
                blocks = _content_to_openai(content)
                if blocks:
                    chat_history.append(HumanMessage(content=blocks))
            elif role == "assistant":
                text = _content_to_text(content)
                if text:
                    chat_history.append(AIMessage(content=text))
        chat_history.append(new_user_msg)
        system_message = BASE_SYSTEM_MSG

    resp = chain.invoke({"system_message": system_message, "chat_history": chat_history})
    history.append({"role": "assistant", "content": resp.content})

    if session_id:
        from langchain_demo.tools.session_store import save_message
        user_text = _content_to_text(user_message[0]["content"]) if user_message else ""
        if user_text:
            save_message(session_id, "user", user_text)
        save_message(session_id, "assistant", resp.content)

    return history
