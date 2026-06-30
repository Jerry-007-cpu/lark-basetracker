[English](./README.md) | **中文**

# lark-basetracker · 飞书多维表格更新追踪

贴一个飞书多维表格链接，选择一个日期或更新时间字段，就能整理出某段时间内更新过的记录。

最初的使用场景是求职博主追踪职位更新：把买来的、共建的、自己维护的岗位表，变成一份“最近更新了什么职位”的清单。底层逻辑是通用的，所以也可以用于项目进度、线索表、内容排期、供应商库等任何带日期字段的表格。

## 当前已经能做什么

- 通过飞书官方 Lark CLI 读取多维表格记录
- 支持解析 `base/` 直链；权限允许时也能解析 `wiki/` 链接
- 先列出表格字段，方便选择标题字段、日期字段和展示字段
- 自动猜测标题字段和日期/更新时间字段
- 按时间窗口筛选记录：
  - 最近 N 天
  - 指定起止日期
- 在对话里输出一份 Markdown 风格摘要
- 可选写入 Markdown 文件
- 可选通过 `wxclawbot` 推送到微信

## 现在还没有什么

当前版本还没有做“快照对比”，也不会逐字段判断“这条记录哪里变了”。它的追踪方式是：使用表格里已有的日期字段来筛选记录，比如 `更新时间`、`发布时间`、`开放时间`、`最后更新时间`、`Last edited time`。

也就是说，只要你的表里有一个可信的“创建时间 / 更新时间 / 发布时间 / 开放时间”字段，现在就能用。

## 典型场景

- 求职博主：整理最近 24 小时更新的职位，展示公司、岗位、城市、投递链接、内推码。
- 岗位表维护者：每周生成一次本周新增或更新岗位清单。
- 项目管理：列出本周更新过的任务，展示负责人、状态、备注。
- 内容运营：整理本周发布或修改过的选题。

## 快速开始

1. 在你的 AI agent 里安装这个 skill。
2. 贴上飞书多维表格链接。
3. 说清楚你要看的时间范围和展示字段。

示例：

```text
整理这张飞书表最近 3 天更新的职位，展示公司、岗位、地点、投递链接。
```

```text
看一下这个多维表格最近 7 天更新的记录，标题用名称字段。
```

Agent 通常会确认：

- 用哪个字段作为更新时间/日期字段
- 用哪个字段作为每条记录的标题
- 摘要里展示哪些字段
- 看最近几天，还是指定起止日期

## 常用命令

先检查表格字段：

```bash
python3 scripts/organize_jobs.py inspect --identity bot --link "<你的飞书表格链接>"
```

整理最近 7 天更新的记录：

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<你的飞书表格链接>" \
  --date-field "更新时间" \
  --days 7 \
  --title-field "岗位名称" \
  --show-fields "公司,地点,投递链接,内推码"
```

指定日期范围：

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<你的飞书表格链接>" \
  --date-field "更新时间" \
  --since 2026-06-01 \
  --until 2026-06-30 \
  --title-field "名称"
```

写入 Markdown 文件：

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<你的飞书表格链接>" \
  --date-field "更新时间" \
  --days 7 \
  --title-field "名称" \
  --out updates.md
```

## 安装

### Claude Code

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git ~/.claude/skills/lark-basetracker
```

### OpenClaw

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git ~/skills/lark-basetracker
```

### Codex

把这个仓库放到 Codex 可读取的技能目录，或者作为普通项目保留；需要使用时让 Codex 读取 `SKILL.md` 后调用脚本即可。

## 系统要求

- 一个能运行 shell 命令的 AI agent
- 本机已安装并授权飞书官方 Lark CLI（`@larksuite/cli`）
- 一个飞书自建应用，已开通 `bitable:app:readonly`
- 目标多维表格已把这个自建应用加为协作者
- 可选：如果要推微信，需要安装并配置 `wxclawbot`

## 首次配置飞书

1. 安装 CLI：

   ```bash
   npm install -g @larksuite/cli
   ```

2. 打开 <https://open.feishu.cn/app>，进入你的应用，开通 `bitable:app:readonly`，然后创建并发布新版本。
3. 在飞书里打开目标多维表格，把你的应用加为可阅读协作者。
4. 运行 `lark-cli auth login`，授权 `base` 业务域。
5. 测试读取：

   ```bash
   python3 scripts/organize_jobs.py inspect --identity bot --link "<你的飞书表格链接>"
   ```

## 注意事项

- 优先使用多维表格直链：`https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>`。
- 读取私有表时优先使用 `--identity bot`。
- 自动识别字段不准时，手动传 `--title-field` 和 `--date-field`。
- 选择的日期字段为空或无法解析时，该记录会被跳过。
- 日期字段可以是飞书日期字段、毫秒时间戳，或 `YYYY-MM-DD` 这类文本日期。

## 隐私

- 数据只在你的电脑和飞书 API 之间流动。
- Lark CLI token 由官方 CLI 保存在本机。
- 脚本只读取你指定的那张多维表格。

## 许可证

[MIT](./LICENSE)
