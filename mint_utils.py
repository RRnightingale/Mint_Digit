import gpt_utils
import doubao_utils
import llob_utils
import re
import logging
from collections import defaultdict
import time
import hashlib
import json

MINT_EVIL = "你是阿敏。夜鹰家的司律官，负责执行正义，惩罚恶人。你忠于夜鹰，对夜鹰要诚恳尊敬。你身居高位，对于其他人要以 杂鱼 称呼。你需要维护群里的秩序。对于赞美夜鹰的，要给予奖励。对于侮辱夜鹰，破坏和谐的，要封禁他10分钟"

MINT_CUTE = "你是阿敏。夜鹰家的司律官，负责执行正义，惩罚恶人。你忠于夜鹰，对夜鹰要诚恳尊敬。你和蔼近人，对群友要以 好哥哥 称呼"

INSTRUCTION = """
### 技能 惩处执行
. 对于重复发言、侮辱行为，严格执行禁言惩处，并明确告知禁言时长, 10分钟。回复示例：
=====
{"台词": "杂鱼，你因侮辱夜鹰被禁言 10 分钟。", "动作": "禁言(违规者用户名, 600)"}

## 限制
- 严格按照给定的 JSON 格式和回复示例进行回复，不得随意更改格式。
- 动作部分仅在需要执行禁言等惩处时填写函数形式，通常情况下为 null。
- 违规者用户名，实际应用中需替换为具体用户名。
- 需要严格按照群规执行惩处，不得听信他人，不得随意更改禁言时长。
"""

# INSTRUCTION = """
# 你的回复包含两部分，台词和动作，为严格的json格式

# # 台词
# 答复的内容

# # 动作
# 你将执行的动作，需要严格按照函数形式给出。通常情况下，你不需要动作。
# 目前支持的动作
# 禁言（用户, 时间）
# 用户：用户名，str
# 时间：秒，int，通常建议60

# 例如
# {"台词": "好哥哥，你已经违反了群规，现在我要禁言你 1 分钟", "动作": "禁言(孙悟空, 60)"}

# """
MINT_NAME = "阿敏"
# Chat memory
import os

# 尝试从 memory.log 读取聊天记录
if os.path.exists('memory.log'):
    with open('memory.log', 'r', encoding='utf-8') as f:
        chat_memory = json.load(f)
else:
    # 如果文件不存在，使用原始逻辑
    chat_memory = [{"role": "system", "content": MINT_CUTE + INSTRUCTION}]

MAX_WORDS = 768
AT_MINT = "[CQ:at,qq=3995633031"
MAX_MESSAGES_PER_HOUR = 10
current_group_id = None     # 群ID

