#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书多维表格更新追踪 —— 贴一个飞书多维表格链接，整理出某时间段内更新过的记录。

典型用法（一般由 agent 按 SKILL.md 自动调用，用户只需贴链接 + 说时间段）：

  # 1) 只解析链接，看看是什么表、有哪些字段（含日期字段，便于挑"更新时间"）
  python3 scripts/organize_jobs.py inspect --identity bot --link "<飞书链接>"

  # 2) 整理：按"更新时间"字段，筛出最近 7 天更新的记录，输出到对话
  python3 scripts/organize_jobs.py list --identity bot --link "<飞书链接>" \
      --date-field "更新时间" --days 7 --title-field "名称"

  # 3) 指定日期范围，并存成 md、同时推微信
  python3 scripts/organize_jobs.py list --identity bot --link "<链接>" \
      --date-field "更新时间" --since 2026-06-01 --until 2026-06-28 \
      --out updates.md --wechat

依赖（本机 macOS）：
  - lark-cli  已完成飞书授权
  - wxclawbot 仅在 --wechat 时需要（npm i -g @claw-lab/wxclawbot-cli，且 QClaw+微信ClawBot 已接入）
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

LARK_CLI_DEFAULT = "~/.local/lib/node_modules/@larksuite/cli/bin/lark-cli"

# 调用身份：user=用户身份(user_access_token) / bot=应用身份(tenant_access_token)
IDENTITY = "bot"


# ---------- 通用 ----------

def expand(p):
    return os.path.abspath(os.path.expanduser(p))


def log(msg):
    print(f"[organize_jobs] {msg}", file=sys.stderr)


def lark_get(lark_cli, path, params=None):
    """
    用 lark-cli api 透传 GET。
    注意：lark-cli 不读 path 里的 ?查询串，查询参数必须用 --params <json> 传。
    """
    cmd = [expand(lark_cli), "api", "GET", path, "--as", IDENTITY]
    if params:
        cmd += ["--params", json.dumps(params, ensure_ascii=False)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"lark-cli 调用失败：\n{res.stderr or res.stdout}")
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        sys.exit(f"lark-cli 返回非 JSON：\n{res.stdout[:500]}")


# ---------- 链接解析 ----------

def parse_link(link, lark_cli):
    """
    支持：
      https://xxx.feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>&view=...
      https://xxx.feishu.cn/wiki/<WIKI_TOKEN>?table=<TABLE_ID>
    返回 (app_token, table_id)
    """
    table_id = None
    m = re.search(r"[?&]table=(tbl[\w]+)", link)
    if m:
        table_id = m.group(1)

    m = re.search(r"/base/([\w]+)", link)
    if m:
        return m.group(1), table_id

    m = re.search(r"/wiki/([\w]+)", link)
    if m:
        wiki_token = m.group(1)
        log(f"检测到 wiki 链接，解析 node token={wiki_token} …")
        data = lark_get(lark_cli, "/open-apis/wiki/v2/spaces/get_node",
                        params={"token": wiki_token, "obj_type": "wiki"})
        node = data.get("data", {}).get("node", {})
        app_token = node.get("obj_token")
        if not app_token:
            sys.exit(f"无法从 wiki 解析出 app_token，返回：{json.dumps(data, ensure_ascii=False)[:400]}")
        return app_token, table_id

    sys.exit("无法识别链接，请确认是飞书 base/ 或 wiki/ 多维表格链接。")


def fetch_tables(lark_cli, app_token):
    """列出某 bitable app 下的所有数据表，返回 [{table_id, name}]。"""
    data = lark_get(lark_cli, f"/open-apis/bitable/v1/apps/{app_token}/tables",
                    params={"page_size": 100})
    items = data.get("data", {}).get("items", []) or []
    return [{"table_id": it.get("table_id"), "name": it.get("name")} for it in items]


