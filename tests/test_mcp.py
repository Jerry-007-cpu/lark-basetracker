import ssl
import tempfile
import unittest
from pathlib import Path

from scripts.basetracker.mcp import MCPClient, _default_ssl_context
from scripts.basetracker.tencent_docs import (
    TencentDocsProvider,
    canonicalize_tencent_docs_link,
    parse_tencent_sheet_id,
)


class MCPClientTests(unittest.TestCase):
    def test_default_ssl_context_keeps_verification_enabled(self):
        context = _default_ssl_context()
        self.assertIsInstance(context, ssl.SSLContext)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_initialization_and_tool_call(self):
        calls = []

        def requester(payload, headers):
            calls.append((payload, headers))
            method = payload["method"]
            if method == "initialize":
                return 200, {"Mcp-Session-Id": "session-1"}, '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18"}}'
            if method == "notifications/initialized":
                return 202, {}, ""
            if method == "tools/list":
                return 200, {}, '{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"demo","inputSchema":{"type":"object"}}]}}'
            return 200, {}, '{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"ok"}]}}'

        client = MCPClient("https://example.test/mcp", "secret", requester=requester)
        self.assertEqual(client.list_tools()[0]["name"], "demo")
        self.assertEqual(client.call_tool("demo", {})["content"][0]["text"], "ok")
        self.assertEqual(calls[0][1]["Authorization"], "secret")
        self.assertEqual(calls[2][1]["Mcp-Session-Id"], "session-1")


class FakeTencentClient:
    def list_tools(self):
        required_file = {"type": "object", "properties": {"file_id": {"type": "string"}}, "required": ["file_id"]}
        required_sheet = {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"},
                "sheet_id": {"type": "string"},
                "page_size": {"type": "integer"},
                "cursor": {"type": "string"},
            },
            "required": ["file_id", "sheet_id"],
        }
        return [
            {"name": "smartsheet.list_tables", "inputSchema": required_file},
            {"name": "smartsheet.list_fields", "inputSchema": required_sheet},
            {"name": "smartsheet.list_records", "inputSchema": required_sheet},
        ]

    def call_tool(self, name, arguments):
        if name.endswith("list_tables"):
            payload = {"tables": [{"sheet_id": "sheet-1", "name": "岗位"}]}
        elif name.endswith("list_fields"):
            payload = {"fields": [
                {"field_id": "f1", "field_name": "岗位", "field_type": 1, "is_primary": True},
                {"field_id": "f2", "field_name": "地点", "field_type": 1},
            ]}
        else:
            payload = {"records": [{"record_id": "r1", "fields": {"f1": "产品经理", "f2": "深圳"}}], "has_next": False}
        return {"structuredContent": payload}


