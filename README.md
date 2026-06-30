**English** | [中文](./README.zh-CN.md)

# lark-basetracker

Track recent updates in any Feishu/Lark Bitable. Paste a table link, choose a date or update-time field, and get a clean digest of records changed within a time window.

The first use case is job posting updates for career creators: turn a shared recruiting table into a daily "what changed" digest. The core flow is generic, so it can also work for leads, content calendars, project lists, vendor databases, or any table that has a usable date field.

## What It Does Today

- Reads records from a Feishu/Lark Bitable through the official Lark CLI
- Resolves `base/` links and can also resolve `wiki/` links when permissions allow it
- Lists table fields so you can pick the right title, date, and display fields
- Auto-suggests a title field and a date/update field from common field names
- Filters records by a time window:
  - last N days
  - explicit `YYYY-MM-DD` start/end dates
- Renders a readable Markdown digest in chat
- Optionally writes the digest to a Markdown file
- Optionally pushes the digest to WeChat through `wxclawbot`

## What It Does Not Do Yet

This version does not compare snapshots or detect field-level diffs between two runs. It tracks updates by filtering records with an existing date-like field, such as `更新时间`, `发布时间`, `开放时间`, `Last edited time`, or another field you choose.

That means it is already useful when your Bitable has a reliable "created at", "updated at", "published at", or "opened at" field.

## Example Use Cases

- Career blogger: "Show me jobs updated in the last 24 hours, include company, role, city, apply link, referral code."
- Recruiting table owner: "Generate this week's new postings from my Feishu table."
- Project tracker: "List tasks updated this week, include owner, status, and notes."
- Content operations: "Show content items published or edited since Monday."

## Quick Start

1. Install this skill in your AI agent.
2. Paste a Feishu/Lark Bitable link.
3. Ask for the update window you care about.

Examples:

```text
Summarize records updated in the last 7 days.
```

```text
整理这张飞书表最近 3 天更新的职位，展示公司、岗位、地点、投递链接。
```

The agent will usually ask:

- Which field should be used as the update/date field
- Which field should be used as the record title
- Which fields should appear in the digest
- Which time window to use

## Commands

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

Write the digest to a Markdown file:

```bash
python3 scripts/organize_jobs.py list --identity bot --link "<your-base-link>" \
  --date-field "更新时间" \
  --days 7 \
  --title-field "名称" \
  --out updates.md
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

Put this repository in your Codex skills directory or keep it as a local project and let Codex read `SKILL.md` before running the script.

## Requirements

- An AI agent that can run shell commands
- The official Lark CLI (`@larksuite/cli`) installed and authorized
- A Feishu/Lark custom app with `bitable:app:readonly` enabled
- The custom app added as a collaborator on the target Bitable
- Optional: `wxclawbot` if you want WeChat pushes

## First-Time Feishu Setup

1. Install the CLI:

   ```bash
   npm install -g @larksuite/cli
   ```

2. Open <https://open.feishu.cn/app>, choose your app, enable `bitable:app:readonly`, then create and publish a new version.
3. Open the target Bitable in Feishu and add your app as a collaborator with read access.
4. Run `lark-cli auth login` and authorize the `base` domain.
5. Test access:

   ```bash
   python3 scripts/organize_jobs.py inspect --identity bot --link "<your-base-link>"
   ```

## Notes

- Prefer a direct Bitable link like `https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>`.
- Use `--identity bot` for private Bitables read by a self-built app.
- If the auto-suggested fields are wrong, pass `--title-field` and `--date-field` explicitly.
- Records without a parseable value in the chosen date field are skipped.
- Date values can be Feishu date fields, timestamps, or simple text dates like `YYYY-MM-DD`.

## Privacy

- Data flows only between your machine and Feishu/Lark APIs.
- Lark CLI tokens are stored locally by the official CLI.
- The script only reads the Bitable you point it at.

## License

[MIT](./LICENSE)
