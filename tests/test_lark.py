import unittest

from scripts.basetracker.lark import LarkBaseProvider, canonicalize_lark_base_link


class FakeLarkProvider(LarkBaseProvider):
    def get(self, path, params=None):
        if path.endswith("/tables"):
            return {"data": {"items": [{"table_id": "tbl1", "name": "岗位"}]}}
        if path.endswith("/fields"):
            return {"data": {"items": [{"field_name": "岗位", "type": 1, "is_primary": True}]}}
        if path.endswith("/records"):
            return {"data": {"items": [{"record_id": "rec1", "fields": {"岗位": "产品经理"}}], "has_more": False}}
        raise AssertionError(path)


class MultiTableLarkProvider(FakeLarkProvider):
    def get(self, path, params=None):
        if path.endswith("/tables"):
            return {"data": {"items": [
                {"table_id": "tbl_jobs", "name": "岗位"},
                {"table_id": "tbl_companies", "name": "公司"},
            ]}}
        return super().get(path, params)


class LarkProviderTests(unittest.TestCase):
    def test_wiki_link_can_be_saved_as_a_canonical_base_target(self):
        link = canonicalize_lark_base_link(
            "https://Example.feishu.cn/wiki/wiki123?from=recent",
            "app123",
            "tbl1",
        )
        self.assertEqual(link, "https://example.feishu.cn/base/app123?table=tbl1")

    def test_base_read_normalizes_record_ids(self):
        data = FakeLarkProvider().read("https://example.feishu.cn/base/app123")
        self.assertEqual(data["table_id"], "tbl1")
        self.assertEqual(data["table_name"], "岗位")
        self.assertEqual(data["records"], [{"source_id": "rec1", "fields": {"岗位": "产品经理"}}])

    def test_multiple_tables_require_an_explicit_selection(self):
        with self.assertRaisesRegex(ValueError, "请发送含 table= 参数"):
            MultiTableLarkProvider().read("https://example.feishu.cn/base/app123")

    def test_table_query_parameter_selects_the_matching_table(self):
        data = MultiTableLarkProvider().read(
            "https://example.feishu.cn/base/app123?table=tbl_companies"
        )
        self.assertEqual(data["table_id"], "tbl_companies")
        self.assertEqual(data["table_name"], "公司")


if __name__ == "__main__":
    unittest.main()
