#!/usr/bin/env python
# coding: utf-8
# ----------------------------------------------------------------------
# Author: arshart@forevernine.com
# Description: Utility functions for interacting with OpenAI GPT
# ----------------------------------------------------------------------

import logging
import traceback
from openai import OpenAI
import os
import json
from typing_extensions import Literal
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

assistant_id = "asst_qnaMzpoY0Om2VvtV5FuxulX1"  # 阿敏assis
THREAD_ID = "thread_StV3HoqfMz2HyztpG1iI8IaC"  # QQ GROUP

# 从环境变量中获取OpenAI API密钥
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("请在.env文件中设置OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

def chat(msg: list):
    """
    调用 GPT-4o 进行对话

    :param msg: 用户输入的提示
    :param event: 事件信息
    :param max_words: 最大词数
    :return: GPT-4o 的回复
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msg
        )
        reply = completion.choices[0].message.content
        
        return reply
    except Exception:
        error_msg = f"Extrac {msg} fail! Error: \n{traceback.format_exc()}\n"
        logging.error(error_msg)
        return f"GPT-4o 系统-崩溃-嘎嘎 "

def dell_e_image(prompt: str, height=1024, width=1024) -> str:
    """
    调用 DALL-E 生成图片

    :param prompt: 图片描述
    :param height: 图片高度
    :param width: 图片宽度
    :return: 图片URL
    """
    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size=f"{width}x{height}",
    quality="standard",
    n=1,
    )

    image_url = response.data[0].url

    return image_url


def create_message(content,
                   role: Literal["user", "assistant"] = "user",
                   timeout=60,
                   thread_id=THREAD_ID):
    message = client.beta.threads.messages.create(thread_id,
                                                  content=content,
                                                  role=role,
                                                  timeout=timeout)
    return message


def run_assistant(thread_id=THREAD_ID, function_call=None) -> str:
    run = client.beta.threads.runs.create_and_poll(
        assistant_id=assistant_id, thread_id=thread_id, timeout=60)
    while run:
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread_id, run_id=run.id)
            rsp = ""
            for message in messages:
                rsp += message.content[0].text.value
            return rsp
        elif run.status == 'requires_action':
            tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            output = function_call(name, arguments)
            run = client.beta.threads.runs.submit_tool_outputs_and_poll(thread_id=thread_id, run_id=run.id,tool_outputs=[
                    {
                        "tool_call_id": tool_call.id,
                        "output": output,
                    }
                ])
        else:
            logging.error(f"Unknown run status: {run}")
            return "系统-崩溃-嘎嘎"
