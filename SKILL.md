---
name: feishu-jobs-digest
description: 贴一个飞书多维表格链接，自动整理出某时间段内开放的岗位清单，直接在对话里显示，并可选推送到微信。适合校招/招聘场景：用户买了岗位表格、想知道"最近开放了哪些岗位"。触发词：飞书岗位整理、整理开放岗位、飞书表格招聘、岗位日报、贴个飞书链接。
---

# 飞书岗位整理（贴链接即用）

用户**只需要贴一个飞书多维表格链接**，就能整理出某段时间内开放的岗位。
你（agent）按下面的流程对话式地完成，不要让用户手动改配置文件。

## 前置条件（首次，一次性）

- 本机已安装 **lark-cli** 并完成飞书授权（见项目根 `CLAUDE.md`）。这是读飞书私有数据的唯一前提，绕不开。
- 如需"推微信"：本机装 **QClaw** 并接入微信 ClawBot + `npm i -g @claw-lab/wxclawbot-cli`。不推微信则不需要。

## 对话流程（你要做的）

1. **用户贴链接**。先解析、看表里有哪些字段：
   ```bash
   python3 scripts/organize_jobs.py inspect --link "<用户给的飞书链接>"
   ```
   输出会列出全部字段，并标出可作"开放时间"的日期字段。

2. **反问用户两件事**（如果链接/上下文里看不出来）：
   - 用哪个字段当「开放时间」（从上一步标了"← 可作为开放时间"的字段里挑）；
   - 看哪段时间——"最近 7 天" / "最近 30 天" / 具体起止日期；
   - 哪个字段是岗位标题（一般叫"岗位名称/职位"）。

3. **整理岗位**并显示在对话里：
   ```bash
   python3 scripts/organize_jobs.py list --link "<链接>" \
       --date-field "开放时间" --days 7 \
       --title-field "岗位名称"
   ```
   - 时间段三选一：`--days N`（最近N天）/ `--since YYYY-MM-DD --until YYYY-MM-DD`（指定范围）；
   - `--show-fields "地点,类型,投递链接"` 控制每个岗位展示哪些字段；留空=展示全部。

4. **（可选）推微信 / 存文件**：
   ```bash
   python3 scripts/organize_jobs.py list --link "<链接>" --date-field "开放时间" \
       --days 7 --title-field "岗位名称" --out 岗位清单.md --wechat
   ```

## 定时（可选）

把第 3/4 步的命令固定好参数，挂到系统定时器，实现"每天自动整理 + 推微信"。
做法见 `README.md`「定时任务」一节（launchd / cron）。注意 QClaw 需在该时间点开机在线。

## 输出示例

```
📌 开放岗位整理（2026-06-21 ~ 今天）　共 2 个

• 产品经理　开放：2026-06-27
    地点：深圳
    类型：实习

• 后端开发　开放：2026-06-26
    地点：北京
    类型：校招
```

## 跨 agent 运行（Claude Code / Codex / OpenClaw 通用）

这个 skill 是标准 SKILL.md + Python 脚本，逻辑不依赖某个特定 agent，**核心无需改动**。
不同 agent 只有"安装位置"和"定时机制"两处外围差异：

- **Claude Code**：放到 `~/.claude/skills/feishu-jobs-digest/`
- **OpenClaw / QClaw**：放到其 skills 目录（或 `clawhub install`）
- **Codex**：放到其技能/提示目录，由 Codex 读取 SKILL.md 后调用脚本

脚本只要求宿主 agent 能跑 shell，并且本机有 lark-cli。定时则各家用各自的调度，或统一用系统 cron/launchd。

## 注意

- 没有"开放时间"的记录会被跳过（避免噪音）。
- 飞书日期字段是毫秒时间戳，脚本已自动转换；也兼容 `YYYY-MM-DD` 文本日期。
- 是 wiki 链接也没关系，脚本会自动 `get_node` 解析出 app_token。
