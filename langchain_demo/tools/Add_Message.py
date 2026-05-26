import gradio as gr


def _extract_file_path(file_item):
    """从Gradio不同版本的文件格式中提取文件路径"""
    if isinstance(file_item, str):
        return file_item
    if isinstance(file_item, dict):
        return file_item.get('path') or file_item.get('name') or str(file_item)
    if isinstance(file_item, (list, tuple)):
        return _extract_file_path(file_item[0]) if file_item else ''
    return str(file_item)


def add_message(history, messages):
    """将用户输入的消息添加到聊天记录中"""
    for m in messages.get('files', []) or []:
        file_path = _extract_file_path(m)
        history.append({"role": "user", "content": {"path": file_path}})
    if messages.get('text'):
        history.append({"role": "user", "content": messages['text']})
    return history, gr.MultimodalTextbox(value=None, interactive=False)
