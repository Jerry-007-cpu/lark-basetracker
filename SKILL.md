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
7. 首次成功读取后进入“读取后引导”，不要只给几条示例指令就结束。

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

### 首次连接与授权

1. 运行 `lark-cli --version` 检查飞书官方 CLI。
2. 缺少 CLI 时，先说明“授权链接需要由 CLI 生成，现在还不能直接授权”，取得用户同意后运行官方推荐安装命令：

   ```bash
   npx @larksuite/cli@latest install
   ```

   该命令需要 Node.js 和 `npx`。如果这两者也缺失，先说明再取得安装同意。
3. 未配置应用时，运行 `lark-cli config init --new`。把返回的官方配置链接原样发给用户。
4. 发送任何飞书配置或授权链接时，同时提醒：“如果页面打不开、一直转圈或验证失败，可以暂时关掉 VPN/代理后重试，完成后再开启。”不要把关闭 VPN 说成必须条件。
5. 应用配置完成后，运行 `lark-cli auth login --domain base --no-wait --json` 发起最小范围的 Base 用户授权。立即把 `verification_url` 原样发给用户，保留返回的 `device_code`，不在用户看到链接前阻塞等待。
6. 用户确认已授权后，运行 `lark-cli auth login --device-code "<device_code>" --json` 完成登录，再用 `lark-cli auth status` 验证。链接过期时重新发起，不复用旧链接。
7. 已安装 CLI 时跳过安装；已配置且授权有效时跳过配置和登录，直接检查字段。

### 读取后引导

首次读取成功后，先用一小段确认表格名、数据表名、身份、只读状态、记录数和识别到的关键字段。然后分轮引导，每轮最多问 3 个问题，并给出基于已识别字段的推荐默认值。

第一轮只确认必需项：

1. 追踪什么：新增、修改、删除、即将截止，或其中几类。
2. 什么时候整理：仅查一次、每 N 天、每个工作日，或每周某天某时。
3. 通知展示哪些字段：求职表默认推荐公司、岗位、城市、批次、开放日期、截止日期和投递链接。

根据回答再按需确认：

- 筛选范围：校招/社招/实习、城市、公司、岗位关键词或状态。
- 无更新时的行为：保持静默，或发送“本期无更新”。
- 结果去向：只在当前对话查看，或推送到用户明确指定的位置。
- 基准时点：需要比较新增、修改和删除时，建议把本次读取作为首个快照基准。

用户选择持续追踪时，先确认当前 Agent 平台是否支持定时任务或自动化。只在用户确认频率、时间、时区和结果去向后创建；平台不支持时，给出一条可复用的对话请求，不要声称已建立自动追踪。

### 多表管理

- 把“飞书用户授权”与“追踪某张表”分开说明。授权是身份级的，不是每张表各绑定一次；只能读取用户本来有权查看的表。
- 同一个 Base 内有多张数据表而链接未指定 `table=` 时，列出数据表名称并请用户选择。不要默认使用第一张。
- 同时追踪多个独立链接时，为每个“数据源 + 数据表 ID”使用独立的追踪名称、字段规则、筛选条件和快照状态。不要跨表复用上一张表的快照文件。
- 用户未说明查哪张表时，用追踪名称和表名给出简短选择；如果只有一个明确匹配，直接执行。
- 只在用户明确要求“合并汇总”时创建汇总组。先分表读取和比较，再合并输出；记录去重规则不明确时，先询问使用职位 ID、投递链接还是其他稳定字段。

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
