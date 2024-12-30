import json
import os
import logging
import re

# 用户信息字典
_users = {}
_file_path = 'user_info.json'  # 用户信息文件的路径


# class User:


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
                    _users[user_id] = user_info
    logging.debug(f"用户信息已加载")

def save_users():
    """保存用户信息到文件"""
    with open(_file_path, 'w', encoding='utf-8') as f:
        json.dump(_users, f, ensure_ascii=False, indent=4)
    logging.info("用户信息已保存")


def set_user_attribute(user_id: str, key: str, value) -> str:
    """
    设置(或更新)某个用户的指定属性。
    例如 set_user_attribute("Alice", "reputation", 20)。
    """
    if user_id not in _users:
        return f"用户 {user_id} 不存在"

    if key == "aliases":
        # 1) 获取现有别名
        existing_aliases = set(_users[user_id].get("aliases", []))
        # 2) 对新提交的 aliases 做清洗
        if isinstance(value, list):
            cleaned_new_aliases = set(clean_username(a) for a in value)
        else:
            # 如果调用方只传一个字符串，就兼容一下
            cleaned_new_aliases = {clean_username(value)}

        # 3) 合并并去重
        merged = existing_aliases | cleaned_new_aliases
        _users[user_id]["aliases"] = list(merged)
        save_users()
        return f"属性 aliases 已合并更新：{merged}"
    else:
        # 普通字段，直接覆盖
        _users[user_id][key] = value
        save_users()
        return f"属性 {key} 已更新为 {value}"


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
        _users[user_id] = {}
        logging.info(f"创建用户{user_id}")

    for key, value in new_data.items():
        set_user_attribute(user_id, key, value)
    save_users()

# def get_user_attribute(user_id: str, key: str):
#     """
#     获取某个用户的指定属性；如果用户或属性不存在，返回 None。
#     """
#     if user_id not in _users:
#         return None
#     return _users[user_id].get(key, None)


def add_user(user_id, aliases=None, reputation=0, note=''):
    """
    添加新用户或更新现有用户的别名
    :param user_id: 用户ID
    :param aliases: 用户别名列表
    :param reputation: 初始声望值
    :param note: 用户备注
    :return: 添加结果信息
    """
    global _users
    user_id = user_id  # 清理用户 ID
    aliases = [clean_username(alias) for alias in (aliases or [])]  # 清理别名

    if user_id in _users:
        # 用户已存在，检查别名是否已存在
        existing_aliases = set(_users[user_id]['aliases'])  # 获取现有别名
        new_aliases = set(aliases)  # 获取新别名

        # 找出需要添加的新别名
        unique_aliases = new_aliases - existing_aliases
        if unique_aliases:
            _users[user_id]['aliases'].extend(unique_aliases)  # 添加新别名
            save_users()
            logging.debug(f"用户 {user_id} 的别名已更新: {unique_aliases}")
            return f"用户 {user_id} 已存在，新增别名: {', '.join(unique_aliases)}"
        else:
            return f"用户 {user_id} 已存在，别名未更改"  # 别名已存在

    # 用户不存在，添加新用户
    _users[user_id] = {
        'aliases': aliases,
        'reputation': reputation,
        'note': note,  # 统一使用 note 字段
    }
    save_users()
    logging.debug(f"用户 {user_id} 已添加")
    return f"用户 {user_id} 已添加"

def update_reputation(user_id, change:int) ->int:
    """
    更新用户声望
    :param user_id: 用户ID
    :param change: 声望变化值
    :return: 更新结果信息
    """
    global _users
    if user_id in _users:
        _users[user_id]['reputation'] += change
        save_users()
        return _users[user_id]['reputation']
    return 0

def update_note(user_id: str, note: str)->str:
    """
    添加用户备注
    :param user_id: 被备注的用户ID
    :param note: 备注内容
    :return: 添加结果信息
    """
    global _users
    if user_id in _users:
        _users[user_id]['note'] = note  # 将备注内容存储到 note 字段
        save_users()
        return f"对用户 {user_id} 的备注已添加/更新"
    return f"目标用户 {user_id} 不存在"

def introduce_user(user_id):
    """
    生成用户介绍信息
    :param user_id: 用户ID
    :return: 用户介绍字符串
    """
    global _users
    if user_id in _users:
        user = _users[user_id]
        aliases = ', '.join(user['aliases']) if user['aliases'] else '无别名'
        reputation = user['reputation']
        note = user['note'] if user['note'] else '无备注'
        return f"{aliases}，声望{reputation}{describe_reputation(reputation)}，{note}\n"
    return f"用户 {user_id} 不存在"


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
    for uid, data in _users.items():
        aliases = data.get("aliases", [])
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

# def add_temp_user(alias:str="", reputation=0, note=''):
#     """
#     添加临时用户
#     :param alias: 用户别名
#     :param reputation: 声望值
#     :param note: 评价
#     :return: 用户ID
#     """
#     global _users
#     counter = 1
#     while f"未知用户{counter:04d}" in _users:
#         counter += 1
#     user_id = f"未知用户{counter:04d}"
#     add_user(user_id, [alias], reputation, note)
#     return user_id

# 在模块加载时自动尝试加载现有数据（保证单例的初始化）
load_users()
