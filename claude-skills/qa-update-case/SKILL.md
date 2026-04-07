---
name: qa-update-case
description: 在 Slack 中根据自然语言描述、PR 链接或 Jira 线索更新现有 QA 测试用例。适用于已有 testcase md / Jira Test issue 的功能点维护：先自动定位对应模块与用例，再生成变更计划预览；用户确认后更新仓库 md 与 Jira description 表格。
---

# QA Update Case

## Purpose

用于“更新已有用例”场景。

典型触发语句：

- 帮我补充 perps 收藏增加一个在通用搜索时也可以收藏的用例
- 帮我更新 perps 收藏用例
- 结合这个 PR 更新 perps 收藏的用例：<PR 链接>

当用户意图是“已有功能点继续补充、修改、纠正、合并或扩展用例”时，使用本 skill。

---

## Core Rules

1. `QA-AGENTS/docs/qa/qa-rules.md` 是测试用例生成的唯一事实来源，必须优先读取。
2. 更新已有用例时，默认同时检查并维护：
   - 对应 testcase md
   - 对应 requirement 文档（如规则有变化）
   - 对应模块 rules 文档（如新增规则）
   - 对应 Jira `Test` issue description 表格
3. 测试用例粒度必须高于“根据 PR 生成测试项”：默认补充更多场景、数据、边界、异常、状态同步与代表性组合。
4. 如果用户给了 PR，不能只复述 PR；必须结合代码规则、现有用例缺口、Jira 当前表格结构做增量更新。
5. 改动前必须先输出“变更计划预览”；用户确认后才能真正更新仓库与 Jira。

---

## Inputs

优先接收自然语言输入，可混合以下信息：

```text
变更：<一句话修改诉求>
PR：<GitHub PR 链接，可选>
Jira：<Jira 链接，可选>
线索：<已有用例主题/模块/文件名关键词，可选>
```

用户也可以直接用大白话：

```text
帮我补充 perps 收藏增加一个在通用搜索时也可以收藏的用例
```

或：

```text
结合这个 PR，帮我更新 perps 收藏用例：<PR 链接>
```

---

## Workflow

### 1. 识别更新意图
满足以下任一条件，优先判定为“更新已有用例”：
- 用户明确说“更新”“补充”“修改”“维护”某个已有用例
- 仓库中可定位到高置信度 testcase md
- Jira 中可定位到对应 Test issue
- 用户给定 PR 且要求“结合 PR 更新 xxx 用例”

### 2. 自动定位现有资产
必须优先定位：
- testcase md
- requirement 文档
- module rules 文档
- Jira Test issue

推荐定位线索：
- 模块名（如 Perps）
- 功能名（如 收藏 / 搜索 / 统一账户）
- PR 修改文件与 commit message
- Jira summary / 标题 / 分节标题

若仓库和 Jira 都找不到高置信度目标，应回退为“新增用例候选”，并在预览中提示用户。

### 3. 读取规则与变更来源
必须读取：
- `QA-AGENTS/docs/qa/qa-rules.md`
- 对应 testcase md
- 对应模块 rules 文档
- 对应 requirement 文档（如存在）
- Jira 当前 description 结构（标题 + 表格）

如用户给了 PR，还必须读取：
- PR 描述与 diff
- 命中的业务规则文件（token / chain / config / metadata / validate / feature flag）

### 4. 生成“变更计划预览”
预览至少包含：
- 识别模块
- 判定结果：更新已有用例
- 命中的 testcase md / Jira Test issue
- 拟新增、修改、删除的测试场景摘要
- 是否同步更新 requirement / rules
- 受影响的 Jira 分节

此阶段只预览，不写仓库、不改 Jira。

### 5. 用户确认后执行
确认后再执行：
1. 更新 requirement 文档（如规则变化）
2. 更新 module rules 文档（如新增规则）
3. 更新 testcase md
4. 更新 Jira `Test` issue description
   - 优先局部更新对应小节与表格
   - 如无现成分节，再新增标题 + 表格
5. 若当前流程需要，提交仓库分支并创建 PR

---

## Output Rules

### A. 预览阶段
默认先输出“变更计划预览”，建议结构：

```text
变更计划预览

1. 类型：更新已有用例
2. 模块：Perps
3. 主题：收藏功能
4. 命中文件：
- docs/qa/testcases/cases/perps/2026-01-20_Perps-收藏功能测试.md
- docs/qa/requirements/Perps-xxx.md（如有）
5. Jira：OK-23956
6. 计划变更：
- 新增“通用搜索结果收藏”分节
- 补充搜索收藏与自选列表状态同步
- 补充异常与上限场景
```

### B. 正式用例内容
更新后的测试用例必须：
- 严格遵守 `qa-rules.md`
- 使用 Markdown 表格
- 表头固定：`| 优先级 | 场景 | 操作步骤 | 预期结果 |`
- 单元格内多行必须使用带序号的 `<br>`
- 预期结果只写可观察结果
- 不得只停留在 PR 粒度概括性测试点，必须补足细粒度场景与数据覆盖

---

## Jira Rules

1. Jira `Test` issue 的测试用例维护在 description 中。
2. description 底层为 ADF 结构，必须按 ADF 读写，不做简单字符串替换。
3. 优先局部更新目标小节，不重写整篇 description，除非必须整体重建。
4. 小节结构保持：
   - heading
   - table
   - rule
5. 表头固定为：
   - 优先级
   - 场景
   - 操作步骤
   - 预期结果

---

## Distinction from “PR Regression Items”

- “根据 PR 生成测试项”：保持现有风格，用于快速概括改动影响。
- “更新测试用例”：必须更细，默认补更多场景、数据与边界，并同步仓库 md 与 Jira 表格。

---

## Checklist

执行前检查：
1. 已确认这是“更新已有用例”而不是“新建用例”。
2. 已读取 `QA-AGENTS/docs/qa/qa-rules.md`、对应 testcase、rules、requirements。
3. 若有 PR，已读取 PR 与命中的规则/配置文件。
4. 已读取 Jira 当前 description 结构。
5. 已先给用户预览，并拿到明确确认。
6. 计划更新内容已覆盖场景、数据、边界、异常、同步一致性等维度，而不是仅复述 PR。
7. Jira 更新方案优先局部修改，不破坏现有表格结构。
