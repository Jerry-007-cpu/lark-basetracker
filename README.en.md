**English** | [中文](./README.md)

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

Codex, Claude Code, and OpenClaw are supported.

### Codex, Claude Code, and OpenClaw

Copy and run one command:

```bash
npx skills add Jerry-007-cpu/lark-basetracker -g
```

You can also send this request directly to your agent:

```text
Install this Skill for me: https://github.com/Jerry-007-cpu/lark-basetracker
```

Start a new conversation after installation.

## 3. Supported data sources

| Source | Current capability |
| --- | --- |
| Feishu/Lark Base link | Read online with the signed-in user's existing view permission |
| Tencent Docs SmartSheet | Read tables, fields, and records through the official MCP server |
| Tencent Docs regular table | Read through the official MCP server and recover table structure |
| CSV / TSV / XLSX | Read locally without an online account |
| Two files or saved states | Compare additions, field-level edits, and removals |

A time field is optional: use date filtering when one exists, or automatically compare saved snapshots when it does not.

## 4. Automatic guidance examples

### First launch

Invoke `$lark-basetracker`. With no saved source, the agent starts here:

```text
Welcome to lark-basetracker. Choose your first source:
1. Feishu/Lark Base
2. Tencent Docs online table
3. CSV, TSV, or XLSX file

Reply with a number and I will guide only that source.
```

### After connecting a table

The agent detects the real table and proposes ready-to-use defaults:

```text
First query settings:
1. Filter field: Open date
2. Query range: Last 7 days
3. Display fields: Company, role, location, batch, open date, deadline, application link

Reply "Use defaults" or change any setting in one message.
```

### Returning with saved sources

Invoke the Skill again and the agent routes the query instead of repeating setup:

```text
Which source should I check?
1. Feishu/Lark | Campus Roles
2. Tencent Docs | Referral Digest
3. Summarize all
```

### Tracking multiple tables

Feishu/Lark authorization applies to your user identity; it is not repeated for every table. Tracking settings and snapshots are still isolated per table:

- If one Base contains multiple subtables and the link does not identify one, the agent lists the names and asks you to choose instead of silently selecting the first.
- Multiple independent table links get separate names, display fields, filters, and snapshot states.
- Tables are combined into one daily or weekly digest only when you explicitly request a digest group and choose a stable deduplication field such as role ID or application link.

Frequently used tables can be saved under short names such as "Campus Roles," "Experienced Roles," or "Referral Digest." These tracking sources are stored locally, with Feishu/Lark and Tencent Docs configurations kept separate.

If one source is saved, a vague update request uses it directly. With multiple sources, the agent asks only when the requested source cannot be identified.

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
