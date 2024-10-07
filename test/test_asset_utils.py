import unittest
import os
import json
import logging
from asset_utils import load_assets, save_assets, recharge, get_balance, user_lottery, ASSET_FILE

class TestAssetUtils(unittest.TestCase):

    # def setUp(self):
    #     # 在每个测试前清理资产文件
    #     if os.path.exists(ASSET_FILE):
    #         os.remove(ASSET_FILE)

    # def tearDown(self):
    #     # 在每个测试后清理资产文件
    #     if os.path.exists(ASSET_FILE):
    #         os.remove(ASSET_FILE)

    def test_load_and_save_assets(self):
        # 测试加载和保存资产
        test_assets = {"user1": 100, "user2": 200}
        with open(ASSET_FILE, 'w') as f:
            json.dump(test_assets, f)
        
        load_assets()
        self.assertEqual(get_balance("user1"), 100)
        self.assertEqual(get_balance("user2"), 200)

        recharge("user3", 300)
        save_assets()

        with open(ASSET_FILE, 'r') as f:
            saved_assets = json.load(f)
        
        self.assertEqual(saved_assets, {"user1": 100, "user2": 200, "user3": 300})

    def test_recharge(self):
        # 测试充值功能
        result = recharge("user1", 100)
        self.assertIn("充值成功", result)
        self.assertGreater(get_balance("user1"), 100)

        result = recharge("user1", 50)
        self.assertIn("充值成功", result)
        self.assertGreater(get_balance("user1"), 150)

    def test_get_balance(self):
        # 测试查询余额功能
        self.assertEqual(get_balance("non_existent_user"), 0)
        # recharge("user1", 100)
        # self.assertEqual(get_balance("user1"), 100)

    def test_user_lottery(self):
        # 测试抽奖功能
        recharge("user1", 1000)
        result = user_lottery("user1")
        self.assertIn("稀有度", result)
        self.assertIn("称号", result)
        logging.info(result)
        # self.assertEqual(get_balance("user1"), 940)

        result = user_lottery("non_existent_user")
        self.assertIn("余额不足", result)

    def test_lottery_10(self):
        recharge("user1", 1000)
        result = user_lottery("user1", times=10)
        logging.info(result)

if __name__ == '__main__':
    unittest.main()

