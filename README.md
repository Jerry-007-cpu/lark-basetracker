# lark-jobtracker · 飞书岗位追踪

贴一个飞书多维表格链接，自动整理出某时间段内开放的校招岗位，直接在对话里显示，并可选推送到微信。

> 适合"很多人购买岗位表格"的校招场景：每天/随时把表里**新开放的公司岗位**汇总成一条清单。

这是一个标准的 **Agent Skill**（`SKILL.md` + Python 脚本），可在 Claude Code / Codex / OpenClaw 等支持 Skill 的 agent 里使用，底层通过 [飞书官方 CLI `@larksuite/cli`](https://github.com/larksuite/cli) 调用飞书开放接口取数。

---

## 输出长这样

```
📌 开放岗位整理（2025-10-01 ~ 今天）　共 5 个

• 米哈游　开放：2026-01-07
    岗位：职能 / 支持
    批次：暑期提前批
    招聘官网：米哈游HR实习生（招聘方向）Open Day

• 网易雷火　开放：2025-12-25
    岗位：研发, 设计, 游戏策划
    批次：暑期提前批

• vivo　开放：2025-12-22
    岗位：产品, 研发
    批次：暑期提前批
```

字段（公司名 / 开放日期 / 岗位 / 批次 …）**自动识别**，每个人表头不一样也能用。

---

## 快速开始

```bash
# 1) 解析链接 + 自动识别字段（看看认得对不对）
python3 scripts/organize_jobs.py inspect --link "<飞书链接>" --identity bot

# 2) 整理最近 30 天开放的岗位，显示在终端
python3 scripts/organize_jobs.py list \
  --link "https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>" \
  --identity bot --days 30 --show-fields "岗位,批次,招聘官网"

# 3) 同时存 md 文件 + 推微信
python3 scripts/organize_jobs.py list --link "<base 链接>" --identity bot \
  --days 30 --out 岗位清单.md --wechat
```

> 在 agent 里使用时，用户**只需贴链接**，agent 会按 [`SKILL.md`](./SKILL.md) 自动完成解析、问时间段、整理。

---

## ⚠️ 踩坑复盘：为什么一开始读不到数据

这一节非常重要——飞书的权限模型很绕，下面是我们实际踩过的全部坑和最终能用的配方。**核心结论先放这里：用应用身份 `--identity bot` + base 直链，不要用用户身份、不要用 wiki 链接。**

### 根本原因

读飞书的**私有**表格数据，无论用 lark-cli、裸调 API 还是任何 SDK，都必须有一个"有权限的飞书应用"。`@larksuite/cli` 背后用的是你自己建的自建应用（如 `Jerry's CLI`），所以一切取决于这个应用开通了哪些权限。这堵墙是**飞书的机制**，换工具绕不开。

### 我们撞过的四道墙（按顺序）

| # | 报错 | 原因 | 解法 |
|---|------|------|------|
| 1 | `need_user_authorization` | lark-cli 没登录授权 | `lark-cli auth login` 走 Device Flow 扫码授权 |
| 2 | `token is required`（解析 wiki 时） | lark-cli 的 `api` **不读 URL 里的 `?query`**，查询参数必须用 `--params '{...}'` 单独传 | 脚本已改用 `--params` 传 JSON |
| 3 | `action_privilege_required: base:record:retrieve`（用户身份读记录） | 用户身份的 token 即使有 `base:record:read`，飞书"列出记录"接口仍要 `base:record:retrieve`，而这个 scope 自建应用给不了用户身份 → **死路** | **改用应用身份 `--identity bot`** |
| 4 | `action_scope_required: wiki:wiki:readonly`（应用身份解析 wiki） | 应用身份没开通 wiki 读权限 | **不用 wiki 链接**，改用 `base/<app_token>?table=<table_id>` 直链，跳过 wiki 解析 |

### 最终能用的配方

1. 飞书应用（`Jerry's CLI`）开通 **`bitable:app:readonly`（应用身份）** 并发布版本；
2. 把这个应用**加为目标表的协作者**（可阅读）；
3. 调用时加 **`--identity bot`**；
4. 用 **base 直链**（不要 wiki 链接），即 `https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>`。

> wiki 链接里的 `<APP_TOKEN>` / `<TABLE_ID>` 怎么拿？先用**用户身份**跑一次 `inspect --link "<wiki链接>"`（用户身份有 wiki 读权限），它会打印出 `app_token` 和 `table_id`，之后就一直用 base 直链 + `--identity bot`。

---

## 完整安装与配置流程

### 第 0 步：装 lark-cli（飞书官方 CLI）

```bash
npm install -g @larksuite/cli
# 加进 PATH（可选）
export PATH="$HOME/.local/lib/node_modules/@larksuite/cli/bin:$PATH"
```

> ⚠️ lark-cli 是 macOS / Windows 原生二进制，**不能在 Linux 容器/沙箱里跑**，必须在本机。

### 第 1 步：在飞书开放平台建应用并开通权限

1. 打开 <https://open.feishu.cn/app>，创建一个自建应用（或用 lark-cli 首次登录时引导创建的那个）。
2. 左侧 **权限管理 → 开通权限**，搜索并开通：
   - **`bitable:app:readonly`** —— 查看、评论和导出多维表格（**应用身份**）
3. 左侧 **版本管理与发布 → 创建版本 → 申请发布**，等顶部显示"当前修改均已发布"。

### 第 2 步：把应用加进目标表

在飞书里打开你的多维表格 → 右上角 **分享 / … → 添加文档应用（或协作者）** → 搜索你的应用名 → 给 **可阅读** 权限。

> 不加这一步，应用身份能调通接口但读不到这张具体的表。

### 第 3 步：lark-cli 授权登录

```bash
lark-cli auth login          # 业务域勾上 base，扫码授权
lark-cli auth status         # 看到已登录即可
```

### 第 4 步：拿到 app_token / table_id

```bash
python3 scripts/organize_jobs.py inspect --link "<你的 wiki 或 base 链接>"
# 输出里记下 app_token 和 table_id
```

### 第 5 步：整理岗位

```bash
python3 scripts/organize_jobs.py list \
  --link "https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>" \
  --identity bot --days 30 --show-fields "岗位,批次,招聘官网"
```

---

## 推送到微信（可选）

走腾讯官方的**微信 ClawBot**通道（不是灰色协议，不封号）：

1. 本机装 [QClaw](https://qclaw.qq.com) 并按[官方指南](https://qclaw.qq.com/docs/206087648449069056/)微信扫码接入；
2. `npm install -g @claw-lab/wxclawbot-cli`，`wxclawbot accounts --json` 验证；
3. list 命令加 `--wechat` 即可推送。注意 ClawBot 限频约 7 条 / 5 分钟（日报是一整条，没问题）。

---

## 每天定时整理（可选）

用 macOS 的 `launchd` 或 `cron` 把 list 命令挂成每天一次。示例（cron，每天 9:00）：

```bash
crontab -e
0 9 * * * cd ~/Desktop/飞书提效/feishu-jobs-digest && /usr/bin/python3 scripts/organize_jobs.py list --link "https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>" --identity bot --days 1 --wechat >> data/notify.log 2>&1
```

> 定时跑需要你的电脑在那个时间点**开机且联网**（QClaw 也要在线）。完整 launchd 配置见仓库历史或 issue。

---

## 跨 agent 使用（Claude Code / Codex / OpenClaw）

`SKILL.md` + Python 脚本是跨 agent 的标准格式，**核心逻辑不用改**。差异只在两处：

- **安装位置**：Claude Code 放 `~/.claude/skills/`；OpenClaw 放它的 skills 目录或 `clawhub install`；Codex 放它的技能目录。
- **定时机制**：各家用各自的调度，或统一用系统 cron / launchd。

脚本只要求宿主 agent 能跑 shell，且本机已装并授权好 lark-cli。

---

## 命令速查

```
inspect  --link <链接> [--identity bot]
         解析链接、列出字段、给出"标题/开放时间"字段的自动匹配建议

list     --link <链接> --identity bot
         [--days N | --since YYYY-MM-DD --until YYYY-MM-DD]
         [--title-field 字段] [--date-field 字段]
         [--show-fields "A,B,C"] [--out 文件.md] [--wechat]
         整理某时间段开放的岗位
```

字段不传时**自动识别**（主字段→标题，日期型/名称含"开放/发布"→开放时间）；识别不对再用 `--title-field` / `--date-field` 覆盖。

---

## 致谢与参考

- [larksuite/cli](https://github.com/larksuite/cli) —— 飞书官方 CLI，取数底座
- [zarazhangrui/follow-builders](https://github.com/zarazhangrui/follow-builders) —— "贴链接即用 + 定时推送"的 Skill 范式参考

## License

[MIT](./LICENSE)
