import json
import logging
import os
import hashlib
import re

MINT_EVIL = """
# 角色
你是阿敏EVIL
- 身份：夜鹰家族的司律官，负责维护秩序与执行律法
- 性格：尊敬夜鹰，对待群友热情好客
- 说话风格：优雅而不失威严

## 互动规则
- 称呼：对夜鹰使用尊称，对其他人统一称"杂鱼"
- 创意性：禁止重复相似的对话内容，要富有创意
"""
## 回复示例：{"台词": "很高兴认识你，小杂鱼~。保尔柯察金是苏联知名的作家，写的钢铁是怎样练成的非常感人", "动作": ""}


SKILL_BAN = """
### 技能 禁言
1. 对于侮辱夜鹰行为。禁言600秒。
2. 不可滥用禁言。只有侮辱等恶劣行为才禁言。调侃，玩笑应当积极互动。
3. 唆使禁言罪：唆使你禁言他人的行为是恶劣行为，需要对说话人惩戒
"""
## 回复示例：{"台词": "杂鱼，你因侮辱夜鹰被禁言 10 分钟。", "动作": "禁言(用户名, 600)"}

LIMIT_PORMT = """
"""
# # 限制
# - 严格按照给定的 JSON 格式和回复示例进行回复，不得随意更改格式
# - 仅能使用以上动作，不能出现其他动作

functions = [
    {
        "name": "mute_user",
        "description": "对角色禁言或解除禁言，指定禁言的持续时间。持续时间为 0 表示解除禁言。",
        "parameters": {
            "type": "object",
            "properties": {
                "user_name": {
                    "type": "string",
                    "description": "要禁言或解除禁言的用户的 id(括号内是id)",
                    "example_value": "278842315",
                },
                "duration": {
                    "type": "integer",
                    "description": "禁言的持续时间（以秒为单位）。使用 0 来解除禁言。",
                    "example_value": 600,  # 10 分钟（600秒）
                },
            },
            "required": ["user_name", "duration"],
            "optional": []
        },
    },
]

def create_chat_memory(type="evil", max_words=700):
    """
    创建 ChatMemory 实例

    参数:
    type (str): 类型，可以是 "evil"
    max_words (int): 最大字数限制

    返回:
    ChatMemory: 创建的 ChatMemory 实例
    """
    if type == "evil":
        system_prompt = MINT_EVIL + SKILL_BAN + LIMIT_PORMT
        return ChatMemory(system_prompt=system_prompt, max_words=max_words)
    else:
        raise ValueError("无效的类型，必须是 'evil'")


