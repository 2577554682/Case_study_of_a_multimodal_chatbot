from dashscope import Files
from env_utils import ALIYUN_API_KEY


def transcribe_audio(audio_path):
    """上传音频到DashScope，获取远程URL"""
    upload_resp = Files.upload(file_path=audio_path, purpose='inference', api_key=ALIYUN_API_KEY)
    if upload_resp.status_code != 200:
        raise RuntimeError(f"DashScope文件上传失败: code={upload_resp.code}, message={upload_resp.message}")

    file_id = upload_resp.output['uploaded_files'][0]['file_id']

    get_resp = Files.get(file_id=file_id, api_key=ALIYUN_API_KEY)
    if get_resp.status_code != 200:
        raise RuntimeError(f"DashScope获取文件信息失败: code={get_resp.code}, message={get_resp.message}")

    url = get_resp.output['url']

    return {
        'type': 'audio_url',
        'audio_url': {
            'url': url
        }
    }
