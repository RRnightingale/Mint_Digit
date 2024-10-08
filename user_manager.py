import json
import os
import logging
import re

# 用户信息字典
users = {}
file_path = 'user_info.json'  # 用户信息文件的路径

def clean_username(user_name):
    """移除用户名中的空格和特殊字符"""
    return re.sub(r'\s+|[^a-zA-Z0-9\u4e00-\u9fa5]', '', user_name)

def load_users():
    """从文件加载用户信息"""
    global users
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_users = json.load(f)
            # 确保用户 ID 唯一
            for user_id, user_info in loaded_users.items():
                if user_id not in users:  # 只添加唯一的用户 ID
                    users[user_id] = user_info
    logging.debug(f"用户信息已加载")

def save_users():
    """保存用户信息到文件"""
    global users
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def add_user(user_id, aliases=None, reputation=0, note=''):
    """
    添加新用户或更新现有用户的别名
    :param user_id: 用户ID
    :param aliases: 用户别名列表
    :param reputation: 初始声望值
    :param note: 用户备注
    :return: 添加结果信息
    """
    global users
    user_id = user_id  # 清理用户 ID
    aliases = [clean_username(alias) for alias in (aliases or [])]  # 清理别名

    if user_id in users:
        # 用户已存在，检查别名是否已存在
        existing_aliases = set(users[user_id]['aliases'])  # 获取现有别名
        new_aliases = set(aliases)  # 获取新别名

        # 找出需要添加的新别名
        unique_aliases = new_aliases - existing_aliases
        if unique_aliases:
            users[user_id]['aliases'].extend(unique_aliases)  # 添加新别名
            save_users()
            logging.debug(f"用户 {user_id} 的别名已更新: {unique_aliases}")
            return f"用户 {user_id} 已存在，新增别名: {', '.join(unique_aliases)}"
        else:
            return f"用户 {user_id} 已存在，别名未更改"  # 别名已存在

    # 用户不存在，添加新用户
    users[user_id] = {
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
    global users
    if user_id in users:
        users[user_id]['reputation'] += change
        save_users()
        return users[user_id]['reputation']
    return 0

def update_note(user_id: str, note: str)->str:
    """
    添加用户备注
    :param user_id: 被备注的用户ID
    :param note: 备注内容
    :return: 添加结果信息
    """
    global users
    if user_id in users:
        users[user_id]['note'] = note  # 将备注内容存储到 note 字段
        save_users()
        return f"对用户 {user_id} 的备注已添加/更新"
    return f"目标用户 {user_id} 不存在"

def introduce_user(user_id):
    """
    生成用户介绍信息
    :param user_id: 用户ID
    :return: 用户介绍字符串
    """
    global users
    if user_id in users:
        user = users[user_id]
        aliases = ', '.join(user['aliases']) if user['aliases'] else '无别名'
        reputation = user['reputation']
        note = user['note'] if user['note'] else '无备注'
        return f"{aliases}，声望{reputation}{describe_reputation(reputation)}，{note}\n"
    return f"用户 {user_id} 不存在"

def search_user(user_name):
    """
    根据用户名或别名搜索用户
    :param name: 用户名或别名
    :return: 匹配的用户ID，如果没找到则返回None
    """
    global users
    cleaned_name = clean_username(user_name)  # 清理搜索名称
    for user_id, user_info in users.items():
        if cleaned_name in user_info['aliases'] or cleaned_name == user_id:
            return user_id
        
    # 如果没找到，则创建临时用户
    user_id = add_temp_user(user_name)
    logging.info(f"创建临时用户 {user_id} {user_name}")
    return user_id

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

def add_temp_user(alias:str="", reputation=0, note=''):
    """
    添加临时用户
    :param alias: 用户别名
    :param reputation: 声望值
    :param note: 评价
    :return: 用户ID
    """
    global users
    counter = 1
    while f"未知用户{counter:04d}" in users:
        counter += 1
    user_id = f"未知用户{counter:04d}"
    add_user(user_id, [alias], reputation, note)
    return user_id

# 初始化用户信息
load_users()
