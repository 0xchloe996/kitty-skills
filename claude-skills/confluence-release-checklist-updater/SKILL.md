---
name: confluence-release-checklist-updater
description: 在 Confluence 现有发版 / 热更新 checklist 页面中，基于 Branch、Commit、Bundle Version 与页面链接，生成并直接更新 checklist 内容。当用户要求“更新 checklist”“直接改到 Confluence/Jira 页面里”“只改 Checklist 的内容”时使用。默认只修改表格中的 `Checklist 的内容` 一列，不改 `客户端`、`执行人`、页面其他正文与结构；客户端名称默认沿用现有页面中的 7 个固定端。
---

# Confluence Release Checklist Updater

## Inputs

优先接收：

```text
Branch:
Commit:
Bundle Version:
更新 Checklist：<Confluence 页面链接>
```

可选：

```text
备注：
PR / release note：
```

规则：
- 页面链接优先使用 Confluence 页面 URL；若只给 page id 也可。
- `Commit` 可为 SHA 或 GitHub commit 链接；优先解析为完整 SHA。
- 若缺少页面链接或 commit，不要硬猜，直接要求补充。

## Workflow

1. 读取页面当前内容，定位现有 checklist 表格。
2. 读取 commit 实际改动，归纳为“主流程 baseline + 改动命中验证”。
3. 按页面现有客户端拆分 checklist；默认保持现有 7 个端，不合并端。
4. 只更新 `Checklist 的内容` 一列；`客户端`、`执行人`、页面其他内容保持不动。
5. checklist 保持轻量：不重复专项测试内容，不展开深度专项步骤。
6. 完成更新后，返回简短确认与页面版本号。

## Output

默认直接执行更新，并简短返回：

```text
已更新 checklist 内容。
- 页面：<url>
- 版本：<version>
```

要求：
- 不在回复里重复整份 checklist，除非用户明确要求。
- 若用户只是要预览，不直接更新页面，先输出三列表预览。
- 若页面结构异常或找不到 checklist 表格，明确报错并说明缺少什么。

## Fixed Rules

1. 只改 `Checklist 的内容`。
2. 不改 `客户端`、`执行人`、页面其他正文与结构。
3. 默认沿用现有 7 个客户端命名：
   - `IOS-TF包`
   - `OneKey-WEB`
   - `安卓`
   - `Desktop-TF 包`
   - `OneKey-Desktop-RN（测Mac平台）`
   - `OneKey-Desktop-RN（测window平台）`
   - `ipad`
4. 每个端的人只看自己那一段。
5. 不把专项功能测试内容重复写进 checklist。
6. checklist 采用“主流程 baseline + 改动命中验证”。

## Script

优先使用 `scripts/update_confluence_checklist.py` 执行页面更新。脚本会：
- 读取本地 Confluence 凭据
- 拉取页面 storage HTML
- 仅替换目标表中对应行的 `Checklist 的内容`
- 保留原有 `客户端` 与 `执行人`
- 通过 Confluence API 回写页面

## Checklist

发送前检查：
1. 页面链接、commit 可解析。
2. 已基于实际 commit 改动生成 checklist，而不是凭空猜测。
3. 只修改了 `Checklist 的内容` 列。
4. 没有改动 `客户端`、`执行人`、页面其他内容与结构。
5. checklist 已按端拆分，并保持轻量。
