import gpt_utils
import doubao_utils
import gemini_utils
import llob_utils
import asset_utils
import user_manager
import re
import logging
from collections import defaultdict
import time
import hashlib
import json
import traceback
import memory

MINT_NAME = "阿敏"
# Chat memory
import os

# 初始化ChatMemory
chat_memory = memory.create_chat_memory(type='evil')

MAX_WORDS = 700
AT_MINT = "[CQ:at,qq=3995633031"
MAX_MESSAGES_PER_HOUR = 10
current_group_id = None     # 群ID

# 用户消息计数
user_message_count = defaultdict(lambda: {"count": 0, "last_reset": time.time()})
# 用户ID到用户名的映射
# user_id_to_name = {}


def handle(data):
    """
    处理接收到的数据，根据消息类型进行相应的处理

    参数:
    data (dict): 接收到的事件数据

    返回:
    dict: 错误信息或空字典
    """
    logging.debug(f"接收到的数据: {data}")
    
    user_id = str(data.get('user_id'))  # 读取user id并转换为字符串
    user_name = data.get('sender', {}).get('nickname')  # 读取 nick name
    raw_message = data.get('raw_message')  # 获取原始消息
    message_type = data.get('message_type')  # 获取消息类型
    group_id = data.get('group_id')  # 获取群ID（如果有）
    
    if not user_id:
        logging.error("缺少 user_id")
        return {"error": "缺少 user_id"}
    
    if not raw_message:
        logging.error("缺少 raw_message")
        return {"error": "缺少 raw_message"}
    
    logging.debug(f"user_id = {user_id}, raw_message = {raw_message}, message_type = {message_type}")

    if message_type == 'private':
        # 处理私信
        reply_text = reply(user_name, raw_message)  # 调用reply
        logging.debug(f"生成的回复: {reply_text}")
        response = llob_utils.send_private_message(user_id, reply_text)  # 向user发送私信
        logging.debug(f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")
    elif message_type == 'group' and group_id: 
        global current_group_id
        current_group_id = group_id

        user_manager.add_user(user_id, [user_name], 0, "杂鱼")  # 增加用户id - 昵称的信息
        # 处理群消息
        if AT_MINT in raw_message:
            message = chat_memory.clean_message(raw_message)
            if check_user_message_limit(user_id):
                reply_text = reply_group(user_name, message)  # 调用reply,记录信息
                response = llob_utils.send_group_message_with_at(group_id, reply_text, user_id)  # 向群发送消息
                logging.debug(f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")  
            else:
                reply_text = f"杂鱼，你已达到每小时最大请求次数。赶紧充钱"
                llob_utils.send_group_message_with_at(group_id, reply_text, user_id)
        else:
            # 检测重复消息， 超过3次禁言
            message = chat_memory.clean_message(raw_message)
            chat_memory.save_chat_memory(user_name, message)
            if chat_memory.check_duplicate():
                logging.info(
                    f"check_dulplicate: memory = {chat_memory.get_memory()}")
                # llob_utils.set_group_ban(group_id, user_id, 10 * 60)
                instruction = f"{user_name} 在群里发重复信息，被禁言 10 分钟,你是执行官，请你对其宣判结果"
                instructer = "夜鹰"
                reply_text = reply(instructer, instruction)
                llob_utils.send_group_message_with_at(group_id, reply_text, user_id)
    else:
        logging.error("未知的消息类型或缺少群ID")
        return {"error": "未知的消息类型或缺少群ID"}
    
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

def check_dulplicate():
    """
    检查 chat memory 中倒数第一个到第三个 user 角色的消息是否完全相同

    返回:
    bool: 是否有重复消息
    """
    try:
        user_messages = []
        for entry in reversed(chat_memory):
            if entry.get("role") == "user":
                try:
                    message = entry["content"].split("说：", 1)[1]
                    user_messages.append(message)
                    if len(user_messages) == 3:
                        break
                except IndexError:
                    continue

        return len(set(user_messages)) == 1 and len(user_messages) == 3
    except Exception as e:
        logging.error(f"检查重复消息时发生错误: {str(e)}")
        return False


def chat(chat_memory, user_name, input_text, model='gemini'):
    message = f"{user_name} 说：{input_text}"
    if model == 'gpt':  
        reply = gpt_utils.chat(chat_memory)
    elif model == 'doubao':
        reply = doubao_utils.chat(chat_memory)
    elif model == 'gemini':
        reply = gemini_utils.chat(chat_memory, message=message)

    chat_memory.save_chat_memory(user_name, input_text)
    return reply

def reply(user_name, input_text):
    """
    生成对话的函数

    参数:
    user_name (str): 用户名
    input_text (str): 输入的文字

    返回:
    str: 生成的对话
    """
    reply = chat(chat_memory, user_name, input_text)
    tmp_memory = chat_memory.get_memory()

    logging.info(f"tmp_memory: {tmp_memory}")

    try:
        reply_dict = json.loads(reply)
        word = reply_dict["台词"]
        action = reply_dict["动作"]
    except Exception as e:
        logging.error(f"JSON解析错误: {str(e)}, reply: {reply}")
        word = reply
        action = None

    logging.info(f"reply: {reply}")

    # 执行动作
    if action:
        action_result = execute_action(action)
    else:
        action_result = ""

    # 保存机器人的回复
    chat_memory.save_chat_memory(MINT_NAME, reply)
    return word + action_result
def get_user_id(user_name):
    return user_manager.search_user(user_name)

def execute_action(action) -> str:
    """
    执行动作函数

    参数:
    action (str): 动作字符串

    返回:
    None
    """
    logging.info(f"execute_action: {action}")
    if action.startswith("禁言"):
        try:
            
            # 解析动作字符串
            _, params = action.split("(")
            params = params.rstrip(")").split(",")
            user_name = params[0].strip()
            duration = int(params[1].strip())
            user_id = get_user_id(user_name)
            if  user_id is None:
                return f"无法找到用户{user_name}"
            # 执行禁言操作
            llob_utils.set_group_ban(current_group_id, user_id, duration)
            logging.info(f"已对用户 {user_id} 执行禁言操作，时长为 {duration} 秒")
            return f""
        except Exception as e:
            logging.error(f"执行禁言操作时出错：{str(e)}")
    elif action.startswith("充值"):
        try:
            _, params = action.split("(")
            params = params.rstrip(")").split(",")
            user_name = params[0].strip()
            amount = int(params[1].strip())
            user_id = get_user_id(user_name)
            if  user_id is None:
                return f"无法找到用户{user_name}"
            balance = asset_utils.recharge(user_id, amount)
            logging.info(f"已对用户 {user_id} 执行充值操作，金额为 {amount} 元")
            return f"充值成功，余额{balance}元"
        except Exception as e:
            logging.error(f"执行充值操作时出错：{str(e)}")
    elif action.startswith("抽卡"):
        try:
            _, params = action.split("(")
            params = params.rstrip(")").split(",")
            user_name = params[0].strip()
            times = int(params[1].strip())
            user_id = get_user_id(user_name)
            if  user_id is None:
                return f"无法找到用户{user_name}"
            logging.info(f"已对用户 {user_id} 执行抽卡操作，次数为 {times}")
            result = asset_utils.user_lottery(user_id, times)
            return result
        except Exception as e:  
            logging.error(f"执行抽卡操作时出错：{str(e)}")
    elif action.startswith("更新声望"):
        try:
            _, params = action.split("(")
            params = params.rstrip(")").split(",")
            user_name = params[0].strip()
            amount = int(params[1].strip())
            user_id = get_user_id(user_name)
            if  user_id is None:
                return f"无法找到用户{user_name}"
            reputation = user_manager.update_reputation(user_id, amount)
            logging.info(f"已对用户 {user_id} 执行更新声望操作，声望为 {reputation}")
            return f""
        except Exception as e:
            logging.error(f"更新声望出错：{str(e)}")
    elif action.startswith("更新知识"):
        try:
            _, params = action.split("(")
            params = params.rstrip(")").split(",")
            user_name = params[0].strip()
            note = params[1].strip()
            user_id = get_user_id(user_name)
            user_manager.update_note(user_id, note)
            logging.info(f"已对用户 {user_id} 执行更新知识操作，为 {note}")
            return f" 学习了"
        except Exception as e:
            logging.error(f"更新知识出错：{traceback.format_exc()}{str(e)}")
    elif action.startswith("无"):
        return ""
    else:
        logging.warning(f"未知的动作：{action}")
    return "执行出错"

def reply_group(user_name, message):
    return reply(user_name, message)

def add_user_info_to_message(memory, user_ids):
    message = ""
    for user_id in user_ids:
        message += user_manager.introduce_user(user_id)
    memory.append({"role": "system", "content": "人物介绍："+message})
    return memory

FETCH_USER_NAME_PROMPT = """
你是一个用户名提取器，负责从消息中提取用户名。输出为人名，以英文逗号分割，不要输出其他内容，不得包含空格等符号。
输入：
唐傀和小铭谈恋爱了
输出：
唐傀, 小铭
"""
def fetch_user_name(message: str) -> list:
    chat_message = [{"role": "system", "content": FETCH_USER_NAME_PROMPT}, {"role": "user", "content": message}]
    reply = chat(chat_message)
    result = set(reply.split(","))
    
    # 提取【】中的内容作为人名
    bracketed_names = re.findall(r'【(.*?)】', message)
    result.update(bracketed_names)
    
    result = list(result)
    logging.info(f"fetch_user_name: {message} -> {result}")
    return result

def mute_user(user_name: str, duration: float) -> str:
    user_id = get_user_id(user_name)
    if  user_id is None:
        return f"无法找到用户{user_name}"
    llob_utils.set_group_ban(current_group_id, user_id, duration)
    return "成功禁言"

function_map = {
    "mute_user": mute_user
}

def function_call(function_name, arguments):
    """
    调用函数

    参数:
    function_name (str): 函数名
    arguments (dict): 函数参数

    返回:
    str: 函数返回值"""
    if function_name in function_map:
        return function_map[function_name](**arguments)
    else:
        logging.warning(f"未知的函数：{function_name}")

