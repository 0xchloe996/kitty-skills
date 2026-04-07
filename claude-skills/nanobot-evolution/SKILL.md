---
name: nanobot-evolution
description: 为 nanobot 提供自我进化、结构化学习记录、上下文压缩与精确检索、本地 Apple Silicon 推理维护。用于：记录错误/用户纠正/功能请求，构建和查询记忆索引，压缩历史 session，上线或巡检本地 llama.cpp 服务，以及在修改记忆体系时统一走这些脚本而不是散落地写文件。
---

# Nanobot Evolution

优先用本 skill 处理三类工作：
1. **自我改进**：记录错误、用户纠正、功能请求、最佳实践。
2. **上下文治理**：压缩 session、重建索引、精确检索过去的事实，避免长上下文直接全量读文件。
3. **本地推理维护**：启动/巡检 Apple Silicon 上的 `llama.cpp` 本地服务。

## 目录

- 结构化学习日志：`memory/evolution/*.jsonl`
- 检索索引：`memory/index/docs.jsonl`
- session 压缩摘要：`memory/index/session_rollups.jsonl`
- 脚本目录：`skills/nanobot-evolution/scripts/`

## 常用命令

### 1) 记录学习项

```bash
python3 /Users/onekey/.nanobot/workspace/skills/nanobot-evolution/scripts/log_learning.py \
  --kind correction \
  --topic "Slack 输出约束" \
  --wrong "在无回复任务里输出说明性文本" \
  --correct "严格不发送任何聊天回复" \
  --context "Hyperliquid cron"
```

支持的 `--kind`：
- `error`
- `correction`
- `request`
- `practice`
- `preference`

### 2) 压缩 session

```bash
python3 /Users/onekey/.nanobot/workspace/skills/nanobot-evolution/scripts/compact_sessions.py
```

### 3) 重建记忆索引

```bash
python3 /Users/onekey/.nanobot/workspace/skills/nanobot-evolution/scripts/rebuild_memory_index.py
```

### 4) 精确检索过去上下文

```bash
python3 /Users/onekey/.nanobot/workspace/skills/nanobot-evolution/scripts/search_memory.py --query "Hyperliquid 无聊天回复 约束"
```

在以下场景优先先查索引，再决定是否读原文件：
- 用户问“之前说过/改过什么”
- 需要回忆某个历史决策、错误、修复方式
- HISTORY.md 已很长，直接全读会浪费 token

### 5) 启动 / 巡检本地 Apple Silicon 模型服务

```bash
bash /Users/onekey/.nanobot/workspace/scripts/start_local_llm.sh
bash /Users/onekey/.nanobot/workspace/scripts/check_local_llm.sh
```

## 使用规则

- 发现**用户纠正**时：先记录到结构化日志；若属于长期稳定偏好，再同步进 `memory/MEMORY.md`。
- 发现**命令失败模式**时：记录 `error`，包含命令、报错、已知修复。
- 发现**功能请求**时：记录 `request`，带验收标准或影响范围。
- 在需要历史回忆时：优先执行 `search_memory.py`，避免直接整份读取 `HISTORY.md`。
- 在 session/记忆文件明显变大后：运行 `compact_sessions.py` 和 `rebuild_memory_index.py`。
- 本地模型异常时：先跑 `check_local_llm.sh`，必要时再重启服务。

## 与已安装公共 skill 的关系

- `self-improving-agent-cn`：可作参考，但默认写入 `~/.openclaw`；本 skill 统一落到 `~/.nanobot/workspace`。
- `memory-manager`：用于三层记忆结构；运行时设置 `OPENCLAW_WORKSPACE=/Users/onekey/.nanobot/workspace`。

## 轻量工作流

1. 新纠正/新请求出现 → `log_learning.py`
2. 有新的 session 或 HISTORY 增长 → `compact_sessions.py`
3. 压缩后 → `rebuild_memory_index.py`
4. 需要回忆 → `search_memory.py`
5. 本地回复变慢/失联 → `check_local_llm.sh` / `start_local_llm.sh`
