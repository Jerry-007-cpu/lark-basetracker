"""Tencent Docs online provider using the official remote MCP server."""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from .core import fields_meta_from_names, parse_markdown_table
from .mcp import MCPClient, MCPError


DEFAULT_ENDPOINT = "https://docs.qq.com/openapi/mcp"
DEFAULT_TOOLS_CACHE = "~/.cache/lark-basetracker/tencent_tools.json"
DEFAULT_TOOLS_CACHE_TTL = 24 * 60 * 60


def parse_tencent_docs_link(link: str) -> tuple[str, str]:
    match = re.search(r"https?://docs\.qq\.com/([^/?#]+)/([^/?#]+)", link)
    if not match:
        raise ValueError("无法识别腾讯文档链接；请发送 docs.qq.com 的具体文档链接。")
    return match.group(1).lower(), match.group(2)


def parse_tencent_sheet_id(link: str) -> str:
    query = parse_qs(urlsplit(link).query)
    return str((query.get("tab") or [""])[0]).strip()


def canonicalize_tencent_docs_link(link: str, sheet_id: str = "") -> str:
    parsed = urlsplit(link)
    selected_sheet_id = sheet_id or parse_tencent_sheet_id(link)
    query = urlencode({"tab": selected_sheet_id}) if selected_sheet_id else ""
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path, query, ""))


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


def _compact_values(values: list[Any]) -> Any:
    cleaned = [value for value in values if value not in (None, "", [])]
    if not cleaned:
        return ""
    return cleaned[0] if len(cleaned) == 1 else cleaned


def _typed_field_value(item: dict[str, Any]) -> Any:
    if item.get("value") not in (None, ""):
        return item["value"]
    if item.get("string_value") not in (None, ""):
        return item["string_value"]
    for key in ("number_value", "bool_value"):
        if key in item and item[key] is not None:
            return item[key]
    text_items = (item.get("text_value") or {}).get("items", [])
    if text_items:
        return "".join(entry.get("text", "") for entry in text_items if isinstance(entry, dict)).strip()
    option_items = (item.get("option_value") or {}).get("items", [])
    if option_items:
        return _compact_values([entry.get("text", "") for entry in option_items if isinstance(entry, dict)])
    url_items = (item.get("url_value") or {}).get("items", [])
    if url_items:
        return _compact_values([
            entry.get("link") or entry.get("url") or entry.get("text", "")
            for entry in url_items if isinstance(entry, dict)
        ])
    auto_number = item.get("auto_number_value") or {}
    if auto_number:
        return auto_number.get("text") or auto_number.get("seq") or ""
    image_items = (item.get("image_value") or {}).get("items", [])
    if image_items:
        return _compact_values([
            entry.get("image_url") or entry.get("image_id") or entry.get("title", "")
            for entry in image_items if isinstance(entry, dict)
        ])
    reference_items = (item.get("reference_value") or {}).get("items", [])
    if reference_items:
        return _compact_values(reference_items)
    return ""


def _normalize_record(item: dict[str, Any], field_map: dict[str, str]) -> dict[str, Any]:
    raw_values = (
        item.get("fields")
        or item.get("values")
        or item.get("record")
        or item.get("field_values")
        or {}
    )
    if isinstance(raw_values, list):
        fields = {}
        for value in raw_values:
            if not isinstance(value, dict):
                continue
            raw_name = _id_value(value, ("field", "field_title", "field_name", "field_id", "fieldId", "name"))
            if raw_name:
                fields[field_map.get(raw_name, raw_name)] = _typed_field_value(value)
    else:
        fields = {
            field_map.get(str(key), str(key)): value
            for key, value in (raw_values.items() if isinstance(raw_values, dict) else [])
        }
    return {
        "source_id": _id_value(item, ("record_id", "recordId", "id")),
        "fields": fields,
    }


