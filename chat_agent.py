from dotenv import load_dotenv
import logging

from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

import user_manager
import llob_utils
import mint_utils
import memory as mint_memory


MAX_HISTORY_MESSAGES = 20  # 最大历史条数
MAX_WORDS_PER_MESSAGE = 50  # 每条信息content数
app = None  # chat agent
config = None


@tool
def lc_mute_user(user_id: str, duration: float) -> str:
    """
    对角色禁言或解除禁言，指定禁言的持续时间。持续时间为 0 表示解除禁言
    Args:
    user_id:  要禁言或解除禁言的用户的 id(括号内是id)
    duration:  禁言的持续时间（以秒为单位）。使用 0 来解除禁言。
    """
    user_id = user_manager.search_user(user_id)
    if user_id is None:
        logging.info(f"禁言用户{user_name}失败")
        return f"无法找到用户{user_name}"
    llob_utils.set_group_ban(mint_utils.current_group_id, user_id, duration)
    result = f"成功禁言 {user_id} {duration}, 请您宣布结果吧"
    logging.info(result)
    return result


def init_app(model='grok'):
    """
    初始化llm
    """
    global app, config
    load_dotenv()

    if model == 'grok':
        from langchain_xai import ChatXAI
        MODEL_NAME = "grok-2-1212"
        llm = ChatXAI(
            model=MODEL_NAME,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
    llm = llm.bind_tools([lc_mute_user])  # 增加禁言功能

    workflow = StateGraph(state_schema=MessagesState)
    # Define the function that calls the model

    def compress_memory(state):
        messages = state["messages"]
        if len(messages) > MAX_HISTORY_MESSAGES:
            # 删除数据
            return {"messages": [RemoveMessage(id=m.id) for m in messages[1:-MAX_HISTORY_MESSAGES+1]]}

    def should_continue(state: MessagesState):
        messages = state["messages"]

        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        else:
            return "compress_memory"

    def call_model(state: MessagesState):
        response = llm.invoke(state["messages"])
        return {"messages": response}

    # Define the (single) node in the graph
    tools = [lc_mute_user]
    tool_node = ToolNode(tools)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("compress_memory", compress_memory)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, [
        "tools", "compress_memory"])
    workflow.add_edge("tools", "agent")
    workflow.add_edge("compress_memory", END)

    # Add memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    config = {"configurable": {"thread_id": "mint "}}  # TODO thread id后续改为群id

    system_prompt = mint_memory.MINT_EVIL + \
        mint_memory.SKILL_BAN + mint_memory.LIMIT_PORMT  # 阿敏的系统初始prompt

    update_memory(content=system_prompt, message_type="system")


def update_memory(content: str, message_type="human"):
    """
        手动增加记忆
    """
    if message_type == "human":
        app.update_state(config, {"messages": HumanMessage(content)})
    elif message_type == "system":
        app.update_state(config, {"messages": SystemMessage(content)})


def chat(user_name: str, input_text: str, target_name: str = None):
    """
        聊天
    """
    if target_name:
        message = HumanMessage(f"{user_name}对{target_name} 说：{input_text}")
    else:
        message = HumanMessage(f"{user_name} 说：{input_text}")
    input = {"messages": [message]}
    output = app.invoke(input, config=config)
    reply = output["messages"][-1].content

    # 压缩记忆里的最后一句
    messages = app.get_state(config).values["messages"]
    last_message = messages[-1]
    last_message.content = last_message.content[:MAX_WORDS_PER_MESSAGE]
    logging.info(messages)
    return reply


init_app()
