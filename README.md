# 多模态 AI 助手

基于 **Qwen3.5-Omni** 多模态大模型的智能对话应用，支持文本、图片、音频输入，对话自动持久化至 PostgreSQL。

## 功能

- 文本智能对话
- 图片内容分析
- 音频语音识别
- 多文件同时上传
- 对话历史持久化（PostgreSQL）
- 长对话自动摘要压缩

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Gradio + 自定义 CSS/JS |
| LLM | 阿里云 DashScope（Qwen3.5-Omni） |
| 框架 | LangChain |
| 数据库 | PostgreSQL + SQLChatMessageHistory |
| 可观测 | LangSmith（可选） |

## 快速开始

### 1. 克隆项目

```bash
git clone <repo-url>
cd Case_study_of_a_multimodal_chatbot
```

### 2. 安装依赖

```bash
pip install gradio langchain langchain-core langchain-community dashscope python-dotenv
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的密钥：

```env
ALIYUN_API_KEY='sk-your-dashscope-key'
LANGSMITH_API_KEY='lsv2_pt_your-key'   # 可选
DB_URI='postgresql://user:password@localhost:5432/dbname'
```

### 4. 启动

```bash
python langchain_demo/tools/gradio_web_ui_2.py
```

浏览器打开 `http://localhost:7860`。

## 项目结构

```
├── langchain_demo/
│   ├── multiModal_chain.py          # LangChain 链定义
│   └── tools/
│       ├── gradio_web_ui_2.py       # Web UI 入口
│       ├── Add_Message.py           # 消息格式化
│       ├── Submit_Message.py        # 消息处理 & 摘要
│       ├── session_store.py         # PostgreSQL 持久化
│       ├── DashScopeOmniLLM.py      # DashScope LLM 封装
│       ├── Image_Processing.py      # 图片处理
│       ├── Voice_Processing.py      # 音频处理
│       └── get_last_message.py      # 消息解析
├── env_utils.py                     # 环境变量加载
├── my_llm.py                        # LLM 初始化
├── .env.example                     # 环境变量模板
└── README.md
```

## License

MIT