def ensure_table_id(lark_cli, app_token, table_id):
    """没有 table_id 时自动从 app 里取：单表直接用，多表打印让用户选。"""
    if table_id:
        return table_id
    tables = fetch_tables(lark_cli, app_token)
    if not tables:
        sys.exit("该多维表格里没有找到任何数据表。")
    if len(tables) == 1:
        log(f"自动选定唯一数据表：{tables[0]['name']}（{tables[0]['table_id']}）")
        return tables[0]["table_id"]
    log(f"该表里有 {len(tables)} 张数据表，默认用第一张：{tables[0]['name']}")
    for t in tables:
        log(f"    - {t['name']}　table_id={t['table_id']}")
    log("如需指定其他表，用 --table-id 覆盖。")
    return tables[0]["table_id"]


# ---------- 字段 / 记录 ----------

FIELD_TYPE_NAME = {
    1: "文本", 2: "数字", 3: "单选", 4: "多选", 5: "日期",
    7: "复选框", 11: "人员", 13: "电话", 15: "超链接",
    17: "附件", 18: "关联", 19: "查找", 20: "公式",
    1001: "创建时间", 1002: "最后更新时间", 1003: "创建人", 1004: "修改人",
}


def fetch_fields(lark_cli, app_token, table_id):
    data = lark_get(lark_cli,
                    f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                    params={"page_size": 200})
    return data.get("data", {}).get("items", []) or []


# ---------- 字段自适应匹配 ----------

# 名称关键词（命中即加分），按优先级从高到低
TITLE_KEYWORDS = ["名称", "标题", "主题", "事项", "项目", "记录", "岗位名称", "职位名称",
                  "岗位", "职位", "职务", "岗位标题", "title", "name", "subject",
                  "position", "job", "role"]
DATE_KEYWORDS = ["更新时间", "最后更新时间", "修改时间", "更新日期", "变更时间",
                 "发布时间", "发布日期", "创建时间", "创建日期", "开放时间", "开放日期",
                 "上线时间", "上线日期", "开始时间", "截止时间", "截止日期", "投递开始",
                 "投递截止", "时间", "日期", "date", "time", "updated", "modified",
                 "created", "open", "publish"]

DATE_TYPES = {5, 1001, 1002}   # 日期 / 创建时间 / 最后更新时间
TEXTLIKE_TYPES = {1, 3, 15, 20}  # 文本 / 单选 / 超链接 / 公式


def _keyword_score(name, keywords):
    """名称命中关键词的得分：越靠前的关键词、越完整匹配，分越高。"""
    lname = name.lower()
    best = 0
    for i, kw in enumerate(keywords):
        k = kw.lower()
        if lname == k:
            best = max(best, 100 - i)          # 完全相等最高
        elif k in lname:
            best = max(best, 60 - i)           # 包含次之
    return best


def auto_match_fields(fields_meta):
    """
    输入 fetch_fields 的返回（含 field_name / type / is_primary）。
    返回 dict: {title, date, date_candidates, all_names}
    任一项可能为 None（没匹配到）。
    """
    names = [f.get("field_name", "") for f in fields_meta]

    # —— 标题字段 ——
    title = None
    # 1) 主字段优先（多维表格第一列通常是主字段）
    for f in fields_meta:
        if f.get("is_primary"):
            title = f["field_name"]
            break
    # 2) 名称关键词
    if not title:
        scored = []
        for f in fields_meta:
            s = _keyword_score(f.get("field_name", ""), TITLE_KEYWORDS)
            if f.get("type") in TEXTLIKE_TYPES:
                s += 5
            if s > 0:
                scored.append((s, f["field_name"]))
        if scored:
            scored.sort(reverse=True)
            title = scored[0][1]
    # 3) 兜底：第一个文本字段
    if not title:
        for f in fields_meta:
            if f.get("type") in TEXTLIKE_TYPES:
                title = f["field_name"]
                break
    if not title and names:
        title = names[0]

    # —— 日期/更新时间字段 ——
    date_scored = []
    for f in fields_meta:
        name = f.get("field_name", "")
        t = f.get("type")
        s = _keyword_score(name, DATE_KEYWORDS)
        if t in DATE_TYPES:
            s += 40                    # 真·日期类型大加分
        elif t == 2:                   # 数字（可能存时间戳）
            s += 2
        if s > 0:
            date_scored.append((s, name, t in DATE_TYPES))
    date_scored.sort(reverse=True)
    date = date_scored[0][1] if date_scored else None
    date_candidates = [n for _, n, _ in date_scored]

    return {"title": title, "date": date,
            "date_candidates": date_candidates, "all_names": names}


