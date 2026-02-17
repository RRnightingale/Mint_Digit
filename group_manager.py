from logger import get_logger
from langchain_core.messages import HumanMessage, AIMessage


logger = get_logger("group_manager")


class Member:
    """成员类：封装群成员信息。"""

    def __init__(self, **kwargs):
        """初始化成员。
        
        Args:
            **kwargs: 成员信息，只读取有效参数
        """
        self.user_id = str(kwargs.get("user_id", ""))
        self.nickname = kwargs.get("nickname", "未知")
        self.join_time = kwargs.get("join_time", 0)
        self.card = kwargs.get("card", "")
        self.sex = kwargs.get("sex", "unknown")
        self.age = kwargs.get("age", 0)
        self.area = kwargs.get("area", "")
        self.level = kwargs.get("level", "0")
        self.qq_level = kwargs.get("qq_level", 0)
        self.last_sent_time = kwargs.get("last_sent_time", 0)
        self.title_expire_time = kwargs.get("title_expire_time", 0)
        self.unfriendly = kwargs.get("unfriendly", False)
        self.card_changeable = kwargs.get("card_changeable", True)
        self.is_robot = kwargs.get("is_robot", False)
        self.shut_up_timestamp = kwargs.get("shut_up_timestamp", 0)
        self.role = kwargs.get("role", "member")
        self.title = kwargs.get("title", "")

    def get_formatted_join_time(self) -> str:
        """获取格式化的入群时间。
        
        Returns:
            格式化后的时间字符串，格式为"YYYY-MM-DD HH:MM:SS"
        """
        import datetime
        
        try:
            dt = datetime.datetime.fromtimestamp(self.join_time)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "未知时间"

    def to_dict(self) -> dict:
        """将成员信息转换为字典。
        
        Returns:
            成员信息字典
        """
        return {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "join_time": self.join_time,
            "formatted_join_time": self.get_formatted_join_time(),
            "card": self.card,
            "sex": self.sex,
            "age": self.age,
            "area": self.area,
            "level": self.level,
            "qq_level": self.qq_level,
            "last_sent_time": self.last_sent_time,
            "title_expire_time": self.title_expire_time,
            "unfriendly": self.unfriendly,
            "card_changeable": self.card_changeable,
            "is_robot": self.is_robot,
            "shut_up_timestamp": self.shut_up_timestamp,
            "role": self.role,
            "title": self.title
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建成员实例。
        
        Args:
            data: 成员信息字典
            
        Returns:
            Member实例
        """
        return cls(**data)


class Group:
    """群组类：管理群组信息，包括群ID、群成员和历史聊天记录。"""

    def __init__(self, group_id: str):
        """初始化群组。
        
        Args:
            group_id: 群聊ID
        """
        self.group_id = group_id
        self.members = []
        self.chat_history = []
        logger.info("创建群组实例: %s", group_id)

    def update_members(self, members: list) -> None:
        """更新群成员信息。
        
        Args:
            members: 群成员列表，可以是Member实例或字典
        """
        self.members = []
        for member in members:
            if isinstance(member, Member):
                self.members.append(member)
            elif isinstance(member, dict):
                self.members.append(Member.from_dict(member))
        logger.debug("更新群 %s 成员信息，成员数量: %d", self.group_id, len(self.members))

    def get_members(self) -> list:
        """获取群成员信息。
        
        Returns:
            群成员列表
        """
        return self.members

    def get_member_by_id(self, user_id: str) -> Member:
        """根据用户ID获取成员。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Member实例，如果不存在则返回None
        """
        for member in self.members:
            if member.user_id == user_id:
                return member
        return None

    def add_message(self, message: str, is_user: bool = True, user_id: str = None) -> None:
        """添加消息到聊天历史。
        
        Args:
            message: 消息内容
            is_user: 是否为用户消息，True表示用户消息，False表示AI回复
            user_id: 用户ID（仅用户消息需要）
        """
        if is_user:
            if user_id:
                content = f"{user_id}说 {message}"
            else:
                content = message
            self.chat_history.append(HumanMessage(content=content))
        else:
            self.chat_history.append(AIMessage(content=message))
        logger.debug("群 %s 添加消息到历史: %s", self.group_id, message)

    def get_chat_history(self) -> list:
        """获取聊天历史。
        
        Returns:
            聊天历史列表
        """
        return self.chat_history

    def clear_chat_history(self) -> None:
        """清空聊天历史。"""
        self.chat_history = []
        logger.info("清空群 %s 的聊天历史", self.group_id)


class GroupManager:
    """群组管理器：管理所有群组实例。"""

    def __init__(self):
        """初始化群组管理器。"""
        self.groups = {}
        logger.info("群组管理器初始化完成")

    def get_or_create_group(self, group_id: str) -> Group:
        """获取或创建群组实例。
        
        Args:
            group_id: 群聊ID
            
        Returns:
            群组实例
        """
        if group_id not in self.groups:
            self.groups[group_id] = Group(group_id)
            logger.info("创建新群组: %s", group_id)
        return self.groups[group_id]

    def get_group(self, group_id: str) -> Group:
        """获取群组实例。
        
        Args:
            group_id: 群聊ID
            
        Returns:
            群组实例，如果不存在则返回None
        """
        return self.groups.get(group_id)

    def remove_group(self, group_id: str) -> None:
        """移除群组实例。
        
        Args:
            group_id: 群聊ID
        """
        if group_id in self.groups:
            del self.groups[group_id]
            logger.info("移除群组: %s", group_id)

    def get_all_groups(self) -> dict:
        """获取所有群组。
        
        Returns:
            所有群组的字典，key为group_id，value为Group实例
        """
        return self.groups


# 全局群组管理器实例
group_manager = GroupManager()
