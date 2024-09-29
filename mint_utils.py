import gpt_utils

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
    new_msg = f"{user_name}说：{message}"
    reply = gpt_utils.gpt_chat(new_msg)
    return reply