def fetch_records(lark_cli, app_token, table_id):
    records, page_token = [], None
    path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        data = lark_get(lark_cli, path, params=params)
        body = data.get("data", {})
        records.extend(body.get("items", []) or [])
        if body.get("has_more") and body.get("page_token"):
            page_token = body["page_token"]
        else:
            break
    return records


# ---------- 值归一化 ----------

def norm(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list):
        return ", ".join(x for x in (norm(i) for i in v) if x)
    if isinstance(v, dict):
        for k in ("text", "name", "en_name", "link", "value"):
            if v.get(k):
                return norm(v[k])
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def to_epoch_ms(v):
    """把飞书日期字段值转成毫秒时间戳；无法解析返回 None。"""
    if v is None or v == "":
        return None
    if isinstance(v, list) and v:
        v = v[0]
    if isinstance(v, dict):
        v = v.get("value") or v.get("text") or ""
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    if s.isdigit():
        return int(s)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return int(datetime.strptime(s, fmt).timestamp() * 1000)
        except ValueError:
            continue
    return None


def ms_to_date(ms):
    try:
        return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")
    except Exception:
        return "?"


# ---------- 业务 ----------

def resolve_range(args):
    """返回 (since_ms, until_ms)；缺省返回 (None, None) 表示不限。"""
    since_ms = until_ms = None
    if args.days is not None:
        since = datetime.now() - timedelta(days=args.days)
        since_ms = int(since.timestamp() * 1000)
    if args.since:
        since_ms = to_epoch_ms(args.since)
    if args.until:
        # until 当天算到 23:59:59
        d = datetime.strptime(args.until, "%Y-%m-%d") + timedelta(days=1)
        until_ms = int(d.timestamp() * 1000)
    return since_ms, until_ms


def cmd_inspect(args):
    global IDENTITY
    IDENTITY = args.identity
    app_token, table_id = parse_link(args.link, args.lark_cli)
    table_id = ensure_table_id(args.lark_cli, app_token, table_id)
    print(f"app_token : {app_token}")
    print(f"table_id  : {table_id}")
    fields = fetch_fields(args.lark_cli, app_token, table_id)
    print(f"\n字段（{len(fields)} 个）：")
    for f in fields:
        t = f.get("type")
        tname = FIELD_TYPE_NAME.get(t, f"type{t}")
        mark = "  ← 主字段" if f.get("is_primary") else ""
        if t in DATE_TYPES:
            mark += "  ← 可作为「日期/更新时间」"
        print(f"  - {f['field_name']}（{tname}）{mark}")

    m = auto_match_fields(fields)
    print("\n—— 自动匹配建议 ——")
    print(f"  标题字段：{m['title'] or '(未识别，请手动指定)'}")
    print(f"  日期/更新时间字段：{m['date'] or '(未识别，请手动指定)'}")
    if len(m["date_candidates"]) > 1:
        print(f"  其他候选日期字段：{', '.join(m['date_candidates'][1:])}")
    print("\n若建议不对，list 时用 --title-field / --date-field 覆盖即可。")


