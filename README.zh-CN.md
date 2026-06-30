[English](./README.md) | **中文**

<div align="center">
  <h1>lark-basetracker</h1>
  <p>把飞书多维表格变成一份清晰的“最近更新了什么”摘要。</p>
  <p>
    <a href="./LICENSE">MIT License</a> ·
    <a href="./SKILL.md">Skill 定义</a> ·
    <a href="./config.example.json">示例配置</a>
  </p>
</div>

## 目录

- [项目简介](#项目简介)
- [为什么做这个项目](#为什么做这个项目)
- [当前能力](#当前能力)
- [工作流程](#工作流程)
- [快速开始](#快速开始)
- [命令示例](#命令示例)
- [安装方式](#安装方式)
- [飞书配置](#飞书配置)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [注意事项](#注意事项)
- [隐私](#隐私)
- [许可证](#许可证)

## 项目简介

`lark-basetracker` 用来整理飞书多维表格在某个时间窗口内更新过的记录。

你只需要贴一个多维表格链接，指定一个日期类字段，比如 `更新时间`、`发布时间`、`Last edited time`，脚本就会输出一份适合发到聊天、文档或微信里的 Markdown 摘要。

这个项目最初面向求职博主整理岗位更新，但底层流程是通用的，也适用于项目管理、客户线索、内容排期、供应商库等场景。

## 为什么做这个项目

很多多维表格其实已经包含了“这周更新了什么”的答案，只是这些答案埋在一堆原始记录里，不适合直接阅读或转发。

这个项目不走重量级同步系统路线，而是直接复用表里已有的日期字段做筛选。这样接入成本低，只要你的表里已经维护了可靠的时间字段，就能立刻跑起来。

## 当前能力

- 通过飞书官方 `lark-cli` 读取多维表格记录
- 支持解析 `base/` 直链；权限允许时也支持 `wiki/` 链接
- 先检查字段，再决定标题字段、日期字段和输出字段
- 自动猜测标题字段和日期/更新时间字段
- 支持按最近 N 天或指定起止日期筛选
- 输出适合聊天展示的 Markdown 风格摘要
- 可选写入本地 Markdown 文件
- 可选通过 `wxclawbot` 推送到微信

## 工作流程

1. 解析用户给的飞书链接，拿到 `app_token` 和 `table_id`。
2. 读取字段列表，自动识别可能的标题字段和日期字段。
3. 通过 `lark-cli` 调用飞书 OpenAPI 拉取记录。
4. 归一化日期值，并按时间范围过滤。
5. 生成一份易读、易转发的摘要。

示例输出：

```text
📌 表格更新整理（2026-06-24 ~ 2026-06-30） 共 2 条

• 产品经理  日期：2026-06-29
    公司：某互联网公司
    地点：深圳
    投递链接：https://example.com

• 后端开发  日期：2026-06-28
    公司：某科技公司
    地点：北京
```

## 快速开始

1. 把这个仓库放到你的 agent 能读取 `SKILL.md` 的位置，或者直接运行脚本。
2. 确保本机已经安装并授权 `lark-cli`。
3. 把你的飞书应用添加为目标多维表格协作者。
4. 先检查字段：

```bash
python3 scripts/organize_jobs.py inspect --identity bot --link "<你的飞书表格链接>"
```

5. 再生成更新摘要：

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<你的飞书表格链接>" \
  --date-field "更新时间" \
  --days 7 \
  --title-field "岗位名称" \
  --show-fields "公司,地点,投递链接,内推码"
```

如果你是通过 AI agent 来用，很多时候直接说自然语言就够了：

```text
整理这张飞书表最近 3 天更新的职位，展示公司、岗位、地点、投递链接。
```

```text
看一下这个多维表格最近 7 天更新的记录，标题用名称字段。
```

## 命令示例

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

推送到微信：

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<你的飞书表格链接>" \
  --date-field "更新时间" \
  --days 1 \
  --title-field "岗位名称" \
  --show-fields "公司,地点,投递链接,内推码" \
  --wechat
```

## 安装方式

### Claude Code

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git ~/.claude/skills/lark-basetracker
```

### OpenClaw

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git ~/skills/lark-basetracker
```

### Codex

把仓库放在 Codex 可读取的位置，并在使用前让 Codex 读取 [`SKILL.md`](./SKILL.md)。

### 直接运行脚本

需要：

- Python 3
- `@larksuite/cli`
- 一个已开通 `bitable:app:readonly` 的飞书自建应用
- 目标多维表格已将该应用添加为协作者
- 可选：如果要推微信，需要安装 `wxclawbot`

## 飞书配置

1. 安装官方 CLI：

```bash
npm install -g @larksuite/cli
```

2. 打开 [飞书开放平台](https://open.feishu.cn/app)，进入你的应用，开通 `bitable:app:readonly`，然后发布新版本。
3. 在飞书里打开目标多维表格，把该应用加为可读协作者。
4. 给 CLI 授权：

```bash
lark-cli auth login
```

5. 验证能否读取：

```bash
python3 scripts/organize_jobs.py inspect --identity bot --link "<你的飞书表格链接>"
```

## 配置说明

[`config.example.json`](./config.example.json) 给出了最常见的配置项：

- `app_token`：多维表格 app token
- `table_id`：目标数据表 ID
- `date_field`：用于筛选更新记录的字段
- `title_field`：每条记录的标题字段
- `show_fields`：摘要里展示的字段
- `wechat_to`：可选的微信接收目标
- `max_items`：给下游工作流使用的输出上限
- `lark_cli`：本机 `lark-cli` 路径
- `wxclawbot`：微信推送命令

## 项目结构

```text
.
├── README.md
├── README.zh-CN.md
├── SKILL.md
├── config.example.json
└── scripts/
    └── organize_jobs.py
```

## 注意事项

- 优先使用 `https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>` 这种直链。
- 读取私有多维表格时，优先使用 `--identity bot`。
- 自动识别字段不准时，手动传 `--title-field` 和 `--date-field`。
- 选定日期字段后，字段为空或无法解析的记录会被跳过。
- 支持的文本日期格式包括 `YYYY-MM-DD`、`YYYY-MM-DD HH:MM`、`YYYY-MM-DD HH:MM:SS`、`YYYY/MM/DD`。
- 当前版本还没有实现快照对比，也不会输出逐字段 diff。

## 隐私

- 数据只在你的本机和飞书 API 之间流动。
- `lark-cli` 的凭证由官方 CLI 保存在本地。
- 脚本只会读取你明确指定的那张多维表格。

## 许可证

本项目基于 MIT License 发布。详情见 [LICENSE](./LICENSE)。
