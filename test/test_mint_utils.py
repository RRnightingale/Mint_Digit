import unittest
import os
import json
import memory
import logging
import mint_utils


class TestMintUtils(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()  # 拿到root logger
        logger.setLevel(logging.DEBUG)

    # def test_chat(self):
    #     chat_memory = memory.create_chat_memory(type='evil')
    #     user_name = "夜鹰"
    #     message = "请禁言雪国"
    #     # rsp = mint_utils.chat(chat_memory=chat_memory,
    #     #                       user_name=user_name, input_text=message)

    #     rsp = mint_utils.reply_without_action(
    #         user_name, message, tool_choice="required")
        # logging.debug(rsp)

    def test_private_chat(self):
        data = {
            "post_type": "message",
            "sender": {"nickname": "夜鹰"},
            "user_id": 631038409,
            "raw_message": "阿敏乖",
            "message_type": "private",
        }
        res = mint_utils.handle(data=data)

    def test_group_chat(self):
        data = {
            "post_type": "message",
            "sender": {"nickname": "夜鹰"},
            "user_id": 631038409,
            "raw_message": "阿敏乖",
            "message_type": "group",
            "group_id": 123
        }
        res = mint_utils.handle(data=data)

        data = {
            "post_type": "message",
            "sender": {"nickname": "夜鹰"},
            "user_id": 631038409,
            "raw_message": '[CQ:at,qq=3995633031,name=阿敏Evil] 黑子，坏。唐槐，坏',
            "message_type": "group",
            "group_id": 123
        }
        res = mint_utils.handle(data=data)

    def test_approve(self):
        data = {
            "post_type": "request",
            "comment": "赞美夜鹰",
            "request_type": "group",
            "flag": "233",
            "user_id": "123456"
        }
        res = mint_utils.handle(data=data)

    def test_not_approve(self):
        data = {
            "post_type": "request",
            "comment": "赞美",
            "request_type": "group",
            "flag": "233",
            "user_id": "123456"
        }
        res = mint_utils.handle(data=data)

    def test_not_approve2(self):
        data = {
            "post_type": "request",
            "comment": " ",
            "request_type": "group",
            "flag": "233",
            "user_id": "123456"
        }
        res = mint_utils.handle(data=data)

    def test_not_approve3(self):
        data = {
            "post_type": "request",
            "comment": " 1",
            "request_type": "group",
            "flag": "233",
            "user_id": "123456"
        }
        res = mint_utils.handle(data=data)

    # def test_save_chat_memory(self):
    #     user_name = "测试用户"
    #     message = "这是一个测试消息"
        
    #     # 调用保存聊天记录的函数
    #     # mint_utils.save_chat_memory(user_name, message)

    #     # 检查 chat_memory 是否更新
    #     # self.assertEqual(len(chat_memory), 1)
    #     self.assertEqual(mint_utils.chat_memory[-1]["role"], "user")
    #     self.assertEqual(mint_utils.chat_memory[-1]["content"], f"{user_name}说：{message}")
        
    #     # 检查 memory.log 文件是否正确保存
    #     with open('memory.log', 'r', encoding='utf-8') as f:
    #         saved_memory = json.load(f)
    #         self.assertEqual(saved_memory, mint_utils.chat_memory)

    def test_ban_action(self):
        from unittest.mock import patch, MagicMock


        # 模拟 llob_utils.set_group_ban 函数
        with patch('mint_utils.llob_utils.set_group_ban') as mock_set_group_ban:
            # 设置测试数据
            mint_utils.current_group_id = 123456
            mint_utils.user_id_to_name['测试用户'] = 789012
            action = "禁言(测试用户, 60)"

            # 执行动作
            mint_utils.execute_action(action)

            # 验证是否正确调用了 set_group_ban 函数
            mock_set_group_ban.assert_called_once_with(123456, 789012, 60)

        # 测试未知用户
        with patch('mint_utils.logging.error') as mock_logging_error:
            action = "禁言(未知用户, 60)"
            mint_utils.execute_action(action)
            mock_logging_error.assert_called_once_with("无法找到用户 未知用户 的ID. ID list: {'测试用户': 789012}")

        # 测试未知动作
        with patch('mint_utils.logging.warning') as mock_logging_warning:
            action = "未知动作(测试用户, 60)"
            mint_utils.execute_action(action)
            mock_logging_warning.assert_called_once_with("未知的动作：未知动作(测试用户, 60)")

    def test_fetch_user_name(self):
        message = "喵帕斯是七圣召唤高手，共鸣冠军"
        result = mint_utils.fetch_user_name(message)# 假设 result 是您要检查的列表
        self.assertIn("喵帕斯", result)  # 检查 "喵帕斯" 是否在 result 列表中

        message = "介绍唐傀"
        result = mint_utils.fetch_user_name(message)# 假设 result 是您要检查的列表
        self.assertIn("唐傀", result)  # 

    def test_clean_message_with_at_and_faces(self):
        # 测试包含CQ表情和at消息的清理
        message = "夜鹰257230693说：[CQ:face,id=15][CQ:face,id=265] @小明"
        expected_cleaned_message = "夜鹰257230693说：表情:15表情:265 @小明"

        # 调用清理消息的函数
        cleaned_message = mint_utils.clean_message(message)

        # 验证清理后的消息是否符合预期
        self.assertEqual(cleaned_message, expected_cleaned_message)

    def test_clean_message_with_only_faces(self):
        # 测试仅包含CQ表情的消息清理
        message = "夜鹰257230693说：[CQ:face,id=15][CQ:face,id=265]"
        expected_cleaned_message = "夜鹰257230693说：表情:15表情:265"

        # 调用清理消息的函数
        cleaned_message = mint_utils.clean_message(message)

        # 验证清理后的消息是否符合预期
        self.assertEqual(cleaned_message, expected_cleaned_message)


if __name__ == '__main__':
    unittest.main()
