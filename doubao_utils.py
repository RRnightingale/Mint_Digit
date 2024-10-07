import requests
import json
import os
import logging
import traceback
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取API访问的URL和鉴权信息
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
API_KEY = os.getenv("DOUBAO_API_KEY")  # 从 .env 文件中获取 DOUBAO_API_KEY
# model_name = "ep-20241001234826-5m4j9"  # 32lite
# model_name = 'ep-20241002215521-dnr7t'  # 128 pro
model_name = "ep-20241003070234-2c94h" # 128lite
# model_name = "ep-20241004185827-ckr55" # char-4k
# model_name = "ep-20241005200634-r9dzn" # pro32
# model_name = "ep-20241006215449-vfjxx" # lite4k
# model_name = "ep-20241006230204-5b886" # mooshot 128k

def chat(messages: list):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": model_name,  # 替换为你的模型ID
        "messages": messages
    }
    
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # 检查HTTP请求是否成功
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        error_msg = f"HTTP请求错误: {e}\n{traceback.format_exc()}\n"
        logging.error(error_msg)
        return "系统-崩溃-嘎嘎"
    except KeyError:
        error_msg = f"响应数据格式错误\n{traceback.format_exc()}\n"
        logging.error(error_msg)
        return "系统-崩溃-嘎嘎"
    