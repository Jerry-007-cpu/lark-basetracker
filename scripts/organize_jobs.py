#!/usr/bin/env python3
"""Conversational table update tracker for Feishu Base, Tencent Docs, and files."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from basetracker.core import (
    auto_match_fields,
    build_state,
    diff_states,
    fields_meta_from_names,
    filter_records,
    load_state,
    read_snapshot,
    render_diff,
    render_records,
    save_state,
)
from basetracker.lark import FIELD_TYPE_NAME, LarkBaseProvider
from basetracker.mcp import MCPError
from basetracker.tencent_docs import DEFAULT_ENDPOINT, TencentDocsProvider


def log(message: str) -> None:
    print(f"[lark-basetracker] {message}", file=sys.stderr)


def comma_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def write_output(path: str | None, text: str) -> None:
    if not path:
        return
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    log(f"已写入 {output}")


def provider_fields(data: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    fields_meta = data.get("fields_meta", [])
    matched = auto_match_fields(fields_meta)
    return matched, matched.get("title") or "", matched.get("date") or ""


def state_and_text(args: argparse.Namespace, data: dict[str, Any], heading: str) -> tuple[dict[str, Any], str]:
    matched, auto_title, auto_date = provider_fields(data)
    title_field = args.title_field or auto_title
    date_field = args.date_field or auto_date
    key_field = args.key_field or matched.get("key") or ""
    state = build_state(
        data["records"],
        source=data.get("source", ""),
        key_field=key_field,
        title_field=title_field,
    )
    previous = load_state(args.previous_state) if args.previous_state else None
    if args.previous_state:
        changes = diff_states(previous, state, ignore_fields=comma_list(args.ignore_fields))
        text = render_diff(changes, title_field=title_field, show_unchanged_fields=comma_list(args.show_fields) or None)
        if args.state_out:
            save_state(args.state_out, state)
            log(f"已保存追踪快照：{Path(args.state_out).expanduser().resolve()}")
        return state, text
    if args.state_only:
        if not args.state_out:
            raise ValueError("--state-only 需要同时指定 --state-out。")
        save_state(args.state_out, state)
        log(f"已保存追踪快照：{Path(args.state_out).expanduser().resolve()}")
        return state, f"已保存表格基准快照，共 {len(data['records'])} 条记录。下次读取时可以直接比较变化。"
    if (args.days is not None or args.since or args.until) and not date_field:
        raise ValueError("没有识别到时间字段。可指定日期列，或先保存快照、下次使用 --previous-state 比较变化。")
    kept, since_ms, until_ms = filter_records(
        data["records"],
        date_field=date_field,
        days=args.days,
        since=args.since,
        until=args.until,
    )
    text = render_records(
        kept,
        title_field=title_field,
        date_field=date_field,
        show_fields=comma_list(args.show_fields) or None,
        since_ms=since_ms,
        until_ms=until_ms,
        heading=heading,
    )
    if args.state_out:
        save_state(args.state_out, state)
        log(f"已保存追踪快照：{Path(args.state_out).expanduser().resolve()}")
    return state, text


def inspect_text(data: dict[str, Any]) -> str:
    fields = data.get("fields_meta", [])
    matched = auto_match_fields(fields)
    lines = []
    if data.get("table_name"):
        lines.append(f"数据表：{data['table_name']}")
    if data.get("table_id"):
        lines.append(f"table_id：{data['table_id']}")
    if data.get("sheet_id"):
        lines.append(f"sheet_id：{data['sheet_id']}")
    if data.get("sheet_name"):
        lines.append(f"工作表：{data['sheet_name']}")
    lines.append(f"字段（{len(fields)} 个）：")
    for field in fields:
        field_type = field.get("type")
        type_name = FIELD_TYPE_NAME.get(field_type, str(field_type or "未知"))
        marks = []
        if field.get("is_primary"):
            marks.append("主字段")
        if field.get("field_name") in matched.get("date_candidates", []):
            marks.append("时间候选")
        suffix = f" ← {'、'.join(marks)}" if marks else ""
        lines.append(f"- {field.get('field_name', '')}（{type_name}）{suffix}")
    lines.extend([
        "",
        f"建议标题字段：{matched.get('title') or '未识别'}",
        f"建议时间字段：{matched.get('date') or '未识别'}",
        f"建议快照主键：{matched.get('key') or '使用平台记录 ID / 标题字段'}",
    ])
    return "\n".join(lines)


def lark_data(args: argparse.Namespace) -> dict[str, Any]:
    provider = LarkBaseProvider(args.lark_cli, identity=args.identity, logger=log)
    return provider.read(args.link, table_id=getattr(args, "table_id", None))


def cmd_inspect(args: argparse.Namespace) -> None:
    print(inspect_text(lark_data(args)))


def cmd_list(args: argparse.Namespace) -> None:
    _state, text = state_and_text(args, lark_data(args), heading="飞书表格更新")
    print(text)
    write_output(args.out, text)
    if args.wechat:
        push_wechat(args, text)


def local_data(path: str, sheet_name: str | None = None) -> dict[str, Any]:
    names, rows = read_snapshot(path, sheet_name=sheet_name)
    return {
        "source": str(Path(path).expanduser().resolve()),
        "fields_meta": fields_meta_from_names(names),
        "records": [{"source_id": "", "fields": row} for row in rows],
    }


def cmd_snapshot(args: argparse.Namespace) -> None:
    _state, text = state_and_text(args, local_data(args.file, args.sheet), heading="文件快照整理")
    print(text)
    write_output(args.out, text)


def state_from_file(path: str, sheet_name: str | None, key_field: str, title_field: str) -> dict[str, Any]:
    if path.lower().endswith(".json"):
        return load_state(path)
    data = local_data(path, sheet_name)
    matched = auto_match_fields(data["fields_meta"])
    return build_state(
        data["records"],
        source=data["source"],
        key_field=key_field or matched.get("key") or "",
        title_field=title_field or matched.get("title") or "",
    )


def cmd_diff(args: argparse.Namespace) -> None:
    before = state_from_file(args.before, args.before_sheet, args.key_field, args.title_field)
    after = state_from_file(args.after, args.after_sheet, args.key_field, args.title_field)
    title_field = args.title_field or after.get("title_field") or before.get("title_field") or ""
    changes = diff_states(before, after, ignore_fields=comma_list(args.ignore_fields))
    text = render_diff(changes, title_field=title_field, show_unchanged_fields=comma_list(args.show_fields) or None)
    print(text)
    write_output(args.out, text)
    if args.state_out:
        save_state(args.state_out, after)


def tencent_provider(args: argparse.Namespace) -> TencentDocsProvider:
    token = os.environ.get(args.token_env, "")
    if not token and args.token_file:
        token_path = Path(args.token_file).expanduser()
        if token_path.is_file():
            token = token_path.read_text(encoding="utf-8").strip()
    return TencentDocsProvider(token, endpoint=args.mcp_url, logger=log)


def tencent_data(args: argparse.Namespace) -> dict[str, Any]:
    return tencent_provider(args).read(
        args.link,
        file_id=args.file_id,
        sheet_id=args.sheet_id,
        sheet_name=args.sheet_name,
    )


def cmd_tencent_tools(args: argparse.Namespace) -> None:
    tools = tencent_provider(args).tools()
    print(json.dumps(list(tools.values()), ensure_ascii=False, indent=2))


def cmd_tencent_inspect(args: argparse.Namespace) -> None:
    print(inspect_text(tencent_data(args)))


def cmd_tencent_list(args: argparse.Namespace) -> None:
    _state, text = state_and_text(args, tencent_data(args), heading="腾讯文档更新")
    print(text)
    write_output(args.out, text)


def push_wechat(args: argparse.Namespace, text: str) -> None:
    command = [args.wxclawbot, "send", "--text", text, "--json"]
    if args.wechat_to:
        command += ["--to", args.wechat_to]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        log(f"微信推送失败：{result.stderr.strip()}")


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--date-field", default="", help="用于时间范围筛选的字段名")
    parser.add_argument("--days", type=int, default=None, help="最近 N 天")
    parser.add_argument("--since", default=None, help="起始日期 YYYY-MM-DD")
    parser.add_argument("--until", default=None, help="结束日期 YYYY-MM-DD（含当天）")
    parser.add_argument("--title-field", default="", help="记录标题字段名")
    parser.add_argument("--show-fields", default="", help="额外展示字段，逗号分隔")
    parser.add_argument("--key-field", default="", help="快照对比使用的稳定唯一字段")
    parser.add_argument("--previous-state", default=None, help="与上次保存的 JSON 状态比较；不要求时间字段")
    parser.add_argument("--state-out", default=None, help="保存本次完整状态为 JSON，供下次比较")
    parser.add_argument("--state-only", action="store_true", help="只保存基准状态，不输出整张表")
    parser.add_argument(
        "--ignore-fields",
        default="最后更新时间,更新时间,修改时间",
        help="快照比较时忽略的字段，逗号分隔",
    )
    parser.add_argument("--out", default=None, help="把结果写入文本文件")


def add_lark_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--link", required=True)
    parser.add_argument("--table-id", default=None, help="多维表格中的具体数据表 ID")
    parser.add_argument("--identity", choices=["user", "bot"], default="user")
    parser.add_argument("--lark-cli", default="lark-cli")


def add_tencent_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--link", required=True)
    parser.add_argument("--file-id", default="", help="必要时覆盖链接中的腾讯文档 file_id")
    parser.add_argument("--sheet-id", default="", help="智能表格工作表 ID")
    parser.add_argument("--sheet-name", default="", help="智能表格工作表名称")
    parser.add_argument("--mcp-url", default=DEFAULT_ENDPOINT)
    parser.add_argument("--token-env", default="TENCENT_DOCS_TOKEN", help="保存 Token 的环境变量名")
    parser.add_argument("--token-file", default="~/.config/lark-basetracker/tencent_docs_token", help="未设置环境变量时读取的 Token 文件")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="通过对话追踪飞书、腾讯文档及本地表格更新")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="检查飞书表格字段")
    add_lark_args(inspect_parser)
    inspect_parser.set_defaults(func=cmd_inspect)

    list_parser = subparsers.add_parser("list", help="整理飞书表格记录")
    add_lark_args(list_parser)
    add_filter_args(list_parser)
    list_parser.add_argument("--wechat", action="store_true")
    list_parser.add_argument("--wechat-to", default="")
    list_parser.add_argument("--wxclawbot", default="wxclawbot")
    list_parser.set_defaults(func=cmd_list)

    snapshot_parser = subparsers.add_parser("snapshot", help="整理本地 CSV/TSV/XLSX，并可保存或比较状态")
    snapshot_parser.add_argument("--file", required=True)
    snapshot_parser.add_argument("--sheet", default=None)
    add_filter_args(snapshot_parser)
    snapshot_parser.set_defaults(func=cmd_snapshot)

    diff_parser = subparsers.add_parser("diff", help="比较两份表格文件或 JSON 状态，不要求时间字段")
    diff_parser.add_argument("--before", required=True)
    diff_parser.add_argument("--after", required=True)
    diff_parser.add_argument("--before-sheet", default=None)
    diff_parser.add_argument("--after-sheet", default=None)
    diff_parser.add_argument("--key-field", default="")
    diff_parser.add_argument("--title-field", default="")
    diff_parser.add_argument("--show-fields", default="")
    diff_parser.add_argument("--ignore-fields", default="最后更新时间,更新时间,修改时间")
    diff_parser.add_argument("--state-out", default=None)
    diff_parser.add_argument("--out", default=None)
    diff_parser.set_defaults(func=cmd_diff)

    tools_parser = subparsers.add_parser("tencent-tools", help="读取腾讯文档 MCP 的实时工具定义")
    tools_parser.add_argument("--mcp-url", default=DEFAULT_ENDPOINT)
    tools_parser.add_argument("--token-env", default="TENCENT_DOCS_TOKEN")
    tools_parser.add_argument("--token-file", default="~/.config/lark-basetracker/tencent_docs_token")
    tools_parser.set_defaults(func=cmd_tencent_tools)

    tencent_inspect = subparsers.add_parser("tencent-inspect", help="检查腾讯文档在线表格字段")
    add_tencent_args(tencent_inspect)
    tencent_inspect.set_defaults(func=cmd_tencent_inspect)

    tencent_list = subparsers.add_parser("tencent-list", help="整理腾讯文档在线表格记录")
    add_tencent_args(tencent_list)
    add_filter_args(tencent_list)
    tencent_list.set_defaults(func=cmd_tencent_list)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (FileNotFoundError, ValueError, RuntimeError, MCPError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
