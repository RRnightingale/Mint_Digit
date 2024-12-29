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


def send_group_message(group_id, message):
    payload = {
        'group_id': group_id,
        'message': [{
            'type': 'text',
            'data': {
                'text': message
            }
        }]
    }
    logging.debug(f"发送消息的 payload: {payload}")
    response = requests.post(f'{BASE_URL}/send_group_msg', json=payload)
    logging.debug(f"响应状态码: {response.status_code}, 响应内容: {response.text}")
    return response

def send_group_message_with_at(group_id, message, user_id):
    payload = {
        'group_id': group_id,
        'message': [
            {
                "type": "at",
                "data": {
                    "qq": user_id,
                    "name": "此栏无效，此人在群里"
                }
            },
            {
                'type': 'text',
            'data': {
                'text': ' ' + message
            }
        }]
    }
    logging.debug(f"发送消息的 payload: {payload}")
    response = requests.post(f'{BASE_URL}/send_group_msg', json=payload)
    logging.debug(f"响应状态码: {response.status_code}, 响应内容: {response.text}")
    return response


def set_group_ban(group_id, user_id, duration=10 * 60):
    """
    设置群禁言

    参数:
    group_id (int): 群ID
    user_id (int): 用户ID
    duration (int): 禁言时长，单位为秒，默认为10分钟

    返回:
    Response: 请求的响应
    """
    payload = {
        'group_id': group_id,
        'user_id': user_id,
        'duration': duration
    }
    response = requests.post(f'{BASE_URL}/set_group_ban', json=payload)
    logging.debug(f"响应状态码: {response.status_code}, 响应内容: {response.text}")
    return response


def set_group_add_request(flag: str, approve=False, reason="阿敏认为你的赞美不够真诚"):
    """
    处理入群请求
    flag: 请求id
    approve: 是否通过
    reason: 拒绝原因
    """

    payload = {
        'flag': flag,
        'approve': approve,
        'reason': reason
    }
    response = requests.post(f'{BASE_URL}/set_group_add_request', json=payload)
    logging.debug(f"响应状态码: {response.status_code}, 响应内容: {response.text}")
    return response
