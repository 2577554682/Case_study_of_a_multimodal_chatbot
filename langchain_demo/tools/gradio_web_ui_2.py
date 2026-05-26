import uuid

import gradio as gr

from langchain_demo.tools.Add_Message import add_message
from langchain_demo.tools.Submit_Message import submit_message
from langchain_demo.tools.session_store import load_history

# ── 调色板（亮色主题）────────────────────────────────────
BG       = "#f8f8fb"   # 暖白基底
SURFACE  = "#ffffff"   # 纯白表面
CARD     = "#f3f4f7"   # 浅灰卡片 / 聊天气泡
BORDER   = "#e4e4eb"   # 淡灰分割线
INPUT_BG = "#ffffff"   # 纯白输入区

TEXT     = "#1a1a2e"   # 深灰蓝主文字
TEXT_SEC = "#6b7280"   # 中灰次级文字
TEXT_TER = "#9ca3af"   # 浅灰三级文字

ACCENT       = "#6366f1"                  # 靛蓝
ACCENT_BG    = "rgba(99,102,241,0.06)"   # 微妙底色
ACCENT_GLOW  = "rgba(99,102,241,0.2)"    # 聚焦光环
SUCCESS      = "#22c55e"                  # 状态绿

DEMO_PROMPTS = [
    "介绍一下你自己，你能做什么？",
    "帮我分析一下这张图片的内容",
    "请用三句话总结这段音频",
    "用 Python 写一个快速排序",
    "翻译这段话为英文",
]


def on_load(session_id: str):
    db_history = load_history(session_id)
    return db_history


def clear_chat():
    return [], str(uuid.uuid4())


# ── 主题 ────────────────────────────────────────────────
theme = gr.themes.Soft(
    primary_hue="indigo",
    neutral_hue="gray",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
).set(
    body_background_fill=BG,
    body_background_fill_dark=BG,
    body_text_color=TEXT,
    body_text_color_dark=TEXT,
    block_background_fill=SURFACE,
    block_background_fill_dark=SURFACE,
    block_border_color=BORDER,
    block_border_color_dark=BORDER,
    input_background_fill=INPUT_BG,
    input_background_fill_dark=INPUT_BG,
    input_border_color=BORDER,
    input_border_color_dark=BORDER,
    button_primary_background_fill=ACCENT,
    button_primary_background_fill_dark=ACCENT,
    button_secondary_background_fill=SURFACE,
    button_secondary_background_fill_dark=SURFACE,
    link_text_color=ACCENT,
    link_text_color_dark=ACCENT,
)

# ── 聊天气泡 JS 注入（debounced 防闪烁）─────────────────
BUBBLE_FIX_JS = f"""
() => {{
    const CARD = '{CARD}';
    const TEXT = '{TEXT}';
    const TEXT_SEC = '{TEXT_SEC}';
    const BORDER = '{BORDER}';
    const ACCENT = '{ACCENT}';

    let pending = false;

    function styleBubble(el) {{
        el.style.background = CARD;
        el.style.color = TEXT;
        el.style.border = '1px solid ' + BORDER;
        el.style.borderRadius = '14px';
        el.style.padding = '12px 18px';
        el.style.fontSize = '0.9375rem';
        el.style.lineHeight = '1.65';
    }}

    function fixChatbot() {{
        if (pending) return;
        pending = true;
        requestAnimationFrame(function() {{
            pending = false;
            var chat = document.querySelector('#chatbot');
            if (!chat) return;

            // 只精准匹配气泡容器，避免触碰文字元素导致重绘
            var bubbles = chat.querySelectorAll(
                '[class*="bubble"], [class*="bubble"] [class*="text"]'
            );
            bubbles.forEach(function(el) {{
                if (el.className && (
                    el.className.includes('bubble') ||
                    el.className.includes('text')
                )) {{
                    styleBubble(el);
                }}
            }});

            // 回退：找 message-wrap 内的主容器
            var wraps = chat.querySelectorAll('[class*="message"]');
            wraps.forEach(function(el) {{
                var bubble = el.querySelector('[class*="bubble"], [class*="text"]');
                if (!bubble && (el.textContent || '').trim().length > 10) {{
                    styleBubble(el);
                }}
            }});
        }});
    }}

    // 初始执行
    setTimeout(fixChatbot, 400);

    // MutationObserver — debounced
    var chat = document.querySelector('#chatbot');
    var initObserver = function() {{
        var c = document.querySelector('#chatbot');
        if (!c) return setTimeout(initObserver, 300);
        new MutationObserver(function(mutations) {{
            // 只在节点增删时触发，忽略属性变化
            var hasChanges = mutations.some(function(m) {{
                return m.addedNodes.length > 0 || m.removedNodes.length > 0;
            }});
            if (hasChanges) setTimeout(fixChatbot, 50);
        }}).observe(c, {{ childList: true, subtree: true }});
    }};
    initObserver();
}}
"""

