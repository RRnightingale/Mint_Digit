import unittest
import os
import json
import mint_utils

class TestMintUtils(unittest.TestCase):


    def test_save_chat_memory(self):
        user_name = "测试用户"
        message = "这是一个测试消息"
        
        # 调用保存聊天记录的函数
        mint_utils.save_chat_memory(user_name, message)
        
        # 检查 chat_memory 是否更新
        # self.assertEqual(len(chat_memory), 1)
        self.assertEqual(mint_utils.chat_memory[-1]["role"], "user")
        self.assertEqual(mint_utils.chat_memory[-1]["content"], f"{user_name}说：{message}")
        
        # 检查 memory.log 文件是否正确保存
        with open('memory.log', 'r', encoding='utf-8') as f:
            saved_memory = json.load(f)
            self.assertEqual(saved_memory, mint_utils.chat_memory)

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


if __name__ == '__main__':
    unittest.main()
