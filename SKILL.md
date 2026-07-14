---
name: lark-basetracker
description: 追踪飞书多维表格在某段时间内更新过的记录。用户贴一个 Feishu/Lark Bitable 链接后，按指定日期/更新时间字段筛选记录，生成清单；适合求职博主整理职位更新，也可用于项目、线索、内容排期等通用表格。触发词：飞书表格更新、多维表格更新、职位更新、表格追踪、basetracker、lark-basetracker。
---

# lark-basetracker（飞书多维表格更新追踪）

用户只需要贴一个飞书多维表格链接，就能按时间窗口整理出更新过的记录。

当前版本的“更新追踪”基于表格里已有的日期字段，例如 `更新时间`、`发布时间`、`开放时间`、`最后更新时间`。还没有实现快照对比或逐字段 diff。

## 运行方式与平台边界

- 这是一个 `SKILL.md` + 本地 Python 脚本的 Skill，适用于能够读取本目录并执行 Shell 命令的 Agent。
- Codex、Claude Code、OpenClaw、QClaw 或其他本地 Agent 都可以复用同一条对话流程；安装位置由各平台决定。
- 本仓库尚未提供飞书智能伙伴 Aily 的原生适配。如果当前运行环境是 Aily，应提示需要先把脚本封装为 Aily 可调用的操作、连接器或 HTTP 服务，不要假装已经完成原生接入。
- 如果 Agent 无法访问本机 `lark-cli` 或无法执行 Python，本 Skill 不能直接运行。

## 前置条件

- 本机已安装 **lark-cli** 并完成飞书授权。
- 目标多维表格已把自建应用加为协作者，应用开通 `bitable:app:readonly`。
- 推荐使用 `--identity bot` 读取私有多维表格。
- 如需推微信，本机需要安装并配置 `wxclawbot`。不推微信则不需要。

## 对话流程

1. **用户贴链接后，先检查字段：**

   ```bash
   python3 scripts/organize_jobs.py inspect --identity bot --link "<用户给的飞书链接>"
   ```

   输出会列出全部字段，并标出可作为日期/更新时间的字段。

2. **如果上下文不明确，反问用户这些信息：**

   - 用哪个字段作为更新时间/日期字段；
   - 看哪段时间：最近 N 天，或具体起止日期；
   - 哪个字段作为每条记录标题；
   - 摘要里展示哪些字段。

3. **生成更新摘要并显示在对话里：**

   ```bash
   python3 scripts/organize_jobs.py list --identity bot --link "<链接>" \
       --date-field "更新时间" --days 7 \
       --title-field "名称" \
       --show-fields "状态,负责人,链接,备注"
   ```

   时间范围二选一：

   - `--days N`：最近 N 天；
   - `--since YYYY-MM-DD --until YYYY-MM-DD`：指定日期范围，结束日期包含当天。

   展示字段：

   - `--show-fields "字段1,字段2,字段3"`：只展示指定字段；
   - 留空：展示除标题字段和日期字段以外的全部字段。

4. **可选：写入文件或推微信：**

   ```bash
   python3 scripts/organize_jobs.py list --identity bot --link "<链接>" \
       --date-field "更新时间" --days 7 \
       --title-field "名称" \
       --out updates.md
   ```

   ```bash
   python3 scripts/organize_jobs.py list --identity bot --link "<链接>" \
       --date-field "更新时间" --days 1 \
       --title-field "岗位名称" \
       --show-fields "公司,地点,投递链接,内推码" \
       --wechat
   ```

## 求职博主场景建议

如果用户是求职博主，优先把输出设计成“职位更新清单”：

- 标题字段：岗位名称、职位、公司 + 岗位等；
- 日期字段：更新时间、开放时间、发布时间；
- 展示字段：公司、岗位、地点、批次、投递链接、内推码、截止时间。

示例输出：

```text
📌 表格更新整理（2026-06-24 ~ 今天） 共 2 条

• 产品经理 开放：2026-06-29
    公司：某互联网公司
    地点：深圳
    投递链接：https://example.com

• 后端开发 开放：2026-06-28
    公司：某科技公司
    地点：北京
```

适合直接理解的用户表达包括：

- “整理这张表今天新增的岗位，带上公司、地点和投递链接。”
- “把最近 7 天开放的校招岗位做成一份可以发社群的清单。”
- “看看这张多维表本周有哪些更新，不是岗位表也可以。”

## 注意

- 没有所选日期字段，或日期无法解析的记录会被跳过。
- 飞书日期字段是毫秒时间戳，脚本会自动转换。
- 文本日期支持 `YYYY-MM-DD`、`YYYY-MM-DD HH:MM`、`YYYY/MM/DD` 等常见格式。
- 如果 wiki 链接权限不够，要求用户提供 base 直链：`https://feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>`。
