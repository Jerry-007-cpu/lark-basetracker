[English](./README.md) | **中文**

# lark-jobtracker · 飞书岗位追踪

贴一个飞书多维表格链接，自动整理出某段时间内开放的校招岗位，直接显示在对话里，并可选推送到微信。

**理念：** 很多人会买共享的飞书岗位表。这个 skill 把那张表变成一份"今天开放了什么"的清单，让你不漏掉任何新岗位。

## 你会得到什么

- 一份**某时间段内开放岗位**的清单（最近 7 天 / 最近 30 天 / 指定日期范围）
- **字段自动识别**——每个人的表头都不一样，它也能认出"公司/岗位/开放时间"
- 按开放时间倒序，带上你关心的字段（岗位、批次、招聘官网、内推码…）
- 可选**推送到微信**，走腾讯官方的 ClawBot 通道（不是灰色协议，不封号）
- 在 **Claude Code、Codex、OpenClaw** 里都能跑——标准 Skill，核心逻辑不用改

## 快速开始

1. 在你的 AI agent 里安装此 skill（见[安装](#安装)）
2. 贴上你的飞书表格链接，或直接说**"整理一下开放的岗位"**
3. Agent 会以对话方式引导你完成，**不用手动改任何配置文件**

Agent 会询问你：

- 看哪段时间（最近 7 天 / 最近 30 天 / 指定起止日期）
- 清单里展示哪些字段
- 要不要同时推到微信

## 对话即可修改

直接告诉你的 agent：

- "只看最近 7 天"
- "再加上内推码这个字段"
- "每天早上 9 点推一次到微信"

## 工作原理

1. 你贴一个飞书多维表格链接
2. skill 解析出 `app_token` / `table_id`
3. 通过飞书官方 [Lark CLI](https://github.com/larksuite/cli)，用**应用身份**拉取记录
4. 按"开放时间"字段在你指定的时间段内筛选，自动匹配标题/日期列
5. 在对话里输出清单——可选再存成 Markdown 文件、或推送微信

## 安装

### Claude Code

```bash
git clone https://github.com/Jerry-007-cpu/lark-jobtracker.git ~/.claude/skills/lark-jobtracker
```

### OpenClaw

```bash
git clone https://github.com/Jerry-007-cpu/lark-jobtracker.git ~/skills/lark-jobtracker
```

## 系统要求

- 一个 AI agent（Claude Code / Codex / OpenClaw）
- 本机已安装并授权飞书官方 **Lark CLI**（`@larksuite/cli`）
- 一个飞书自建应用，已开通 **`bitable:app:readonly`**（应用身份），并被加为目标表的协作者

> 和"读公开内容"的 skill 不同，飞书数据是**私有**的，所以一次性的飞书应用配置绕不开。几分钟搞定，见[首次配置](#首次配置飞书)。

## 首次配置（飞书）

读飞书私有表需要一个有权限的应用，中间有几个坑。下面是**实测能用的配方**：

1. 装 CLI：`npm install -g @larksuite/cli`
2. 打开 <https://open.feishu.cn/app> → 你的应用 → **权限管理** → 开通 **`bitable:app:readonly`** → **版本管理与发布** → 创建并发布版本
3. 飞书里打开你的表 → **分享 / 协作者** → 把你的应用加为可阅读
4. `lark-cli auth login`（勾上 `base` 业务域，扫码授权）
5. 拿一次表的 id：`python3 scripts/organize_jobs.py inspect --link "<你的链接>"`

### 踩坑复盘

| 报错 | 原因 | 解法 |
|------|------|------|
| `need_user_authorization` | lark-cli 没授权 | `lark-cli auth login` 扫码 |
| `token is required` | lark-cli 的 `api` 不读 URL 里的 `?query` | 脚本已改用 `--params` 传参 |
| `base:record:retrieve` 用户身份读不了 | 用户身份拿不到这个 scope | **改用应用身份 `--identity bot`** |
| `wiki:wiki:readonly` 应用身份缺失 | 应用身份没 wiki 读权限 | **用 base 直链**跳过 wiki 解析 |

**两条铁律：**

- 用 **`--identity bot`**（应用身份），别用默认用户身份
- 用 **base 直链** `https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>`，别用 wiki 链接

## 推送到微信（可选）

走腾讯官方微信 ClawBot：装 [QClaw](https://qclaw.qq.com) 并扫码接入 → `npm install -g @claw-lab/wxclawbot-cli` → list 命令加 `--wechat`。限频约 7 条/5 分钟（日报一整条，没问题）。

## 隐私

- 你的飞书数据只在你自己的电脑和飞书 API 之间流动，不发给任何第三方
- Lark CLI 的 token 存在本机
- skill 只读你指定的那张表

## 致谢

- [larksuite/cli](https://github.com/larksuite/cli) —— 飞书官方 CLI，取数底座
- [zarazhangrui/follow-builders](https://github.com/zarazhangrui/follow-builders) —— "贴链接即用 + 定时推送" 的 Skill 范式参考

## 许可证

[MIT](./LICENSE)
