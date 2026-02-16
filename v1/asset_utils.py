import json
import random
from collections import defaultdict
import doubao_utils
import logging

# 用户资产数据
user_assets = {}

# 资产文件路径
ASSET_FILE = 'user_assets.json'

def load_assets():
    """从文件加载用户资产数据"""
    global user_assets
    try:
        with open(ASSET_FILE, 'r') as f:
            user_assets = json.load(f)
    except FileNotFoundError:
        user_assets = {}

def save_assets():
    """保存用户资产数据到文件"""
    with open(ASSET_FILE, 'w') as f:
        json.dump(user_assets, f)

def recharge(user_id: str, amount: float) -> float:
    """
    用户充值功能
    
    参数:
    user_id (str): 用户ID
    amount (float): 充值金额
    
    返回:
    str: 充值结果消息
    """
    if user_id not in user_assets:
        user_assets[user_id] = 0
    user_assets[user_id] += amount
    save_assets()
    return user_assets[user_id]

def get_balance(user_id: str) -> float:
    """
    查询用户余额
    
    参数:
    user_id (str): 用户ID
    
    返回:
    float: 用户余额
    """
    return user_assets.get(user_id, 0)

TITLE_PROMPT = """
# 角色
你是一个强大的称号生成系统，能够根据不同稀有度生成原神背景的独特称号。

## 技能
### 技能 1：生成称号
1. 称号具有SSR, SR, R, N的稀有度。 根据要求输出对应称号
2. 回复示例：
=====
   - 稀有度：<SSR/SR/R/N>
   - 称号：<具体称号名称>
=====

## 限制
- 只生成符合四种稀有度分布的称号，拒绝生成其他类型内容。
- 严格按照给定的格式输出称号信息。

现在，按照一下稀有度和次数要求抽取
"""

def draw_rarity() -> str:
    """
    抽奖功能
    
    参数:
    user_id (str): 用户ID
    cost (float): 抽奖成本
    
    返回:
    str: 抽奖结果消息
    """
    rarity_probabilities = [
        ("SSR", 0.01),  
        ("SR", 0.05),    
        ("R", 0.30),      
        ("N", 0.64)      
    ]
    rarity = random.choices([r[0] for r in rarity_probabilities], 
                            weights=[r[1] for r in rarity_probabilities])[0]
    
    return rarity

def user_lottery(user_id: str, times: int = 1, cost: float = 60) -> str:
    """
    用户抽奖功能
    
    参数:
    user_id (str): 用户ID
    
    返回:
    str: 抽奖结果消息
    """
    if user_id not in user_assets or user_assets[user_id] < cost * times:
        return f"余额不足，无法抽奖。当前余额：{get_balance(user_id)} 元，抽奖需要 {cost * times} 元。"
    
    user_assets[user_id] -= cost * times
    save_assets()
    
    results = defaultdict(int)
    for _ in range(times):
        rarity = draw_rarity()
        results[rarity] += 1
    
    result_str = ", ".join([f"{rarity} {count}次" for rarity, count in results.items() if count > 0])
    
    prompt = [{"role": "system", "content": TITLE_PROMPT+result_str}]
    logging.info(prompt)
    reply = doubao_utils.chat(prompt)

    return reply


# 初始化时加载用户资产数据
load_assets()
