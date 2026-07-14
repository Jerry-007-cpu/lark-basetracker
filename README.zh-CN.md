[English](./README.md) | **中文**

<div align="center">
  <h1>lark-basetracker</h1>
  <p><strong>把表格链接发给 Agent，直接问“最近更新了什么”。</strong></p>
  <p>支持飞书多维表格、腾讯文档在线表格，以及 CSV / TSV / XLSX。</p>
</div>

## 1. 它能做什么

`lark-basetracker` 是一个对话式 Agent Skill。它会读取表格、识别字段，并输出最近新增、修改或删除的记录。

主要面向求职博主，例如：

- 整理今天新增或重新开放的校招、实习和社招岗位
- 提取公司、岗位、城市、截止时间和投递链接
- 比较两次表格内容，找出职位信息具体改了什么
- 生成适合发社群、公众号或微信的更新清单

同样可以用于项目进度、客户线索、内容排期、供应商资料等其他表格。

## 2. 安装

支持 Codex、Claude Code、OpenClaw 和 QClaw。

### Codex、Claude Code、OpenClaw

复制这一条命令即可：

```bash
npx skills add Jerry-007-cpu/lark-basetracker -g
```

也可以直接把这句话发给 Agent：

```text
请帮我安装这个 Skill：https://github.com/Jerry-007-cpu/lark-basetracker
安装完成后，引导我连接需要追踪的表格。
```

安装完成后，新开一个对话即可使用。

### QClaw

直接把上面的安装请求发给 QClaw。QClaw 会使用仓库内置适配器，同时安装 Skill 和配套运行文件。

<details>
<summary>QClaw 安装失败时的备用方法</summary>

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git
cd lark-basetracker
python3 scripts/install_agent.py --platform qclaw
```

安装后重新启动 QClaw，并在 Skills 页面审核启用。

</details>

### 首次连接表格

飞书和腾讯文档是两种不同的数据来源，**只需要连接你要使用的那个，不是两个都要完成**。

#### 使用飞书多维表格

对 Agent 说：

```text
请帮我完成 lark-basetracker 的首次飞书连接。
```

Agent 会把飞书官方配置和用户授权页面发给你，按页面提示完成即可。默认使用你的用户身份，只有查看权限也可以读取，不需要把机器人添加为表格协作者。

#### 使用腾讯文档

首次连接需要两步：

1. 打开[腾讯文档官方授权页](https://docs.qq.com/open/auth/mcp.html)获取个人 Token。
2. 对 Agent 说“帮我安全配置 lark-basetracker 的腾讯文档连接”，然后在隐藏输入框中填写 Token。

#### 使用 CSV、TSV 或 XLSX

不需要连接任何账号，直接把文件发给 Agent。

不要把 App Secret、Access Token 或腾讯文档 Token 直接粘贴到聊天中。

## 3. 支持的数据来源

| 数据来源 | 当前能力 |
| --- | --- |
| 飞书多维表格链接 | 使用本人账号原有查看权限在线读取 |
| 腾讯文档智能表格 | 通过腾讯文档官方 MCP 读取工作表、字段和记录 |
| 腾讯文档普通在线表格 | 通过官方 MCP 读取内容并恢复表格结构 |
| CSV / TSV / XLSX | 本地读取，不连接在线账号 |
| 两次快照或状态文件 | 比较新增、逐字段修改和删除 |

表格不强制要求时间字段：有时间字段时按日期筛选；没有时自动保存并比较两次快照。

## 4. 怎么使用

安装并完成对应的数据源连接后，把表格链接或文件连同需求一起发给 Agent：

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

Agent 会自动检查字段、选择日期筛选或快照比较，并生成结果。普通用户不需要自己运行整理命令。

示例输出：

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

[MIT License](./LICENSE)
