---
name: qa-add-case
description: 在 Slack 中根据自然语言需求、PR 链接或 Jira 线索新增 QA 测试用例。适用于仓库与 Jira 中尚无现成用例的功能点：先基于 QA-AGENTS/docs/qa 规则生成变更计划预览，待用户确认后再新建 testcase md、必要的 requirement/rules 文档，并新建 Jira Test issue（description 为标题+表格结构）。
---

# QA Add Case

## Purpose

用于“新增用例”场景。

典型触发语句：

- 帮我新增 perps 统一账户的用例
- 帮我新增 xxx 功能的测试用例
- 这是需求 + PR，帮我新建对应的测试用例

当用户意图是“新功能 / 新主题 / 仓库与 Jira 中都没有现成用例，需要新建一套完整用例资产”时，使用本 skill。

---

## Core Rules

1. `QA-AGENTS/docs/qa/qa-rules.md` 是测试用例生成的唯一事实来源，必须优先读取。
2. 新增用例时，必须同时检查并维护：
   - `docs/qa/requirements/<模块>-<功能>.md`
   - `docs/qa/rules/<module>-rules.md`（必要时更新）
   - `docs/qa/testcases/cases/<module>/YYYY-MM-DD_<模块>-<测试主题>.md`
3. 用例需要比“根据 PR 生成测试项”更细：默认补足主流程、边界、异常、状态切换、同步一致性、代表数据与关键数据组合。
4. 若需求涉及 token / chain / whitelist / metadata / 校验规则 / feature flag，除 PR 外还要补读业务代码仓库中的相关规则文件，再生成更细粒度测试用例。
5. Jira 侧默认创建 `Test` 类型 issue；测试用例维护在 issue description 中，结构必须兼容 Jira ADF：多段标题 + 每段一张 4 列表格。
6. 改动前必须先给用户“变更计划预览”，用户明确确认后，才能真正写仓库、建 Jira、提 PR。

---

## Inputs

优先接收自然语言输入，可混合以下信息：

```text
需求：<一句话需求/功能描述>
PR：<GitHub PR 链接，可选>
Jira：<Jira 链接，可选；新增场景通常可为空>
补充说明：<业务规则 / 风险点 / 指定模块，可选>
```

用户也可以直接大白话输入，例如：

```text
帮我新增 perps 统一账户的用例
```

或：

```text
帮我新增 xxx 功能用例，结合这个 PR 一起看：<PR 链接>
```

---

## Workflow

### 1. 识别新增意图
满足以下任一条件，优先判定为“新增用例”：
- 用户明确说“新增用例”“新建用例”“补一套新用例”
- 根据仓库检索结果，找不到对应 testcase md
- 根据 Jira 检索结果，找不到对应 `Test` issue

### 2. 读取规则与现状
必须读取：
- `QA-AGENTS/docs/qa/qa-rules.md`
- 对应模块 `docs/qa/rules/<module>-rules.md`
- 相关 `docs/qa/requirements/*.md`
- 同模块现有 testcase（用于复用风格、避免重复）

如用户提供 PR，还必须读取：
- PR 描述
- PR diff
- 命中的业务规则文件（token / chain / metadata / validate / config / feature flag）

### 3. 生成“变更计划预览”
预览至少包含：
- 识别模块
- 判定结果：新增用例
- 拟新增/更新的仓库文件
- 是否需要更新 module rules / requirements
- 是否需要新建 Jira Test issue
- 测试覆盖摘要（主流程 / 边界 / 异常 / 数据组合 / 回归点）

此阶段只预览，不落库、不建 Jira。

### 4. 用户确认后执行
确认后再执行：
1. 新建或补充 requirement 文档
2. 必要时更新模块 rules 文档
3. 新建 testcase md
4. 新建 Jira `Test` issue
5. 以 Jira 当前模板写入 description：
   - `# 标题` 对应为多个编号小节标题
   - 每个小节下使用 4 列表格：`优先级 | 场景 | 操作步骤 | 预期结果`
6. 若用户要求或当前流程需要，提交仓库分支并创建 PR

---

## Output Rules

### A. 预览阶段
默认先输出“变更计划预览”，建议结构：

```text
变更计划预览

1. 类型：新增用例
2. 模块：Perps
3. 主题：统一账户
4. 仓库文件：
- 新增 docs/qa/requirements/Perps-统一账户.md
- 更新 docs/qa/rules/perps-rules.md（如需要）
- 新增 docs/qa/testcases/cases/perps/YYYY-MM-DD_Perps-统一账户.md
5. Jira：新建 Test issue
6. 覆盖点：...
```

### B. 正式用例内容
生成的测试用例必须：
- 严格遵守 `qa-rules.md`
- 使用 Markdown 表格
- 表头固定：`| 优先级 | 场景 | 操作步骤 | 预期结果 |`
- 单元格内多行必须使用带序号的 `<br>`
- 预期结果只写可观察结果，禁用“正常 / 成功 / 符合预期 / 正确地”等词
- 文件内容不能包裹外层代码块；聊天窗口展示时若需要完整贴出，则必须放进单个 markdown 代码块

---

## Jira Rules

1. 新增场景默认创建 Jira `Test` 类型 issue。
2. description 采用 ADF 结构写入，不做简单字符串拼接。
3. description 结构保持为：
   - heading
   - table
   - rule
   - heading
   - table
4. 表头固定为：
   - 优先级
   - 场景
   - 操作步骤
   - 预期结果
5. 如果存在相近旧 issue，不要直接覆盖；先在预览中提示用户是否复用旧 issue。

---

## Distinction from “PR Regression Items”

- “根据 PR 生成测试项”：保持现有粗粒度输出风格，用于快速回归项。
- “新增测试用例”：必须更细，默认展开更多场景和数据覆盖，最终要能落仓库 md 与 Jira 表格。

---

## Checklist

执行前检查：
1. 已确认这是“新增”而不是“更新已有用例”。
2. 已读取 `QA-AGENTS/docs/qa/qa-rules.md` 与相关模块规则。
3. 若有 PR，已读取 PR 与命中的规则/配置文件。
4. 已先给用户预览，且拿到明确确认。
5. requirement / rules / testcase / Jira Test issue 四层维护关系已考虑完整。
6. Jira description 方案兼容 ADF 表格结构。
7. 用例覆盖深度已明显高于“测试项”，不是只复述 PR。
