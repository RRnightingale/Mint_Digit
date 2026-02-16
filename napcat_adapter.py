from typing import Any, Dict, Optional

from events import Event


AMIN_QQ = "3995633031"  # TODO: 后续挪到配置文件


def from_napcat_payload(payload: Dict[str, Any]) -> Optional[Event]:
    """将 NapCat(OneBot) 的原始上报 JSON 转成内部 Event。

    当前只关心 post_type=message 的事件，其余先忽略。
    """
    post_type = payload.get("post_type")
    if post_type != "message":
        return None

    message_type = payload.get("message_type")
    user_id = str(payload.get("user_id")) if payload.get("user_id") is not None else None
    group_id = (
        str(payload.get("group_id")) if payload.get("group_id") is not None else None
    )
    raw_message = payload.get("raw_message") or ""

    # 简单检测是否 @ 了阿敏（基于 CQ 码）
    is_at_amin = False
    if AMIN_QQ and f"[CQ:at,qq={AMIN_QQ}" in raw_message:
        is_at_amin = True

    return Event(
        post_type=post_type,
        message_type=message_type,
        user_id=user_id,
        group_id=group_id,
        raw_message=raw_message,
        is_at_amin=is_at_amin,
    )

