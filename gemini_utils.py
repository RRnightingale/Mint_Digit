import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
import socks
import socket
import logging
import traceback
from memory import ChatMemory
from dotenv import load_dotenv
from time import time
from collections import deque

# 加载 .env 文件中的环境变量
load_dotenv()

# # 设置 VPN 连接
# # socks.setdefaultproxy(socks.SOCKS5, "192.168.98.228", 10811)
# socks.setdefaultproxy(socks.SOCKS5, "127.0.0.1", 10808)
# socket.socket = socks.socksocket

# 从环境变量中获取 API 密钥
API_KEY = os.getenv("GEMINI_API_KEY")  # 从 .env 文件中获取 GEMINI_API_KEY
if not API_KEY:
    raise ValueError("请在.env文件中设置 GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

# 创建模型配置
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# 修改计数相关变量
pro_call_times = deque()  # 存储 pro 模型调用时间的双端队列
WINDOW_SIZE = 60  # 滑动窗口大小（1分钟）
MAX_PRO_CALLS = 5  # pro 模型每分钟最大调用次数

# 修改默认模型名称
default_model_name = "gemini-1.5-pro"


def get_current_model():
    """
    优先使用 pro 模型的配额（每分钟5次），用完后才使用 flash
    """
    current_time = time()

    # 移除超过1分钟的记录
    while pro_call_times and current_time - pro_call_times[0] >= WINDOW_SIZE:
        pro_call_times.popleft()

    # 如果最近1分钟内 pro 的使用次数少于5次，继续使用 pro
    if len(pro_call_times) < MAX_PRO_CALLS:
        pro_call_times.append(current_time)
        model_name = "gemini-1.5-pro"
        logging.info(
            f"使用模型: {model_name}, 当前分钟内第 {len(pro_call_times)} 次使用pro")
        return model_name

    # pro 配额用完，使用 flash
    model_name = "gemini-1.5-flash"
    logging.info(f"使用模型: {model_name}, pro额度已用完")
    return model_name

def chat(memory: ChatMemory, message: str):
    """
    调用 Gemini 进行对话

    :param messages: 用户输入的消息列表
    :return: Gemini 的回复
    """
    # 获取当前应该使用的模型
    current_model = get_current_model()

    model = genai.GenerativeModel(
        model_name=current_model,  # 使用动态确定的模型名称
        generation_config=generation_config,
        system_instruction=memory.system_prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )

    try:
        chat_session = model.start_chat(
            history=memory.get_google_chat_history())
        response = chat_session.send_message(message)
        return response.text
    except Exception as e:
        error_msg = f"调用 Gemini 失败: {e}\n{traceback.format_exc()}\n"
        logging.error(error_msg)
        return "gemin-崩溃-嘎嘎"
