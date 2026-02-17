from fastapi import APIRouter, HTTPException
from logger import get_logger
from group_manager import group_manager


logger = get_logger("visualization")
router = APIRouter(prefix="/api", tags=["visualization"])


@router.get("/groups")
def get_all_groups():
    """获取所有群组信息。"""
    try:
        groups = group_manager.get_all_groups()
        result = {}
        for group_id, group in groups.items():
            result[group_id] = {
                "group_id": group.group_id,
                "member_count": len(group.members),
                "chat_history_count": len(group.chat_history),
                "members": [member.to_dict() for member in group.members]
            }
        logger.info("获取所有群组信息成功，群组数量: %d", len(result))
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error("获取所有群组信息失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取群组信息失败: {str(e)}")


@router.get("/groups/{group_id}")
def get_group_info(group_id: str):
    """获取指定群组信息。
    
    Args:
        group_id: 群聊ID
    """
    try:
        group = group_manager.get_group(group_id)
        if not group:
            logger.warning("群组不存在: %s", group_id)
            raise HTTPException(status_code=404, detail=f"群组不存在: {group_id}")
        
        result = {
            "group_id": group.group_id,
            "member_count": len(group.members),
            "chat_history_count": len(group.chat_history),
            "members": [member.to_dict() for member in group.members]
        }
        logger.info("获取群组信息成功: %s", group_id)
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取群组信息失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取群组信息失败: {str(e)}")


@router.get("/groups/{group_id}/members")
def get_group_members(group_id: str):
    """获取指定群组的成员列表。
    
    Args:
        group_id: 群聊ID
    """
    try:
        group = group_manager.get_group(group_id)
        if not group:
            logger.warning("群组不存在: %s", group_id)
            raise HTTPException(status_code=404, detail=f"群组不存在: {group_id}")
        
        members = [member.to_dict() for member in group.members]
        logger.info("获取群组成员列表成功: %s，成员数量: %d", group_id, len(members))
        return {"status": "success", "data": {"group_id": group_id, "members": members}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取群组成员列表失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取群组成员列表失败: {str(e)}")


@router.get("/groups/{group_id}/ranking")
def get_group_ranking(group_id: str):
    """获取指定群组的入群排名。
    
    Args:
        group_id: 群聊ID
    """
    try:
        group = group_manager.get_group(group_id)
        if not group:
            logger.warning("群组不存在: %s", group_id)
            raise HTTPException(status_code=404, detail=f"群组不存在: {group_id}")
        
        # 按入群时间排序
        members = sorted(group.members, key=lambda m: m.join_time)
        
        # 格式化输出
        ranking = []
        for index, member in enumerate(members, 1):
            ranking.append({
                "rank": index,
                "user_id": member.user_id,
                "nickname": member.nickname,
                "join_time": member.join_time,
                "formatted_join_time": member.get_formatted_join_time()
            })
        
        logger.info("获取群组入群排名成功: %s，成员数量: %d", group_id, len(ranking))
        return {"status": "success", "data": {"group_id": group_id, "ranking": ranking}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取群组入群排名失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取群组入群排名失败: {str(e)}")


@router.get("/groups/{group_id}/history")
def get_group_history(group_id: str, limit: int = 50):
    """获取指定群组的聊天历史。
    
    Args:
        group_id: 群聊ID
        limit: 返回的历史记录数量限制，默认50条
    """
    try:
        group = group_manager.get_group(group_id)
        if not group:
            logger.warning("群组不存在: %s", group_id)
            raise HTTPException(status_code=404, detail=f"群组不存在: {group_id}")
        
        # 获取历史记录
        history = group.get_chat_history()
        
        # 限制返回数量
        if limit > 0:
            history = history[-limit:]
        
        # 格式化输出
        formatted_history = []
        for msg in history:
            msg_type = msg.__class__.__name__
            formatted_history.append({
                "type": msg_type,
                "content": msg.content
            })
        
        logger.info("获取群组聊天历史成功: %s，历史记录数量: %d", group_id, len(formatted_history))
        return {"status": "success", "data": {"group_id": group_id, "history": formatted_history}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取群组聊天历史失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取群组聊天历史失败: {str(e)}")


@router.delete("/groups/{group_id}/history")
def clear_group_history(group_id: str):
    """清空指定群组的聊天历史。
    
    Args:
        group_id: 群聊ID
    """
    try:
        group = group_manager.get_group(group_id)
        if not group:
            logger.warning("群组不存在: %s", group_id)
            raise HTTPException(status_code=404, detail=f"群组不存在: {group_id}")
        
        group.clear_chat_history()
        logger.info("清空群组聊天历史成功: %s", group_id)
        return {"status": "success", "message": f"群组 {group_id} 的聊天历史已清空"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("清空群组聊天历史失败: %s", e)
        raise HTTPException(status_code=500, detail=f"清空群组聊天历史失败: {str(e)}")
