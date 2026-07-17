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

The agent first checks for the official `lark-cli`. If it is missing, the agent asks for your permission before running the official recommended installer:

```bash
npx @larksuite/cli@latest install
```

This requires Node.js and `npx`. **Without `lark-cli`, the user authorization link cannot be generated yet.** After installation, the agent sends the Feishu/Lark application setup page first, then asks the CLI to generate the user authorization link. If either page fails to load, keeps spinning, or fails verification, temporarily disable your VPN/proxy and retry; you can turn it back on afterward.

An existing CLI installation is reused. If the application is already configured and authorization remains valid, the agent reads the table directly. The Skill uses your user identity by default and initially requests only Base record retrieval (`base:record:retrieve`), so view-only permission works and the bot does not need to be added as a table collaborator. A Wiki link may additionally require the read-only `wiki:node:read` scope to resolve the underlying Base.

Binding a Feishu/Lark table follows the same flow as Tencent Docs: verify with the signed-in user, detect the concrete subtable, fields, and record count, save the normalized Base target, then show the three default query settings. The same consistent output-format guarantee applies to both providers.

#### Tencent Docs

Follow these steps for the first connection:

1. Get a new personal token from the [official Tencent Docs authorization page](https://docs.qq.com/open/auth/mcp.html).
2. Ask the agent to securely configure Tencent Docs for `lark-basetracker`. The agent locates the configuration script and gives you one command beginning with `python3` that contains its full path.
3. Run that complete command in Terminal first. A line ending in `%` or `$` is the shell prompt; **do not paste the token directly there**.
4. Paste the token and press Enter only after Terminal displays this prompt:

   ```text
   粘贴腾讯文档 MCP Token（输入不会显示）：
   ```

   No characters appear while you type or paste; this is expected. After `已安全保存` appears, return to the conversation and tell the agent that configuration is complete so it can verify the connection and read the table.

If you paste a token directly after `%` or `$`, the shell treats it as a command and may store it in terminal history. Revoke that token immediately on the official authorization page, generate a new one, and do not reuse the exposed token.

After configuration, send the Tencent Docs link and ask the agent to bind it. The agent detects the specific worksheet from the link, verifies its name, fields, and record count, and only then saves it under the real worksheet name. The first inspection does not download the full table; later reads reuse the saved worksheet and tool metadata.

Tencent Docs date columns may be returned as text. The tracker recognizes full dates and common month-day forms such as `2026-07-17`, `2026.7.17`, `7.17`, and `7月17日`; a missing year uses the current year. Notes or invalid dates mixed into the date column are skipped record by record.

#### CSV, TSV, or XLSX

No account connection is needed. Send the file directly to the agent.

Never paste App Secrets, access tokens, or Tencent Docs tokens directly into chat, and do not send screenshots that show a complete token.

### What the agent asks after the first read

After confirming the table, subtable, and detected fields, the agent guides you through a tracking setup in short rounds. The first round asks:

1. Track additions, edits, removals, upcoming deadlines, or a combination?
2. Run once, every N days, each workday, or weekly at a chosen time?
3. Which fields should appear in the digest or notification?

Immediately after the first bind or read, the agent shows concrete defaults for the detected date/filter field, a seven-day query range, and display fields. You can accept all three by saying "Use the defaults" or change them together.

A second round can refine filters, whether no-change runs stay silent, and where results should go. The agent recommends defaults from the detected schema instead of making you design the setup from scratch.

Recurring schedules require automation support from the current agent platform. Before creating one, the agent confirms the time, timezone, and destination.

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
