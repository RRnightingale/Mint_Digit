from typing import Any, Dict, Optional

from events import Event
from config import get_config
from logger import get_logger


logger = get_logger("napcat_adapter")
config = get_config()


def from_napcat_payload(payload: Dict[str, Any]) -> Optional[Event]:
    """将 NapCat(OneBot) 的原始上报 JSON 转成内部 Event。

    当前只关心 post_type=message 的事件，其余先忽略。
    """
    logger.debug("处理 NapCat 原始 payload: %s", payload)
    
    post_type = payload.get("post_type")
    if post_type != "message":
        logger.debug("忽略非消息事件: %s", post_type)
        return None

    message_type = payload.get("message_type")
    user_id = str(payload.get("user_id")) if payload.get("user_id") is not None else None
    group_id = (
        str(payload.get("group_id")) if payload.get("group_id") is not None else None
    )
    raw_message = payload.get("raw_message") or ""

    is_at_amin = False
    if config.amin_qq and f"[CQ:at,qq={config.amin_qq}" in raw_message:
        is_at_amin = True
        logger.debug("检测到 @ 事件")

    event = Event(
        post_type=post_type,
        message_type=message_type,
        user_id=user_id,
        group_id=group_id,
        raw_message=raw_message,
        is_at_amin=is_at_amin,
    )
    
    logger.debug("转换为内部 Event: %s", event)
    return event

