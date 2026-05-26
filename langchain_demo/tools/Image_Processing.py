# 图片处理函数
import base64
import io

from PIL import Image


def transcribe_image(image_path):
    """使用Base64处理图片"""
    with Image.open(image_path) as img:
        img_format = img.format if img.format else 'JPEG'

        buffered = io.BytesIO()

        # 保留原始格式（避免JPEG强制转换导致透明通道丢失）
        img.save(buffered, format=img_format)
        image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return {
            'type':'image_url',
            'image_url':{
                'url':f'data:image/{img_format.lower()};base64,{image_data}',
                'detail':'high'
            }
        }