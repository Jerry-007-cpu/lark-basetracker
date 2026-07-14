[English](./README.md) | **中文**

<div align="center">
  <h1>lark-basetracker</h1>
  <p><strong>把表格链接发给 Agent，直接问“最近更新了什么”。</strong></p>
  <p>支持飞书多维表格、腾讯文档在线表格，以及 CSV / TSV / XLSX。</p>
</div>

## 它能做什么

`lark-basetracker` 是一个对话式 Agent Skill。它会读取表格、识别字段，并输出最近新增、修改或删除的记录。

主要面向求职博主，例如：

- 整理今天新增或重新开放的校招、实习和社招岗位
- 提取公司、岗位、城市、截止时间和投递链接
- 比较两次表格内容，找出职位信息具体改了什么
- 生成适合发社群、公众号或微信的更新清单

同样可以用于项目进度、客户线索、内容排期、供应商资料等其他表格。

## 怎么使用

安装并完成一次账号连接后，只需要在 Agent 对话里发送链接和需求：

```text
这是岗位表：<表格链接>
帮我整理最近 7 天新增或更新的岗位，展示公司、岗位、地点和投递链接。
```

```text
和上次相比，这张表新增、修改和删除了什么？
<表格链接>
```

```text
整理这张项目表本周更新的任务，展示负责人和状态。
<表格链接>
```

Agent 会在后台自动检查字段、选择时间或快照模式并生成结果。普通用户不需要自己运行命令。

## 支持的数据来源

| 数据来源 | 当前能力 |
| --- | --- |
| 飞书多维表格链接 | 使用本人账号原有权限在线读取 |
| 腾讯文档智能表格 | 通过腾讯文档官方 MCP 在线读取工作表、字段和记录 |
| 腾讯文档普通在线表格 | 通过官方 MCP 读取内容并恢复表格结构 |
| CSV / TSV / XLSX | 本地读取，不连接在线账号 |
| 两次快照或状态文件 | 比较新增、逐字段修改和删除 |

只有查看权限也可以正常使用，不需要编辑表格，也不需要把机器人添加为协作者。但 Skill 不会绕过表格所有者设置的查看、下载或会员限制。

## 需要时间字段吗

不一定。

### 有时间字段

可以直接查询“最近 7 天”“本周”“今天”的记录。推荐使用：

- `创建时间`：判断新增记录
- `最后更新时间`：判断被修改的记录
- `发布时间`、`开放时间`：按业务时间筛选

飞书的“创建时间”和“最后更新时间”可以由系统自动维护，不需要手工填写。

### 没有时间字段

Skill 会保存第一次读取的完整状态。下次再读取时，将两次状态进行比较，输出：

- 新增了哪些记录
- 删除了哪些记录
- 哪些字段从什么值改成了什么值

这种方式需要一个稳定的唯一字段，例如职位 ID、编号、投递链接或平台记录 ID。标题也能作为备用主键，但重名或改名时可能影响判断。

## 腾讯文档（微信里常用的腾讯文档）

仓库已经内置[腾讯文档官方 MCP](https://developer.cloud.tencent.com/mcp/server/11803)客户端，不再要求宿主 Agent 自己实现 MCP 调用。

首次使用：

1. 打开[腾讯文档官方授权页](https://docs.qq.com/open/auth/mcp.html)获取个人 Token。
2. 对 Agent 说：“帮我安全配置 lark-basetracker 的腾讯文档连接。”
3. Agent 会启动隐藏输入，不会让 Token 出现在聊天或终端历史中。

配置后，直接发送 `docs.qq.com` 链接即可。程序会先读取实时工具定义，再调用智能表格或普通表格对应的只读工具。

常见错误：

- `400006`：Token 无效或已过期，需要重新授权。
- `400007`：当前腾讯文档账户缺少对应 VIP 能力。

如果在线读取不适用于该文档类型，可以把腾讯文档导出为 XLSX、CSV 或 TSV 后发送给 Agent。

## 第一次连接飞书

在 Agent 对话里说：

```text
请帮我完成 lark-basetracker 的首次飞书连接。
```

Agent 会检查飞书官方 `lark-cli`，并依次发给你应用配置和用户授权页面。打开官方链接完成操作即可。

默认使用用户身份，所以读取范围和你本人当前账号的权限一致。只有查看权限属于正常主流程；不需要逐张表格添加应用协作者。

不要把 App Secret、Access Token 等密钥粘贴到对话中。

## 支持的 Agent

| Agent | 状态 | 安装位置 |
| --- | --- | --- |
| [Codex](https://learn.chatgpt.com/docs/build-skills.md) | 已适配 | 用户级 `.agents/skills` |
| [Claude Code](https://code.claude.com/docs/en/skills) | 已适配 | 用户级 `.claude/skills` |
| [OpenClaw](https://docs.openclaw.ai/skills) | 已适配 | 用户级 `.openclaw/skills` |
| [QClaw](https://github.com/QuantumClaw/QClaw) | 已适配 | QClaw 共享 Skill + 独立运行目录 |

推荐直接把仓库链接发给 Agent：

```text
请从这个仓库安装 lark-basetracker，并按我的 Agent 平台选择正确的安装方式：
https://github.com/Jerry-007-cpu/lark-basetracker
```

<details>
<summary>查看手动安装方法</summary>

先克隆仓库，然后运行对应安装器：

```bash
python3 scripts/install_agent.py --platform codex
python3 scripts/install_agent.py --platform claude-code
python3 scripts/install_agent.py --platform openclaw
python3 scripts/install_agent.py --platform qclaw
```

QClaw 的原生 Skill 安装器只保存单个 Markdown 文件，因此本仓库的安装器还会复制所需 Python 运行文件。安装后重新启动 QClaw，并在 Skills 页面审核启用。

如需只安装到当前项目，可为 Codex、Claude Code 或 OpenClaw 添加 `--scope project`。

</details>

## 输出示例

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

## 底层结构

项目已经把平台读取与表格分析分开：

- 飞书 Provider：解析 Base / Wiki 链接并读取字段、记录
- 腾讯文档 Provider：执行 MCP 初始化、工具发现和在线读取
- 文件 Provider：读取 CSV、TSV、XLSX
- 通用核心：字段识别、日期筛选、状态保存、逐字段差异比较、文本输出

因此不同 Agent 共享相同的追踪结果，只在安装目录和运行环境上存在差异。

## 当前限制

- 腾讯文档不同文档类型返回结构不同；智能表格支持最完整，普通表格依赖官方 `get_content` 返回的结构化内容。
- 快照比较最好提供稳定唯一字段；没有唯一字段时对重名、排序变化的判断能力有限。
- XLSX 需要 Python 包 `openpyxl`，CSV 和 TSV 不需要额外依赖。
- 暂不读取飞书 `.base` 备份文件。
- 飞书 Aily 和微信渠道发布不在当前适配范围。

## 隐私

- 默认只执行读取操作。
- 飞书数据在本机 Agent、`lark-cli` 和飞书 API 之间流动。
- 腾讯文档 Token 保存在本机环境变量或权限为 `0600` 的配置文件中。
- 快照状态默认保存在用户指定的本地 JSON 文件中。
- 不要提交 Token、App Secret 或包含真实业务数据的状态文件。

## 开发验证

```bash
python3 -B -m unittest discover -s tests -v
python3 -B -m py_compile scripts/organize_jobs.py scripts/basetracker/*.py
```

## License

[MIT](./LICENSE)
