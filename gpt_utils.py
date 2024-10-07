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
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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