def cmd_list(args):
    global IDENTITY
    IDENTITY = args.identity
    app_token, table_id = parse_link(args.link, args.lark_cli)
    table_id = args.table_id or table_id
    table_id = ensure_table_id(args.lark_cli, app_token, table_id)

    # 字段自适应：没显式指定时，自动匹配
    if not args.title_field or not args.date_field:
        fields_meta = fetch_fields(args.lark_cli, app_token, table_id)
        m = auto_match_fields(fields_meta)
        if not args.title_field:
            args.title_field = m["title"] or ""
            log(f"自动匹配标题字段：{args.title_field or '(未识别)'}")
        if not args.date_field:
            args.date_field = m["date"] or ""
            log(f"自动匹配日期/更新时间字段：{args.date_field or '(未识别)'}"
                + (f"；其他候选：{', '.join(m['date_candidates'][1:])}"
                   if len(m["date_candidates"]) > 1 else ""))

    records = fetch_records(args.lark_cli, app_token, table_id)
    log(f"共 {len(records)} 条记录")

    since_ms, until_ms = resolve_range(args)
    date_field = args.date_field

    kept = []
    for r in records:
        fields = r.get("fields", {})
        dms = to_epoch_ms(fields.get(date_field)) if date_field else None
        if date_field and dms is None:
            continue  # 没有所选日期字段的跳过
        if since_ms is not None and dms is not None and dms < since_ms:
            continue
        if until_ms is not None and dms is not None and dms >= until_ms:
            continue
        kept.append((dms, fields))

    # 按日期/更新时间倒序
    kept.sort(key=lambda x: (x[0] is None, -(x[0] or 0)))

    text = render(args, kept, since_ms, until_ms)
    print(text)

    if args.out:
        with open(expand(args.out), "w", encoding="utf-8") as f:
            f.write(text)
        log(f"已写入 {expand(args.out)}")

    if args.wechat:
        push_wechat(args, text)


def render(args, kept, since_ms, until_ms):
    rng = ""
    if since_ms or until_ms:
        a = ms_to_date(since_ms) if since_ms else "…"
        b = ms_to_date(until_ms - 1) if until_ms else "今天"
        rng = f"（{a} ~ {b}）"
    lines = [f"📌 表格更新整理{rng}　共 {len(kept)} 条"]
    if not kept:
        lines.append("（该时间段内没有符合条件的记录）")
        return "\n".join(lines)

    title_field = args.title_field
    show = args.show_fields.split(",") if args.show_fields else None

    for dms, fields in kept:
        title = norm(fields.get(title_field)) if title_field else ""
        title = title or "(未命名记录)"
        date_str = ms_to_date(dms) if dms else ""
        head = f"\n• {title}"
        if date_str:
            head += f"　日期：{date_str}"
        lines.append(head)
        keys = show if show else [k for k in fields.keys()
                                  if k not in (title_field, args.date_field)]
        for k in keys:
            k = k.strip()
            val = norm(fields.get(k))
            if val:
                lines.append(f"    {k}：{val}")
    return "\n".join(lines)


def push_wechat(args, text):
    cmd = [args.wxclawbot, "send", "--text", text, "--json"]
    if args.wechat_to:
        cmd += ["--to", args.wechat_to]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print((res.stdout or "").strip())
    if res.returncode != 0:
        log(f"微信推送失败：{res.stderr.strip()}")


# ---------- CLI ----------

def build_parser():
    p = argparse.ArgumentParser(description="飞书多维表格更新追踪")
    p.add_argument("--lark-cli", default=LARK_CLI_DEFAULT)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("inspect", help="解析链接、列出字段")
    pi.add_argument("--link", required=True)
    pi.add_argument("--identity", choices=["user", "bot"], default="bot",
                    help="调用身份：user=用户身份 / bot=应用身份(tenant)")
    pi.set_defaults(func=cmd_inspect)

    pl = sub.add_parser("list", help="整理某时间段内更新的记录")
    pl.add_argument("--link", required=True)
    pl.add_argument("--identity", choices=["user", "bot"], default="bot",
                    help="调用身份：user=用户身份 / bot=应用身份(tenant)")
    pl.add_argument("--table-id", default=None, help="链接没带 table 时手动指定")
    pl.add_argument("--date-field", default="", help='用作"日期/更新时间"的字段名')
    pl.add_argument("--days", type=int, default=None, help="最近 N 天")
    pl.add_argument("--since", default=None, help="起始日期 YYYY-MM-DD")
    pl.add_argument("--until", default=None, help="结束日期 YYYY-MM-DD（含当天）")
    pl.add_argument("--title-field", default="", help="记录标题字段名")
    pl.add_argument("--show-fields", default="", help="额外展示字段，逗号分隔；留空=全部")
    pl.add_argument("--out", default=None, help="写出 md 文件路径")
    pl.add_argument("--wechat", action="store_true", help="同时推送微信")
    pl.add_argument("--wechat-to", default="", help="微信接收人，留空=默认")
    pl.add_argument("--wxclawbot", default="wxclawbot")
    pl.set_defaults(func=cmd_list)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
