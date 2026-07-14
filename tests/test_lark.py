import unittest

from scripts.basetracker.lark import LarkBaseProvider


class FakeLarkProvider(LarkBaseProvider):
    def get(self, path, params=None):
        if path.endswith("/tables"):
            return {"data": {"items": [{"table_id": "tbl1", "name": "岗位"}]}}
        if path.endswith("/fields"):
            return {"data": {"items": [{"field_name": "岗位", "type": 1, "is_primary": True}]}}
        if path.endswith("/records"):
            return {"data": {"items": [{"record_id": "rec1", "fields": {"岗位": "产品经理"}}], "has_more": False}}
        raise AssertionError(path)


class LarkProviderTests(unittest.TestCase):
    def test_base_read_normalizes_record_ids(self):
        data = FakeLarkProvider().read("https://example.feishu.cn/base/app123")
        self.assertEqual(data["table_id"], "tbl1")
        self.assertEqual(data["records"], [{"source_id": "rec1", "fields": {"岗位": "产品经理"}}])


if __name__ == "__main__":
    unittest.main()
