# utils for ll one bot

import requests
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 解耦 URL
BASE_URL = 'http://localhost:3000'

def send_private_message(user_id, message):
    """
    发送私信的函数

    参数:
    user_id (int): 用户ID
    message (str): 要发送的消息

    返回:
    Response: 请求的响应
    """
    payload = {
        'user_id': user_id,
        'message': [{
            'type': 'text',
            'data': {
                'text': message
            }
        }]
    }
    logging.debug(f"发送消息的 payload: {payload}")
    response = requests.post(f'{BASE_URL}/send_private_msg', json=payload)
    logging.debug(f"响应状态码: {response.status_code}, 响应内容: {response.text}")
    return response
