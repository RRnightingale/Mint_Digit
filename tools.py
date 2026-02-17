from logger import get_logger
from config import get_config
import napcat_client
from group_manager import group_manager


logger = get_logger("tools")
config = get_config()


def ban_group_member(group_id: str, user_id: str, duration: int = 1800) -> str:
    """禁言群成员。
    
    Args:
        group_id: 群聊ID
        user_id: 用户ID
        duration: 禁言时长（秒），默认1800秒（30分钟）
        
    Returns:
        操作结果描述
    """
    try:
        resp = napcat_client.set_group_ban(group_id, user_id, duration)
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                logger.info("禁言成功: group_id=%s, user_id=%s, duration=%d", group_id, user_id, duration)
                return f"已成功禁言用户 {user_id}，时长 {duration} 秒"
            else:
                logger.warning("禁言失败: %s", data)
                return f"禁言失败: {data.get('message', '未知错误')}"
        else:
            logger.error("禁言请求失败: status_code=%d", resp.status_code if resp else None)
            return "禁言请求失败"
    except Exception as e:
        logger.error("禁言操作出错: %s", e)
        return f"禁言操作出错: {str(e)}"


def kick_group_member(group_id: str, user_id: str, reject_add_request: bool = False) -> str:
    """踢出群成员。
    
    Args:
        group_id: 群聊ID
        user_id: 用户ID
        reject_add_request: 是否拒绝加群请求，默认False
        
    Returns:
        操作结果描述
    """
    try:
        resp = napcat_client.set_group_kick(group_id, user_id, reject_add_request)
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                logger.info("踢人成功: group_id=%s, user_id=%s, reject_add_request=%s", group_id, user_id, reject_add_request)
                return f"已成功踢出用户 {user_id}"
            else:
                logger.warning("踢人失败: %s", data)
                return f"踢人失败: {data.get('message', '未知错误')}"
        else:
            logger.error("踢人请求失败: status_code=%d", resp.status_code if resp else None)
            return "踢人请求失败"
    except Exception as e:
        logger.error("踢人操作出错: %s", e)
        return f"踢人操作出错: {str(e)}"


def get_group_member_info(group_id: str, user_id: str) -> str:
    """获取群成员信息。
    
    Args:
        group_id: 群聊ID
        user_id: 用户ID
        
    Returns:
        成员信息描述
    """
    try:
        group = group_manager.get_group(group_id)
        if not group:
            return f"群组 {group_id} 不存在"
        
        member = group.get_member_by_id(user_id)
        if not member:
            return f"用户 {user_id} 不在群组中"
        
        info = f"用户ID: {member.user_id}\n"
        info += f"昵称: {member.nickname}\n"
        info += f"入群时间: {member.get_formatted_join_time()}\n"
        info += f"群名片: {member.card}\n"
        info += f"性别: {member.sex}\n"
        info += f"年龄: {member.age}\n"
        info += f"等级: {member.level}\n"
        info += f"QQ等级: {member.qq_level}\n"
        info += f"角色: {member.role}\n"
        
        return info
    except Exception as e:
        logger.error("获取群成员信息出错: %s", e)
        return f"获取群成员信息出错: {str(e)}"


def get_group_members_list(group_id: str) -> str:
    """获取群成员列表。
    
    Args:
        group_id: 群聊ID
        
    Returns:
        成员列表描述
    """
    try:
        group = group_manager.get_group(group_id)
        if not group:
            return f"群组 {group_id} 不存在"
        
        members = group.get_members()
        if not members:
            return f"群组 {group_id} 没有成员"
        
        info = f"群组 {group_id} 成员列表（共 {len(members)} 人）：\n"
        for i, member in enumerate(members, 1):
            info += f"{i}. {member.nickname} (ID: {member.user_id})\n"
        
        return info
    except Exception as e:
        logger.error("获取群成员列表出错: %s", e)
        return f"获取群成员列表出错: {str(e)}"


def get_group_basic_info(group_id: str) -> str:
    """获取群基本信息。
    
    Args:
        group_id: 群聊ID
        
    Returns:
        群基本信息描述
    """
    try:
        group_info = napcat_client.get_group_info(group_id)
        if not group_info:
            return f"群组 {group_id} 不存在"
        
        info = f"群ID: {group_info.get('group_id', group_id)}\n"
        info += f"群名称: {group_info.get('group_name', '未知')}\n"
        info += f"群成员数: {group_info.get('member_count', 0)}\n"
        info += f"群主ID: {group_info.get('owner_id', '未知')}\n"
        
        return info
    except Exception as e:
        logger.error("获取群基本信息出错: %s", e)
        return f"获取群基本信息出错: {str(e)}"


# 定义工具列表，用于function call
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ban_group_member",
            "description": "禁言群成员",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "群聊ID"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "用户ID"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "禁言时长（秒），默认1800秒（30分钟）"
                    }
                },
                "required": ["group_id", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "kick_group_member",
            "description": "踢出群成员",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "群聊ID"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "用户ID"
                    },
                    "reject_add_request": {
                        "type": "boolean",
                        "description": "是否拒绝加群请求，默认False"
                    }
                },
                "required": ["group_id", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_group_member_info",
            "description": "获取群成员信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "群聊ID"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "用户ID"
                    }
                },
                "required": ["group_id", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_group_members_list",
            "description": "获取群成员列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "群聊ID"
                    }
                },
                "required": ["group_id"]
            }
        }
    }
]


# 工具映射字典，用于根据工具名称调用对应的函数
TOOL_FUNCTIONS = {
    "ban_group_member": ban_group_member,
    "kick_group_member": kick_group_member,
    "get_group_member_info": get_group_member_info,
    "get_group_members_list": get_group_members_list
}
