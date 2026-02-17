from typing import Optional

import requests

from logger import get_logger
from config import get_config


logger = get_logger("napcat_client")
config = get_config()


def send_private_message(user_id: str, text: str) -> Optional[requests.Response]:
    """通过 NapCat 向指定 QQ 发送私聊消息。"""
    if not user_id or not text:
        return None
    logger.info("来了一次")
    payload = {"user_id": int(user_id), "message": text}
    try:
        resp = requests.post(
            f"{config.napcat_base_url}/send_private_msg", json=payload, timeout=5
        )
        return resp
    except Exception as e:
        logger.error("send_private_message 出错: %s", e)
        return None


def send_group_message(group_id: str, text: str) -> Optional[requests.Response]:
    """通过 NapCat 在指定群发送群消息。"""
    if not group_id or not text:
        return None

    payload = {"group_id": int(group_id), "message": text}
    try:
        resp = requests.post(
            f"{config.napcat_base_url}/send_group_msg", json=payload, timeout=5
        )
        return resp
    except Exception as e:
        logger.error("send_group_message 出错: %s", e)
        return None


def get_group_member_list(group_id: str) -> Optional[list]:
    """获取群成员列表。"""
    if not group_id:
        return None

    try:
        resp = requests.get(
            f"{config.napcat_base_url}/get_group_member_list", 
            params={"group_id": int(group_id)}, 
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                return data.get("data", [])
        return None
    except Exception as e:
        logger.error("get_group_member_list 出错: %s", e)
        return None


def get_group_member_info(group_id: str, user_id: str) -> Optional[dict]:
    """获取群成员信息。"""
    if not group_id or not user_id:
        return None

    try:
        resp = requests.get(
            f"{config.napcat_base_url}/get_group_member_info", 
            params={"group_id": int(group_id), "user_id": int(user_id)}, 
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                return data.get("data", {})
        return None
    except Exception as e:
        logger.error("get_group_member_info 出错: %s", e)
        return None


def set_group_ban(group_id: str, user_id: str, duration: int = 1800) -> Optional[requests.Response]:
    """设置群成员禁言。
    
    Args:
        group_id: 群聊ID
        user_id: 用户ID
        duration: 禁言时长（秒），默认1800秒（30分钟）
        
    Returns:
        API响应对象
    """
    if not group_id or not user_id:
        return None
    
    payload = {
        "group_id": int(group_id),
        "user_id": int(user_id),
        "duration": duration
    }
    
    try:
        logger.info("设置群成员禁言: group_id=%s, user_id=%s, duration=%d", group_id, user_id, duration)
        resp = requests.post(
            f"{config.napcat_base_url}/set_group_ban", 
            json=payload, 
            timeout=5
        )
        logger.info("禁言操作响应: status_code=%d, body=%s", resp.status_code, resp.text)
        return resp
    except Exception as e:
        logger.error("set_group_ban 出错: %s", e)
        return None


def set_group_kick(group_id: str, user_id: str, reject_add_request: bool = False) -> Optional[requests.Response]:
    """设置群成员踢出。
    
    Args:
        group_id: 群聊ID
        user_id: 用户ID
        reject_add_request: 是否拒绝加群请求，默认False
        
    Returns:
        API响应对象
    """
    if not group_id or not user_id:
        return None
    
    payload = {
        "group_id": int(group_id),
        "user_id": int(user_id),
        "reject_add_request": reject_add_request
    }
    
    try:
        logger.info("踢出群成员: group_id=%s, user_id=%s, reject_add_request=%s", group_id, user_id, reject_add_request)
        resp = requests.post(
            f"{config.napcat_base_url}/set_group_kick", 
            json=payload, 
            timeout=5
        )
        logger.info("踢人操作响应: status_code=%d, body=%s", resp.status_code, resp.text)
        return resp
    except Exception as e:
        logger.error("set_group_kick 出错: %s", e)
        return None


def get_group_info(group_id: str) -> Optional[dict]:
    """获取群信息。
    
    Args:
        group_id: 群聊ID
        
    Returns:
        群信息字典
    """
    if not group_id:
        return None
    
    try:
        resp = requests.get(
            f"{config.napcat_base_url}/get_group_info", 
            params={"group_id": int(group_id)}, 
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                return data.get("data", {})
        return None
    except Exception as e:
        logger.error("get_group_info 出错: %s", e)
        return None
