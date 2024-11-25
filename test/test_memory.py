import unittest
import os
import json
from memory import ChatMemory
import memory
import logging


class TestChatMemory(unittest.TestCase):
    def setUp(self):
        """每个测试用例前运行"""
        # self.system_prompt = "你是测试助手"
        # self.memory = ChatMemory(self.system_prompt)
        self.memory = memory.create_chat_memory()
        # # 确保每次测试前删除测试用的memory文件
        # if os.path.exists('memory.log'):
        #     os.remove('memory.log')

    # def tearDown(self):
    #     """每个测试用例后运行"""
    #     if os.path.exists('memory.log'):
    #         os.remove('memory.log')

    def test_init_memory(self):
        """测试内存初始化"""
        memory = ChatMemory(self.system_prompt)
        self.assertEqual(len(memory.chat_memory), 1)
        self.assertEqual(memory.chat_memory[0]["role"], "system")
        self.assertEqual(memory.chat_memory[0]["content"], self.system_prompt)

    def test_save_chat_memory(self):
        """测试保存聊天记录"""
        self.memory.save_chat_memory("测试用户", "测试消息")
        self.assertEqual(len(self.memory.chat_memory), 2)
        self.assertEqual(self.memory.chat_memory[1]["role"], "user")
        self.assertEqual(self.memory.chat_memory[1]["content"], "测试用户说：测试消息")

    def test_memory_limit(self):
        """测试内存限制"""
        # 添加大量消息直到超过限制
        long_message = "很" * 100
        for i in range(10):
            self.memory.save_chat_memory(f"用户{i}", long_message)

        # 验证总字数不超过限制
        total_words = sum(len(msg["content"])
                          for msg in self.memory.chat_memory)
        self.assertLessEqual(total_words, self.memory.max_words)

    def test_clean_message(self):
        """测试消息清理功能"""
        test_cases = [
            (
                "[CQ:at,qq=123456,name=测试]你好",
                "测试你好"
            ),
            (
                "[CQ:image,file=abc.jpg]看图",
                "[xx]看图"  # xx为哈希值，这里只测试格式
            ),
            (
                "[CQ:face,id=123]笑脸",
                "表情:123笑脸"
            ),
            (
                "普通消息",
                "普通消息"
            )
        ]

        for input_msg, expected_format in test_cases:
            cleaned = self.memory.clean_message(input_msg)
            if "image" in input_msg:
                # 对于图片，只检查格式而不检查具体哈希值
                self.assertTrue(cleaned.startswith(
                    "[") and cleaned.endswith("]看图"))
            else:
                self.assertEqual(cleaned, expected_format)

    def test_check_duplicate(self):
        """测试重复消息检测"""
        # 测试三条相同的消息
        for _ in range(3):
            self.memory.save_chat_memory("测试用户", "重复消息")
        self.assertTrue(self.memory.check_duplicate())

        # 测试不同的消息
        self.memory = ChatMemory(self.system_prompt)  # 重置内存
        self.memory.save_chat_memory("用户1", "消息1")
        self.memory.save_chat_memory("用户2", "消息2")
        self.memory.save_chat_memory("用户3", "消息3")
        self.assertFalse(self.memory.check_duplicate())

    def test_save_to_file(self):
        """测试保存到文件"""
        self.memory.save_chat_memory("测试用户", "测试消息")
        self.assertTrue(os.path.exists('memory.log'))

        with open('memory.log', 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertEqual(len(saved_data), 2)  # 系统提示 + 一条消息
        self.assertEqual(saved_data[1]["content"], "测试用户说：测试消息")

    def test_load_from_file(self):
        """测试从文件加载"""
        # 先保存一些数据
        self.memory.save_chat_memory("测试用户", "测试消息")

        # 创建新的实例，应该加载已保存的数据
        new_memory = ChatMemory(self.system_prompt)
        self.assertEqual(len(new_memory.chat_memory), 2)
        self.assertEqual(new_memory.chat_memory[1]["content"], "测试用户说：测试消息")

    def test_get_gpt_compatible_memory(self):
        """测试获取GPT兼容的聊天记录"""
        # self.memory.save_chat_memory("测试用户", "测试消息")
        gpt_memory = self.memory.get_gpt_compatible_memory()
        logging.info(gpt_memory)

        # self.assertEqual(len(gpt_memory), 2)  # 系统提示 + 一条消息
        # self.assertEqual(gpt_memory[0]["role"], "system")
        # self.assertEqual(gpt_memory[0]["content"], self.system_prompt)
        # self.assertEqual(gpt_memory[1]["role"], "user")
        # self.assertEqual(gpt_memory[1]["content"], "测试用户 说: 测试消息")

    def test_get_google_chat_history(self):
        """测试获取Google模型兼容的聊天记录"""
        # 添加一条用户消息和一条系统消息
        self.memory.save_chat_memory("测试用户", "用户消息")
        self.memory.save_chat_memory("阿敏", "系统回复")

        google_history = self.memory.get_google_chat_history()

        # 验证格式和内容
        self.assertEqual(len(google_history), 3)  # 初始系统提示 + 用户消息 + 系统回复

        # 验证系统提示
        self.assertEqual(google_history[0]["role"], "model")
        self.assertEqual(google_history[0]["parts"][0], self.system_prompt)

        # 验证用户消息
        self.assertEqual(google_history[1]["role"], "user")
        self.assertEqual(google_history[1]["parts"][0], "测试用户 说: 用户消息")

        # 验证系统回复
        self.assertEqual(google_history[2]["role"], "model")
        self.assertEqual(google_history[2]["parts"][0], "系统回复")

    def test_create_chat_memory(self):
        """测试创建ChatMemory实例的工厂函数"""
        from memory import create_chat_memory, MINT_EVIL, SKILL_BAN, LIMIT_PORMT

        # 测试创建evil类型的内存
        evil_memory = create_chat_memory(type="evil", max_words=500)
        self.assertEqual(evil_memory.max_words, 500)
        self.assertEqual(evil_memory.system_prompt,
                         MINT_EVIL + SKILL_BAN + LIMIT_PORMT)

        # 测试无效类型
        with self.assertRaises(ValueError):
            create_chat_memory(type="invalid")

    def test_system_prompt(self):
        print(self.memory.system_prompt)

    def test_doubao_chat_history(self):
        print(self.memory.get_doubao_chat_history())

if __name__ == '__main__':
    unittest.main()
