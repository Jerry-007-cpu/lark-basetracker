import stat
import tempfile
import unittest
from pathlib import Path

from scripts.basetracker.sources import (
    add_source,
    get_source,
    load_registry,
    remove_source,
    render_source_picker,
)


class SourceRegistryTests(unittest.TestCase):
    def test_sources_are_saved_separately_and_rendered_as_a_picker(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = str(Path(directory) / "sources.json")
            add_source(
                registry,
                name="27暑期秋招",
                kind="lark",
                location="https://example.feishu.cn/base/app1?table=tbl1",
                table_id="tbl1",
            )
            add_source(
                registry,
                name="内推汇总",
                kind="tencent",
                location="https://docs.qq.com/sheet/example",
                sheet_id="sheet1",
            )

            sources = load_registry(registry)["sources"]
            picker = render_source_picker(sources)
            self.assertEqual(len(sources), 2)
            self.assertIn("飞书｜27暑期秋招", picker)
            self.assertIn("腾讯文档｜内推汇总", picker)
            self.assertIn("全部汇总", picker)
            self.assertEqual(stat.S_IMODE(Path(registry).stat().st_mode), 0o600)

    def test_duplicate_targets_are_rejected_and_sources_can_be_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = str(Path(directory) / "sources.json")
            add_source(
                registry,
                name="岗位表",
                kind="lark",
                location="https://example.feishu.cn/base/app1?table=tbl1",
                table_id="tbl1",
            )
            with self.assertRaisesRegex(ValueError, "已保存为"):
                add_source(
                    registry,
                    name="另一个名字",
                    kind="lark",
                    location="https://example.feishu.cn/base/app1?table=tbl1",
                    table_id="tbl1",
                )

            self.assertEqual(get_source(registry, "岗位表")["table_id"], "tbl1")
            removed = remove_source(registry, "岗位表")
            self.assertEqual(removed["name"], "岗位表")
            self.assertEqual(load_registry(registry)["sources"], [])

    def test_tencent_target_can_be_renamed_after_verified_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = str(Path(directory) / "sources.json")
            add_source(
                registry,
                name="腾讯文档智能表格",
                kind="tencent",
                location="https://docs.qq.com/smartsheet/ABC123?tab=sheet-1&viewId=view-1",
                sheet_id="sheet-1",
            )
            add_source(
                registry,
                name="27秋招正式批+提前批",
                kind="tencent",
                location="https://docs.qq.com/smartsheet/ABC123?tab=sheet-1",
                sheet_id="sheet-1",
                sheet_name="27秋招正式批+提前批",
                replace=True,
            )
            sources = load_registry(registry)["sources"]
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0]["name"], "27秋招正式批+提前批")
            self.assertEqual(sources[0]["sheet_name"], "27秋招正式批+提前批")


if __name__ == "__main__":
    unittest.main()
