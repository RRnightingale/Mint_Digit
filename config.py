from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import os

from logger import get_logger
from prompt import SYSTEM_PROMPT


logger = get_logger("config")


@dataclass
class Config:
    """应用配置类。"""
    napcat_base_url: str
    amin_qq: str
    special_group_id: str
    langchain_api_key: str
    langchain_base_url: str
    langchain_model: str
    system_prompt: str


def load_config() -> Config:
    """加载配置文件。"""
    load_dotenv()
    
    napcat_base_url = os.getenv("NAPCAT_BASE_URL", "http://127.0.0.1:3000")
    amin_qq = os.getenv("AMIN_QQ", "3992928622")
    special_group_id = os.getenv("SPECIAL_GROUP_ID", "237893748")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY", "sk001")
    langchain_base_url = os.getenv("LANGCHAIN_BASE_URL", "http://test.com")
    langchain_model = os.getenv("LANGCHAIN_MODEL", "doubao-seed-2-0-pro-260215")
    system_prompt = SYSTEM_PROMPT
    
    logger.info("配置加载完成: NAPCAT_BASE_URL=%s, AMIN_QQ=%s, SPECIAL_GROUP_ID=%s, LANGCHAIN_API_KEY=%s, LANGCHAIN_BASE_URL=%s, LANGCHAIN_MODEL=%s", 
                napcat_base_url, amin_qq, special_group_id, langchain_api_key, langchain_base_url, langchain_model)
    
    return Config(
        napcat_base_url=napcat_base_url,
        amin_qq=amin_qq,
        special_group_id=special_group_id,
        langchain_api_key=langchain_api_key,
        langchain_base_url=langchain_base_url,
        langchain_model=langchain_model,
        system_prompt=system_prompt
    )


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例。"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