# ── 全局 CSS ────────────────────────────────────────────
GLOBAL_CSS = f"""
/* ── 滚动条 ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {TEXT_TER}; }}
* {{ scrollbar-width: thin; scrollbar-color: {BORDER} transparent; }}

/* ── 聊天气泡 CSS ── */
#chatbot {{ height: calc(100vh - 260px) !important; min-height: 420px; }}

#chatbot .bubble,
#chatbot [class*="bubble"],
#chatbot [class*="message"] [class*="text"] {{
    background: {CARD} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 12px 18px !important;
    font-size: 0.9375rem !important;
    line-height: 1.65 !important;
}}

/* ── 输入框聚焦光效 ── */
#input-box {{
    background: {INPUT_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 16px !important;
    padding: 14px 18px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}}
#input-box:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT_GLOW} !important;
}}

/* ── 演示按钮：胶囊样式 ── */
#demo-prompts {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}}
#demo-prompts button {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 20px !important;
    color: {TEXT_SEC} !important;
    font-size: 0.8rem !important;
    padding: 6px 16px !important;
    height: auto !important;
    min-height: unset !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    text-align: center !important;
    white-space: nowrap !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
}}
#demo-prompts button:hover {{
    background: {ACCENT_BG} !important;
    border-color: {ACCENT} !important;
    color: {ACCENT} !important;
    box-shadow: 0 2px 6px rgba(99,102,241,0.12) !important;
    transform: translateY(-1px);
}}

/* ── 清空按钮 ── */
#clear-btn button {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    color: {TEXT_TER} !important;
    font-size: 0.75rem !important;
    padding: 4px 12px !important;
    height: auto !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
    font-weight: 400 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}}
#clear-btn button:hover {{
    color: #ef4444 !important;
    border-color: rgba(239,68,68,0.3) !important;
    background: rgba(239,68,68,0.04) !important;
}}

/* ── 通用过渡 ── */
button {{ transition: all 0.15s ease !important; }}

/* ── 隐藏 Gradio 默认页脚 ── */
footer {{ display: none !important; }}

/* ── 多模态文字域 ── */
#input-box textarea {{
    font-size: 0.9375rem !important;
    line-height: 1.6 !important;
    color: {TEXT} !important;
    background: {INPUT_BG} !important;
}}
#input-box textarea::placeholder {{
    color: {TEXT_TER} !important;
}}

/* ── 侧边栏卡片微阴影 ── */
#sidebar-card {{
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
"""

