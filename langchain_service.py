from logger import get_logger
from config import get_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

logger = get_logger("langchain_service")
config = get_config()

# 模块级初始化 - 在启动时就完成初始化
logger.info("开始初始化LangChain服务...")

# 创建大模型实例
llm = None
try:
    llm = ChatOpenAI(
        api_key=config.langchain_api_key,
        base_url=config.langchain_base_url,
        model=config.langchain_model
    )
    logger.info("大模型实例创建成功")
except Exception as e:
    logger.error("创建大模型实例失败: %s", e)

# 创建输出解析器
output_parser = StrOutputParser()
logger.info("输出解析器创建成功")

# 聊天历史存储
chat_history = []
logger.info("聊天历史存储创建成功")

logger.info("LangChain服务初始化完成")


def text_to_text(prompt: str) -> str:
    """文本到文本的大模型调用。
    
    Args:
        prompt: 输入文本
        
    Returns:
        大模型生成的文本
    """
    logger.debug("调用text_to_text: %s", prompt)
    
    try:
        if not llm:
            logger.error("大模型实例未初始化")
            return "处理消息时出错"
        
        # 创建提示模板，包含历史记录
        prompt_template = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # 创建链
        chain = prompt_template | llm | output_parser
        
        # 执行链
        result = chain.invoke({
            "input": prompt,
            "chat_history": chat_history
        })
        logger.info("大模型回复: %s", result)
        
        # 记录到历史
        chat_history.append(HumanMessage(content=prompt))
        chat_history.append(AIMessage(content=result))
        logger.info("记录到历史成功")
        
        return result
    except Exception as e:
        logger.error("调用大模型出错: %s", e)
        return "处理消息时出错"


def record_chat_history(message: str) -> bool:
    """记录聊天历史到LangChain。
    
    Args:
        message: 聊天消息
        
    Returns:
        是否记录成功
    """
    logger.debug("记录聊天历史: %s", message)
    
    try:
        # 记录到历史
        chat_history.append(HumanMessage(content=message))
        logger.info("记录聊天历史成功: %s", message)
        
        return True
    except Exception as e:
        logger.error("记录聊天历史出错: %s", e)
        return False


def get_chat_history() -> list:
    """获取聊天历史。
    
    Returns:
        聊天历史列表
    """
    try:
        return chat_history
    except Exception as e:
        logger.error("获取聊天历史出错: %s", e)
        return []
