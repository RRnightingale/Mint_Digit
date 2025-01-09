import unittest
import os
import user_manager
import logging
# from user_manager import add_user, update_reputation, get_user_info, search_user, introduce_user, load_users, save_users


class TestUserManager(unittest.TestCase):
    def setUp(self):
        user_manager._users.clear()  # 清零
        user_manager._file_path = 'test/test_user_info.json'  # 设置路径
        # 确保在每个测试前加载用户信息
        # user_manager.load_users()

    # def tearDown(self):
    #     if os.path.exists(self.test_file):
    #         os.remove(self.test_file)

    def test_update_user(self):
        """
            测试在 _users 中不存在该 user_id 时，直接新建用户的逻辑。
        """
        result = user_manager.update_user(
            user_id="user001",
            new_data={
                "aliases": ["Alias001", "TestUser"],
                "nick_name": "Nick001"
            }
        )
        user = user_manager.search_user("user001")
        logging.info(user)
        # 验证 _users 中确实有该 user_id
        # self.assertIn("user001", user_manager._users)
        # self.assertEqual(user_manager._users["user001"]["aliases"], [
        #                  "Alias001", "TestUser"])
        # self.assertEqual(
        #     user_manager._users["user001"]["nick_name"], "Nick001")

    def test_update_existing_user_add_alias(self):
        """
        测试当 user 已存在时，对 aliases 做合并去重。
        """
        user_manager.update_user(
            user_id="user001",
            new_data={
                "aliases": ["Alias001"],
                "nick_name": "Nick001"
            }
        )

        user_manager.update_user(
            user_id="user001",
            new_data={
                "aliases": ["NewAlias", "Alias001"],
                "nick_name": "NewNick"
            }
        )
        # self.assertIn("已存在，对 new_data 进行了覆盖写", result)
        # 验证合并后的 aliases
        merged_aliases = user_manager._users["user001"]["aliases"]
        # 集合后可能顺序不定，我们只检查是否包含
        self.assertEqual(set(merged_aliases), {"Alias001", "NewAlias"})
        # 检查 nick_name 覆盖成功
        self.assertEqual(
            user_manager._users["user001"]["nick_name"], "NewNick")

    def test_update_existing_user_new_field(self):
        """
        测试当 user 已存在时，如果 new_data 带了新的字段（非 aliases），则直接覆盖/追加。
        """
        user_manager.update_user(
            user_id="user002",
            new_data={
                "aliases": ["User002"],
                "nick_name": "OriginalNick"
            }
        )
        # 给 user002 传入一个全新的字段 "twitter_id"
        result = user_manager.update_user("user002", {
            "twitter_id": "@user002_account"
        })
        self.assertIn("user002", user_manager._users)
        # 原字段保留
        self.assertEqual(
            user_manager._users["user002"]["nick_name"], "OriginalNick")
        # 新字段新增
        self.assertEqual(
            user_manager._users["user002"]["twitter_id"], "@user002_account")

    def test_search_by_exact_user_id(self):
        """
        测试：search_user 传入与某 user_id 完全匹配(清理后一致)，应返回该 user_id
        """
        # 先创建一个用户
        user_manager.update_user("453", {
            "aliases": ["alice", "al"]
        })

        # 1) 传入 "453"
        result1 = user_manager.search_user("453")
        self.assertEqual(result1, "453")

        # 2) 有特殊字符或空格，但 clean_username 后应该得到 "453"
        result2 = user_manager.search_user("  a li  ce !@#")
        self.assertEqual(result2, "453")



#     def test_add_user(self):
#         result = add_user("001", ["小明", "明明"], 100, "活跃用户")
#         self.assertEqual(result, "用户 001 已添加")
        
#         result = add_user("001", ["小明", "明明"], 100, "活跃用户")
#         self.assertEqual(result, "用户 001 已存在")

#     def test_update_reputation(self):
#         add_user("001", reputation=100)
#         result = update_reputation("001", 20)
#         self.assertEqual(result, "用户 001 的声望已更新为 120")
        
#         result = update_reputation("002", 20)
#         self.assertEqual(result, "用户 002 不存在")

#     # def test_add_and_get_note(self):
#     #     add_user("001")
        
#     #     result = add_note("001", "很好的用户")
#     #     self.assertEqual(result, "对用户 001 的备注已添加/更新")
        
#     #     info = get_user_info("001")
#     #     self.assertEqual(info['note'], "很好的用户")

#     def test_search_user(self):
#         add_user("001", ["小明", "明明"])
        
#         result = search_user("小明")
#         self.assertEqual(result, "001")
        
#         result = search_user("不存在")
#         self.assertIsNone(result)

#     def test_get_user_info(self):
#         add_user("001", ["小明", "明明"], 100, "活跃用户")
        
#         info = get_user_info("001")
#         self.assertEqual(info, {
#             'user_id': "001",
#             'aliases': ["小明", "明明"],
#             'reputation': 100,
#             'note': "活跃用户"
#         })
        
#         info = get_user_info("小明")
#         self.assertEqual(info['user_id'], "001")
        
#         info = get_user_info("不存在")
#         self.assertIsNone(info)

#     def test_save_and_load(self):
#         add_user("001", ["小明"], 100, "测试用户")
#         save_users()
        
#         # 重新加载用户信息
#         load_users()
#         self.assertIn("001", users)
#         self.assertEqual(users["001"]["aliases"], ["小明"])
#         self.assertEqual(users["001"]["reputation"], 100)
#         self.assertEqual(users["001"]["note"], "测试用户")

#     def test_introduce_user(self):
#         """测试用户介绍功能"""
#         add_user("001", ["小明", "明明"], 200, "是个杂鱼")
        
#         # 测试有效用户的介绍
#         intro = introduce_user("001")
#         self.assertEqual(intro, "001，小明, 明明，声望200，是个杂鱼")
        
#         # 测试不存在的用户
#         intro = introduce_user("不存在")
#         self.assertEqual(intro, "用户 不存在 不存在")


if __name__ == '__main__':
    unittest.main()
