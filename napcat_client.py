import os
from typing import Optional

import requests


# NapCat OneBot HTTP 服务端地址，例如 http://127.0.0.1:3000
NAPCAT_BASE_URL = os.getenv("NAPCAT_BASE_URL", "http://127.0.0.1:3000")


def send_private_message(user_id: str, text: str) -> Optional[requests.Response]:
    """通过 NapCat 向指定 QQ 发送私聊消息。"""
    if not user_id or not text:
        return None

    payload = {"user_id": int(user_id), "message": text}
    try:
        resp = requests.post(
            f"{NAPCAT_BASE_URL}/send_private_msg", json=payload, timeout=5
        )
        return resp
    except Exception as e:
        print(f"[napcat_client] send_private_message 出错: {e}")
        return None


def send_group_message(group_id: str, text: str) -> Optional[requests.Response]:
    """通过 NapCat 在指定群发送群消息。"""
    if not group_id or not text:
        return None

    payload = {"group_id": int(group_id), "message": text}
    try:
        resp = requests.post(
            f"{NAPCAT_BASE_URL}/send_group_msg", json=payload, timeout=5
        )
        return resp
    except Exception as e:
        print(f"[napcat_client] send_group_message 出错: {e}")
        return None

