import requests
from openai import OpenAI
import json
import os
import logging
import traceback
from dotenv import load_dotenv
from memory import ChatMemory

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取API密钥
API_KEY = os.getenv("GROK_API_KEY")  # 从 .env 文件中获取 GROK_API_KEY
if not API_KEY:
    raise ValueError("请在.env文件中设置 GROK_API_KEY")

API_URL = "https://api.x.ai/v1/chat/completions"  # Grok的实际API地址
MODEL_NAME = "grok-beta"  # Grok的模型名称

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.x.ai/v1",
)


def chat(memory: ChatMemory):
    """
    调用 Grok 进行对话

    :param memory: 聊天记录对象
    :param message: 用户输入的消息
    :return: Grok 的回复
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "model": MODEL_NAME,
        "messages": memory.get_gpt_compatible_memory(),
        "stream": False,
        "temperature": 0.8
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()  # 检查HTTP请求是否成功

        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP 错误: {http_err}\n响应内容: {response.text}\n{traceback.format_exc()}\n"
        logging.error(error_msg)
        return "Grok-HTTP错误-嘎嘎"
    except Exception as e:
        error_msg = f"调用 Grok API 失败: {e}\n{traceback.format_exc()}\n"
        logging.error(error_msg)
        return "Grok-崩溃-嘎嘎"


def chat_with_function(memory: ChatMemory, function_call=None):
    """
    调用 Grok 进行对话

    :param memory: 聊天记录对象
    :param message: 用户输入的消息
    :return: Grok 的回复
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    tools = [{"type": "function", "function": f} for f in memory.functions]
    messages = memory.get_gpt_compatible_memory()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        temperature=0.8,
        timeout=60
    )
    # reply = response.choices[0].message.content

    if response.choices[0].finish_reason == 'tool_calls':
        respone_message = response.choices[0].message
        tool_calls = respone_message.tool_calls
        for tool_call in tool_calls:
            tool_call_id = tool_calls['id']
            name = tool_calls['function']['name']
            arguments = json.loads(tool_call['function']['arguments'])
            result = function_call(name, arguments)

            function_call_result_message = {
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call_id
            }

            new_messages = messages + \
                [respone_message, function_call_result_message]
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=new_messages,
                tools=tools,
            )
    return response.choices[0].message.content
    # data = {
    #     "model": MODEL,
    #     "messages": messages,
    #     "stream": False,
    #     "temperature": 0.8
    # }

    # try:
    #     response = requests.post(API_URL, headers=headers, json=data)
    #     response.raise_for_status()  # 检查HTTP请求是否成功

    #     response_data = response.json()
    #     return response_data["choices"][0]["message"]["content"]

    # except requests.exceptions.HTTPError as http_err:
    #     error_msg = f"HTTP 错误: {http_err}\n响应内容: {response.text}\n{traceback.format_exc()}\n"
    #     logging.error(error_msg)
    #     return "Grok-HTTP错误-嘎嘎"
    # except Exception as e:
    #     error_msg = f"调用 Grok API 失败: {e}\n{traceback.format_exc()}\n"
    #     logging.error(error_msg)
    #     return "Grok-崩溃-嘎嘎"
