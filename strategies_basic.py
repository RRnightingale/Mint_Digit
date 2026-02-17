from events import Event, BotReply
import napcat_client
from logger import get_logger
from config import get_config
from langchain_service import text_to_text
from group_manager import group_manager, Member
from tools import TOOLS, TOOL_FUNCTIONS, get_group_basic_info
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
import re


logger = get_logger("policy")
config = get_config()


class Policy:
    """策略类：负责意图识别、动作执行和消息发送。"""

    def handle(self, event: Event) -> dict:
        """处理事件：进行意图识别，根据不同条件执行不同动作，并发送消息。"""
        logger.debug("开始处理事件: %s", event)
        
        reply_text = None
        
        # 检查是否为特殊群聊
        is_special_group = event.is_group and event.group_id == config.special_group_id
        
        # 特殊群聊处理
        if is_special_group:
            logger.debug("处理特殊群聊事件")
            
            # 获取或创建群组实例
            group = group_manager.get_or_create_group(event.group_id)
            
            # 检查是否为指令模式（以/开头）
            if event.raw_message.strip().startswith("/"):
                logger.debug("处理指令模式事件")
                reply_text = self._handle_command(event)
            else:
                if event.is_at_amin:
                    logger.debug("处理特殊群聊@事件，调用LangChain")
                    # 调用LangChain，使用群组的历史记录，支持function call
                    reply_text = self._handle_special_group_at(event, group)
                else:
                    logger.debug("处理特殊群聊普通事件，记录历史")
                    # 记录普通消息到群组历史
                    group.add_message(event.raw_message, is_user=True, user_id=event.user_id)
                    reply_text = self._handle_group_chat(event)
        else:
            # 普通群聊或单聊处理
            # 检查是否为指令模式（以/开头）
            if event.raw_message.strip().startswith("/"):
                logger.debug("处理指令模式事件")
                reply_text = self._handle_command(event)
            else:
                if event.is_private:
                    logger.debug("处理单聊事件")
                    reply_text = self._handle_private_chat(event)
                elif event.is_group:
                    if event.is_at_amin:
                        logger.debug("处理群聊@事件")
                        reply_text = self._handle_group_at(event)
                    else:
                        logger.debug("处理普通群聊事件")
                        reply_text = self._handle_group_chat(event)
        
        if not reply_text:
            logger.debug("没有生成回复")
            return {"status": "no_reply"}
        
        return {
            "status": "sent",
            "reply": reply_text,
            # "napcat_status": getattr(resp, "status_code", None) if resp is not None else None,
        }

    def _handle_special_group_at(self, event: Event, group) -> str:
        """处理特殊群聊被@事件，调用LangChain。
        
        Args:
            event: 事件对象
            group: 群组实例
            
        Returns:
            大模型回复
        """
        logger.debug("处理特殊群聊@事件: %s", event)
        
        try:
            # 获取群组的历史记录
            chat_history = group.get_chat_history()
            
            # 确保群组有成员信息（如果没有则加载）
            if not group.get_members():
                logger.debug("群组没有成员信息，开始加载")
                member_list = napcat_client.get_group_member_list(group.group_id)
                if member_list:
                    members = [Member.from_dict(member) for member in member_list]
                    group.update_members(members)
                    logger.debug("群组成员信息加载完成，成员数量: %d", len(members))
            
            # 调用langchain_service中的text_to_text函数
            # 传入群组的历史记录，支持function call
            reply = text_to_text_with_history_and_tools(
                event.raw_message, 
                chat_history,
                event.group_id,
                event.raw_message,
                group,
                event.user_id
            )
            
            # 记录用户输入和模型回复到群组历史
            group.add_message(event.raw_message, is_user=True, user_id=event.user_id)
            group.add_message(reply, is_user=False)
            
            return reply
        except Exception as e:
            logger.error("调用LangChain服务出错: %s", e)
            return "处理消息时出错"

    def _handle_command(self, event: Event) -> str:
        """处理指令模式事件。"""
        command = event.raw_message.strip()
        logger.debug("处理指令: %s", command)
        
        if command == "/入群排名":
            return self._handle_join_group_ranking(event)
        else:
            return f"未知指令: {command}"

    def _handle_join_group_ranking(self, event: Event) -> str:
        """处理/入群排名指令。"""
        if not event.is_group:
            return "该指令只能在群聊中使用"
        
        try:
            # 获取群组实例
            group = group_manager.get_or_create_group(event.group_id)
            
            # 获取群成员入群时间列表
            members = self._get_group_members_join_time(event.group_id, group)
            
            # 按入群时间排序
            members.sort(key=lambda m: m.join_time)
            
            # 格式化输出
            reply = "入群排名（按入群时间从早到晚）：\n"
            for member in members:
                reply += f"{member.nickname} - {member.get_formatted_join_time()}\n"
            
            return reply
        except Exception as e:
            logger.error("处理/入群排名指令出错: %s", e)
            return "获取入群排名失败"

    def _get_group_members_join_time(self, group_id: str, group) -> list:
        """获取群成员入群时间列表。
        
        Args:
            group_id: 群聊ID
            group: 群组实例
            
        Returns:
            成员列表，每个成员是Member实例
        """
        logger.debug("获取群 %s 的成员入群时间", group_id)
        
        try:
            # 1. 获取群成员列表
            member_list = napcat_client.get_group_member_list(group_id)
            logger.debug("群成员列表: %s", member_list)
            
            if not member_list:
                logger.warning("未获取到群成员列表")
                return []
            
            # 2. 从字典创建Member实例
            members = [Member.from_dict(member) for member in member_list]
            
            # 3. 更新群组的成员信息
            group.update_members(members)
            
            logger.debug("获取到的成员入群时间列表: %s", members)
            return members
        except Exception as e:
            logger.error("获取群成员入群时间出错: %s", e)
            # 出错时返回模拟数据
            return [
                Member(user_id="1", nickname="成员1", join_time=1672531200),
                Member(user_id="2", nickname="成员2", join_time=1672617600),
                Member(user_id="3", nickname="成员3", join_time=1672704000),
            ]

    def _handle_private_chat(self, event: Event) -> str:
        """单聊动作。"""
        return "你好"

    def _handle_group_at(self, event: Event) -> str:
        """群聊被@动作。"""
        return "不好"

    def _handle_group_chat(self, event: Event) -> str:
        """普通群聊动作。"""
        return None

    def _send_message(self, event: Event, text: str) -> object:
        """发送消息。"""
        if event.is_private:
            return napcat_client.send_private_message(event.user_id, text)
        elif event.is_group:
            return napcat_client.send_group_message(event.group_id, text)
        return None