class TencentProviderTests(unittest.TestCase):
    def test_smartsheet_normalization(self):
        provider = TencentDocsProvider("secret", client=FakeTencentClient())
        data = provider.read("https://docs.qq.com/smartsheet/ABC123")
        self.assertEqual(data["sheet_id"], "sheet-1")
        self.assertEqual(data["records"][0]["source_id"], "r1")
        self.assertEqual(data["records"][0]["fields"]["岗位"], "产品经理")

    def test_tab_query_and_current_mcp_payload_are_normalized(self):
        class CurrentTencentClient(FakeTencentClient):
            def __init__(self):
                self.record_arguments = None

            def list_tools(self):
                required_file = {"type": "object", "properties": {"file_id": {"type": "string"}}, "required": ["file_id"]}
                required_sheet = {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string"},
                        "sheet_id": {"type": "string"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"},
                    },
                    "required": ["file_id", "sheet_id"],
                }
                return [
                    {"name": "smartsheet.list_tables", "inputSchema": required_file},
                    {"name": "smartsheet.list_fields", "inputSchema": required_sheet},
                    {"name": "smartsheet.list_records", "inputSchema": required_sheet},
                ]

            def call_tool(self, name, arguments):
                if name.endswith("list_tables"):
                    payload = {"sheets": [
                        {"sheet_id": "sheet-1", "title": "26秋招"},
                        {"sheet_id": "sheet-2", "title": "27秋招"},
                    ]}
                elif name.endswith("list_fields"):
                    payload = {"fields": [
                        {"field_id": "f1", "field_title": "公司名称", "field_type": "text"},
                        {"field_id": "f2", "field_title": "招聘岗位", "field_type": "select"},
                        {"field_id": "f3", "field_title": "投递链接", "field_type": "url"},
                    ]}
                else:
                    self.record_arguments = arguments
                    payload = {
                        "records": [{
                            "record_id": "r1",
                            "field_values": [
                                {"field": "公司名称", "text_value": {"items": [{"text": "某"}, {"text": "科技"}]}},
                                {"field": "招聘岗位", "option_value": {"items": [{"text": "产品类"}]}},
                                {"field": "投递链接", "url_value": {"items": [{"link": "https://example.test/jobs"}]}},
                            ],
                        }],
                        "has_more": False,
                        "total": 246,
                    }
                return {"structuredContent": payload}

        client = CurrentTencentClient()
        provider = TencentDocsProvider("secret", client=client)
        link = "https://docs.qq.com/smartsheet/ABC123?tab=sheet-2&_t=123&viewId=view-1"
        data = provider.read(link)
        self.assertEqual(parse_tencent_sheet_id(link), "sheet-2")
        self.assertEqual(data["sheet_name"], "27秋招")
        self.assertEqual(data["record_count"], 246)
        self.assertEqual(data["records"][0]["fields"]["公司名称"], "某科技")
        self.assertEqual(data["records"][0]["fields"]["招聘岗位"], "产品类")
        self.assertEqual(data["records"][0]["fields"]["投递链接"], "https://example.test/jobs")
        self.assertEqual(
            canonicalize_tencent_docs_link(link),
            "https://docs.qq.com/smartsheet/ABC123?tab=sheet-2",
        )

        metadata = provider.read(link, metadata_only=True)
        self.assertEqual(metadata["records"], [])
        self.assertEqual(metadata["record_count"], 246)
        self.assertEqual(client.record_arguments["limit"], 1)

    def test_tool_definitions_can_be_loaded_from_cache(self):
        class CountingClient(FakeTencentClient):
            def __init__(self):
                self.list_count = 0

            def list_tools(self):
                self.list_count += 1
                return super().list_tools()

        with tempfile.TemporaryDirectory() as directory:
            cache = str(Path(directory) / "tools.json")
            first_client = CountingClient()
            first = TencentDocsProvider("secret", client=first_client, tools_cache_path=cache)
            self.assertIn("smartsheet.list_tables", first.tools())
            self.assertEqual(first_client.list_count, 1)

            second_client = CountingClient()
            second = TencentDocsProvider("secret", client=second_client, tools_cache_path=cache)
            self.assertIn("smartsheet.list_tables", second.tools())
            self.assertEqual(second_client.list_count, 0)

    def test_current_offset_pagination_reads_each_page_once(self):
        class OffsetClient:
            def __init__(self):
                self.offsets = []

            def list_tools(self):
                required_file = {"type": "object", "properties": {"file_id": {"type": "string"}}, "required": ["file_id"]}
                required_sheet = {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string"},
                        "sheet_id": {"type": "string"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"},
                    },
                    "required": ["file_id", "sheet_id"],
                }
                return [
                    {"name": "smartsheet.list_tables", "inputSchema": required_file},
                    {"name": "smartsheet.list_fields", "inputSchema": required_sheet},
                    {"name": "smartsheet.list_records", "inputSchema": required_sheet},
                ]

            def call_tool(self, name, arguments):
                if name.endswith("list_tables"):
                    payload = {"sheets": [{"sheet_id": "sheet-1", "title": "岗位"}]}
                elif name.endswith("list_fields"):
                    payload = {"fields": [{"field_id": "f1", "field_title": "公司名称", "field_type": "text"}]}
                else:
                    offset = arguments.get("offset", 0)
                    self.offsets.append(offset)
                    count = 100 if offset == 0 else 1
                    payload = {
                        "records": [
                            {"record_id": f"r{offset + index}", "field_values": [
                                {"field": "公司名称", "text_value": {"items": [{"text": f"公司{offset + index}"}]}}
                            ]}
                            for index in range(count)
                        ],
                        "has_more": offset == 0,
                        "next": 100 if offset == 0 else 0,
                        "total": 101,
                    }
                return {"structuredContent": payload}

        client = OffsetClient()
        provider = TencentDocsProvider("secret", client=client)
        data = provider.read("https://docs.qq.com/smartsheet/ABC123?tab=sheet-1")
        self.assertEqual(client.offsets, [0, 100])
        self.assertEqual(len(data["records"]), 101)
        self.assertEqual(data["record_count"], 101)


if __name__ == "__main__":
    unittest.main()
