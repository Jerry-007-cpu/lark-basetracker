**English** | [中文](./README.zh-CN.md)

<div align="center">
  <h1>lark-basetracker</h1>
  <p><strong>Turn a job board into a publishable daily update — or track any Feishu/Lark Bitable.</strong></p>
  <p>A Bitable update-tracking skill built for AI agents.</p>
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
- [Use Cases](#use-cases)
- [Agent Integration](#agent-integration)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [CLI Examples](#cli-examples)
- [Installation](#installation)
- [Feishu Setup](#feishu-setup)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Notes](#notes)
- [Privacy](#privacy)
- [Roadmap](#roadmap)
- [License](#license)

## About

`lark-basetracker` helps an agent or operator summarize records created or updated within a time window from a Feishu/Lark Bitable.

You paste a Bitable link, choose a date-like field such as `更新时间` or `Last edited time`, and get a readable Markdown digest of matching records.

Its primary audience is career creators who maintain job-posting tables and need a quick answer to questions such as “what opened today?” or “what changed this week?”. The filtering and rendering flow is not tied to recruitment fields, so it also works with project trackers, lead lists, content calendars, vendor databases, and other tables with a reliable date field.

The repository includes both an agent-facing [`SKILL.md`](./SKILL.md) and a command-line script. Agents that can load the skill and run local commands can inspect fields, choose a time window, and generate a digest from natural-language requests.

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

## Use Cases

### Career content creation (primary)

- Collect new or reopened campus, internship, and experienced-hire roles each day
- Extract company, role, city, hiring batch, deadline, and application link from a job board
- Produce an update list ready for a community, newsletter, Feishu document, or WeChat

### Any Bitable

- Project management: tasks updated this week and their owners
- Lead tracking: recently created or contacted prospects
- Content operations: topics recently published, edited, or scheduled
- Vendor management: recently updated quotes, statuses, or documents

The same workflow can be reused whenever the table has a trustworthy date field such as `Last modified time`, `Created time`, `Published at`, or `Open date`.

## Agent Integration

This repository separates a generic tracking script from its `SKILL.md` instructions. Compatibility depends less on the agent brand than on whether the runtime can load a skill, run Python, and access an authorized `lark-cli` installation.

| Agent / platform | Current integration | Status |
| --- | --- | --- |
| Codex | Install in the local skills directory; load `SKILL.md` and run the script | Ready |
| Claude Code | Install in the local skills directory; load `SKILL.md` and run the script | Ready |
| [OpenClaw](https://docs.openclaw.ai/skills) | Install as a Git Skill and run the local script | Ready |
| [QClaw](https://github.com/QuantumClaw/QClaw) and other local agents | Import the repository or skill and provide Python, shell, and `lark-cli` | Reusable; installation varies |
| [Feishu Aily](https://www.feishu.cn/content/s855fpkr) | Wrap the tracker as an Aily operation, connector, or HTTP service | No native adapter is included yet |

> `SKILL.md` tells the agent how to operate the tracker. Data access is performed by the local script through the official Lark CLI. Runtimes that cannot execute local commands need a service adapter.

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

1. Install the repository in your agent's skills directory, or run the script directly.
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

### Codex

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git ~/.codex/skills/lark-basetracker
```

### Claude Code

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git ~/.claude/skills/lark-basetracker
```

### OpenClaw

```bash
openclaw skills install git:Jerry-007-cpu/lark-basetracker@main
```

### QClaw / Other Local Agents

Import the repository into the platform's supported skills directory and make sure the agent can execute `python3` and `lark-cli`. Skill locations and installation commands vary by platform.

### Feishu Aily

This repository does not yet include a directly importable Aily adapter. Aily uses Feishu's cloud skill runtime, while the current tracker depends on local Python and `lark-cli`. Integration requires wrapping the script as an operation, connector, or HTTP service that Aily can call.

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

[`config.example.json`](./config.example.json) shows common values an agent or downstream workflow may reuse. The current script does not load this file automatically; direct runs still use command-line arguments.

- `app_token`: Bitable app token
- `table_id`: target table ID
- `date_field`: field used for filtering updates
- `title_field`: field used as each record title
- `show_fields`: fields included in the digest
- `wechat_to`: optional WeChat target
- `max_items`: reserved output cap for downstream workflows
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
- “Updated” means the value of your selected date field; the tracker does not independently detect changed cells.

## Privacy

- By default, data flows only between your machine and Feishu/Lark APIs.
- Lark CLI credentials are stored locally by the official CLI.
- The script only reads the Bitable you explicitly point it to.
- Only when `--wechat` is explicitly used is the generated digest passed to `wxclawbot` for delivery.

## Roadmap

- Feishu Aily / internal Feishu agent connector or service adapter
- Publish to a skill registry such as ClawHub for one-command QClaw / OpenClaw installation
- Structured JSON output for more agents and automation workflows
- Scheduled runs and a reusable “daily job updates” template
- Snapshot comparison and field-level change summaries
- More publishing channels and career-content templates

## License

Distributed under the MIT License. See [LICENSE](./LICENSE) for details.