class TencentDocsProvider:
    def __init__(
        self,
        token: str,
        endpoint: str = DEFAULT_ENDPOINT,
        logger: Callable[[str], None] | None = None,
        client: MCPClient | None = None,
        tools_cache_path: str = "",
        tools_cache_ttl: int = DEFAULT_TOOLS_CACHE_TTL,
    ):
        if not token:
            raise ValueError("未配置 TENCENT_DOCS_TOKEN。请先在腾讯文档官方授权页获取 Token，并写入环境变量。")
        self.client = client or MCPClient(endpoint, token)
        self.endpoint = endpoint
        self.log = logger or (lambda _message: None)
        self.tools_cache_path = Path(tools_cache_path).expanduser() if tools_cache_path else None
        self.tools_cache_ttl = tools_cache_ttl
        self._tools: dict[str, dict[str, Any]] | None = None
        self._tools_from_cache = False

    def _load_tools_cache(self) -> list[dict[str, Any]] | None:
        path = self.tools_cache_path
        if not path or not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            age = time.time() - float(payload.get("saved_at", 0))
            tools = payload.get("tools")
            if payload.get("endpoint") != self.endpoint or age > self.tools_cache_ttl:
                return None
            return tools if isinstance(tools, list) else None
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None

    def _save_tools_cache(self, tools: list[dict[str, Any]]) -> None:
        path = self.tools_cache_path
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name = ""
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=path.parent, delete=False
            ) as handle:
                json.dump({
                    "endpoint": self.endpoint,
                    "saved_at": time.time(),
                    "tools": tools,
                }, handle, ensure_ascii=False)
                temporary_name = handle.name
            os.chmod(temporary_name, 0o600)
            os.replace(temporary_name, path)
        finally:
            if temporary_name and os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def tools(self, refresh: bool = False) -> dict[str, dict[str, Any]]:
        if refresh:
            self._tools = None
            self._tools_from_cache = False
        if self._tools is None:
            cached = None if refresh else self._load_tools_cache()
            if cached is not None:
                self.log("已加载腾讯文档工具缓存。")
                tools = cached
                self._tools_from_cache = True
            else:
                self.log("正在连接腾讯文档并读取所需工具定义…")
                tools = self.client.list_tools()
                self._save_tools_cache(tools)
                self.log("腾讯文档连接成功。")
            self._tools = {tool["name"]: tool for tool in tools}
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
            "cursor": ("cursor", "offset", "page_token", "pageToken"),
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
        try:
            actual_name, tool = self._tool(requested_name)
            arguments = self._arguments(tool, values)
        except MCPError:
            if not self._tools_from_cache:
                raise
            self.log("腾讯文档工具缓存已变化，正在刷新…")
            self.tools(refresh=True)
            actual_name, tool = self._tool(requested_name)
            arguments = self._arguments(tool, values)
        try:
            return unwrap_result(self.client.call_tool(actual_name, arguments)), tool
        except MCPError:
            if not self._tools_from_cache:
                raise
            self.log("腾讯文档工具调用与缓存不一致，正在刷新后重试…")
            self.tools(refresh=True)
            actual_name, tool = self._tool(requested_name)
            arguments = self._arguments(tool, values)
            return unwrap_result(self.client.call_tool(actual_name, arguments)), tool

    def _read_smartsheet(
        self,
        file_id: str,
        sheet_id: str = "",
        sheet_name: str = "",
        metadata_only: bool = False,
    ) -> dict[str, Any]:
        self.log("正在读取腾讯文档工作表列表…")
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
        self.log(f"已选择工作表：{selected['name'] or selected['sheet_id']}")

        field_map: dict[str, str] = {}
        fields_meta = []
        try:
            self.log("正在读取字段…")
            fields_payload, _ = self.call(
                "smartsheet.list_fields",
                file_id=file_id,
                sheet_id=selected["sheet_id"],
                page_size=100,
            )
            raw_fields = _find_list(fields_payload, ("fields", "field_list", "fieldList", "items", "list"))
            for index, item in enumerate(raw_fields):
                if not isinstance(item, dict):
                    continue
                field_id = _id_value(item, ("field_id", "fieldId", "id"))
                name = _id_value(item, ("field_title", "field_name", "fieldName", "name", "title")) or field_id
                if field_id:
                    field_map[field_id] = name
                fields_meta.append({
                    "field_name": name,
                    "type": item.get("field_type", item.get("type", 1)),
                    "is_primary": bool(item.get("is_primary", item.get("isPrimary", False))),
                })
        except MCPError:
            self.log("当前腾讯文档 MCP 未提供字段列表，将从记录内容识别字段。")

        records = []
        record_count = 0
        cursor = ""
        page_size = 1 if metadata_only else 100
        self.log("正在获取记录数量…" if metadata_only else "正在读取记录…")
        for _page in range(100):
            payload, _ = self.call(
                "smartsheet.list_records",
                file_id=file_id,
                sheet_id=selected["sheet_id"],
                page_size=page_size,
                cursor=cursor,
            )
            raw_records = _find_list(payload, ("records", "record_list", "recordList", "items", "list"))
            normalized_records = [
                _normalize_record(item, field_map)
                for item in raw_records if isinstance(item, dict)
            ]
            records.extend(normalized_records)
            total = _find_value(payload, ("total", "total_count", "totalCount"))
            if total not in (None, ""):
                record_count = int(total)
            else:
                record_count = max(record_count, len(records))
            if metadata_only:
                break
            next_cursor = _find_value(payload, ("next_cursor", "nextCursor", "page_token", "pageToken", "next"))
            has_next = _find_value(payload, ("has_next", "hasNext", "has_more", "hasMore"))
            if not next_cursor or has_next is False:
                break
            cursor = next_cursor
        if not fields_meta:
            names = list(records[0]["fields"].keys()) if records else []
            fields_meta = fields_meta_from_names(names)
        self.log(f"已识别 {len(fields_meta)} 个字段、{record_count} 条记录。")
        return {
            "file_id": file_id,
            "sheet_id": selected["sheet_id"],
            "sheet_name": selected["name"],
            "tables": normalized_tables,
            "fields_meta": fields_meta,
            "records": [] if metadata_only else records,
            "record_count": record_count,
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
            "record_count": len(rows),
        }

    def read(
        self,
        link: str,
        file_id: str = "",
        sheet_id: str = "",
        sheet_name: str = "",
        metadata_only: bool = False,
    ) -> dict[str, Any]:
        doc_type, parsed_file_id = parse_tencent_docs_link(link)
        selected_file_id = file_id or parsed_file_id
        selected_sheet_id = sheet_id or parse_tencent_sheet_id(link)
        has_smartsheet = any(name.endswith("smartsheet.list_tables") for name in self.tools())
        if doc_type == "smartsheet" or has_smartsheet:
            try:
                data = self._read_smartsheet(
                    selected_file_id,
                    sheet_id=selected_sheet_id,
                    sheet_name=sheet_name,
                    metadata_only=metadata_only,
                )
            except (MCPError, ValueError):
                if doc_type == "smartsheet":
                    raise
                data = self._read_generic(selected_file_id)
        else:
            data = self._read_generic(selected_file_id)
        data["source"] = link
        data["doc_type"] = doc_type
        return data
