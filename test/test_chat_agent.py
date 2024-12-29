import unittest
import logging
import chat_agent


class TestMintUtils(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()  # 拿到root logger
        logger.setLevel(logging.DEBUG)

    def test_chat(self):
        user_name = "夜鹰"
        content = "早上好"
        output = chat_agent.chat(user_name=user_name, input_text=content)
        logging.info(output)

    # def test_memory()


if __name__ == '__main__':
    unittest.main()
