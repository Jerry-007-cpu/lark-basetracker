import json
import tempfile
import unittest
from pathlib import Path

from scripts.basetracker.core import (
    build_state,
    diff_states,
    parse_markdown_table,
    render_diff,
    save_state,
    load_state,
)


class SnapshotDiffTests(unittest.TestCase):
    def test_diff_without_time_field(self):
        before = build_state([
            {"fields": {"职位ID": "job-1", "岗位": "产品经理", "地点": "北京"}},
            {"fields": {"职位ID": "job-2", "岗位": "研发", "地点": "上海"}},
        ], key_field="职位ID", title_field="岗位")
        after = build_state([
            {"fields": {"职位ID": "job-1", "岗位": "产品经理", "地点": "深圳"}},
            {"fields": {"职位ID": "job-3", "岗位": "设计师", "地点": "杭州"}},
        ], key_field="职位ID", title_field="岗位")

        diff = diff_states(before, after)
        self.assertEqual([record["key"] for record in diff["added"]], ["job-3"])
        self.assertEqual([record["key"] for record in diff["removed"]], ["job-2"])
        self.assertEqual(diff["changed"][0]["changes"]["地点"], {"before": "北京", "after": "深圳"})
        text = render_diff(diff, title_field="岗位")
        self.assertIn("新增 1 · 修改 1 · 删除 1", text)
        self.assertIn("北京 → 深圳", text)

    def test_state_round_trip(self):
        state = build_state([{"fields": {"ID": "1", "名称": "示例"}}], key_field="ID", title_field="名称")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            save_state(str(path), state)
            self.assertEqual(load_state(str(path))["records"][0]["key"], "1")

    def test_parse_markdown_table(self):
        names, rows = parse_markdown_table("""
| 岗位 | 地点 |
| --- | --- |
| 产品 | 深圳 |
""")
        self.assertEqual(names, ["岗位", "地点"])
        self.assertEqual(rows, [{"岗位": "产品", "地点": "深圳"}])


if __name__ == "__main__":
    unittest.main()