def get_policy() -> Policy:
    """获取策略实例。"""
    return Policy()


def parse_at_mentions(raw_message: str, group) -> str:
    """解析raw_message中的@信息，从group中获取对应的成员信息。
    
    Args:
        raw_message: 原始消息内容
        group: 群组实例
        
    Returns:
        成员信息的字符串描述
    """
    try:
        # 匹配 [CQ:at,qq=数字] 格式的@信息
        pattern = r'\[CQ:at,qq=(\d+)\]'
        matches = re.findall(pattern, raw_message)
        
        if not matches:
            return ""
        
        member_info_list = []
        for qq in matches:
            member = group.get_member_by_id(qq)
            if member:
                # 使用群昵称（card），如果没有则使用QQ昵称（nickname）
                display_name = member.card if member.card else member.nickname
                info = f"成员 {display_name} (QQ: {member.user_id})"
                info += f" - 角色: {member.role}"
                info += f" - 头衔: {member.title if member.title else '无'}"
                member_info_list.append(info)
        
        if member_info_list:
            return "\n".join(member_info_list)
        return ""
    except Exception as e:
        logger.error("解析@信息出错: %s", e)
        return ""


def text_to_text_with_history_and_tools(prompt: str, chat_history: list, group_id: str, raw_message: str, group, user_id: str) -> str:
    """使用历史记录和工具调用大模型。
    
    Args:
        prompt: 输入文本
        chat_history: 聊天历史列表
        group_id: 群聊ID
        raw_message: 原始消息内容
        group: 群组实例
        user_id: 用户ID
        
    Returns:
        大模型生成的文本
    """
    try:
        if not config.langchain_api_key:
            logger.error("LangChain API Key未配置")
            return "处理消息时出错"
        
        # 解析@信息，获取成员信息
        member_info = parse_at_mentions(raw_message, group)
        
        # 获取说话者的信息
        speaker_info = ""
        if user_id:
            speaker = group.get_member_by_id(user_id)
            if speaker:
                # 使用群昵称（card），如果没有则使用QQ昵称（nickname）
                display_name = speaker.card if speaker.card else speaker.nickname
                speaker_info = f"说话者 {display_name} (QQ: {speaker.user_id})"
                speaker_info += f" - 角色: {speaker.role}"
                speaker_info += f" - 头衔: {speaker.title if speaker.title else '无'}"
        
        # 获取LLM自身的信息
        bot_info = ""
        if config.amin_qq:
            bot = group.get_member_by_id(config.amin_qq)
            if bot:
                # 使用群昵称（card），如果没有则使用QQ昵称（nickname）
                display_name = bot.card if bot.card else bot.nickname
                bot_info = f"你的身份 {display_name} (QQ: {bot.user_id})"
                bot_info += f" - 角色: {bot.role}"
                bot_info += f" - 头衔: {bot.title if bot.title else '无'}"
            else:
                bot_info = f"你的QQ号: {config.amin_qq}"
        
        # 获取群基本信息（通过工具函数）
        group_basic_info = get_group_basic_info(group_id)
        
        # 构建上下文信息
        if member_info:
            member_info_text = f"\n被@的成员信息：\n{member_info}\n"
        else:
            member_info_text = ""
        
        group_info_text = f"\n当前群聊信息：\n{group_basic_info}\n"
        
        if speaker_info:
            speaker_info_text = f"\n说话者信息：\n{speaker_info}\n"
        else:
            speaker_info_text = ""
        
        if bot_info:
            bot_info_text = f"\n你的身份信息：\n{bot_info}\n"
        else:
            bot_info_text = ""
        
        # 使用prompt模板解析变量
        prompt_template = ChatPromptTemplate.from_template(config.system_prompt)
        enhanced_system_prompt = prompt_template.format(
            group_info=group_info_text,
            member_info=member_info_text,
            speaker_info=speaker_info_text,
            bot_info=bot_info_text
        )
        
        # 创建大模型实例，绑定工具
        llm = ChatOpenAI(
            api_key=config.langchain_api_key,
            base_url=config.langchain_base_url,
            model=config.langchain_model
        ).bind_tools(TOOLS)
        
        # 创建系统消息（包含上下文）
        system_message = SystemMessage(content=enhanced_system_prompt)
        
        # 构建消息列表
        messages = [system_message] + chat_history + [HumanMessage(content=prompt)]
        
        # 记录完整的prompt
        logger.info("发送给LLM的完整prompt: %s", messages)
        
        # 调用大模型
        response = llm.invoke(messages)
        logger.info("大模型响应: %s", response.content)
        
        # 检查是否有工具调用
        if response.tool_calls:
            logger.info("检测到工具调用: %s", response.tool_calls)
            
            # 处理工具调用
            tool_results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # 添加 group_id 到参数中（如果工具需要）
                if "group_id" not in tool_args:
                    tool_args["group_id"] = group_id
                
                logger.info("调用工具: %s, 参数: %s", tool_name, tool_args)
                
                # 调用工具函数
                if tool_name in TOOL_FUNCTIONS:
                    result = TOOL_FUNCTIONS[tool_name](**tool_args)
                    logger.info("工具调用结果: %s", result)
                    
                    # 添加工具结果到消息列表
                    tool_results.append(ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"]
                    ))
            
            # 将工具调用和结果添加到消息列表
            messages.append(response)
            messages.extend(tool_results)
            
            # 再次调用大模型获取最终回复
            final_response = llm.invoke(messages)
            logger.info("最终回复: %s", final_response.content)
            
            return final_response.content
        else:
            # 没有工具调用，直接返回回复
            return response.content
            
    except Exception as e:
        logger.error("调用大模型出错: %s", e)
        return f"处理消息时出错: {str(e)}"
