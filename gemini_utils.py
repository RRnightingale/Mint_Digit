import google.generativeai as genai
import os
import socks
import socket
import logging
import traceback
from memory import ChatMemory
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 设置 VPN 连接
# socks.setdefaultproxy(socks.SOCKS5, "192.168.98.228", 10811)
socks.setdefaultproxy(socks.SOCKS5, "127.0.0.1", 10808)
socket.socket = socks.socksocket

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

model_name = "gemini-1.5-pro-002"  # 模型名称


def chat(memory: ChatMemory, message: str):
    """
    调用 Gemini 进行对话

    :param messages: 用户输入的消息列表
    :return: Gemini 的回复
    """
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        system_instruction=memory.system_prompt,
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
