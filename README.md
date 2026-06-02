# 多模态 AI 助手

基于 **Qwen3.5-Omni** 多模态大模型的智能对话应用，支持文本、图片、音频、视频输入，对话历史自动持久化至 PostgreSQL。

## 架构

```
用户 (浏览器)
    │
    ▼
┌──────────────────────────────────────┐
│  Gradio Web UI (langchain_demo/tools/) │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ Chat UI  │  │ 文件上传          │  │
│  │ (聊天界面) │  │ (图片/音频/视频)  │  │
│  └────┬─────┘  └────────┬─────────┘  │
└───────┼─────────────────┼────────────┘
        │                 │
        ▼                 ▼
┌──────────────────────────────────────────┐
│             消息处理流程                    │
│                                          │
│  Add_Message.py       消息格式化 & 追加    │
│       │                                   │
│       ▼                                   │
│  Submit_Message.py    消息处理 & 摘要压缩   │
│       │                                   │
│       ├── Image_Processing.py   图片→Base64 │
│       ├── Voice_Processing.py   音频→DashScope │
│       └── get_last_message.py  消息提取     │
│       │                                   │
│       ▼                                   │
│  multiModal_chain.py    LangChain 链调用   │
│       │                                   │
│       ▼                                   │
│  DashScopeOmniLLM.py    自定义 DashScope    │
│                          LLM 封装           │
│       │                                   │
│       ▼                                   │
│  DashScope API (Qwen3.5-Omni)             │
└──────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│  PostgreSQL               │
│  (session_store.py)       │
│  对话历史持久化 + 加载     │
└──────────────────────────┘
```

## 功能

| 功能 | 说明 |
|---|---|
| **文本对话** | 自然语言多轮对话 |
| **图片分析** | 上传 JPG/PNG/WebP，Base64 编码后送入多模态模型分析 |
| **音频识别** | 上传 WAV，通过 DashScope Files API 转写为远程 URL 后处理 |
| **多文件上传** | 同时上传多张图片/多个音频文件 |
| **对话持久化** | 基于 `SQLChatMessageHistory` 自动保存至 PostgreSQL |
| **长对话摘要** | 超过 12 轮自动压缩早期对话为摘要，保留最近 8 轮完整上下文 |
| **流式输出** | 基于 DashScope 流式 API 逐 token 输出响应 |
| **自定义 UI** | Gradio 靛蓝色主题 + 聊天气泡 CSS 美化 + JS 防闪烁 |

## 技术栈

| 层 | 技术 |
|---|---|
| **前端** | Gradio + 自定义 CSS/JS |
| **多模态 LLM** | 阿里云 DashScope — Qwen3.5-Omni |
| **框架** | LangChain (`ChatPromptTemplate` + BaseChatModel 封装) |
| **数据库** | PostgreSQL + `SQLChatMessageHistory` |
| **可观测** | LangSmith（可选） |

## 快速开始

### 前置要求

- Python 3.10+
- 阿里云 DashScope API Key（[开通](https://bailian.console.aliyun.com/)）
- PostgreSQL 数据库

### 安装

```bash
git clone https://github.com/2577554682/Case_study_of_a_multimodal_chatbot.git
cd Case_study_of_a_multimodal_chatbot

pip install gradio langchain langchain-core langchain-community dashscope python-dotenv
```

### 配置

```bash
cp .env.example .env
```

编辑 `.env` 填入配置：

| 变量 | 必填 | 说明 |
|---|---|---|
| `ALIYUN_API_KEY` | 是 | DashScope API 密钥 |
| `DB_URI` | 是 | PostgreSQL 连接串，如 `postgresql://user:pass@localhost:5432/dbname` |
| `LANGSMITH_API_KEY` | 否 | LangSmith 追踪（可选） |

### 启动

```bash
python langchain_demo/tools/gradio_web_ui_2.py
```

浏览器访问 `http://localhost:7860`。

## 项目结构

```
Case_study_of_a_multimodal_chatbot/
├── langchain_demo/
│   ├── __init__.py
│   ├── multiModal_chain.py              # LangChain Chain 定义
│   └── tools/
│       ├── __init__.py
│       ├── gradio_web_ui_2.py           # 主入口 — Gradio Web UI
│       ├── Add_Message.py               # 用户消息格式化 & 追加
│       ├── Submit_Message.py            # 核心处理 & 自动摘要
│       ├── session_store.py             # PostgreSQL 持久化
│       ├── DashScopeOmniLLM.py          # DashScope 多模态 LLM 封装
│       ├── Image_Processing.py          # 图片 → Base64 处理
│       ├── Voice_Processing.py          # 音频 → DashScope 远程 URL
│       └── get_last_message.py          # 最新用户消息提取
├── env_utils.py                         # 环境变量加载
├── my_llm.py                            # LLM 实例初始化
├── .env.example                         # 环境变量模板
├── .gitignore
└── README.md
```

## 核心模块说明

### DashScopeOmniLLM — 自定义 LLM 封装

`langchain_demo/tools/DashScopeOmniLLM.py` 实现了 LangChain 的 `BaseChatModel` 接口，将 DashScope 多模态 API 适配为 LangChain 兼容的 ChatModel。核心能力：

- **多模态内容转换** — 将 LangChain 标准 `HumanMessage` 中的 `text`、`image_url`、`audio_url`、`video_url` 块转换为 DashScope API 格式
- **流式支持** — 实现 `_stream` 方法，支持逐 token 输出
- **批量生成** — 实现 `_generate` 方法，支持一次性完整响应

### 多媒体处理流程

```
用户上传图片
    │
    ▼
Image_Processing.py  →  PIL 读取 → Base64 编码 → data URI
    │
    ▼
DashScope API → Qwen3.5-Omni 分析

用户上传音频
    │
    ▼
Voice_Processing.py  →  DashScope Files.upload → 获取远程 URL
    │
    ▼
DashScope API → Qwen3.5-Omni 识别
```

### 对话摘要压缩

`Submit_Message.py` 中的 `_compress_history` 实现了自动摘要：

- **阈值**：超过 12 轮对话触发压缩
- **策略**：早期历史（`[:-8]`）通过 LLM 生成摘要，保留最近 8 轮完整消息
- **注入**：摘要以 system prompt 前缀形式注入，不丢失上下文

## 依赖

| 包 | 用途 |
|---|---|
| `gradio` | Web UI 框架 |
| `langchain` / `langchain-core` / `langchain-community` | LLM 应用框架 |
| `dashscope` | 阿里云 DashScope 多模态 API |
| `python-dotenv` | 环境变量管理 |
| `Pillow` | 图片处理（Base64 编码） |

## 许可证

MIT