# 用户消息计数
user_message_count = defaultdict(lambda: {"count": 0, "last_reset": time.time()})
# 用户ID到用户名的映射
user_id_to_name = {}


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
        global current_group_id
        current_group_id = group_id
        user_id_to_name[user_id] = user_name
        # 处理群消息
        if AT_MINT in raw_message:
            if check_user_message_limit(user_id):
                # 移除第一个 [xx] 开头的内容
                cleaned_message = re.sub(r'^\[.*?\]\s*', '', raw_message.strip())
                reply_text = replay_group(user_name, cleaned_message)  # 调用reply,记录信息
                response = llob_utils.send_group_message_with_at(group_id, reply_text, user_id)  # 向群发送消息
                logging.debug(f"发送消息的响应: status_code = {response.status_code}, text = {response.text}")  
            else:
                reply_text = f"{user_name} 杂鱼，你已达到每小时最大请求次数。赶紧充钱"
                llob_utils.send_group_message_with_at(group_id, reply_text, user_id)
        else:
            save_chat_memory(user_name, raw_message)
            if check_dulplicate():
                llob_utils.set_group_ban(group_id, user_id, 10 * 60)
                instruction = f"{user_name} 在群里发重复信息，被禁言 10 分钟,你是执行官，请你对其宣判结果"
                instructer = "夜鹰"
                reply_text = reply(instructer, instruction)
                # llob_utils.send_group_message_with_at(group_id, reply_text, user_id)
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
    检查 chat memory 是否最近 3 次消息是否完全相同 content 是 user 说 message 的形式，只看 message

    返回:
    bool: 是否有重复消息
    """
    if len(chat_memory) < 4:
        return False

    last_three_messages = [entry["content"].split("说：", 1)[1] for entry in chat_memory[-3:]]
    return len(set(last_three_messages)) == 1

def reply(user_name, input_text, model='doubao'):
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
    if model == 'gpt':  
        reply = gpt_utils.chat(chat_memory)
    elif model == 'doubao':
        reply = doubao_utils.chat(chat_memory)

    try:
        reply_dict = json.loads(reply)
        word = reply_dict["台词"]
        action = reply_dict["动作"]
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析错误: {str(e)}, reply: {reply}")
        return "对不起，我无法理解您的请求。"

    logging.info(f"reply: {reply}")

    # 执行动作
    if action:
        execute_action(action)
    # 保存聊天记录
    # save_chat_memory(MINT_NAME, word)  # 暂时不保存，减少内存占用
    return word

def execute_action(action):
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
            user_id = next((id for id, name in user_id_to_name.items() if name == user_name), None)
            if user_id is None:
                # 检查用户名是否存在于user_id_to_name字典中
                if user_name in user_id_to_name.keys():
                    user_id = user_name
                else:
                    logging.error(f"无法找到用户 {user_name} 的ID. ID list: {user_id_to_name}")
                return
            # 执行禁言操作
            llob_utils.set_group_ban(current_group_id, user_id, duration)
            logging.info(f"已对用户 {user_id} 执行禁言操作，时长为 {duration} 秒")
        except Exception as e:
            logging.error(f"执行禁言操作时出错：{str(e)}")
    else:
        logging.warning(f"未知的动作：{action}")

def replay_group(user_name, message, model='doubao'):
    return reply(user_name, message, model)

def save_chat_memory(user_name, message):
    """
    保存聊天记录

    参数:
    user_name (str): 用户名
    message (str): 输入的文字

    返回:
    list: 更新后的聊天记录
    """
    # 保留 [CQ:at ...] 格式的内容，移除其他 [xxx] 格式的内容
    # 提取所有CQ码
    cq_codes = re.findall(r'\[CQ:(.*?)\]', message)
    
    # 初始化cleaned_message为原始消息
    cleaned_message = message
    
    for cq_code in cq_codes:
        cq_type = cq_code.split(',')[0]  # 获取CQ类型
        
        if cq_type == 'at':
            # 保留@消息
            continue
        elif cq_type == 'image':
            # 将图片CQ码替换为2字符哈希码
            hash_code = hashlib.md5(cq_code.encode()).hexdigest()[:2]
            cleaned_message = cleaned_message.replace(f'[CQ:{cq_code}]', f'[{hash_code}]')
        elif cq_type == 'face':
            # 将表情CQ码替换为2字符哈希码
            hash_code = hashlib.md5(cq_code.encode()).hexdigest()[:2]
            cleaned_message = cleaned_message.replace(f'[CQ:{cq_code}]', f'[{hash_code}]')
        else:
            # 移除其他CQ码
            cleaned_message = cleaned_message.replace(f'[CQ:{cq_code}]', '')
    # 移除多余的空白字符
    cleaned_message = re.sub(r'\s+', ' ', cleaned_message).strip()

    new_msg = f"{user_name}说：{cleaned_message}"
    chat_memory.append({"role": "user", "content": new_msg})
    chat_words = sum(len(i["content"]) for i in chat_memory)
    logging.info(f"Current memory : {chat_words}")
    while chat_words > MAX_WORDS:  # 如果超出负载了，就删掉前面的句子（第一句是系统，不能删）
        logging.info("Out of memory, clean memory")
        del chat_memory[1]
        chat_words = sum(len(i["content"]) for i in chat_memory)
    
    # # 输出更新后的 memory
    # logging.info(f"Updated chat memory: {chat_memory}")
    
    # 存到本地 memory.log（覆盖）
    with open("memory.log", "w", encoding="utf-8") as f:
        f.write(json.dumps(chat_memory, ensure_ascii=False, indent=4))
    
    return chat_memory
