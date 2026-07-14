import unittest

from scripts.basetracker.mcp import MCPClient
from scripts.basetracker.tencent_docs import TencentDocsProvider


class MCPClientTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
