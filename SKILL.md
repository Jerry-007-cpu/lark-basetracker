---
name: lark-basetracker
description: 通过自然语言追踪飞书多维表格、腾讯文档在线表格或 CSV/TSV/XLSX 的新增、修改和删除记录。支持按创建/更新时间筛选，也支持在没有时间字段时保存并比较两次快照。适合求职岗位更新、项目、线索、内容排期等表格；当用户发送 Feishu/Lark Base、docs.qq.com 链接或表格文件并询问最近更新、变化或职位清单时使用。
---

# lark-basetracker

让用户只通过对话完成操作。把字段检查、命令执行和格式整理留在后台，不要求普通用户复制 Python、Shell 或 `lark-cli` 命令。

## 选择数据来源

- 飞书 `base/` 或 `wiki/` 链接：使用飞书用户身份在线读取。
- 腾讯文档 `docs.qq.com` 链接：使用仓库内置的腾讯文档 MCP 客户端在线读取。
- CSV、TSV、XLSX：直接读取本地文件。
- 用户询问“两次之间改了什么”或表中没有时间字段：使用持久快照比较。

只执行只读操作。除非用户明确要求，否则不要写入在线表格、推送消息或创建文件。

## 对话规则

1. 从用户消息提取链接或文件、时间范围、展示字段，以及“新增/修改/发布/开放”的含义。
2. 自动检查字段。只有多个时间字段代表不同业务含义且无法判断时，问一个简短问题。
3. 优先输出可直接阅读或转发的清单，不输出调试日志。
4. 用户已给出足够信息时直接执行，不重复确认。
5. 不要求用户提供编辑权限。用户本人的查看权限是正常主流程。
6. 不在聊天正文中索取 App Secret、Access Token 或腾讯文档 Token。

## 飞书在线读取

默认使用 `user` 身份。后台检查字段：

```bash
python3 scripts/organize_jobs.py inspect --identity user --link "<飞书链接>"
```

按时间字段整理：

```bash
python3 scripts/organize_jobs.py list --identity user --link "<飞书链接>" \
  --date-field "<时间字段>" --days 7 \
  --title-field "<标题字段>" --show-fields "<字段1,字段2>"
```

字段语义优先级：

- “新增”使用 `创建时间`。
- “修改/更新”使用 `最后更新时间` 或 `更新时间`。
- “发布”使用 `发布时间`。
- “开放”使用 `开放时间`。

首次使用时检查 `lark-cli --version`。缺少时先说明并取得同意，再安装飞书官方 CLI。随后用 `lark-cli config init --new` 配置应用，并用 `lark-cli auth login --domain base --no-wait --json` 发起用户授权。把官方返回的验证链接原样交给用户，不重写链接，不在用户看到链接前阻塞等待。

## 腾讯文档在线读取

腾讯文档使用官方 MCP 地址 `https://docs.qq.com/openapi/mcp`。先检查实时工具定义：

```bash
python3 scripts/organize_jobs.py tencent-tools
```

检查在线表格字段：

```bash
python3 scripts/organize_jobs.py tencent-inspect --link "<docs.qq.com 链接>"
```

整理在线表格：

```bash
python3 scripts/organize_jobs.py tencent-list --link "<docs.qq.com 链接>" \
  --days 7 --show-fields "<字段1,字段2>"
```

内置客户端会执行 MCP 初始化、`tools/list` 和 `tools/call`，并根据实时 JSON Schema 组装参数。智能表格优先调用 `smartsheet.list_tables`、`smartsheet.list_fields`、`smartsheet.list_records`；普通在线表格通过 `get_content` 读取结构化内容。

如果没有 Token，引导用户打开 `https://docs.qq.com/open/auth/mcp.html` 获取个人 Token，然后在本机终端运行：

```bash
python3 scripts/configure_tencent_docs.py
```

该脚本使用隐藏输入并保存到权限为 `0600` 的本地文件。也可由运行环境设置 `TENCENT_DOCS_TOKEN`。不要让用户把 Token 发到聊天中。

出现 `400006` 时重新授权；出现 `400007` 时说明腾讯文档账户缺少对应 VIP 能力。在线读取失败时，回退到用户上传的 XLSX、CSV 或 TSV，不声称能够绕过查看、下载或会员权限。

## 本地文件与快照比较

按时间字段整理单份文件：

```bash
python3 scripts/organize_jobs.py snapshot --file "<文件>" \
  --date-field "<时间字段>" --days 7
```

没有时间字段时，保存当前完整状态：

```bash
python3 scripts/organize_jobs.py snapshot --file "<文件>" \
  --key-field "<稳定唯一字段>" --state-out "<状态文件.json>" --state-only
```

下次读取时比较并更新同一个状态文件：

```bash
python3 scripts/organize_jobs.py snapshot --file "<新文件>" \
  --key-field "<稳定唯一字段>" \
  --previous-state "<状态文件.json>" --state-out "<状态文件.json>"
```

也可直接比较两份导出文件：

```bash
python3 scripts/organize_jobs.py diff --before "<旧文件>" --after "<新文件>" \
  --key-field "<稳定唯一字段>" --title-field "<标题字段>"
```

快照比较不要求时间字段。它会分别列出新增、逐字段修改和删除记录。优先使用平台记录 ID、职位 ID、编号、投递链接等稳定唯一字段；标题可能变化时不要把标题当主键。没有稳定字段时可暂用标题，但要向用户说明重名和改名可能影响判断。

飞书或腾讯文档在线数据也支持 `--state-out` 和 `--previous-state`，使用方式相同。

## 输出

求职场景默认标题为“岗位更新”，优先展示公司、岗位、地点、批次、截止时间、投递链接和内推码。其他表格根据用户措辞选择字段。

示例：

```text
📌 表格快照变化　新增 1 · 修改 1 · 删除 0

新增记录
• 数据产品经理
    公司：某科技公司
    地点：深圳

修改记录
• 后端开发
    截止时间：2026-07-20 → 2026-07-31
```

## 平台边界

- Codex、Claude Code、OpenClaw：安装完整 Skill 目录后运行本仓库脚本。
- QClaw：其 Skill 安装器只保存 Markdown；必须使用 `scripts/install_agent.py --platform qclaw` 同时安装运行文件。
- XLSX 读取需要 `openpyxl`；缺少时先取得用户同意再安装，或请用户改发 CSV。
- 当前不解析飞书 `.base` 备份文件。
