**English** | [中文](./README.zh-CN.md)

<div align="center">
  <h1>lark-basetracker</h1>
  <p><strong>Send a table link to your agent and ask what changed.</strong></p>
  <p>Supports Feishu/Lark Base, Tencent Docs online tables, and CSV / TSV / XLSX files.</p>
</div>

## What it does

`lark-basetracker` is a conversational Agent Skill that reads a table, detects its fields, and reports recently added, changed, or removed records.

It is designed first for job-update creators:

- Collect newly posted or reopened graduate, internship, and experienced roles
- Extract company, role, location, deadline, and application links
- Compare two table states and show the exact field changes
- Produce a clean digest for communities, newsletters, or chat groups

The same workflow also works for projects, leads, content calendars, vendors, and other tables.

## Use it through conversation

After one-time installation and account setup, send a link and describe the result you want:

```text
Here is my jobs table: <table link>
Summarize roles added or updated in the last 7 days. Include company, role, location, and application link.
```

```text
What was added, edited, or removed since the last snapshot?
<table link>
```

The agent inspects fields, chooses date filtering or snapshot comparison, and formats the answer in the background. Normal users do not need to run commands.

## Data sources

| Source | Current capability |
| --- | --- |
| Feishu/Lark Base link | Read online with the signed-in user's existing permissions |
| Tencent Docs SmartSheet | Read tables, fields, and records through the official MCP server |
| Tencent Docs regular table | Read through the official MCP server and recover table structure |
| CSV / TSV / XLSX | Read locally without an online account |
| Two files or saved states | Compare additions, field-level edits, and removals |

View-only permission is a supported primary scenario. The Skill does not bypass owner-defined viewing, download, or membership restrictions.

## Is a time field required?

No.

With a time field, the Skill can answer requests such as “today,” “this week,” or “the last 7 days.” Useful fields include `Created Time`, `Last Modified Time`, `Published Time`, and `Open Time`.

Without a time field, the Skill saves a complete state and compares it with the next read. It reports added records, removed records, and exact before/after field values. Snapshot comparison works best with a stable unique field such as a job ID, record number, application URL, or provider record ID.

## Tencent Docs

The repository includes its own client for the [official Tencent Docs MCP endpoint](https://developer.cloud.tencent.com/mcp/server/11803). The host agent does not need to implement MCP calls itself.

For first-time setup:

1. Get a personal token from the [official Tencent Docs authorization page](https://docs.qq.com/open/auth/mcp.html).
2. Ask the agent to securely configure Tencent Docs for `lark-basetracker`.
3. The agent starts a hidden-input prompt so the token does not appear in chat or shell history.

The client initializes MCP, discovers the live tools and JSON schemas, then uses the appropriate read-only SmartSheet or content tools.

Error `400006` means the token needs to be checked or renewed. Error `400007` means the Tencent Docs account lacks the required VIP capability. Exported XLSX, CSV, or TSV remains available as a fallback.

## First Feishu connection

Ask your agent:

```text
Set up the first Feishu connection for lark-basetracker.
```

The agent checks the official `lark-cli`, then sends the official application setup and user authorization links. The default identity is the signed-in user, so a table only needs to be viewable by that user; the app does not need to be added as a collaborator on every table.

Never paste App Secrets or access tokens into chat.

## Supported agents

| Agent | Status | Installation target |
| --- | --- | --- |
| [Codex](https://learn.chatgpt.com/docs/build-skills.md) | Supported | User `.agents/skills` |
| [Claude Code](https://code.claude.com/docs/en/skills) | Supported | User `.claude/skills` |
| [OpenClaw](https://docs.openclaw.ai/skills) | Supported | User `.openclaw/skills` |
| [QClaw](https://github.com/QuantumClaw/QClaw) | Supported | Shared QClaw Skill plus a separate runtime directory |

The recommended installation request is:

```text
Install lark-basetracker from this repository and choose the correct adapter for my agent:
https://github.com/Jerry-007-cpu/lark-basetracker
```

<details>
<summary>Manual installation</summary>

Clone the repository, then run the matching installer:

```bash
python3 scripts/install_agent.py --platform codex
python3 scripts/install_agent.py --platform claude-code
python3 scripts/install_agent.py --platform openclaw
python3 scripts/install_agent.py --platform qclaw
```

QClaw's native installer stores only one Markdown file, so this installer also copies the Python runtime. Restart QClaw and review/enable the Skill afterward.

Use `--scope project` for a project-only Codex, Claude Code, or OpenClaw installation.

</details>

## Example output

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

## Architecture

Provider access and table analysis are separated:

- Feishu provider: Base/Wiki parsing, fields, and records
- Tencent Docs provider: MCP initialization, tool discovery, and online reads
- File provider: CSV, TSV, and XLSX
- Shared core: field detection, date filtering, state persistence, field-level diffing, and rendering

All supported agents therefore share the same tracking behavior and differ only in installation and runtime layout.

## Current limitations

- Tencent Docs document types return different structures. SmartSheet has the strongest support; regular tables depend on structured content returned by official `get_content`.
- Snapshot comparison should use a stable unique field. Duplicate names and reordered rows are less reliable without one.
- XLSX requires `openpyxl`; CSV and TSV use the Python standard library.
- Feishu `.base` backup files are not currently parsed.
- Feishu Aily and publishing to WeChat channels are outside the current adapter set.

## Privacy

- Operations are read-only by default.
- Feishu data flows between the local agent, `lark-cli`, and Feishu APIs.
- Tencent Docs tokens stay in an environment variable or a local `0600` token file.
- Snapshot states are local JSON files at paths selected by the user.
- Never commit tokens, App Secrets, or state files containing real business data.

## Development checks

```bash
python3 -B -m unittest discover -s tests -v
python3 -B -m py_compile scripts/organize_jobs.py scripts/basetracker/*.py
```

## License

[MIT](./LICENSE)
