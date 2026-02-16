import json
import os
import logging
import re

# 用户信息字典
_users = {}
_file_path = 'user_info.json'  # 用户信息文件的路径


class User:
    def __init__(self, user_id: str, data: dict = {}) -> None:
        self.user_id = user_id
        self.data = data

    def __str__(self):
        """
            生成用户介绍信息
            :param user_id: 用户ID
            :return: 用户介绍字符串
        """
        describtion = f"user id: {self.user_id}"
        aliases = self.data.get("aliases", None)
        if aliases:
            describtion += f", 名字:[{','.join(aliases)}]"
        reputation = self.data.get('reputation')
        if reputation:
            describtion += f", 声望:{reputation}"
        note = self.data.get('note')
        if note:
            describtion += f", 信息：{note}"
        describtion += '\n'
        return describtion

    def set_attribute(self, key: str, value) -> str:
        """
        设置(或更新)某个用户的指定属性。
        例如 set_user_attribute("Alice", "reputation", 20)。
        """
        if key == "aliases":
            # 1) 获取现有别名
            existing_aliases = set(self.data.get("aliases", []))
            # 2) 对新提交的 aliases 做清洗
            if isinstance(value, list):
                cleaned_new_aliases = set(clean_username(a) for a in value)
            else:
                # 如果调用方只传一个字符串，就兼容一下
                cleaned_new_aliases = {clean_username(value)}

            # 3) 合并并去重
            merged = existing_aliases | cleaned_new_aliases
            self.data["aliases"] = list(merged)
            return f"属性 aliases 已合并更新：{merged}"
        else:
            # 普通字段，直接覆盖
            self.data[key] = value
            return f"属性 {key} 已更新为 {value}"

    def __getitem__(self, key: str):
        """
        允许通过字典方式访问用户属性，例如 user["aliases"]。
        
        :param key: 属性键
        :return: 属性值
        """
        return self.__getattr__(key)

    def __getattr__(self, key: str):
        """
        允许通过属性方式访问用户属性，例如 user.aliases。
        仅在常规属性未找到时调用。
        
        :param key: 属性键
        :return: 属性值
        :raises AttributeError: 属性不存在时抛出异常
        """
        if key in self.data:
            return self.data[key]
        raise AttributeError(f"'User' object has no attribute '{key}'")


def clean_username(user_name):
    """移除用户名中的空格和特殊字符（仅保留中英文、数字）"""
    return re.sub(r'\s+|[^a-zA-Z0-9\u4e00-\u9fa5]', '', user_name)


def load_users():
    """从文件加载用户信息"""
    if os.path.exists(_file_path):
        with open(_file_path, 'r', encoding='utf-8') as f:
            loaded_users = json.load(f)
            # 确保用户 ID 唯一
            for user_id, user_info in loaded_users.items():
                if user_id not in _users:  # 只添加唯一的用户 ID
                    # _users[user_id] = user_info
                    _users[user_id] = User(user_id, data=user_info)
    logging.debug(f"用户信息已加载")


def save_users():
    """保存用户信息到文件"""
    with open(_file_path, 'w', encoding='utf-8') as f:
        users_dict = {uid: user.data for uid, user in _users.items()}
        json.dump(users_dict, f, ensure_ascii=False, indent=4)
    logging.info("用户信息已保存")

def update_user(user_id: str, new_data: dict) -> None:
    """
    没有 user_id 就创建新用户；若已存在则覆盖写（有则覆盖，无则增加）。
    其中，对 'aliases' 字段采用合并逻辑，其它字段直接覆盖。
    
    :param user_id: 用户 ID
    :param new_data: dict, 扁平的用户信息。例如：
                     {
                         "aliases": ["Alice", "AL"],
                         "nick_name": "小艾",
                         "twitter_id": "@alicedemo"
                     }
    """
    if user_id not in _users:
        user = User(user_id=user_id)
        _users[user_id] = user
        logging.info(f"创建用户{user_id}")
    else:
        user = _users[user_id]

    for key, value in new_data.items():
        user.set_attribute(key=key, value=value)
        # set_user_attribute(user_id, key, value)
    save_users()


def get_user_by_id(user_id: str) -> User:
    if user_id in _users:
        return _users[user_id]
    else:
        logging.error(f"Not such user {user_id}")
        return None


def search_user(name: str) -> str:
    """
    根据字符串搜索用户：
    1. 若与 user_id 相同(去除特殊字符后)则返回该 user_id
    2. 若该字符串出现在用户的 'aliases' 列表中，则返回该 user_id
    3. 否则返回 None
    """
    cleaned = clean_username(name)
    # 第一步：先检查是否有相同的 user_id
    if cleaned in _users:
        return cleaned

    # 第二步：若 user_id 不匹配，则遍历，查看 aliases 是否包含
    for uid, user in _users.items():
        aliases = user.aliases
        if cleaned in aliases:
            return uid
    return None

def describe_reputation(reputation):
    """
    根据声望值生成描述信息
    :param reputation: 声望值
    :return: 描述信息字符串
    """
    if reputation < -100:
        return "恶徒"
    elif reputation < 100:
        return "杂鱼"
    elif reputation < 1000:
        return "普通"
    elif reputation < 10000:
        return "友善"
    else:
        return "尊敬"

# 在模块加载时自动尝试加载现有数据（保证单例的初始化）
load_users()
