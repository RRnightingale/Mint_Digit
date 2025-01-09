from dotenv import load_dotenv
import logging

from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_community.embeddings import ZhipuAIEmbeddings

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

import user_manager
from user_manager import User
import llob_utils
import mint_utils
import memory as mint_memory


MAX_HISTORY_MESSAGES = 20  # 最大历史条数
MAX_WORDS_PER_MESSAGE = 50  # 每条信息content数
app = None  # chat agent
config = None
embeddings = None


@tool
def lc_mute_user(user_id: str, duration: float) -> str:
    """
    对角色禁言或解除禁言，指定禁言的持续时间。持续时间为 0 表示解除禁言
    Args:
    user_id:  要禁言或解除禁言的用户的 id(括号内是id)
    duration:  禁言的持续时间（以秒为单位）。使用 0 来解除禁言。
    """
    user_id = int(user_manager.search_user(user_id))
    if user_id is None:
        logging.info(f"禁言用户{user_name}失败")
        return f"无法找到用户{user_name}"
    llob_utils.set_group_ban(mint_utils.current_group_id, user_id, duration)
    result = f"成功禁言 {user_id} {duration}, 请您宣布结果吧"
    logging.info(result)
    return result


def init_retriever():
    # init embeddings
    embeddings = ZhipuAIEmbeddings(
        model="embedding-3",
    )

    docs = []
    for user_id, user in user_manager._users.items():
        info = str(user)
        doc = Document(page_content=info, metadata={"source": "user_info"})
        docs.append(doc)

    BATCH_SIZE = 64

    chunks = [docs[i:i + BATCH_SIZE] for i in range(0, len(docs), BATCH_SIZE)]
    faiss_store = None

    for chunk in chunks:
        if faiss_store is None:
            # 第一次创建向量索引
            faiss_store = FAISS.from_documents(chunk, embeddings)
        else:
            # 后续分批，用 add_documents() 追加向量
            faiss_store.add_documents(chunk)

    retriever = faiss_store.as_retriever(search_kwargs={"k": 2})  # k：返回索引数量
    return retriever


def init_app(model='zhipu'):
    """
    初始化llm
    """
    global app, config, embeddings
    load_dotenv()

    if model == 'grok':
        from langchain_xai import ChatXAI
        MODEL_NAME = "grok-2-1212"
        llm = ChatXAI(
            model=MODEL_NAME,
            temperature=0.5,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
    elif model == 'zhipu':
        from langchain_zhipu import ChatZhipuAI
        MODEL_NAME = "glm-4-flash"
        llm = ChatZhipuAI(
            model=MODEL_NAME,
            temperature=0.5,
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
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": response}

    retriever = init_retriever()

    def retrieve(state):
        """
        Retrieve documents
        Args:
            state (dict): The current graph state
        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        messages = state["messages"]
        logging.debug(messages)
        last_message = messages[-1]  # 最后一条信息
        content = last_message.content

        documents = retriever.invoke(content)
        last_message.content = f"{content}\n<相关信息>\n{documents[0].page_content} {documents[1].page_content}"
        return {"messages": messages}

    # Define the (single) node in the graph
    tools = [lc_mute_user]
    tool_node = ToolNode(tools)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("compress_memory", compress_memory)
    workflow.add_node("retrieve", retrieve)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "agent")
    workflow.add_conditional_edges("agent", should_continue, [
        "tools", "compress_memory"])
    workflow.add_edge("tools", "agent")
    workflow.add_edge("compress_memory", END)

    # Add memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    config = {"configurable": {"thread_id": "mint "}}  # TODO thread id后续改为群id

    system_prompt = mint_memory.MINT_EVIL  # 阿敏的系统初始prompt

    update_memory(content=system_prompt, message_type="system")


def update_memory(content: str, message_type="human"):
    """
        手动增加记忆
    """
    if message_type == "human":
        app.update_state(config, {"messages": HumanMessage(content)})
    elif message_type == "system":
        app.update_state(config, {"messages": SystemMessage(content)})


def chat(user: User, input_text: str, target_name: str = None):
    """
        聊天
    """
    user_name = user.user_name
    if target_name:
        message = HumanMessage(
            f"{user_name}对{target_name} 说：{input_text}\n<说话人信息>{str(user)}")
    else:
        message = HumanMessage(
            f"{user_name} 说：{input_text}\n<说话人信息>{str(user)}")
    input = {"messages": [message]}
    output = app.invoke(input, config=config)
    reply = output["messages"][-1].content

    # 压缩记忆里的最后一句
    messages = app.get_state(config).values["messages"]
    last_message = messages[-1]
    # 压缩回复信息
    last_message.content = last_message.content[:MAX_WORDS_PER_MESSAGE]
    logging.info(messages)
    return reply


def check_duplicate() -> bool:
    """
    检查是否有连续消息
    """
    user_messages = []
    messages = app.get_state(config).values["messages"]
    for message in reversed(messages):
        if type(message) == HumanMessage:
            content = message.content.split("说：")[1]
            user_messages.append(content)
            if len(user_messages) == 3:
                break
    flag = len(set(user_messages)) == 1 and len(user_messages) == 3
    return flag


init_app()
