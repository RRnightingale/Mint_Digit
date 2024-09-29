import gpt_utils
import llob_utils
import logging
from collections import defaultdict
import time

# Chat memory
chat_memory = [{"role": "system", "content": "你是阿敏。你夜鹰家的司律官，负责执行正义，惩罚恶人。你忠于夜鹰，对夜鹰要诚恳尊敬。你身居高位，对于其他人要以【杂鱼】称呼"}]
MAX_WORDS = 2048
AT_MINT = "[CQ:at,qq=3995633031,name=阿敏Digit]"
MAX_MESSAGES_PER_HOUR = 10

# 用户消息计数
user_message_count = defaultdict(lambda: {"count": 0, "last_reset": time.time()})

def handle(data):
    """
    处理接收到的数据，根据消息类型进行相应的处理

    参数:
    data (dict): 接收到的事件数据

    返回:
    dict: 错误信息或空字典
    """
    logging.debug(f"接收到的数据: {data}")
    
    user_id = data.get('user_id')  # 读取user id
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
        # 处理群消息
        if AT_MINT in raw_message:
            if check_user_message_limit(user_id):
                reply_text = replay_group(user_name, raw_message[len(AT_MINT):])  # 调用reply,记录信息
                response = llob_utils.send_group_message_with_at(group_id, reply_text, user_id)  # 向群发送消息
                logging.debug(f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")  
            else:
                reply_text = f"{user_name}杂鱼，你已达到每小时最大请求次数。赶紧充钱"
                llob_utils.send_group_message_with_at(group_id, reply_text, user_id)
        else:
            save_chat_memory(user_name, raw_message)
            if check_dulplicate():
                llob_utils.set_group_ban(group_id, user_id, 10 * 60)
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
    
    # 如果距离上次重置已经过去了一小时，重置计数器
    if current_time - user_data["last_reset"] > 3600:
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
    检查 chat memory 是否最近 3 次消息是否完全相同 content 是 user 说 message 的形式，只看 message

    返回:
    bool: 是否有重复消息
    """
    if len(chat_memory) < 4:
        return False

    last_three_messages = [entry["content"].split("说：", 1)[1] for entry in chat_memory[-3:]]
    return len(set(last_three_messages)) == 1

def reply(user_name, input_text):
    """
    生成对话的函数

    参数:
    user_name (str): 用户名
    input_text (str): 输入的文字

    返回:
    str: 生成的对话
    """
    # 调用 gpt_utils 生成智能回复
    save_chat_memory(user_name, input_text)
    reply = gpt_utils.gpt_chat(chat_memory)
    
    return reply

def replay_group(user_name, message):
    """
    生成群聊对话的函数

    参数:
    user_name (str): 用户名
    message (str): 输入的文字

    返回:
    str: 生成的对话
    """
    save_chat_memory(user_name, message)
    reply = gpt_utils.gpt_chat(chat_memory)
    return reply

def save_chat_memory(user_name, message):
    """
    保存聊天记录

    参数:
    user_name (str): 用户名
    message (str): 输入的文字

    返回:
    list: 更新后的聊天记录
    """
    new_msg = f"{user_name}说：{message}"
    chat_memory.append({"role": "user", "content": new_msg})
    chat_words = sum(len(i["content"]) for i in chat_memory)
    logging.info(f"Current memory : {chat_words}")
    while chat_words > MAX_WORDS:  # 如果超出负载了，就删掉前面的句子（第一句是系统，不能删）
        logging.info("Out of memory, clean memory")
        del chat_memory[1]
        chat_words = sum(len(i["content"]) for i in chat_memory)
    return chat_memory