# ── 主体布局 ────────────────────────────────────────────
with gr.Blocks(
    title="多模态 AI 助手",
    theme=theme,
    css=GLOBAL_CSS,
) as block:
    session_id = gr.State(str(uuid.uuid4()))

    # ── 聊天气泡修复脚本 ──
    gr.HTML(f"<script>{BUBBLE_FIX_JS}</script>")

    # ── 顶栏 ──
    gr.HTML(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                max-width:1200px;margin:0 auto;padding:18px 28px 16px 28px;
                background:{SURFACE};">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:34px;height:34px;border-radius:9px;
                        background:linear-gradient(135deg,{ACCENT},#818cf8);
                        display:flex;align-items:center;justify-content:center;">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
                     stroke="white" stroke-width="2.2" stroke-linecap="round">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                </svg>
            </div>
            <span style="font-size:1.05rem;font-weight:600;color:{TEXT};letter-spacing:-0.01em;">
                多模态 AI 助手
            </span>
            <span style="font-size:0.68rem;padding:3px 10px;border-radius:20px;
                         background:{ACCENT_BG};color:{ACCENT};
                         border:1px solid rgba(99,102,241,0.12);
                         display:inline-flex;align-items:center;line-height:1.4;">
                Qwen3.5-Omni
            </span>
        </div>
        <div style="font-size:0.78rem;color:{SUCCESS};display:flex;align-items:center;gap:5px;
                    background:rgba(34,197,94,0.06);padding:4px 12px;border-radius:20px;">
            <span style="display:inline-block;width:6px;height:6px;border-radius:50%;
                         background:{SUCCESS};opacity:0.85;"></span>
            在线
        </div>
    </div>
    """)

    # ── 主体 ──
    with gr.Row():
        # 左侧栏
        with gr.Column(scale=1, min_width=220):
            gr.HTML(f"""
            <div id="sidebar-card"
                 style="background:{SURFACE};border:1px solid {BORDER};
                        border-radius:14px;padding:20px 18px;margin-bottom:16px;">
                <h3 style="color:{TEXT_TER};font-size:0.7rem;font-weight:600;
                           text-transform:uppercase;letter-spacing:0.06em;
                           margin:0 0 12px 0;">
                    功能亮点
                </h3>
                <div style="color:{TEXT_SEC};font-size:0.8rem;line-height:1.8;">
                    <span style="color:{ACCENT};font-weight:500;">&bull;</span> 文本智能对话<br>
                    <span style="color:{ACCENT};font-weight:500;">&bull;</span> 图片内容分析<br>
                    <span style="color:{ACCENT};font-weight:500;">&bull;</span> 音频语音识别<br>
                    <span style="color:{ACCENT};font-weight:500;">&bull;</span> 多文件同时上传<br>
                    <span style="color:{ACCENT};font-weight:500;">&bull;</span> 对话历史持久化<br>
                    <span style="color:{ACCENT};font-weight:500;">&bull;</span> 长对话自动摘要
                </div>
            </div>
            """)

            gr.HTML(f"""
            <div style="background:{SURFACE};border:1px solid {BORDER};
                        border-radius:14px;padding:20px 18px;margin-bottom:16px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <h3 style="color:{TEXT_TER};font-size:0.7rem;font-weight:600;
                           text-transform:uppercase;letter-spacing:0.06em;
                           margin:0 0 4px 0;">
                    快速体验
                </h3>
            </div>
            """)

            with gr.Column(elem_id="demo-prompts"):
                for prompt in DEMO_PROMPTS:
                    btn = gr.Button(prompt, size="sm")
                    btn.click(
                        fn=lambda: None, inputs=[], outputs=[],
                        js=f"""() => {{
                            var ta = document.querySelector('#input-box textarea');
                            if (ta) {{
                                var s = Object.getOwnPropertyDescriptor(
                                    HTMLTextAreaElement.prototype, 'value').set;
                                s.call(ta, {repr(prompt)});
                                ta.dispatchEvent(new Event('input', {{bubbles: true}}));
                            }}
                        }}"""
                    )

            gr.HTML(f"""
            <div style="margin-top:16px;padding:0 4px;">
                <p style="color:{TEXT_TER};font-size:0.72rem;line-height:1.6;margin:0;">
                    基于 Qwen3.5-Omni 多模态大模型
                </p>
            </div>
            """)

        # 右侧聊天区
        with gr.Column(scale=3, min_width=480):
            chatbot = gr.Chatbot(
                height=550,
                elem_id="chatbot",
                show_label=False,
            )

            chat_input = gr.MultimodalTextbox(
                interactive=True,
                file_types=["image", "audio", ".mp4"],
                file_count="multiple",
                placeholder="输入消息，或上传图片 / 音频 / 视频……",
                show_label=False,
                sources=["microphone", "upload"],
                elem_id="input-box",
            )

            with gr.Row():
                gr.HTML(
                    f'<span style="font-size:0.72rem;color:{TEXT_TER};'
                    f'padding-top:5px;">支持 JPG / PNG / WAV / MP4</span>'
                )
                with gr.Column(scale=0, min_width=0, elem_id="clear-btn"):
                    clear_btn = gr.Button("清空对话", size="sm")

            clear_btn.click(clear_chat, [], [chatbot, session_id])

            chat_input.submit(
                add_message,
                [chatbot, chat_input],
                [chatbot, chat_input],
            ).then(
                submit_message,
                [chatbot, session_id],
                [chatbot],
            ).then(
                lambda: gr.MultimodalTextbox(interactive=True),
                None,
                [chat_input],
            )

    # ── 底部 ──
    gr.HTML(f"""
    <div style="text-align:center;padding:10px 0 16px 0;color:{TEXT_TER};font-size:0.68rem;">
        Powered by DashScope &nbsp;&middot;&nbsp; 会话自动保存至 PostgreSQL
    </div>
    """)

    block.load(on_load, [session_id], [chatbot])

if __name__ == "__main__":
    block.launch()
