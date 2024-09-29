import unittest
import llob_utils
import json

class TestSendPrivateMessage(unittest.TestCase):

    def test_send_private_message(self):
        user_id = 631038409
        message = "测试消息"

        # 调用实际的 send_private_message 函数
        response = llob_utils.send_private_message(user_id, message)

        # 验证响应状态码
        self.assertEqual(response.status_code, 200)

        # 验证响应内容
        response_data = response.json()
        self.assertEqual(response_data['status'], 'ok')
        self.assertEqual(response_data['retcode'], 0)
        self.assertIn('message_id', response_data['data'])

if __name__ == '__main__':
    unittest.main()
