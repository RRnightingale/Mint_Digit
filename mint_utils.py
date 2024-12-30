import logging
from collections import defaultdict
import time
import traceback

import llob_utils
import user_manager
import memory
import chat_agent

MINT_NAME = "阿敏"

# 初始化ChatMemory
chat_memory = memory.create_chat_memory(type='evil')


MAX_WORDS = 900  # old limit
AT_MINT = "[CQ:at,qq=3995633031"
MAX_MESSAGES_PER_HOUR = 10

# 用户消息计数, 用于计算每个人的发言次数
user_message_count = defaultdict(lambda: {"count": 0, "last_reset": time.time()})

current_group_id = 0     # 群ID


def handle(data: dict):
    """
    处理接收到的数据，根据消息类型进行相应的处理

    参数:
    data (dict): 接收到的事件数据

    返回:
    dict: 错误信息或空字典
    """
    global current_group_id
    logging.debug(f"接收到的数据: {data}")
    post_type = data.get('post_type')  # 数据类型
    if post_type == "message":  # 私聊或群聊

        user_id = str(data.get('user_id'))  # 读取user id并转换为字符串
        group_user_name = data.get('sender', {}).get('card', "")  # 可能为空
        nickname = data.get('sender', {}).get('nickname')  # 读取 nick name
        user_name = group_user_name or nickname  # 有群名用群
        # user_name = f"{user_name}({user_id})"  # nick name太危险了，还是用id吧
        raw_message = data.get('raw_message')  # 获取原始消息
        message_type = data.get('message_type')  # 获取消息类型
        group_id = data.get('group_id')  # 获取群ID（如果有）

        user_name = user_name_check(user_name=user_name, user_id=user_id)

        if not user_id:
            logging.error("缺少 user_id")
            return {"error": "缺少 user_id"}

        if not raw_message:
            logging.error("缺少 raw_message")
            return {"error": "缺少 raw_message"}

        if message_type == 'private':
            # 处理私信， 私聊不做过滤（夜鹰通道）
            reply_text = chat_agent.chat(
                user_name=user_name, input_text=raw_message)
            # reply_text = reply_without_action(
            #     user_name, raw_message)  # 调用reply
            logging.debug(f"生成的回复: {reply_text}")
            response = llob_utils.send_private_message(
                user_id, reply_text)  # 向user发送私信
            logging.debug(
                f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")
        elif message_type == 'group' and group_id:  # 处理群聊
            current_group_id = group_id  # 更新群id

            user_manager.update_user(user_id, {
                "aliases": [nickname, group_user_name]
            })

            # 如果艾特阿敏
            if AT_MINT in raw_message:
                message = chat_memory.clean_message(raw_message)
                if check_user_message_limit(user_id):

                    reply_text = chat_agent.chat(
                        user_name=user_name, input_text=message)
                    # reply_text = reply_group(
                        # user_name, message)  # 调用reply,记录信息
                    response = llob_utils.send_group_message_with_at(
                        group_id, reply_text, user_id)  # 向群发送消息
                    logging.debug(
                        f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")
                else:
                    reply_text = f"杂鱼，你已达到每小时最大请求次数。赶紧充钱"
                    llob_utils.send_group_message_with_at(
                        group_id, reply_text, user_id)
            else: # 增加记忆
                # 检测重复消息， 超过3次禁言
                message = chat_memory.clean_message(raw_message)
                content = f"{user_name} 说：{message}"
                chat_agent.update_memory(content)
                # chat_memory.save_chat_memory(user_name, message)
                if chat_agent.check_duplicate():
                    logging.info(
                        f"check_dulplicate: memory = {chat_memory.get_memory()}")
                    # llob_utils.set_group_ban(group_id, user_id, 10 * 60)
                    instruction = f"{user_id} 在群里发重复信息，你是执行官，请你对其禁言 10 分钟, 说明缘由"
                    instructer = "夜鹰"
                    # reply_text = reply_without_action(
                    #     instructer, instruction, tool_choice="required")
                    reply_text = chat_agent.chat(
                        user_name=instructer, input_text=instruction)
                    llob_utils.send_group_message_with_at(
                        group_id, reply_text, user_id)
        else:
            logging.error("未知的消息类型或缺少群ID")
            return {"error": "未知的消息类型或缺少群ID"}

    elif post_type == "request":
        # 好友请求或加群请求

        comment = data.get('comment')  # 验证信息
        request_type = data.get('request_type')  # 好友or群申请
        user_id = data.get('user_id')
        flag = data.get('flag')  # 请求号
        if request_type == "group":  # 加群申请
            logging.info(f"收到 {user_id} 的加群请求")
            # if 赞美夜鹰 则 通过
            instruction = f"判断以下请求是否赞美夜鹰(需要内容为赞美，且赞美目标为夜鹰)，是则 回复【是】，否则回复【否】。不能包含其他回复: ---{comment}---"
            instructer = "夜鹰"
            reply_text = chat_agent.chat(instructer, instruction)

            approve = "是" in reply_text  # 同意加群
            logging.info(f"{user_id} 申请加群， 结果 {approve}, {reply_text}")
            llob_utils.set_group_add_request(flag=flag, approve=approve)

    return {}

def check_user_message_limit(user_id):
    """
    检查用户是否超过每小时消息限制

    参数:
    user_id (int): 用户ID

    返回:
    bool: 是否在限制内
    """
    current_time = time.time()
    user_data = user_message_count[user_id]
    
    # 如果距离上次重置已经过去了10分钟，重置计数器
    if current_time - user_data["last_reset"] > 600:
        user_data["count"] = 0
        user_data["last_reset"] = current_time
    
    # 增加计数器
    user_data["count"] += 1
    
    # 检查是否超过限制
    if user_data["count"] <= MAX_MESSAGES_PER_HOUR:
        return True
    else:
        logging.info(f"用户 {user_id} 已达到每小时最大请求次数")
        return False

def user_name_check(user_name: str, user_id: str, check="夜鹰", real_user_id="631038409", flag="(冒充的)") -> str:
    if check in user_name and user_id != real_user_id:
        return user_name + flag
    return user_name
