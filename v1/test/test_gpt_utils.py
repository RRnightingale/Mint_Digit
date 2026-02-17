#!/usr/bin/env python
# coding: utf-8
# ----------------------------------------------------------------------
# Author: arshart@forevernine.com
# Description: Test cases for gpt_utils.py
# ----------------------------------------------------------------------

import unittest
from unittest.mock import patch, MagicMock
import gpt_utils

class TestGPTUtils(unittest.TestCase):

    # @patch('gpt_utils.client.chat.completions.create')
    # def test_gpt_chat(self, mock_create):
    #     # Mock the response from OpenAI
    #     mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content='Hello, world!'))])
        
    #     response = gpt_utils.gpt_chat("Hello")
    #     self.assertEqual(response, "Hello, world!")
    #     self.assertIn({"role": "user", "content": "Hello"}, gpt_utils.chat_memory)
    #     self.assertIn({"role": "assistant", "content": "Hello, world!"}, gpt_utils.chat_memory)

    # @patch('gpt_utils.client.images.generate')
    # def test_dell_e_image(self, mock_generate):
    #     # Mock the response from OpenAI
    #     mock_generate.return_value = MagicMock(data=[MagicMock(url='http://example.com/image.png')])
        
    #     image_url = gpt_utils.dell_e_image("A cat")
    #     self.assertEqual(image_url, 'http://example.com/image.png')

    # 跑一次要钱，偶尔跑跑
    def test_chatgpt(self):
        reply = gpt_utils.chat("很高兴问候你全家")
        self.assertIsInstance(reply, str)
        print(reply)

    # def test_dell_e_image_real(self):
    #     image_url = gpt_utils.dell_e_image("A cat")
    #     print(image_url)
    #     self.assertIsInstance(image_url, str)
    #     self.assertTrue(image_url.startswith("http"))

if __name__ == '__main__':
    unittest.main()