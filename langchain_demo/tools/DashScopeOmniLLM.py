from typing import Any, Iterator

from http import HTTPStatus

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from dashscope import MultiModalConversation

from env_utils import ALIYUN_API_KEY


def _convert_block_to_dashscope(block: dict) -> dict:
    block_type = block.get("type", "")
    if block_type == "text":
        return {"text": block["text"]}
    if block_type == "image_url":
        return {"image": block["image_url"]["url"]}
    if block_type == "audio_url":
        return {"audio": block["audio_url"]["url"]}
    if block_type == "video_url":
        return {"video": block["video_url"]["url"]}
    if "text" in block:
        return {"text": block["text"]}
    if "image" in block:
        return {"image": block["image"]}
    if "audio" in block:
        return {"audio": block["audio"]}
    if "video" in block:
        return {"video": block["video"]}
    return block


_ROLE_MAP = {"human": "user", "ai": "assistant", "system": "system"}


def _convert_message_to_dashscope(msg: BaseMessage) -> dict:
    role = _ROLE_MAP.get(msg.type, msg.type)

    if isinstance(msg.content, str):
        return {"role": role, "content": [{"text": msg.content}]}

    if isinstance(msg.content, list):
        content = []
        for block in msg.content:
            if isinstance(block, str):
                content.append({"text": block})
            elif isinstance(block, dict):
                content.append(_convert_block_to_dashscope(block))
        return {"role": role, "content": content}

    return {"role": role, "content": [{"text": str(msg.content)}]}


class DashScopeOmniChatModel(BaseChatModel):
    """LangChain ChatModel wrapping DashScope MultiModalConversation API.
    Supports text, image, audio, and video inputs."""

    model: str = "qwen3.5-omni-plus-2026-03-15"
    temperature: float = 1.0

    def _convert_messages(self, messages: list[BaseMessage]) -> list[dict]:
        return [_convert_message_to_dashscope(m) for m in messages]

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        dashscope_messages = self._convert_messages(messages)

        response = MultiModalConversation.call(
            model=self.model,
            messages=dashscope_messages,
            api_key=ALIYUN_API_KEY,
            temperature=self.temperature,
        )

        if response.status_code == HTTPStatus.OK:
            text = response.output.choices[0].message.content[0]["text"]
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])
        raise RuntimeError(
            f"DashScope API error: status={response.status_code}, "
            f"code={response.code}, message={response.message}"
        )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        dashscope_messages = self._convert_messages(messages)

        response_generator = MultiModalConversation.call(
            model=self.model,
            messages=dashscope_messages,
            api_key=ALIYUN_API_KEY,
            temperature=self.temperature,
            stream=True,
        )

        for chunk in response_generator:
            if chunk.status_code == HTTPStatus.OK:
                text = chunk.output.choices[0].message.content[0]["text"]
                yield ChatGenerationChunk(message=AIMessageChunk(content=text))
            else:
                raise RuntimeError(
                    f"DashScope stream error: code={chunk.code}, message={chunk.message}"
                )

    @property
    def _llm_type(self) -> str:
        return "dashscope-omni"
