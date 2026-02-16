from events import Event, BotReply
from strategies_basic import handle_private_chat, handle_group_at


def dispatch_event(event: Event) -> BotReply:
    """根据事件类型和是否 @阿敏 选择不同的策略。"""
    if event.is_private:
        return handle_private_chat(event)

    if event.is_group and event.is_at_amin:
        return handle_group_at(event)

    # 其他情况暂时不回复
    return BotReply(text=None)

