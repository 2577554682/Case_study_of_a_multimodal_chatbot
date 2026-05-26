import os
from dotenv import load_dotenv
load_dotenv(override=True)

ALIYUN_API_KEY = os.getenv('ALIYUN_API_KEY')
DB_URI = os.getenv('DB_URI')
