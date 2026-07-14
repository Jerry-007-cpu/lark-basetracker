"""Small dependency-free MCP Streamable HTTP client."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable


class MCPError(RuntimeError):
    pass


def _parse_sse(body: str) -> list[dict[str, Any]]:
    messages = []
    data_lines = []
    for line in body.splitlines() + [""]:
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
        elif not line.strip() and data_lines:
            raw = "\n".join(data_lines)
            data_lines = []
            try:
                messages.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return messages


class MCPClient:
    def __init__(
        self,
        endpoint: str,
        token: str,
        timeout: int = 30,
        requester: Callable[[dict[str, Any], dict[str, str]], tuple[int, dict[str, str], str]] | None = None,
    ):
        self.endpoint = endpoint
        self.token = token
        self.timeout = timeout
        self.requester = requester
        self.session_id = ""
        self.initialized = False
        self.next_id = 1

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    def _http_request(self, payload: dict[str, Any], headers: dict[str, str]) -> tuple[int, dict[str, str], str]:
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.status, dict(response.headers.items()), response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise MCPError(f"腾讯文档 MCP 请求失败（HTTP {exc.code}）：{body[:800]}") from exc
        except urllib.error.URLError as exc:
            raise MCPError(f"无法连接腾讯文档 MCP：{exc.reason}") from exc

    def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        requester = self.requester or self._http_request
        status, response_headers, body = requester(payload, self._headers())
        for key, value in response_headers.items():
            if key.lower() == "mcp-session-id":
                self.session_id = value
        if status == 202 or not body.strip():
            return None
        if body.lstrip().startswith("{"):
            message = json.loads(body)
        else:
            messages = _parse_sse(body)
            request_id = payload.get("id")
            message = next((item for item in messages if item.get("id") == request_id), messages[-1] if messages else None)
            if message is None:
                raise MCPError("腾讯文档 MCP 返回了无法解析的响应。")
        if message.get("error"):
            error = message["error"]
            raise MCPError(f"腾讯文档 MCP 错误 {error.get('code', '')}：{error.get('message', error)}")
        return message

    def _request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request_id = self.next_id
        self.next_id += 1
        message = self._post({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        })
        if message is None:
            raise MCPError(f"腾讯文档 MCP 调用 {method} 未返回结果。")
        return message.get("result")

    def initialize(self) -> None:
        if self.initialized:
            return
        self._request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "lark-basetracker", "version": "1.0.0"},
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        self.initialized = True

    def list_tools(self) -> list[dict[str, Any]]:
        self.initialize()
        tools = []
        cursor = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            result = self._request("tools/list", params) or {}
            tools.extend(result.get("tools", []) or [])
            cursor = result.get("nextCursor")
            if not cursor:
                return tools

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.initialize()
        result = self._request("tools/call", {"name": name, "arguments": arguments}) or {}
        if result.get("isError"):
            raise MCPError(_result_text(result) or f"腾讯文档工具 {name} 调用失败。")
        return result


def _result_text(result: dict[str, Any]) -> str:
    parts = []
    for item in result.get("content", []) or []:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "\n".join(parts)
