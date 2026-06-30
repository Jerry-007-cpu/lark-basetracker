**English** | [中文](./README.zh-CN.md)

<div align="center">
  <h1>lark-basetracker</h1>
  <p>Turn any Feishu/Lark Bitable into a clean "what changed recently" digest.</p>
  <p>
    <a href="./LICENSE">MIT License</a> ·
    <a href="./SKILL.md">Skill Definition</a> ·
    <a href="./config.example.json">Example Config</a>
  </p>
</div>

## Table of Contents

- [About](#about)
- [Why This Exists](#why-this-exists)
- [What It Can Do](#what-it-can-do)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [CLI Examples](#cli-examples)
- [Installation](#installation)
- [Feishu Setup](#feishu-setup)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Notes](#notes)
- [Privacy](#privacy)
- [License](#license)

## About

`lark-basetracker` helps an agent or operator summarize records updated within a time window from a Feishu/Lark Bitable.

You paste a Bitable link, choose a date-like field such as `更新时间` or `Last edited time`, and get a readable Markdown digest of matching records.

The first target scenario is job-posting tracking for career creators, but the workflow is generic enough for project trackers, lead lists, content calendars, vendor databases, and other operational tables.

## Why This Exists

Many Bitables already contain the answer to "what changed this week", but the answer is buried inside raw rows. This project turns that table into a repeatable update feed without building a full sync system.

Instead of snapshot diffing, the current version uses an existing date or update field in the table. That keeps setup lightweight and makes it useful immediately for teams who already maintain reliable timestamps.

## What It Can Do

- Read records from a Feishu/Lark Bitable through the official Lark CLI
- Resolve direct `base/` links and, when permissions allow, `wiki/` links
- Inspect table fields before listing records
- Auto-suggest a title field and a date/update field from common names
- Filter by either `--days N` or an explicit `--since` / `--until` range
- Render a clean Markdown digest for chat or downstream publishing
- Optionally write the digest to a local Markdown file
- Optionally send the digest to WeChat through `wxclawbot`

## How It Works

1. Parse the Bitable link and resolve `app_token` plus `table_id`.
2. Inspect fields and identify likely title/date candidates.
3. Fetch records through Lark OpenAPI via `lark-cli`.
4. Normalize date values and filter records by the requested window.
5. Render a digest that is easy to paste into chat, docs, or WeChat.

Example output:

```text
📌 Bitable updates (2026-06-24 ~ 2026-06-30) total 2

• Product Manager  Date: 2026-06-29
    Company: Example Tech
    City: Shenzhen
    Apply Link: https://example.com

• Backend Engineer  Date: 2026-06-28
    Company: Example Cloud
    City: Beijing
```

## Quick Start

1. Install the repository where your agent can read `SKILL.md`, or run the script directly.
2. Make sure `lark-cli` is installed and authorized.
3. Add your Feishu app as a collaborator on the target Bitable.
4. Inspect fields:

```bash
python3 scripts/organize_jobs.py inspect --identity bot --link "<your-base-link>"
```

5. Generate an update digest:

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<your-base-link>" \
  --date-field "更新时间" \
  --days 7 \
  --title-field "岗位名称" \
  --show-fields "公司,地点,投递链接,内推码"
```

If you are using this through an AI agent, a natural-language prompt is usually enough:

```text
Summarize records updated in the last 7 days.
```

```text
整理这张飞书表最近 3 天更新的职位，展示公司、岗位、地点、投递链接。
```

## CLI Examples

Inspect a table and list fields:

```bash
python3 scripts/organize_jobs.py inspect --identity bot --link "<your-base-link>"
```

List records updated in the last 7 days:

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<your-base-link>" \
  --date-field "更新时间" \
  --days 7 \
  --title-field "岗位名称" \
  --show-fields "公司,地点,投递链接,内推码"
```

Use an explicit date range:

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<your-base-link>" \
  --date-field "更新时间" \
  --since 2026-06-01 \
  --until 2026-06-30 \
  --title-field "名称"
```

Write the digest to a file:

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<your-base-link>" \
  --date-field "更新时间" \
  --days 7 \
  --title-field "名称" \
  --out updates.md
```

Push the digest to WeChat:

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<your-base-link>" \
  --date-field "更新时间" \
  --days 1 \
  --title-field "岗位名称" \
  --show-fields "公司,地点,投递链接,内推码" \
  --wechat
```

## Installation

### Claude Code

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git ~/.claude/skills/lark-basetracker
```

### OpenClaw

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git ~/skills/lark-basetracker
```

### Codex

Keep this repository in a readable local workspace and let Codex load [`SKILL.md`](./SKILL.md) before running the script.

### Direct Script Usage

Requirements:

- Python 3
- `@larksuite/cli`
- A Feishu/Lark app with `bitable:app:readonly`
- The app added as a collaborator on the target Bitable
- Optional: `wxclawbot` for WeChat delivery

## Feishu Setup

1. Install the official CLI:

```bash
npm install -g @larksuite/cli
```

2. Open [Feishu Open Platform](https://open.feishu.cn/app), select your app, enable `bitable:app:readonly`, then publish a new version.
3. Open the target Bitable and add the app as a collaborator with read access.
4. Authorize the CLI:

```bash
lark-cli auth login
```

5. Verify access:

```bash
python3 scripts/organize_jobs.py inspect --identity bot --link "<your-base-link>"
```

## Configuration

[`config.example.json`](./config.example.json) shows the most common values you may want to reuse:

- `app_token`: Bitable app token
- `table_id`: target table ID
- `date_field`: field used for filtering updates
- `title_field`: field used as each record title
- `show_fields`: fields included in the digest
- `wechat_to`: optional WeChat target
- `max_items`: output cap for downstream workflows
- `lark_cli`: path to the installed Lark CLI
- `wxclawbot`: command used for WeChat delivery

## Project Structure

```text
.
├── README.md
├── README.zh-CN.md
├── SKILL.md
├── config.example.json
└── scripts/
    └── organize_jobs.py
```

## Notes

- Prefer a direct Bitable URL like `https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>`.
- Use `--identity bot` for private Bitables read by a self-built Feishu app.
- If auto-detected fields are wrong, pass `--title-field` and `--date-field` explicitly.
- Records without a parseable value in the selected date field are skipped.
- Supported text date formats include `YYYY-MM-DD`, `YYYY-MM-DD HH:MM`, `YYYY-MM-DD HH:MM:SS`, and `YYYY/MM/DD`.
- This version does not compare two snapshots or compute field-level diffs.

## Privacy

- Data flows only between your machine and Feishu/Lark APIs.
- Lark CLI credentials are stored locally by the official CLI.
- The script only reads the Bitable you explicitly point it to.

## License

Distributed under the MIT License. See [LICENSE](./LICENSE) for details.
