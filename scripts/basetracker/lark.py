"""Feishu/Lark Base provider backed by the official lark-cli."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Any, Callable


FIELD_TYPE_NAME = {
    1: "文本", 2: "数字", 3: "单选", 4: "多选", 5: "日期",
    7: "复选框", 11: "人员", 13: "电话", 15: "超链接",
    17: "附件", 18: "关联", 19: "查找", 20: "公式",
    1001: "创建时间", 1002: "最后更新时间", 1003: "创建人", 1004: "修改人",
}


def resolve_executable(command: str) -> str:
    if os.path.sep in command or command.startswith("~"):
        return os.path.abspath(os.path.expanduser(command))
    return shutil.which(command) or command


class LarkBaseProvider:
    def __init__(self, lark_cli: str = "lark-cli", identity: str = "user", logger: Callable[[str], None] | None = None):
        self.lark_cli = lark_cli
        self.identity = identity
        self.log = logger or (lambda _message: None)

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        command = [resolve_executable(self.lark_cli), "api", "GET", path, "--as", self.identity]
        if params:
            command += ["--params", json.dumps(params, ensure_ascii=False)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"lark-cli 调用失败：\n{result.stderr or result.stdout}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"lark-cli 返回非 JSON：\n{result.stdout[:500]}") from exc

    def parse_link(self, link: str) -> tuple[str, str | None]:
        table_match = re.search(r"[?&]table=(tbl[\w]+)", link)
        table_id = table_match.group(1) if table_match else None
        base_match = re.search(r"/base/([\w]+)", link)
        if base_match:
            return base_match.group(1), table_id
        wiki_match = re.search(r"/wiki/([\w]+)", link)
        if wiki_match:
            wiki_token = wiki_match.group(1)
            data = self.get(
                "/open-apis/wiki/v2/spaces/get_node",
                params={"token": wiki_token, "obj_type": "wiki"},
            )
            app_token = data.get("data", {}).get("node", {}).get("obj_token")
            if not app_token:
                raise ValueError("无法从 Wiki 链接解析出多维表格 Token。")
            return app_token, table_id
        raise ValueError("无法识别链接，请确认是飞书 base/ 或 wiki/ 多维表格链接。")

    def fetch_tables(self, app_token: str) -> list[dict[str, str]]:
        data = self.get(f"/open-apis/bitable/v1/apps/{app_token}/tables", {"page_size": 100})
        items = data.get("data", {}).get("items", []) or []
        return [{"table_id": item.get("table_id", ""), "name": item.get("name", "")} for item in items]

    def ensure_table_id(self, app_token: str, table_id: str | None) -> str:
        if table_id:
            return table_id
        tables = self.fetch_tables(app_token)
        if not tables:
            raise ValueError("该多维表格里没有找到任何数据表。")
        if len(tables) > 1:
            self.log(f"检测到 {len(tables)} 张数据表，默认使用第一张：{tables[0]['name']}")
        return tables[0]["table_id"]

    def fetch_fields(self, app_token: str, table_id: str) -> list[dict[str, Any]]:
        data = self.get(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
            {"page_size": 200},
        )
        return data.get("data", {}).get("items", []) or []

    def fetch_records(self, app_token: str, table_id: str) -> list[dict[str, Any]]:
        records = []
        page_token = None
        path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            data = self.get(path, params=params)
            body = data.get("data", {})
            for item in body.get("items", []) or []:
                records.append({
                    "source_id": item.get("record_id", ""),
                    "fields": item.get("fields", {}) or {},
                })
            if body.get("has_more") and body.get("page_token"):
                page_token = body["page_token"]
            else:
                return records

    def read(self, link: str, table_id: str | None = None) -> dict[str, Any]:
        app_token, parsed_table_id = self.parse_link(link)
        selected_table_id = self.ensure_table_id(app_token, table_id or parsed_table_id)
        return {
            "source": link,
            "app_token": app_token,
            "table_id": selected_table_id,
            "fields_meta": self.fetch_fields(app_token, selected_table_id),
            "records": self.fetch_records(app_token, selected_table_id),
        }