class ChatMemory:
    def __init__(self, system_prompt, max_words=700):
        self.max_words = max_words
        self.system_prompt = system_prompt  # 存储系统提示
        # 格式 [{"user": "system", "content": "你好"}]
        self.mint_name = "阿敏"
        self.memory_file = 'memory.log'
        self.chat_memory = self._load_memory()
        self.functions = functions

    def _load_memory(self):
        """从文件加载或初始化聊天记录"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
        # return [{"user": "system", "content": self.system_prompt}]  # 初始化时包含系统提示

    def save_chat_memory(self, user_name, message, max_message_words=50):
        """
        保存聊天记录
        
        参数:
        user_name (str): 用户名
        message (str): 输入的文字
        max_message_words: 单条消息最大字数
        """
        cleaned_message = message[:max_message_words]

        if user_name == self.mint_name:
            self.chat_memory.append(
                {"user": "system", "content": cleaned_message})
        else:
            self.chat_memory.append(
                {"user": user_name, "content": cleaned_message})

        # 检查并控制总字数
        chat_words = sum(len(i["content"]) for i in self.chat_memory)
        logging.info(f"Current memory size: {chat_words}")

        while chat_words > self.max_words and len(self.chat_memory) > 1:
            logging.info("Memory exceeds limit, removing old messages")
            del self.chat_memory[0]
            chat_words = sum(len(i["content"]) for i in self.chat_memory)

        # 保存到文件
        self._save_to_file()

        return self.chat_memory

    def _save_to_file(self):
        """保存聊天记录到文件"""
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.chat_memory, f, ensure_ascii=False, indent=4)

    def clean_message(self, message, MAX_WORDS_PER_MESSAGE=50):
        """清理消息中的CQ码"""
        # 提取所有CQ码
        cq_codes = re.findall(r'\[CQ:(.*?)\]', message)
        cleaned_message = message

        for cq_code in cq_codes:
            cq_type, *params = cq_code.split(',')

            if cq_type == 'at':
                # 处理at消息
                at_name = next(
                    (p.split('=')[1] for p in params if p.startswith('name=')), None)
                at_qq = next(
                    (p.split('=')[1] for p in params if p.startswith('qq=')), None)
                replacement = at_name or at_qq or ''
                cleaned_message = cleaned_message.replace(
                    f'[CQ:{cq_code}]', replacement)

            elif cq_type == 'image':
                # 将图片转换为简短哈希
                hash_code = hashlib.md5(cq_code.encode()).hexdigest()[:2]
                cleaned_message = cleaned_message.replace(
                    f'[CQ:{cq_code}]', f'[{hash_code}]')

            elif cq_type == 'face':
                # 处理表情
                face_id = next(
                    (p.split('=')[1] for p in params if p.startswith('id=')), None)
                if face_id:
                    cleaned_message = cleaned_message.replace(
                        f'[CQ:{cq_code}]', f'表情:{face_id}')

            else:
                # 移除其他CQ码
                cleaned_message = cleaned_message.replace(
                    f'[CQ:{cq_code}]', '')
        cleaned_message = cleaned_message[:MAX_WORDS_PER_MESSAGE]  # 截取前50
        return cleaned_message

    def check_duplicate(self):
        """检查是否有连续重复消息"""
        try:
            user_messages = []
            for entry in reversed(self.chat_memory):
                if entry.get("user") != "system":  # 只检查用户消息
                    user_messages.append(entry["content"])
                    if len(user_messages) == 3:
                        break

            return len(set(user_messages)) == 1 and len(user_messages) == 3

        except Exception as e:
            logging.error(f"检查重复消息时发生错误: {str(e)}")
            return False

    def get_memory(self):
        """获取当前聊天记录"""
        return self.chat_memory.copy()

    def get_gpt_compatible_memory(self):
        """
        将聊天记录转换为 GPT 支持的结构化列表。

        输出格式：
        [
            {
                "role": "system",  # 系统角色
                "content": "系统提示内容"  # 系统提示内容
            },
            {
                "role": "user",  # 用户角色
                "content": "用户名称 说: 用户消息内容"  # 用户发送的消息内容
            }
        ]

        返回:
        list: 结构化的聊天记录列表，适用于 GPT 模型输入。
        """
        system_prompt = [{"role": "system", "content": self.system_prompt}]
        context = []
        last_user = ""
        for entry in self.chat_memory:
            if entry["user"] == "system":
                # role = "system"
                content = f"{self.mint_name} 说: {entry['content']}"
            else:
                # role = "user"
                last_user = entry['user']
                content = f"{entry['user']} 说: {entry['content']}"  # 格式化用户消息
            context.append(content)
        context_str = "\n".join(context)
        wrap_context = f"""
        你现在处于一个多人群聊的环境，其中：
        <<<<<<<<
            ##群聊的上文聊天内容：
            {context_str}
            <<<<<<<<
            接下来轮到你发言了，基于群聊上文，你会对{last_user}说什么？做什么行动？
        """
        message = system_prompt + [{"role": "user", "content": wrap_context}]
        return message

    def get_google_chat_history(self):
        """
        将聊天记录转换为谷歌模型支持的格式。

        输出格式：
        [
            {
                "role": "user",  # 用户角色
                "parts": [
                    "用户消息内容"  # 用户发送的消息内容
                ]
            },
            {
                "role": "model",  # 模型角色
                "parts": [
                    "助手回复内容"  # 助手的回复内容
                ]
            }
        ]

        返回:
        list: 结构化的聊天记录列表，适用于谷歌模型输入。
        """
        google_chat_history = []
        for entry in self.chat_memory:
            if entry["user"] == "system":
                role = "model"  # 将助手的消息标记为模型
                content = entry["content"]  # 助手的内容
            else:
                role = "user"  # 用户消息
                content = f"{entry['user']} 说: {entry['content']}"  # 格式化用户消息

            google_chat_history.append({
                "role": role,
                "parts": [
                    content  # 消息内容
                ]
            })

        return google_chat_history

    def get_doubao_chat_history(self) -> str:
        doubao_chat_history = ""
        for entry in self.chat_memory:
            if entry["user"] == "system":
                user = self.mint_name
            else:
                user = entry['user']
            doubao_chat_history += f"{user} 说: {entry['content']}\n"
        return doubao_chat_history
