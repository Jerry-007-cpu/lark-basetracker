#!/usr/bin/env python3
"""Store a Tencent Docs MCP token without putting it in shell history or chat."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="安全保存腾讯文档 MCP Token")
    parser.add_argument("--token-file", default="~/.config/lark-basetracker/tencent_docs_token")
    args = parser.parse_args()
    print("下一步会进入隐藏输入。请等提示出现后再粘贴 Token；输入期间屏幕不会显示字符。")
    token = getpass.getpass("粘贴腾讯文档 MCP Token（输入不会显示）：").strip()
    if not token:
        raise SystemExit("没有收到 Token，未保存。")
    path = Path(args.token_file).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    print(f"已安全保存到：{path}")
    print("请回到 Agent 对话并回复“已配置”，继续验证腾讯文档连接。")


if __name__ == "__main__":
    main()
