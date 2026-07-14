**English** | [中文](./README.zh-CN.md)

<div align="center">
  <h1>lark-basetracker</h1>
  <p><strong>Send a table link to your agent and ask what changed.</strong></p>
  <p>Supports Feishu/Lark Base, Tencent Docs online tables, and CSV / TSV / XLSX files.</p>
</div>

## 1. What it does

`lark-basetracker` is a conversational Agent Skill that reads a table, detects its fields, and reports recently added, changed, or removed records.

It is designed first for job-update creators:

- Collect newly posted or reopened graduate, internship, and experienced roles
- Extract company, role, location, deadline, and application links
- Compare two table states and show the exact field changes
- Produce a clean digest for communities, newsletters, or chat groups

The same workflow also works for projects, leads, content calendars, vendors, and other tables.

## 2. Install

Codex, Claude Code, OpenClaw, and QClaw are supported.

### Codex, Claude Code, and OpenClaw

Copy and run one command:

```bash
npx skills add Jerry-007-cpu/lark-basetracker -g
```

You can also send this request directly to your agent:

```text
Install this Skill for me: https://github.com/Jerry-007-cpu/lark-basetracker
After installation, guide me through connecting the table I want to track.
```

Start a new conversation after installation.

### QClaw

Send the same installation request to QClaw. QClaw will use the repository adapter to install both the Skill and its bundled runtime files.

<details>
<summary>Fallback when QClaw installation fails</summary>

```bash
git clone https://github.com/Jerry-007-cpu/lark-basetracker.git
cd lark-basetracker
python3 scripts/install_agent.py --platform qclaw
```

Restart QClaw and review/enable the Skill afterward.

</details>

### Connect a table for the first time

Feishu and Tencent Docs are separate data sources. **Connect only the one you want to use; you do not need to set up both.**

#### Feishu/Lark Base

Ask your agent:

```text
Set up the first Feishu connection for lark-basetracker.
```

The agent sends the official application setup and user authorization pages. Follow those pages to finish. The Skill uses your user identity by default, so view-only permission works and the bot does not need to be added as a table collaborator.

#### Tencent Docs

The first connection has two steps:

1. Get a personal token from the [official Tencent Docs authorization page](https://docs.qq.com/open/auth/mcp.html).
2. Ask the agent to securely configure Tencent Docs for `lark-basetracker`, then enter the token in the hidden prompt.

#### CSV, TSV, or XLSX

No account connection is needed. Send the file directly to the agent.

Never paste App Secrets, access tokens, or Tencent Docs tokens directly into chat.

## 3. Supported data sources

| Source | Current capability |
| --- | --- |
| Feishu/Lark Base link | Read online with the signed-in user's existing view permission |
| Tencent Docs SmartSheet | Read tables, fields, and records through the official MCP server |
| Tencent Docs regular table | Read through the official MCP server and recover table structure |
| CSV / TSV / XLSX | Read locally without an online account |
| Two files or saved states | Compare additions, field-level edits, and removals |

A time field is optional: use date filtering when one exists, or automatically compare saved snapshots when it does not.

## 4. Use it through conversation

After installation and the relevant data-source connection, send a table link or file with your request:

```text
Here is my jobs table: <table link>
Summarize roles added or updated in the last 7 days. Include company, role, location, and application link.
```

```text
What was added, edited, or removed since the last snapshot?
<table link>
```

```text
Summarize tasks updated in this project table this week. Include owner and status.
<table link>
```

The agent detects fields, chooses date filtering or snapshot comparison, and formats the result. Normal users do not need to run processing commands.

Example output:

```text
📌 Table snapshot changes  Added 1 · Changed 1 · Removed 0

Added
• Data Product Manager
    Company: Example Tech
    Location: Shenzhen

Changed
• Backend Engineer
    Deadline: 2026-07-20 → 2026-07-31
```

[MIT License](./LICENSE)
