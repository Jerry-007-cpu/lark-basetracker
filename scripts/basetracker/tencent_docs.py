"""Tencent Docs online provider using the official remote MCP server."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from .core import fields_meta_from_names, parse_markdown_table
from .mcp import MCPClient, MCPError


DEFAULT_ENDPOINT = "https://docs.qq.com/openapi/mcp"


def parse_tencent_docs_link(link: str) -> tuple[str, str]:
    match = re.search(r"https?://docs\.qq\.com/([^/?#]+)/([^/?#]+)", link)
    if not match:
        raise ValueError("无法识别腾讯文档链接；请发送 docs.qq.com 的具体文档链接。")
    return match.group(1).lower(), match.group(2)


def _decode_text(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        return ""
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return text


def unwrap_result(result: dict[str, Any]) -> Any:
    structured = result.get("structuredContent")
    if structured not in (None, {}):
        return structured
    decoded = []
    for item in result.get("content", []) or []:
        if isinstance(item, dict) and item.get("type") == "text":
            decoded.append(_decode_text(str(item.get("text", ""))))
    if len(decoded) == 1:
        return decoded[0]
    return decoded


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _find_list(payload: Any, preferred_keys: tuple[str, ...]) -> list[Any]:
    for node in _walk(payload):
        if isinstance(node, dict):
            for key in preferred_keys:
                value = node.get(key)
                if isinstance(value, list):
                    return value
    if isinstance(payload, list):
        return payload
    return []


def _find_value(payload: Any, keys: tuple[str, ...]) -> Any:
    for node in _walk(payload):
        if isinstance(node, dict):
            for key in keys:
                if node.get(key) not in (None, ""):
                    return node[key]
    return None


def _id_value(item: dict[str, Any], names: tuple[str, ...]) -> str:
    for name in names:
        if item.get(name) not in (None, ""):
            return str(item[name])
    return ""


class TencentDocsProvider:
    def __init__(
        self,
        token: str,
        endpoint: str = DEFAULT_ENDPOINT,
        logger: Callable[[str], None] | None = None,
        client: MCPClient | None = None,
    ):
        if not token:
            raise ValueError("未配置 TENCENT_DOCS_TOKEN。请先在腾讯文档官方授权页获取 Token，并写入环境变量。")
        self.client = client or MCPClient(endpoint, token)
        self.log = logger or (lambda _message: None)
        self._tools: dict[str, dict[str, Any]] | None = None

    def tools(self) -> dict[str, dict[str, Any]]:
        if self._tools is None:
            self._tools = {tool["name"]: tool for tool in self.client.list_tools()}
        return self._tools

    def _tool(self, name: str) -> tuple[str, dict[str, Any]]:
        tools = self.tools()
        if name in tools:
            return name, tools[name]
        match = next(((tool_name, tool) for tool_name, tool in tools.items() if tool_name.endswith(name)), None)
        if match:
            return match
        raise MCPError(f"腾讯文档 MCP 当前没有提供工具 {name}；请检查 tools/list 返回结果。")

    @staticmethod
    def _arguments(tool: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
        schema = tool.get("inputSchema", {}) or {}
        properties = schema.get("properties", {}) or {}
        if not properties:
            return {key: value for key, value in values.items() if value not in (None, "")}
        aliases = {
            "file_id": ("file_id", "fileId", "doc_id", "docId"),
            "sheet_id": ("sheet_id", "sheetId", "table_id", "tableId"),
            "cursor": ("cursor", "page_token", "pageToken"),
            "page_size": ("page_size", "pageSize", "limit"),
        }
        arguments = {}
        for canonical, value in values.items():
            if value in (None, ""):
                continue
            target = next((name for name in aliases.get(canonical, (canonical,)) if name in properties), None)
            if target:
                arguments[target] = value
        missing = [name for name in schema.get("required", []) if name not in arguments]
        if missing:
            raise MCPError(f"腾讯文档工具参数发生变化，缺少：{', '.join(missing)}。请查看 tools/list。")
        return arguments

    def call(self, requested_name: str, **values: Any) -> tuple[Any, dict[str, Any]]:
        actual_name, tool = self._tool(requested_name)
        arguments = self._arguments(tool, values)
        return unwrap_result(self.client.call_tool(actual_name, arguments)), tool

    def _read_smartsheet(self, file_id: str, sheet_id: str = "", sheet_name: str = "") -> dict[str, Any]:
        tables_payload, _ = self.call("smartsheet.list_tables", file_id=file_id)
        tables = _find_list(tables_payload, ("tables", "table_list", "tableList", "sheets", "items", "list"))
        normalized_tables = []
        for item in tables:
            if not isinstance(item, dict):
                continue
            normalized_tables.append({
                "sheet_id": _id_value(item, ("sheet_id", "sheetId", "table_id", "tableId", "tableID", "id")),
                "name": _id_value(item, ("name", "sheet_name", "sheetName", "title")),
                "raw": item,
            })
        if not normalized_tables:
            raise MCPError("腾讯文档 MCP 没有返回可用的智能表格工作表。")
        selected = None
        if sheet_id:
            selected = next((item for item in normalized_tables if item["sheet_id"] == sheet_id), None)
        elif sheet_name:
            selected = next((item for item in normalized_tables if item["name"] == sheet_name), None)
        else:
            selected = normalized_tables[0]
        if not selected:
            available = "、".join(item["name"] or item["sheet_id"] for item in normalized_tables)
            raise ValueError(f"找不到指定工作表；可用工作表：{available}")

        field_map: dict[str, str] = {}
        fields_meta = []
        try:
            fields_payload, _ = self.call(
                "smartsheet.list_fields",
                file_id=file_id,
                sheet_id=selected["sheet_id"],
                page_size=200,
            )
            raw_fields = _find_list(fields_payload, ("fields", "field_list", "fieldList", "items", "list"))
            for index, item in enumerate(raw_fields):
                if not isinstance(item, dict):
                    continue
                field_id = _id_value(item, ("field_id", "fieldId", "id"))
                name = _id_value(item, ("field_name", "fieldName", "name", "title")) or field_id
                if field_id:
                    field_map[field_id] = name
                fields_meta.append({
                    "field_name": name,
                    "type": item.get("field_type", item.get("type", 1)),
                    "is_primary": bool(item.get("is_primary", item.get("isPrimary", index == 0))),
                })
        except MCPError:
            self.log("当前腾讯文档 MCP 未提供字段列表，将从记录内容识别字段。")

        records = []
        cursor = ""
        for _page in range(100):
            payload, _ = self.call(
                "smartsheet.list_records",
                file_id=file_id,
                sheet_id=selected["sheet_id"],
                page_size=200,
                cursor=cursor,
            )
            raw_records = _find_list(payload, ("records", "record_list", "recordList", "items", "list"))
            for item in raw_records:
                if not isinstance(item, dict):
                    continue
                raw_values = item.get("fields") or item.get("values") or item.get("record") or {}
                if isinstance(raw_values, list):
                    raw_values = {
                        _id_value(value, ("field_id", "fieldId", "name")): value.get("value")
                        for value in raw_values if isinstance(value, dict)
                    }
                fields = {
                    field_map.get(str(key), str(key)): value
                    for key, value in (raw_values.items() if isinstance(raw_values, dict) else [])
                }
                records.append({
                    "source_id": _id_value(item, ("record_id", "recordId", "id")),
                    "fields": fields,
                })
            next_cursor = _find_value(payload, ("next_cursor", "nextCursor", "page_token", "pageToken"))
            has_next = _find_value(payload, ("has_next", "hasNext", "has_more", "hasMore"))
            if not next_cursor or has_next is False:
                break
            cursor = str(next_cursor)
        if not fields_meta:
            names = list(records[0]["fields"].keys()) if records else []
            fields_meta = fields_meta_from_names(names)
        return {
            "file_id": file_id,
            "sheet_id": selected["sheet_id"],
            "sheet_name": selected["name"],
            "tables": normalized_tables,
            "fields_meta": fields_meta,
            "records": records,
        }

    def _read_generic(self, file_id: str) -> dict[str, Any]:
        payload, _ = self.call("get_content", file_id=file_id)
        if isinstance(payload, str):
            text = payload
        else:
            text_value = _find_value(payload, ("content", "text", "markdown", "data"))
            text = text_value if isinstance(text_value, str) else json.dumps(payload, ensure_ascii=False)
        names, rows = parse_markdown_table(text)
        return {
            "file_id": file_id,
            "sheet_id": "",
            "sheet_name": "",
            "tables": [],
            "fields_meta": fields_meta_from_names(names),
            "records": [{"source_id": "", "fields": row} for row in rows],
        }

    def read(self, link: str, file_id: str = "", sheet_id: str = "", sheet_name: str = "") -> dict[str, Any]:
        doc_type, parsed_file_id = parse_tencent_docs_link(link)
        selected_file_id = file_id or parsed_file_id
        has_smartsheet = any(name.endswith("smartsheet.list_tables") for name in self.tools())
        if doc_type == "smartsheet" or has_smartsheet:
            try:
                data = self._read_smartsheet(selected_file_id, sheet_id=sheet_id, sheet_name=sheet_name)
            except (MCPError, ValueError):
                if doc_type == "smartsheet":
                    raise
                data = self._read_generic(selected_file_id)
        else:
            data = self._read_generic(selected_file_id)
        data["source"] = link
        data["doc_type"] = doc_type
        return data
