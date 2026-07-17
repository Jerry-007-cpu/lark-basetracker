import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from scripts.basetracker.core import (
    build_state,
    diff_states,
    parse_markdown_table,
    filter_records,
    render_diff,
    render_records,
    save_state,
    load_state,
    to_epoch_ms,
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

    def test_text_dates_without_year_use_current_year(self):
        expected_year = datetime.now().year
        for value in ("7.17", "7/17", "7-17", "7月17日"):
            with self.subTest(value=value):
                parsed = datetime.fromtimestamp(to_epoch_ms(value) / 1000)
                self.assertEqual((parsed.year, parsed.month, parsed.day), (expected_year, 7, 17))

    def test_full_text_dates_support_dots_and_chinese(self):
        for value in ("2026.7.17", "2026年7月17日"):
            with self.subTest(value=value):
                parsed = datetime.fromtimestamp(to_epoch_ms(value) / 1000)
                self.assertEqual((parsed.year, parsed.month, parsed.day), (2026, 7, 17))

    def test_non_date_in_date_column_is_skipped(self):
        records = [
            {"fields": {"公司": "有效记录", "开启时间": "7.17"}},
            {"fields": {"公司": "说明文字", "开启时间": "祝各位同学一切顺利"}},
            {"fields": {"公司": "错误日期", "开启时间": "13.40"}},
        ]
        kept, _since, _until = filter_records(records, date_field="开启时间")
        self.assertEqual([fields["公司"] for _date, fields in kept], ["有效记录"])

    def test_large_result_uses_one_consistent_compact_template(self):
        kept = []
        for index in range(21):
            kept.append((None, {
                "公司": f"公司{index}",
                "地点": "深圳" if index else "",
                "投递链接": f"https://example.test/{index}",
            }))
        text = render_records(
            kept,
            title_field="公司",
            show_fields=["地点", "投递链接"],
            output_format="auto",
        )
        record_lines = [line for line in text.splitlines() if line.startswith("• ")]
        self.assertEqual(len(record_lines), 21)
        self.assertTrue(all("｜地点：" in line and "｜投递链接：https://" in line for line in record_lines))
        self.assertIn("公司0｜地点：—｜投递链接：https://example.test/0", record_lines[0])
        self.assertIn("公司20｜地点：深圳｜投递链接：https://example.test/20", record_lines[-1])

    def test_detailed_result_keeps_requested_fields_with_placeholders(self):
        text = render_records(
            [(None, {"公司": "示例", "投递链接": "https://example.test"})],
            title_field="公司",
            show_fields=["地点", "投递链接"],
            output_format="detailed",
        )
        self.assertIn("地点：—", text)
        self.assertIn("投递链接：https://example.test", text)


if __name__ == "__main__":
    unittest.main()
