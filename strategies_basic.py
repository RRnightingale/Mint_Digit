from events import Event, BotReply


def handle_private_chat(event: Event) -> BotReply:
    """单聊策略：当前版本固定回复“你好”."""
    return BotReply(text="你好")


def handle_group_at(event: Event) -> BotReply:
    """群聊且被 @ 阿敏 的策略：当前版本固定回复“不好”."""
    return BotReply(text="不好")

