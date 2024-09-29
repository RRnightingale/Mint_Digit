import gpt_utils
import logging

# Chat memory
chat_memory = [{"role": "system", "content": "你是阿敏。你夜鹰家的司律官，负责执行正义，惩罚恶人。你忠于夜鹰，对夜鹰要诚恳尊敬。你身居高位，对于其他人要以【杂鱼】称呼"}]
MAX_WORDS = 2048

def handle(group_msg):
    return reply

def reply(input_text):
    """
    生成对话的函数
    
    参数:
    input_text (str): 输入的文字
    
    返回:
    str: 生成的对话
    """
    
    # 调用 gpt_utils 生成智能回复
    reply = gpt_utils.gpt_chat(input_text)
    
    return reply

def replay_group(user_name, message):
    new_msg = save_chat_memory(user_name, message)
    reply = gpt_utils.gpt_chat(new_msg)
    return reply

def save_chat_memory(user_name, message):
    new_msg = f"{user_name}说：{message}"
    chat_memory.append({"role": "user", "content": new_msg})
    chat_words = sum(len(i["content"]) for i in chat_memory)
    logging.info(f"Current memory : {chat_words}")
    while chat_words > MAX_WORDS:  # 如果超出负载了，就删掉前面的句子（第一句是系统，不能删）
        logging.info("Out of memory, clean memory")
        del chat_memory[1]
        chat_words = sum(len(i["content"]) for i in chat_memory)
    return chat_memory
