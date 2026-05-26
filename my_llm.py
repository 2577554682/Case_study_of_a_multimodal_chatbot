import dashscope

from env_utils import ALIYUN_API_KEY
from langchain_demo.tools.DashScopeOmniLLM import DashScopeOmniChatModel

dashscope.api_key = ALIYUN_API_KEY

multiModal_llm = DashScopeOmniChatModel(
    model='qwen3.5-omni-plus-2026-03-15',
    temperature=1,
)
