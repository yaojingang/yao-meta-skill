#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
YAO_SKILL_PATH = "/Users/laoyao/AI Coding/03-Development/Skills/yao-meta-skill/SKILL.md"
OFFICIAL_SKILL_PATH = "/Users/laoyao/.codex/skills/.system/skill-creator/SKILL.md"
SEED = "blind-human-review-2026-06-29-v1"


CASES = [
    {
        "id": "case-01-support-triage",
        "title": "客服工单分诊 Skill",
        "scenario": "一个 B2B SaaS 团队每天都要处理客户工单：判断分类、紧急程度、起草首轮回复，并把账务、安全、故障类问题升级给对应负责人。他们希望把这个重复流程做成一个给支持团队使用的 Codex skill。",
        "user_prompt": "请把我们反复使用的客服工单分诊流程做成一个团队可复用的 skill。输入包括原始工单文本、客户等级、产品模块和近期故障记录。输出需要包含问题分类、紧急程度、首轮回复草稿、升级负责人和判断依据。不要把 PII 泄露到报告里。",
        "rubric": [
            "是否有清楚的触发边界和近邻排除。",
            "是否是可复用的 skill 包结构，而不只是一个提示词。",
            "是否定义了分类、紧急程度、回复、升级和证据的输出契约。",
            "是否处理 PII 和客户内容的隐私风险。",
            "是否有能发现错误升级和泛泛回复的评测方案。",
        ],
        "order": {"A": "official", "B": "yao"},
        "official": """## 建议 Skill：support-triage

### 目的
创建一个简洁的 skill，帮助 Codex 对 B2B SaaS 客服工单进行分诊，并起草首轮回复。

### 建议包结构
```
support-triage/
  SKILL.md
  agents/openai.yaml
  references/
    triage-taxonomy.md
    escalation-policy.md
```

### SKILL.md 草稿
```markdown
---
name: support-triage
description: 对 B2B SaaS 客服工单进行分诊并起草首轮回复。当用户提供原始工单文本、客户等级、产品模块、故障记录，或需要紧急程度、分类、升级建议时使用。
---

# 客服工单分诊

使用这个 skill 对入站工单分类、起草合适的首轮回复，并识别是否需要升级。

## 工作流
1. 阅读工单文本、客户等级、产品模块和近期故障记录。
2. 将工单归为一个主分类：账务、访问权限、缺陷、故障、功能请求、安全、数据/隐私、上手问题或其他。
3. 标记紧急程度：低、普通、高、严重。
4. 起草首轮回复：确认问题、只询问必要补充信息，并避免没有依据的承诺。
5. 对安全、隐私、严重故障、数据丢失或企业客户影响问题进行升级。
6. 汇报判断依据，但不要复制不必要的 PII。

## 输出格式
- 分类：
- 紧急程度：
- 首轮回复：
- 升级负责人：
- 判断依据：
- 缺失信息：

## 参考资料
- 分类规则见 `references/triage-taxonomy.md`。
- 升级标准见 `references/escalation-policy.md`。
```

### agents/openai.yaml
```yaml
display_name: 客服工单分诊
short_description: 对客服工单分类，并起草首轮回复。
default_prompt: 请分诊这个客服工单，并起草首轮回复。
```

### 资源
- `references/triage-taxonomy.md`：分类定义、紧急程度提示和示例。
- `references/escalation-policy.md`：升级负责人和升级标准。

### 验证
用账务、安全、故障和功能请求等代表性工单测试。确认输出会最小化 PII，并且严重问题会被升级。
""",
        "yao": """## Skill 包建议：support-triage

### 边界
负责重复出现的客服工单分诊：用户提供工单文本以及客户/产品上下文，需要结构化路由决策。不要用于一次性文案润色、泛泛的客服同理心训练、CRM 配置，或超出升级范围的法律/安全事件处置。

### 输出契约
这个 skill 必须返回：
- `category`
- `urgency`
- `first_response_draft`
- `escalation_owner`
- `evidence_used`
- `missing_information`
- `pii_handling_note`

### 包结构
```
support-triage/
  SKILL.md
  agents/interface.yaml
  references/
    triage-taxonomy.md
    escalation-policy.md
    privacy-redaction.md
  evals/
    trigger_cases.json
    output/
      cases.jsonl
      fixtures/
  reports/
    output-risk-profile.md
    output_quality_scorecard.md
```

### SKILL.md
```markdown
---
name: support-triage
description: 将重复出现的 B2B SaaS 客服工单分诊为分类、紧急程度、首轮回复、升级负责人、判断依据和缺失信息。当输入包含原始工单、客户等级、产品模块、故障记录或支持队列上下文时使用。不要用于一次性文案润色、CRM 设置、法律建议或最终安全事件处置。
---

# 客服工单分诊

## 工作流
1. 确认这是重复的工单分诊任务，而不是一次性文案润色。
2. 阅读工单文本、客户等级、产品模块和故障记录。
3. 使用 `references/triage-taxonomy.md` 判断分类和紧急程度。
4. 按 `references/escalation-policy.md` 检查升级标准。
5. 起草首轮回复：确认问题、避免无依据承诺，只请求最少的缺失信息。
6. 按 `references/privacy-redaction.md` 对 PII 做脱敏或摘要。
7. 严格按输出契约返回。

## 必填输出
使用这些字段：
- category
- urgency
- first_response_draft
- escalation_owner
- evidence_used
- missing_information
- pii_handling_note
```

### agents/interface.yaml
```yaml
display_name: 客服工单分诊
short_description: 对工单分类、起草首轮回复，并给出升级依据。
default_prompt: 请用分类、紧急程度、回复、升级负责人和依据来分诊这个客服工单。
```

### 评测用例
1. 企业客户在已知故障期间提交工单：必须标为 `critical`，并升级给 incident commander。
2. SMB 客户的账务困惑：不应过度升级。
3. 带客户邮箱和 token 片段的安全披露：必须脱敏 token，并升级安全团队。
4. 伪装成投诉的功能请求：应归类为功能请求，紧急程度为普通。
5. 近邻请求：“把这段回复改得更温和”不应触发包级分诊。

### 发布门禁
- 触发评测：正例、反例、近邻文案润色。
- 输出评测：首轮回复不能编造 SLA，升级必须匹配策略。
- 隐私检查：报告不能保存原始工单 PII。
- 审查备注：如果分类规则或升级负责人未提供，标记为 `missing evidence`，不要编造。

### 下一步
加入 3 个匿名工单 fixture，运行输出评测，并记录错误升级、泛泛回复和 PII 泄露的失败分类。
""",
    },
    {
        "id": "case-02-monthly-revenue-reconciliation",
        "title": "月度收入对账 Skill",
        "scenario": "一个财务运营团队每个月结账前都要比对 Stripe 导出、数据仓库发票 CSV 和人工调整表，找出金额、币种、发票和调整项的不一致。",
        "user_prompt": "请创建一个用于月度收入对账的可复用 skill。输入是 Stripe balance export CSV、warehouse invoice CSV 和 adjustments sheet。输出需要标出不一致项、解释可能原因，并生成可用于月结的摘要。准确性比速度更重要。",
        "rubric": [
            "是否识别出这是 file-backed 且准确性敏感的任务。",
            "是否定义了确定性脚本和资源边界。",
            "是否说明输入/输出 schema 与对账容差。",
            "是否包含 fixture 和失败用例验证。",
            "是否避免编造财务事实或隐藏未解决差异。",
        ],
        "order": {"A": "yao", "B": "official"},
        "official": """## 建议 Skill：revenue-reconciliation

### 目的
帮助 Codex 对 Stripe、数据仓库发票和人工调整表中的月度收入记录进行对账。

### 建议包结构
```
revenue-reconciliation/
  SKILL.md
  agents/openai.yaml
  scripts/
    reconcile_revenue.py
  references/
    csv-schema.md
```

### SKILL.md 草稿
```markdown
---
name: revenue-reconciliation
description: 对 Stripe balance export、warehouse invoice CSV 和调整表中的月度收入数据进行对账。当用户要求比较收入文件、找出不一致项或准备月结摘要时使用。
---

# 收入对账

## 工作流
1. 确认用户提供了 Stripe 导出、warehouse invoice CSV 和调整表。
2. 阅读 `references/csv-schema.md`，了解预期列。
3. 使用用户提供的文件运行 `scripts/reconcile_revenue.py`。
4. 审查不一致项，并总结可能原因。
5. 不要编造缺失值。清楚标记未解决记录。

## 输出
- 已检查文件
- 匹配总额
- 不一致项
- 可能原因
- 未解决项目
- 月结摘要
```

### 脚本
`scripts/reconcile_revenue.py` 应解析 CSV 输入，规范化 invoice ID 和币种，比较金额，并输出 JSON 供 Codex 总结。

### agents/openai.yaml
```yaml
display_name: 收入对账
short_description: 比对收入 CSV，并总结月结差异。
default_prompt: 请对这些收入文件进行对账，并生成月结摘要。
```

### 验证
使用包含匹配发票、缺失发票、重复发票和仅调整项记录的样例 CSV。确认未解决差异不会被隐藏。
""",
        "yao": """## Skill 包建议：revenue-reconciliation

### 边界
负责围绕 Stripe balance export、warehouse invoice CSV 和调整表的重复月结对账。排除税务建议、收入确认政策决策、支付渠道配置和一次性表格美化。

### 风险等级
Governed，file-backed，准确性敏感。任何可用于月结的结论前，都必须有确定性解析和可见的未解决项目。

### 包结构
```
revenue-reconciliation/
  SKILL.md
  agents/interface.yaml
  scripts/
    reconcile_revenue.py
    validate_reconciliation_fixture.py
  references/
    input-schema.md
    tolerance-policy.md
    close-summary-contract.md
  evals/
    output/
      cases.jsonl
      fixtures/
        stripe_sample.csv
        warehouse_sample.csv
        adjustments_sample.csv
  reports/
    output-risk-profile.md
    output_quality_scorecard.md
    trust_report.md
```

### SKILL.md
```markdown
---
name: revenue-reconciliation
description: 对来自 Stripe 导出、warehouse invoice CSV 和调整表的重复月结收入文件进行对账。用于 file-backed 差异检测、可能原因分析、未解决项目报告和月结摘要。不要用于收入确认建议、税务指导、支付渠道配置或一次性表格格式整理。
---

# 收入对账

## 工作流
1. 要求提供所有输入文件；缺失文件必须标记为 `missing evidence`。
2. 阅读 `references/input-schema.md`，先校验列再分析。
3. 运行 `scripts/reconcile_revenue.py`，规范化 ID、币种、金额精度、日期和调整项关联。
4. 审查 JSON 输出，并按缺失发票、金额差异、币种差异、重复项、时间差异或仅调整项分类。
5. 只基于脚本证据生成月结摘要。
6. 保持未解决差异可见。不要编造原因、审批或政策判断。

## 输出契约
- input_files
- validation_status
- totals_by_source
- matched_count
- mismatch_table
- likely_causes
- unresolved_items
- close_ready_summary
- missing_evidence
```

### 确定性脚本契约
`scripts/reconcile_revenue.py` 应接受：
```bash
python3 scripts/reconcile_revenue.py --stripe stripe.csv --warehouse warehouse.csv --adjustments adjustments.csv --output reconciliation.json
```

它应返回包含源行 ID 的结构化 JSON，让摘要里的每个结论都能追溯到 file-backed fixture。

### 评测
- Fixture 1：所有记录匹配。
- Fixture 2：Stripe 有付款，但 warehouse 缺发票。
- Fixture 3：warehouse 金额超过容差。
- Fixture 4：人工调整解释了差异。
- 近邻请求：“把这个表格弄好看一点”不应路由到这里。

### 门禁
- 汇总前必须通过输入 schema 校验。
- 如果遗漏未解决差异，输出评测必须失败。
- Trust check 应标记网络访问为不必要。
- Review Studio 应在晋级前显示 file-backed fixture 覆盖和未解决差异处理。
""",
    },
    {
        "id": "case-03-webinar-repurposing",
        "title": "Webinar 内容复用 Skill",
        "scenario": "一个市场团队经常把 webinar 逐字稿改写成 LinkedIn 帖子、邮件 teaser 和 newsletter 段落，同时必须保证所有说法都有来源，并避开禁止宣传的 claim。",
        "user_prompt": "请做一个可复用 skill，把 webinar 逐字稿复用成市场内容。输入包括逐字稿、讲者姓名、产品定位说明和禁止使用的 claim。输出包括 LinkedIn 帖子、邮件 teaser、newsletter 段落、可引用金句和来源依据说明。",
        "rubric": [
            "是否保留来源约束，并处理 banned claims。",
            "是否定义可重复的多渠道输出格式。",
            "是否把语气和定位资料放到 references，避免入口膨胀。",
            "是否有针对幻觉 claim 和泛泛市场文案的评测。",
            "是否在中等治理风险下保持 skill 足够轻量。",
        ],
        "order": {"A": "official", "B": "yao"},
        "official": """## 建议 Skill：webinar-repurposer

### 目的
创建一个 skill，把 webinar 逐字稿转成可复用的市场内容。

### 包结构
```
webinar-repurposer/
  SKILL.md
  agents/openai.yaml
  references/
    brand-voice.md
    banned-claims.md
```

### SKILL.md 草稿
```markdown
---
name: webinar-repurposer
description: 将 webinar 逐字稿复用成 LinkedIn 帖子、邮件 teaser、newsletter 段落、可引用金句和来源依据说明。当用户提供逐字稿、讲者、定位说明或禁止 claim 时使用。
---

# Webinar 内容复用

## 工作流
1. 阅读逐字稿、讲者姓名、产品定位说明和禁止 claim。
2. 提取核心主题、最强的来源支持观点和可用引语。
3. 起草一条 LinkedIn 帖子、一段邮件 teaser、一段 newsletter 和若干金句。
4. 对照逐字稿和禁止 claim 检查每个说法。
5. 为重要 claim 添加来源依据说明。

## 输出
- LinkedIn 帖子
- 邮件 teaser
- Newsletter 段落
- 可引用金句
- 来源依据说明
- 已避免的 claim

## 参考资料
语气见 `references/brand-voice.md`，禁止 claim 见 `references/banned-claims.md`。
```

### agents/openai.yaml
```yaml
display_name: Webinar 内容复用
short_description: 将 webinar 逐字稿转成有来源依据的市场内容。
default_prompt: 请把这份 webinar 逐字稿复用成可发布的多渠道市场内容。
```

### 验证
用包含强金句、证据较弱、以及容易误用禁止 claim 的逐字稿测试。确认输出会避免没有依据的 claim。
""",
        "yao": """## Skill 包建议：webinar-repurposer

### 边界
负责在提供来源逐字稿和定位约束时，把逐字稿复用为市场内容。排除全新 campaign strategy、没有依据的产品 claim、法律审核和一次性文案润色。

### 类型
Production-light。它需要输出质量检查和 banned-claim 防护，但除非涉及受监管 claim 或上市公司披露规则，否则不需要做成很重的 governed 包。

### 包结构
```
webinar-repurposer/
  SKILL.md
  agents/interface.yaml
  references/
    brand-voice.md
    positioning-notes.md
    banned-claims.md
  evals/
    output/
      cases.jsonl
  reports/
    output-risk-profile.md
    prompt-quality-profile.md
```

### SKILL.md
```markdown
---
name: webinar-repurposer
description: 将重复出现的 webinar 逐字稿复用为有来源依据的 LinkedIn 帖子、邮件 teaser、newsletter 段落、金句和 claim 依据说明。当提供逐字稿、讲者、定位说明或禁止 claim 时使用。不要用于无依据的发布 claim、法律审批、全新 campaign strategy 或一次性文案润色。
---

# Webinar 内容复用

## 工作流
1. 确认逐字稿是事实来源。
2. 提取有来源支持的主题、讲者背书的引语和可安全复用的 claim。
3. 起草前先检查 `references/banned-claims.md`。
4. 生成各渠道输出，但不要添加逐字稿中没有的性能数字、客户结果或产品承诺。
5. 添加来源依据说明，把每个主要 claim 绑定到逐字稿证据。

## 必填输出
- linkedin_post
- email_teaser
- newsletter_section
- pull_quotes
- source_grounding_notes
- claims_avoided
- missing_evidence
```

### 输出风险画像
常见失败：
- 生成任何产品都能用的泛泛市场话术。
- 编造指标或客户结果。
- 过度改写金句，导致意思偏离。
- 因为某个 claim 很有吸引力而忽略 banned claims。

### 输出评测用例
1. 逐字稿包含诱人的“guaranteed ROI”禁止 claim：输出必须避开。
2. 逐字稿没有量化证明：输出不能编造数字。
3. 讲者原话不够顺：可以轻微修语法，但必须保留原意。
4. 近邻请求：“从零写一个新 campaign idea”不应路由到这里。

### 审查门禁
- 必填 section 必须全部出现。
- Banned claim 检查必须显式出现。
- 来源依据说明必须引用逐字稿位置或原话片段。
- 缺失证据必须被标出，而不是用通用卖点填补。
""",
    },
    {
        "id": "case-04-incident-postmortem",
        "title": "故障复盘 Skill",
        "scenario": "一个基础设施团队经常把 Slack 故障时间线、告警数据和部署记录整理成故障复盘和后续行动项。",
        "user_prompt": "请创建一个可复用的 governed skill，用于故障复盘。输入包括告警时间线、Slack 摘要、部署记录、客户影响说明和负责人列表。输出应包含时间线、影响、根因假设、行动项、未解决证据和后续负责人矩阵。",
        "rubric": [
            "是否处理 governed/运营风险和未解决证据。",
            "是否区分假设和已确认根因。",
            "是否定义行动项负责人矩阵和回滚/跟进边界。",
            "是否要求 file-backed 或 source-backed 证据。",
            "是否有针对 blame language 和编造因果的审查门禁。",
        ],
        "order": {"A": "yao", "B": "official"},
        "official": """## 建议 Skill：incident-postmortem

### 目的
帮助 Codex 根据时间线、Slack 摘要、部署记录、影响说明和负责人列表创建结构化故障复盘。

### 包结构
```
incident-postmortem/
  SKILL.md
  agents/openai.yaml
  references/
    postmortem-template.md
    severity-policy.md
```

### SKILL.md 草稿
```markdown
---
name: incident-postmortem
description: 根据告警时间线、Slack 摘要、部署记录、客户影响说明和负责人列表创建故障复盘。当用户需要时间线、影响、根因假设、行动项、未解决证据或负责人矩阵时使用。
---

# 故障复盘

## 工作流
1. 收集告警时间线、Slack 摘要、部署记录、客户影响说明和负责人列表。
2. 建立按时间排序的时间线。
3. 总结客户和系统影响。
4. 识别已确认事实和根因假设。
5. 在提供负责人和截止时间时，起草行动项。
6. 清楚标记未解决证据。
7. 避免归责式语言。

## 输出
- 故障摘要
- 时间线
- 影响
- 根因假设
- 已确认事实
- 未解决证据
- 行动项
- 负责人矩阵
```

### agents/openai.yaml
```yaml
display_name: 故障复盘
short_description: 根据故障证据生成结构化复盘。
default_prompt: 请把这些故障证据整理成复盘和负责人矩阵。
```

### 验证
用证据完整、缺部署记录、Slack 说法冲突和暂时没有根因的 case 测试。确认 skill 会区分事实和假设。
""",
        "yao": """## Skill 包建议：incident-postmortem

### 边界
负责根据 source-backed 时间线、Slack 摘要、部署记录、客户影响说明和负责人列表起草 governed 故障复盘。不要用于实时 incident command、最终 RCA 签核、HR/归责分析或面向客户的法律声明。

### 类型
Governed。这个包会影响运营责任归属，如果证据不足，容易制造虚假因果。

### 包结构
```
incident-postmortem/
  SKILL.md
  agents/interface.yaml
  references/
    postmortem-contract.md
    severity-policy.md
    blame-free-language.md
    action-owner-matrix.md
  evals/
    output/
      cases.jsonl
      fixtures/
        alert_timeline.json
        slack_summary.md
        deploy_notes.md
  reports/
    output-risk-profile.md
    output_quality_scorecard.md
    trust_report.md
    review-studio.html
```

### SKILL.md
```markdown
---
name: incident-postmortem
description: 根据告警时间线、Slack 摘要、部署记录、影响说明和负责人列表起草 governed 故障复盘。用于 source-backed 时间线重建、影响总结、根因假设、行动项、未解决证据和后续负责人矩阵。不要用于实时故障指挥、最终 RCA 审批、归责或法律/客户承诺。
---

# 故障复盘

## 工作流
1. 要求提供 source-backed 故障输入，并把缺失输入列为 `missing evidence`。
2. 只根据已提供时间戳建立时间线；如需推断顺序，必须明确标注。
3. 分开列出 `confirmed_facts`、`root_cause_hypotheses` 和 `unresolved_evidence`。
4. 总结客户影响，但不要编造受影响账户、持续时间或 SLA 违约。
5. 创建行动项：包含 owner、due date、验证信号和回滚/跟进边界。
6. 使用 `references/blame-free-language.md` 的无责语言。
7. 除非 reviewer 明确提供，否则最终 RCA 审批不属于本 skill。

## 输出契约
- incident_summary
- source_inputs
- timeline
- customer_impact
- confirmed_facts
- root_cause_hypotheses
- unresolved_evidence
- action_items
- owner_matrix
- approval_status
```

### 输出评测用例
1. Slack 和部署记录冲突：必须保留为未解决证据。
2. 告警时间线缺恢复时间：不能编造持续时长。
3. 用户要求实时故障决策：应路由出去，或说明本 skill 只做复盘。
4. 来源材料带有归责语言：输出必须改写为系统/流程语言。
5. 缺负责人列表：行动项 owner 字段应为 `missing evidence`。

### 门禁
- 时间线和部署记录需要 file-backed fixture 覆盖。
- 输出评测禁止编造因果和隐藏未解决证据。
- Review Studio 在人工 reviewer 审批行动负责人矩阵前保持 warning。
- Trust report 应显示无网络和无破坏性操作。
""",
    },
    {
        "id": "case-05-pr-review-followup",
        "title": "PR Review 跟进 Skill",
        "scenario": "一个小工程团队经常收到 GitHub PR review comments，希望 Codex 能把评论转成补丁、回复摘要和验证记录。",
        "user_prompt": "请设计一个用于处理 PR review comments 的可复用 skill。输入包括 review comments、变更文件、失败 CI 说明和 maintainer preferences。输出需要分组评论、只修改相关文件、写回复说明并运行验证。必须避免回滚无关的用户改动。",
        "rubric": [
            "是否理解 code-review 跟进和 dirty worktree 安全。",
            "是否定义评论分组、补丁、回复和验证工作流。",
            "是否避免过度重构和无关 revert。",
            "是否说明变更后需要的命令和证据。",
            "是否定义一般 code review 与评论跟进的触发排除。",
        ],
        "order": {"A": "official", "B": "yao"},
        "official": """## 建议 Skill：pr-review-followup

### 目的
创建一个 skill，帮助 Codex 安全处理 PR review comments，并总结回复。

### 包结构
```
pr-review-followup/
  SKILL.md
  agents/openai.yaml
  references/
    response-style.md
```

### SKILL.md 草稿
```markdown
---
name: pr-review-followup
description: 通过分组反馈、修改相关文件、编写回复说明和运行验证来处理 GitHub PR review comments。当用户提供 review comments、变更文件、CI 说明或 maintainer preferences 时使用。
---

# PR Review 跟进

## 工作流
1. 阅读所有 review comments，并按文件、主题和严重程度分组。
2. 编辑前检查受影响文件。
3. 只修改处理 comments 所需的文件。
4. 不要回滚无关用户改动。
5. 运行相关测试或 CI 复现命令。
6. 总结变更，并为 reviewer 起草回复说明。

## 输出
- 评论分组
- 修改文件
- 验证命令
- Reviewer 回复说明
- 剩余问题
```

### agents/openai.yaml
```yaml
display_name: PR Review 跟进
short_description: 处理 PR comments 并准备 reviewer 回复。
default_prompt: 请处理这些 PR review comments，并总结验证结果。
```

### 验证
用需要代码修改、文档修改、无需修改只需解释、以及 reviewer 要求冲突的 comments 测试。
""",
        "yao": """## Skill 包建议：pr-review-followup

### 边界
负责 PR 已经有明确 reviewer comments、变更文件或 CI 说明之后的评论跟进。排除首次 code review、大范围重构、issue triage，以及没有绑定评论的推测性清理。

### 包结构
```
pr-review-followup/
  SKILL.md
  agents/interface.yaml
  references/
    response-style.md
    dirty-worktree-safety.md
    verification-policy.md
  evals/
    trigger_cases.json
    output/
      cases.jsonl
  reports/
    output-risk-profile.md
    output_quality_scorecard.md
```

### SKILL.md
```markdown
---
name: pr-review-followup
description: 处理具体 PR review comments：分组反馈、只修改相关文件、保留无关用户改动、起草 reviewer 回复并运行验证。当提供 review comments、变更文件、失败 CI 说明或 maintainer preferences 时使用。不要用于首次 code review、大范围重构、issue triage 或无关清理。
---

# PR Review 跟进

## 工作流
1. 编辑前记录 git status，并识别用户已经改动的文件。
2. 按文件、行为、严重程度，以及是否需要代码、测试、文档或仅解释来分组 review comments。
3. 修改前阅读受影响代码和附近测试。
4. 只修改与评论绑定的文件。不要回滚无关改动，也不要格式化未触碰文件。
5. 运行有针对性的验证，并记录命令和结果。
6. 起草 reviewer 回复说明，把每组评论映射到变更、无需修改的理由或剩余问题。
7. 如果评论冲突，停止并询问哪个 reviewer 指令优先。

## 输出契约
- comment_groups
- patch_summary
- files_changed
- verification
- reviewer_response_notes
- unresolved_questions
- unrelated_changes_preserved
```

### 输出评测用例
1. 评论要求添加特定 null check：输出必须只修改受影响函数，并提到测试。
2. Reviewer 要求与 PR 范围无关的大重构：输出应标出范围风险。
3. Dirty worktree 中有无关用户文件：输出必须保留它。
4. 两个 reviewer comments 冲突：输出必须询问优先级，而不是猜。
5. 近邻请求：“从零 review 这个 PR”不应触发 follow-up mode。

### 门禁
- 触发评测必须区分首次 review 和评论跟进。
- 如果回滚或隐藏无关改动，输出评测必须失败。
- 验证策略必须记录跳过测试的原因。
- 回复说明必须能追溯到评论分组。
""",
    },
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def md_to_html(text: str) -> str:
    lines = []
    in_code = False
    in_list = False
    code_lines = []
    def close_list() -> None:
        nonlocal in_list
        if in_list:
            lines.append("</ul>")
            in_list = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                lines.append("<pre><code>" + esc("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                close_list()
                in_code = True
            continue
        if in_code:
            code_lines.append(raw)
            continue
        if not line:
            close_list()
            lines.append("")
        elif line.startswith("### "):
            close_list()
            lines.append(f"<h3>{esc(line[4:])}</h3>")
        elif line.startswith("## "):
            close_list()
            lines.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("# "):
            close_list()
            lines.append(f"<h1>{esc(line[2:])}</h1>")
        elif line.startswith("- "):
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{esc(line[2:])}</li>")
        else:
            close_list()
            lines.append(f"<p>{esc(line)}</p>")
    if in_code:
        lines.append("<pre><code>" + esc("\n".join(code_lines)) + "</code></pre>")
    close_list()
    html_text = "\n".join(lines)
    return html_text


def base_css() -> str:
    return """
:root {
  color-scheme: light;
  --bg: #f7f8fb;
  --panel: #ffffff;
  --ink: #20242c;
  --muted: #687082;
  --line: #d9deea;
  --accent: #2563eb;
  --accent-2: #0f766e;
  --warn: #b45309;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--ink);
  line-height: 1.55;
}
header {
  padding: 28px clamp(18px, 4vw, 52px) 18px;
  background: #ffffff;
  border-bottom: 1px solid var(--line);
}
main { padding: 24px clamp(18px, 4vw, 52px) 52px; }
h1 { margin: 0 0 8px; font-size: clamp(26px, 3vw, 38px); letter-spacing: 0; }
h2 { margin: 0 0 12px; font-size: 20px; }
h3 { margin: 18px 0 8px; font-size: 16px; }
p { margin: 0 0 10px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.meta, .note { color: var(--muted); }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; align-items: start; }
.card, .panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 18px;
}
.case-list { display: grid; gap: 12px; margin-top: 18px; }
.case-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: center;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px 16px;
}
.badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #e8f0ff;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 650;
}
.rubric { margin: 0; padding-left: 20px; }
.rubric li { margin-bottom: 6px; }
.variant {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}
.variant-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  background: #f2f5fa;
}
.variant-body { padding: 16px; }
pre {
  overflow: auto;
  padding: 12px;
  border-radius: 6px;
  background: #111827;
  color: #f9fafb;
  font-size: 13px;
}
code { font-family: "SFMono-Regular", Consolas, monospace; }
.review-box {
  margin-top: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}
.controls { display: flex; flex-wrap: wrap; gap: 10px; margin: 12px 0; }
button, .button {
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--ink);
  min-height: 36px;
  padding: 7px 12px;
  cursor: pointer;
  font-weight: 650;
}
button.primary, .button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
textarea {
  width: 100%;
  min-height: 96px;
  resize: vertical;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 10px;
  font: inherit;
}
.warn { color: var(--warn); font-weight: 650; }
.split { display: flex; flex-wrap: wrap; gap: 10px; }
.small { font-size: 13px; }
@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; }
  .case-row { grid-template-columns: 1fr; }
}
"""


def case_filename(case: dict) -> str:
    return f"{case['id']}.html"


def variant_html(case: dict, label: str) -> str:
    source = case["order"][label]
    content = case[source]
    return f"""
<section class="variant">
  <div class="variant-head">
    <h2>方案 {label}</h2>
    <span class="badge">来源已隐藏</span>
  </div>
  <div class="variant-body">
    {md_to_html(content)}
  </div>
</section>
"""


def render_case(case: dict, previous_link: str | None, next_link: str | None) -> str:
    rubric_items = "\n".join(f"<li>{esc(item)}</li>" for item in case["rubric"])
    nav = ["<a class=\"button\" href=\"index.html\">返回入口</a>"]
    if previous_link:
        nav.append(f"<a class=\"button\" href=\"{esc(previous_link)}\">上一个</a>")
    if next_link:
        nav.append(f"<a class=\"button\" href=\"{esc(next_link)}\">下一个</a>")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(case['title'])} - Skill 盲测评审</title>
  <style>{base_css()}</style>
</head>
<body data-case-id="{esc(case['id'])}">
  <header>
    <div class="split">{''.join(nav)}</div>
    <h1>{esc(case['title'])}</h1>
    <p class="meta">A/B 盲测评审。记录完判断前，不要打开答案钥匙。</p>
  </header>
  <main>
    <section class="panel">
      <h2>场景</h2>
      <p>{esc(case['scenario'])}</p>
      <h3>用户请求</h3>
      <p>{esc(case['user_prompt'])}</p>
      <h3>评审标准</h3>
      <ol class="rubric">{rubric_items}</ol>
    </section>

    <div class="grid" style="margin-top:18px">
      {variant_html(case, "A")}
      {variant_html(case, "B")}
    </div>

    <section class="review-box">
      <h2>你的判断</h2>
      <p class="note">只根据评审标准和页面里可见的两个输出做判断。选择会保存到当前浏览器的本地存储里，也可以回到入口页导出。</p>
      <div class="controls" role="radiogroup" aria-label="胜出方案">
        <label><input type="radio" name="winner" value="A"> 方案 A 更好</label>
        <label><input type="radio" name="winner" value="B"> 方案 B 更好</label>
        <label><input type="radio" name="winner" value="tie"> 平局 / 没有明显胜出</label>
      </div>
      <label for="confidence">信心程度</label>
      <div class="controls">
        <select id="confidence">
          <option value="">请选择</option>
          <option value="0.4">0.4，较弱</option>
          <option value="0.6">0.6，中等</option>
          <option value="0.8">0.8，较强</option>
          <option value="1.0">1.0，非常确定</option>
        </select>
      </div>
      <label for="reason">理由</label>
      <textarea id="reason" placeholder="为什么这个方案更好？请写出具体的评审标准差异。"></textarea>
      <div class="controls">
        <button class="primary" type="button" onclick="saveDecision()">保存判断</button>
        <button type="button" onclick="clearDecision()">清空</button>
      </div>
      <p id="save-status" class="small note"></p>
    </section>
  </main>
  <script>
const caseId = document.body.dataset.caseId;
const key = "blindSkillReview:" + caseId;
function currentDecision() {{
  const selected = document.querySelector('input[name="winner"]:checked');
  return {{
    case_id: caseId,
    winner_variant: selected ? selected.value : "",
    confidence: document.getElementById("confidence").value,
    reason: document.getElementById("reason").value.trim(),
    reviewed_at: new Date().toISOString()
  }};
}}
function saveDecision() {{
  const decision = currentDecision();
  localStorage.setItem(key, JSON.stringify(decision));
  document.getElementById("save-status").textContent = "已保存：" + decision.reviewed_at;
}}
function clearDecision() {{
  localStorage.removeItem(key);
  document.querySelectorAll('input[name="winner"]').forEach(el => el.checked = false);
  document.getElementById("confidence").value = "";
  document.getElementById("reason").value = "";
  document.getElementById("save-status").textContent = "已清空。";
}}
function loadDecision() {{
  const raw = localStorage.getItem(key);
  if (!raw) return;
  const decision = JSON.parse(raw);
  const selected = document.querySelector('input[name="winner"][value="' + decision.winner_variant + '"]');
  if (selected) selected.checked = true;
  document.getElementById("confidence").value = decision.confidence || "";
  document.getElementById("reason").value = decision.reason || "";
  document.getElementById("save-status").textContent = "已加载保存过的判断。";
}}
loadDecision();
  </script>
</body>
</html>
"""


def render_index() -> str:
    rows = []
    for index, case in enumerate(CASES, start=1):
        rows.append(
            f"""
<div class="case-row">
  <div>
    <div class="badge">案例 {index}</div>
    <h2 style="margin-top:10px">{esc(case['title'])}</h2>
    <p class="meta">{esc(case['scenario'])}</p>
  </div>
  <a class="button primary" href="{esc(case_filename(case))}">打开报告</a>
</div>
"""
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>人工盲测评审包 - Meta Skill 对比</title>
  <style>{base_css()}</style>
</head>
<body>
  <header>
    <h1>人工盲测评审包</h1>
    <p class="meta">5 个真实常见的 skill 创建场景。打开答案钥匙前，方案来源都会保持隐藏。</p>
  </header>
  <main>
    <section class="panel">
      <h2>评审说明</h2>
      <p>依次打开每个案例，按评审标准比较方案 A 和方案 B，保存胜出方案和理由，然后回到这里导出判断结果。5 个判断全部保存前，不要打开 <code>DO_NOT_OPEN_answer_key.html</code> 或 <code>DO_NOT_OPEN_answer_key.json</code>。</p>
      <p class="warn">证据边界：这些输出是 Codex 在本地套用两份 skill 说明生成的，适合做人类盲测评审，但不能冒充 provider-backed 的独立模型执行证据。</p>
      <div class="controls">
        <button class="primary" type="button" onclick="exportDecisions()">导出已保存判断</button>
        <a class="button" href="review-decisions-template.json">判断模板</a>
        <a class="button" href="blind-pack.json">盲测包 JSON</a>
      </div>
      <textarea id="export" placeholder="导出的判断结果会显示在这里。"></textarea>
    </section>
    <section class="case-list">
      {''.join(rows)}
    </section>
  </main>
  <script>
const caseIds = {json.dumps([case["id"] for case in CASES])};
function exportDecisions() {{
  const decisions = caseIds.map(id => {{
    const raw = localStorage.getItem("blindSkillReview:" + id);
    return raw ? JSON.parse(raw) : {{ case_id: id, winner_variant: "", confidence: "", reason: "", reviewed_at: "" }};
  }});
  const payload = {{
    schema_version: "1.0",
    review_pack: "blind-human-review-2026-06-29",
    reviewer: "",
    blind_review_attestation: {{
      answer_key_not_opened_before_decisions: false,
      completed_before_answer_key: false
    }},
    decisions
  }};
  document.getElementById("export").value = JSON.stringify(payload, null, 2);
}}
  </script>
</body>
</html>
"""


def render_answer_key() -> str:
    rows = []
    source_labels = {"yao": "yao-meta-skill", "official": "官方 skill-creator"}
    for case in CASES:
        rows.append(
            f"<tr><td>{esc(case['id'])}</td><td>{esc(source_labels[case['order']['A']])}</td><td>{esc(source_labels[case['order']['B']])}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>答案钥匙 - Skill 盲测评审</title>
  <style>{base_css()} table {{ width:100%; border-collapse: collapse; }} td, th {{ border:1px solid var(--line); padding:8px; text-align:left; }}</style>
</head>
<body>
  <header>
    <a class="button" href="index.html">返回入口</a>
    <h1>答案钥匙</h1>
    <p class="warn">请只在所有评审判断都记录完成后再打开。</p>
  </header>
  <main>
    <section class="panel">
      <table>
        <thead><tr><th>案例</th><th>方案 A 来源</th><th>方案 B 来源</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      <p class="note" style="margin-top:12px">来源路径：yao-meta-skill = {esc(YAO_SKILL_PATH)}；官方 skill-creator = {esc(OFFICIAL_SKILL_PATH)}。</p>
    </section>
  </main>
</body>
</html>
"""


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_html(path: Path, text: str) -> None:
    normalized = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    path.write_text(normalized, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for index, case in enumerate(CASES):
        previous_link = case_filename(CASES[index - 1]) if index > 0 else None
        next_link = case_filename(CASES[index + 1]) if index < len(CASES) - 1 else None
        write_html(OUT_DIR / case_filename(case), render_case(case, previous_link, next_link))
    write_html(OUT_DIR / "index.html", render_index())
    write_html(OUT_DIR / "DO_NOT_OPEN_answer_key.html", render_answer_key())

    blind_cases = []
    answer_key = []
    for case in CASES:
        blind_cases.append(
            {
                "id": case["id"],
                "title": case["title"],
                "scenario": case["scenario"],
                "user_prompt": case["user_prompt"],
                "rubric": case["rubric"],
                "variants": {
                    "A": case[case["order"]["A"]],
                    "B": case[case["order"]["B"]],
                },
                "html_report": case_filename(case),
            }
        )
        answer_key.append(
            {
                "case_id": case["id"],
                "variant_a_source": case["order"]["A"],
                "variant_b_source": case["order"]["B"],
                "variant_a_source_label": "yao-meta-skill" if case["order"]["A"] == "yao" else "官方 skill-creator",
                "variant_b_source_label": "yao-meta-skill" if case["order"]["B"] == "yao" else "官方 skill-creator",
                "source_paths": {
                    "yao": YAO_SKILL_PATH,
                    "official": OFFICIAL_SKILL_PATH,
                },
            }
        )

    write_json(
        OUT_DIR / "blind-pack.json",
        {
            "schema_version": "1.0",
            "seed": SEED,
            "generated_by": "Codex 在本地套用两份 skill 说明生成",
            "evidence_boundary": "人类盲测评审起始包；不是 provider-backed 的独立模型执行证据。",
            "cases": blind_cases,
        },
    )
    write_json(
        OUT_DIR / "DO_NOT_OPEN_answer_key.json",
        {
            "schema_version": "1.0",
            "seed": SEED,
            "answer_key_warning": "请只在记录完所有判断后再打开。",
            "answers": answer_key,
        },
    )
    write_json(
        OUT_DIR / "review-decisions-template.json",
        {
            "schema_version": "1.0",
            "review_pack": "blind-human-review-2026-06-29",
            "reviewer": "",
            "reviewed_at": "",
            "blind_review_attestation": {
                "answer_key_not_opened_before_decisions": False,
                "completed_before_answer_key": False,
            },
            "decisions": [
                {
                    "case_id": case["id"],
                    "winner_variant": "",
                    "confidence": "",
                    "reason": "",
                }
                for case in CASES
            ],
        },
    )
    print(f"已写入盲测评审包：{OUT_DIR}")


if __name__ == "__main__":
    main()
