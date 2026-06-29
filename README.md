**English** | [中文](./README.zh-CN.md)

# lark-jobtracker

Paste a Feishu (Lark) Bitable link and get a clean digest of the campus-recruiting positions that opened in any time window — shown right in your chat, optionally pushed to WeChat.

**Idea:** lots of students buy shared Feishu job tables. This turns that table into a "what opened" digest, so you never miss a new posting.

## What you get

- A digest of positions opened within any time window you pick (last 7 days, last 30 days, a date range)
- **Auto-detected fields** — works even though everyone's table uses different column names
- Sorted newest-first, with the fields you care about (positions, batch, official link, referral code…)
- Optional push to **WeChat** via the official ClawBot channel (not a grey-area hack — won't get you banned)
- Runs in **Claude Code, Codex, or OpenClaw** — it's a standard Skill, the core logic doesn't change between them

## Quick start

1. Install this skill in your AI agent (see [Installation](#installation))
2. Paste your Feishu table link, or just say *"organize the open jobs"*
3. The agent guides you through the rest conversationally — no config files to edit by hand

The agent will ask you:

- Which time window (last 7 days / last 30 days / a specific date range)
- Which fields to show in the digest
- Whether to also push it to WeChat

## Adjust it by chatting

Just tell your agent:

- "Only show the last 7 days"
- "Also include the referral-code field"
- "Push it to WeChat every morning at 9"

## How it works

1. You paste a Feishu Bitable link
2. The skill resolves it to `app_token` / `table_id`
3. It pulls the records through the official [Lark CLI](https://github.com/larksuite/cli) using **application identity**
4. It filters by the "open date" field within your window, auto-matching the title/date columns
5. It renders a digest in chat — and optionally writes a Markdown file and/or pushes to WeChat

## Installation

### Claude Code

```bash
git clone https://github.com/Jerry-007-cpu/lark-jobtracker.git ~/.claude/skills/lark-jobtracker
```

### OpenClaw

```bash
git clone https://github.com/Jerry-007-cpu/lark-jobtracker.git ~/skills/lark-jobtracker
```

## Requirements

- An AI agent (Claude Code / Codex / OpenClaw)
- The official **Lark CLI** (`@larksuite/cli`) installed and authorized on your machine
- A Feishu custom app with **`bitable:app:readonly`** enabled (application identity), added as a collaborator on your table

> Unlike skills that read public content, Feishu data is **private** — so a one-time Feishu app setup is unavoidable. It takes a few minutes; see [Setup](#first-time-setup-feishu).

## First-time setup (Feishu)

The thing nobody tells you: reading a private Feishu table needs an app with the right permission, and there are a couple of traps. Here's the recipe that actually works.

1. Install the CLI: `npm install -g @larksuite/cli`
2. At <https://open.feishu.cn/app>, open your app → **权限管理** → enable **`bitable:app:readonly`** → **版本管理与发布** → create & publish a version.
3. Open your table in Feishu → **Share / collaborators** → add your app with read access.
4. `lark-cli auth login` (pick the `base` domain, scan to authorize).
5. Get the table ids once: `python3 scripts/organize_jobs.py inspect --link "<your link>"`.

**Two traps we hit (and how to avoid them):**

- Use **`--identity bot`** (application identity). User identity can't get the `base:record:retrieve` privilege a self-built app needs to list records.
- Use a **base direct link** (`https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>`), not the wiki link — application identity has no wiki-read scope, so the base link skips that step.

Full troubleshooting table is in [README.zh-CN.md](./README.zh-CN.md#踩坑复盘).

## Privacy

- Your Feishu data stays between your own machine and Feishu's API — nothing is sent to any third party.
- The Lark CLI stores its tokens locally on your machine.
- The skill only reads the table you point it at.

## Acknowledgements

- [larksuite/cli](https://github.com/larksuite/cli) — the official Feishu CLI that powers data access
- [zarazhangrui/follow-builders](https://github.com/zarazhangrui/follow-builders) — inspiration for the "paste-a-link + scheduled digest" Skill pattern

## License

[MIT](./LICENSE)
