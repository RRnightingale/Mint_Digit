import unittest
from doubao_utils import chat
import os

class TestChatWithDoubao(unittest.TestCase):

    def test_chat_with_doubao_success(self):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]

        response = chat(messages)
        print(response)
        # self.assertIsNotNone(response)
        # self.assertIn("choices", response)  # 假设成功响应中包含 "choices" 字段

    def test_chat_with_doubao_failure(self):
        # 使用无效的API Key或其他方式来模拟失败
        original_api_key = os.getenv("DOUBAO_API_KEY")
        os.environ["DOUBAO_API_KEY"] = "invalid_api_key"

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]

        response = chat(messages)
        self.assertIsNone(response)

        # 恢复原始的API Key
        os.environ["DOUBAO_API_KEY"] = original_api_key

if __name__ == '__main__':
    unittest.main()
