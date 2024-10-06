import unittest
import os
from user_manager import add_user, update_reputation, add_note, get_user_info, search_user, introduce_user, load_users, save_users

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.test_file = 'test/test_user_info.json'
        # 确保在每个测试前加载用户信息
        load_users()

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_add_user(self):
        result = add_user("001", ["小明", "明明"], 100, "活跃用户")
        self.assertEqual(result, "用户 001 已添加")
        
        result = add_user("001", ["小明", "明明"], 100, "活跃用户")
        self.assertEqual(result, "用户 001 已存在")

    def test_update_reputation(self):
        add_user("001", reputation=100)
        result = update_reputation("001", 20)
        self.assertEqual(result, "用户 001 的声望已更新为 120")
        
        result = update_reputation("002", 20)
        self.assertEqual(result, "用户 002 不存在")

    # def test_add_and_get_note(self):
    #     add_user("001")
        
    #     result = add_note("001", "很好的用户")
    #     self.assertEqual(result, "对用户 001 的备注已添加/更新")
        
    #     info = get_user_info("001")
    #     self.assertEqual(info['note'], "很好的用户")

    def test_search_user(self):
        add_user("001", ["小明", "明明"])
        
        result = search_user("小明")
        self.assertEqual(result, "001")
        
        result = search_user("不存在")
        self.assertIsNone(result)

    def test_get_user_info(self):
        add_user("001", ["小明", "明明"], 100, "活跃用户")
        
        info = get_user_info("001")
        self.assertEqual(info, {
            'user_id': "001",
            'aliases': ["小明", "明明"],
            'reputation': 100,
            'note': "活跃用户"
        })
        
        info = get_user_info("小明")
        self.assertEqual(info['user_id'], "001")
        
        info = get_user_info("不存在")
        self.assertIsNone(info)

    def test_save_and_load(self):
        add_user("001", ["小明"], 100, "测试用户")
        save_users()
        
        # 重新加载用户信息
        load_users()
        self.assertIn("001", users)
        self.assertEqual(users["001"]["aliases"], ["小明"])
        self.assertEqual(users["001"]["reputation"], 100)
        self.assertEqual(users["001"]["note"], "测试用户")

    def test_introduce_user(self):
        """测试用户介绍功能"""
        add_user("001", ["小明", "明明"], 200, "是个杂鱼")
        
        # 测试有效用户的介绍
        intro = introduce_user("001")
        self.assertEqual(intro, "001，小明, 明明，声望200，是个杂鱼")
        
        # 测试不存在的用户
        intro = introduce_user("不存在")
        self.assertEqual(intro, "用户 不存在 不存在")

if __name__ == '__main__':
    unittest.main()
