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

### Start using it

After installation, invoke `$lark-basetracker` or click the Skill's default prompt. If no source is saved, the agent shows one short choice:

```text
1. Feishu/Lark Base
2. Tencent Docs online table
3. CSV, TSV, or XLSX file
```

Choose one source and the agent guides only that connection. If sources already exist, it shows the saved-source picker instead. After the first successful read, it recommends the date/filter field, a seven-day range, and display fields; accept them together or change them in one reply.

<details>
<summary>Connection and security notes</summary>

- Feishu/Lark uses the signed-in user with minimum read access; a bot does not need to be added as a collaborator. The agent installs/configures the official `lark-cli` only when needed.
- Tencent Docs uses a personal token from the [official authorization page](https://docs.qq.com/open/auth/mcp.html). Enter it only in the hidden Terminal prompt provided by the agent, never directly in chat or at a `%`/`$` shell prompt.
- CSV, TSV, and XLSX files require no account connection.
- If a Feishu setup or authorization page keeps spinning, temporarily disabling a VPN/proxy may help; it is not required in normal cases.

</details>

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

### Tracking multiple tables

Feishu/Lark authorization applies to your user identity; it is not repeated for every table. Tracking settings and snapshots are still isolated per table:

- If one Base contains multiple subtables and the link does not identify one, the agent lists the names and asks you to choose instead of silently selecting the first.
- Multiple independent table links get separate names, display fields, filters, and snapshot states.
- Tables are combined into one daily or weekly digest only when you explicitly request a digest group and choose a stable deduplication field such as role ID or application link.

Frequently used tables can be saved under short names such as "Campus Roles," "Experienced Roles," or "Referral Digest." These tracking sources are stored locally, with Feishu/Lark and Tencent Docs configurations kept separate.

When you invoke the Skill again:

- Say "Check Campus Roles for updates in the last 7 days" to route directly to that source.
- If only one source is saved, a vague request such as "Check for updates" uses it directly.
- If multiple sources are saved and the request is ambiguous, the agent shows a short picker:

```text
You have 3 saved tracking sources. Which one should I check?
1. Feishu/Lark | Campus Roles
2. Feishu/Lark | Experienced Roles
3. Tencent Docs | Referral Digest
4. Summarize all
```

After saving a second source, the agent explains once that you can ask for a source by name or request a summary of all sources. The Skill cannot open a prompt by itself without a scheduler; "invoke" means clicking the Skill, sending a request, or starting a scheduled run.

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

Every record in one result uses the same field order and link format. Results over 20 records automatically switch to a compact one-line layout without dropping application links; missing requested fields are shown as `—`.

[MIT License](./LICENSE)
