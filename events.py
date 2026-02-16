from dataclasses import dataclass
from typing import Optional


@dataclass
class Event:
    """统一的内部事件结构，从 NapCat/OneBot 原始 JSON 解析而来。"""

    post_type: str
    message_type: Optional[str]
    user_id: Optional[str]
    group_id: Optional[str]
    raw_message: str
    is_at_amin: bool = False

    @property
    def is_private(self) -> bool:
        return self.message_type == "private"

    @property
    def is_group(self) -> bool:
        return self.message_type == "group"


@dataclass
class BotReply:
    """机器人对一次事件的简单文本回复。"""

    text: Optional[str] = None

