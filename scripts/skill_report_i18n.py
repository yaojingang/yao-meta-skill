"""Bilingual text helpers for the static skill overview report."""

import html
import re


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_skill_overview.py to keep bilingual report copy and fallback rules out of HTML rendering."


TEXT_ZH = {
    "Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use when asked to create a skill, turn a repeated process into a reusable skill, improve an existing skill, add evals, or package a skill for team reuse.": "从工作流、提示词、对话记录、文档或笔记中创建、重构、评估和打包 agent skill；适用于新建 Skill、沉淀重复流程、改进现有 Skill、补充 eval 或团队复用打包。",
    "Understand the request.": "理解用户请求。",
    "Execute the main task.": "执行核心任务。",
    "Validate the result.": "校验交付结果。",
    "Understand the request": "理解用户请求。",
    "Execute the main task": "执行核心任务。",
    "Validate the result": "校验交付结果。",
    "Decide whether the request should become a skill and choose the lightest fit.": "判断请求是否应该沉淀为 Skill，并选择最轻量可靠的模式。",
    "Capture job, output, exclusions, constraints, and standards.": "捕捉任务、输出、排除项、约束和质量标准。",
    "Run reference scan: external benchmarks first, user references second, local fit third; surface only uncertainty or conflict.": "运行参考扫描：先看外部 benchmark，再看用户材料，最后校验本地适配；只暴露不确定性或冲突。",
    "Write the `description` early and test route quality before expanding the package.": "尽早写出 `description`，先测试路由质量，再扩展包体。",
    "Add output-risk, artifact-design, prompt-quality, and system-model reports only when they matter.": "只在确有价值时添加 output-risk、artifact-design、prompt-quality 和 system-model 报告。",
    "Use $yao-meta-skill to turn my workflow or notes into a reusable skill with lean structure, clear triggering, and the right evals.": "当你需要把工作流或笔记沉淀成结构精简、触发清晰且带必要 eval 的可复用 Skill 时使用 $yao-meta-skill。",
    "Turn rough requests into a compact reusable demo skill.": "把粗糙请求整理成紧凑、可复用的演示 Skill。",
    "Tighten trigger and exclusions": "收紧触发与排除边界",
    "Add the first execution asset": "补上第一个执行资产",
    "Promote from scaffold to production-ready": "从脚手架推进到生产可用",
    "Borrow one proven pattern on purpose": "有选择地借鉴一个成熟模式",
    "Harden portability semantics": "加固跨环境语义",
    "Create an iteration evidence loop": "建立迭代证据回路",
    "补齐世界证据": "补齐世界证据",
    "The package needs clearer near-neighbor exclusions before it grows.": "在继续扩展前，需要先把相邻但不应触发的场景说清楚。",
    "The package is still mostly prose. Add one asset that removes repeated manual work.": "当前包体仍偏文本说明，应先增加一个能减少重复人工操作的资产。",
    "The first version exists; the next gain usually comes from adding the smallest useful gates.": "第一版已经存在，下一步收益通常来自补上最小但有效的质量门禁。",
    "You already have public benchmark objects. The next gain is to choose one pattern intentionally instead of absorbing everything loosely.": "已经有公开 benchmark 对象，下一步应主动选择一个模式借鉴，而不是松散吸收所有做法。",
    "The skill already signals reuse across environments, so contract clarity matters early.": "这个 Skill 已经面向跨环境复用，因此早期就需要把契约语义说清楚。",
    "The package should show what changed and why after the first draft.": "第一版之后，包体应该能说明改了什么以及为什么改。",
    "Add 3 to 5 should-trigger and should-not-trigger examples.": "增加 3 到 5 个应触发和不应触发的例子。",
    "Refine the frontmatter description to name the recurring job and non-goals.": "精炼 frontmatter description，明确重复任务和非目标。",
    "Run a first trigger evaluation pass before expanding the package.": "扩展包体前先跑一轮触发评估。",
    "Move stable procedural guidance into references if users will need it repeatedly.": "如果用户会反复使用某段流程说明，把它沉淀到 references。",
    "Create one deterministic helper script if a repeated step can be executed instead of described.": "如果某个重复步骤可以执行而不是描述，就沉淀成一个确定性 helper script。",
    "Keep the main SKILL.md compact and route-oriented.": "保持主 SKILL.md 简洁，并围绕路由与入口组织。",
    "Decide whether this skill is personal, team-reused, or library-grade.": "判断这个 Skill 是个人使用、团队复用，还是库级基础能力。",
    "Add only the gates that match that risk level.": "只添加与风险等级匹配的质量门禁。",
    "Record lifecycle metadata and review cadence once reuse becomes real.": "一旦进入真实复用，就记录生命周期元数据和评审节奏。",
    "Decide whether to borrow method, structure, execution, or portability, but only one of them first.": "先判断要借鉴的是方法、结构、执行方式还是可迁移性，并且第一轮只借鉴其中一个。",
    "Record what you will not borrow so the package stays light.": "记录本轮不借鉴的内容，避免包体过重。",
    "Confirm activation mode, execution context, and trust assumptions.": "确认激活模式、执行上下文和信任假设。",
    "Add or review degradation strategy for non-native targets.": "补充或复核非原生目标端的降级策略。",
    "Package the skill once to verify adapter expectations.": "至少打包一次 Skill，用来验证 adapter 预期。",
    "Generate the HTML skill report and keep it aligned with the package.": "生成 HTML Skill 报告，并保持它与包体内容一致。",
    "Record reference scan choices and non-goals.": "记录参考扫描的取舍和非目标。",
    "Capture the next iteration choice explicitly before adding more files.": "在继续增加文件前，明确记录下一轮迭代选择。",
    "Cleaner routing and fewer accidental activations.": "路由更清晰，误触发更少。",
    "Stronger execution quality without bloating the entrypoint.": "在不膨胀入口文件的前提下提升执行质量。",
    "A clearer path from exploratory package to maintained asset.": "更清晰地从探索性包体走向可维护资产。",
    "A cleaner package shape with less accidental over-design.": "包体形态更清晰，也减少偶然过度设计。",
    "Safer cross-environment reuse with less target drift.": "跨环境复用更安全，目标漂移更少。",
    "A clearer path for the next author or reviewer.": "让下一位作者或评审者更容易接手。",
    "提交有效 intake packet，并让 ledger 通过 artifact SHA-256 校验。": "提交有效 intake packet，并让 ledger 通过 artifact SHA-256 校验。",
    "全部外部/人工证据被 ledger 接受后，才能进入公开 world-class claim 复核。": "全部外部/人工证据被 ledger 接受后，才能进入公开 world-class claim 复核。",
}

TEXT_EN = {
    "把一次性经验沉淀为可复用、可评估、可迁移的 Skill 包体。": "Turn one-off experience into a reusable, evaluable, and portable skill package.",
    "Skill 作者、复用团队和后续 reviewer。": "Skill authors, reuse teams, and later reviewers.",
    "创建完成后建议先打开 reports/skill-overview.html，再继续扩展包体。": "After creation, open reports/skill-overview.html before expanding the package further.",
    "触发面保持精简，并锚定在 frontmatter description。": "The trigger surface stays lean and anchored in the frontmatter description.",
    "已生成 Skill IR，核心语义可先于平台打包被审查和迁移。": "Skill IR is generated so core semantics can be reviewed and migrated before platform packaging.",
    "已生成目标编译报告，可审查 IR 到 OpenAI、Claude、generic 等目标契约的映射。": "Target compilation evidence is generated to review how IR maps to OpenAI, Claude, generic, and other target contracts.",
    "已生成 Output Eval Lab scorecard，可比较 with-skill 与 baseline 输出质量。": "Output Eval Lab scorecard is generated to compare with-skill and baseline output quality.",
    "已生成 Output Execution Runs，可区分记录样本、命令执行和模型执行证据。": "Output Execution Runs is generated to distinguish recorded fixtures, command runs, and model-run evidence.",
    "已生成 Output Review Adjudication，可记录盲评决策、一致率和待评审项。": "Output Review Adjudication is generated to record blind-review decisions, agreement rate, and pending cases.",
    "已生成 Runtime Conformance Matrix，可审查目标端消费能力。": "Runtime Conformance Matrix is generated to review target-side consumption capability.",
    "已生成 Security Trust Report，可审查脚本、依赖、secret 和包完整性风险。": "Security Trust Report is generated to review scripts, dependencies, secrets, and package-integrity risk.",
    "已生成 Skill Atlas，可审查多 Skill 组合中的路由冲突、过期资产和 owner 缺口。": "Skill Atlas is generated to review route collisions, stale assets, and owner gaps across a skill library.",
    "已生成 Registry Audit，可审查版本、owner、license、checksum 和目标兼容矩阵。": "Registry Audit is generated to review version, owner, license, checksum, and target compatibility metadata.",
    "已生成 Install Simulation，可审查 zip 解压、入口加载、接口元数据和 adapter 可读性。": "Install Simulation is generated to review zip extraction, entrypoint loading, interface metadata, and adapter readability.",
    "已生成 Adoption Drift Report，可把本地使用反馈转为下一轮迭代信号。": "Adoption Drift Report is generated to turn local usage feedback into next-iteration signals.",
    "已生成 Review Waivers 台账，可记录 reviewer 对 warning 风险的批准、理由和到期时间。": "Review Waivers ledger is generated to record reviewer approval, rationale, scope, and expiry for accepted warning risk.",
    "已生成 Review Annotations 台账，可把 reviewer 批注挂到 gate、文件和行号。": "Review Annotations ledger is generated to attach reviewer notes to gates, files, and line numbers.",
    "已生成 Review Studio 2.0，可在一页中查看 blocker、warning、证据路径和发布闸门。": "Review Studio 2.0 is generated to inspect blockers, warnings, evidence paths, and release gates on one page.",
    "已打包 agents/interface.yaml，便于后续做跨平台适配。": "Portable interface metadata is packaged for later adapter-based export.",
    "长指导被拆到 references 中，入口文件可以保持轻量。": "Extended guidance is separated into references so the entrypoint can stay compact.",
    "确定性辅助逻辑放在 scripts 中，而不是藏在提示词里。": "Deterministic helper logic lives in scripts instead of hidden prompt text.",
    "包内包含可随 Skill 迁移的质量门禁或触发检查。": "The package includes portable quality gates or trigger checks.",
    "这份报告用于快速理解新生成 Skill 的定位、原理、触发边界和交付内容。": "Use this report to quickly understand the generated skill's role, principles, trigger boundary, and deliverables.",
    "先确认重复任务、真实输入形态和可交付输出，再决定是否继续加 references、scripts 或 evals。": "Clarify the recurring job, real input shape, and deliverable output before adding references, scripts, or evals.",
    "如果需求仍然模糊，优先回到 intent dialogue 收紧边界，再扩展包体结构。": "If the request is still fuzzy, tighten the boundary through intent dialogue before expanding the package.",
    "尚未生成盲评审定报告。": "The blind review adjudication report has not been generated yet.",
    "尚未生成输出执行证据报告。": "The output execution evidence report has not been generated yet.",
    "先记录 reviewer 对 A/B 的选择，再打开答案 key 计算一致率。": "Record the reviewer's A/B choice before opening the answer key and calculating agreement.",
    "缺少真实 reviewer 决策时只显示待评审，不伪造人工结论。": "When real reviewer decisions are missing, show pending status instead of fabricating human conclusions.",
    "recorded fixture 只能证明可复现样本，不等同于模型执行。": "A recorded fixture proves reproducible samples only; it is not model execution.",
    "只有 provider runner 返回 model metadata 时才计入 model-executed。": "Only provider runners that return model metadata count as model-executed.",
    "SKILL.md 已存在，是 Skill 的入口。": "SKILL.md exists and acts as the skill entrypoint.",
    "README.md 已存在，便于人工阅读。": "README.md exists for human-readable usage.",
    "agents/interface.yaml 已存在，便于跨平台适配。": "agents/interface.yaml exists for cross-platform adaptation.",
    "manifest.json 已存在，生命周期信息可追踪。": "manifest.json exists so lifecycle metadata is traceable.",
    "reports/ 已存在，生成证据可以随包体迁移。": "reports/ exists so generated evidence can travel with the package.",
    "references/ 已存在，长指导可以从入口文件拆出。": "references/ exists so long guidance can stay out of the entrypoint.",
    "scripts/ 已存在，确定性逻辑有位置承载。": "scripts/ exists to hold deterministic logic.",
    "evals/ 已存在，触发或质量检查可以随包体迁移。": "evals/ exists so trigger or quality checks can travel with the package.",
    "frontmatter description 已存在，具备基础路由面。": "The frontmatter description exists, giving the skill a basic routing surface.",
    "description 有足够长度说明任务边界。": "The description is long enough to explain the task boundary.",
    "description 已包含使用场景或排除边界信号。": "The description includes usage-scenario or exclusion-boundary signals.",
    "evals/ 已存在，可承载触发样例或质量检查。": "evals/ exists and can hold trigger examples or quality checks.",
    "intent-confidence 报告已生成，可辅助判断触发稳定性。": "The intent-confidence report exists and helps judge trigger stability.",
    "入口文件保持克制，可维护性较好。": "The entrypoint stays restrained, which supports maintainability.",
    "references/ 已承载扩展指导。": "references/ carries extended guidance.",
    "scripts/ 已承载确定性逻辑。": "scripts/ carries deterministic logic.",
    "evals/ 已承载可迁移检查。": "evals/ carries portable checks.",
    "agents/interface.yaml 已存在。": "agents/interface.yaml exists.",
    "manifest.json 已存在。": "manifest.json exists.",
    "目标平台或 adapter target 已声明。": "Target platforms or adapter targets are declared.",
    "入口文件未发现明显私有绝对路径。": "No obvious private absolute paths were found in the entrypoint.",
    "分数越高代表上下文成本越低。": "A higher score means lower context cost.",
    "上下文成本处于可控区间。": "Context cost is within a controlled range.",
    "上下文成本偏高，建议压缩入口或拆分 references。": "Context cost is high; compress the entrypoint or split references further.",
    "手动触发 + description 路由": "Manual activation plus description-based routing",
    "跨平台": "Cross-platform",
    "本地复用": "Local reuse",
    "输入材料": "Input material",
    "Skill 包体": "Skill package",
    "可复用能力": "Reusable capability",
    "入口层": "Entrypoint layer",
    "参考层": "Reference layer",
    "脚本层": "Script layer",
    "评估层": "Evaluation layer",
    "报告层": "Report layer",
    "评分雷达": "Rating Radar",
    "交付流程": "Delivery Flow",
    "能力矩阵": "Capability Matrix",
    "分层结构": "Layered Structure",
    "风险热力": "Risk Heatmap",
    "资产分布": "Asset Distribution",
    "迭代时间": "Iteration Timeline",
    "执行确定性": "Execution certainty",
    "知识密度": "Knowledge density",
    "发生概率": "Probability",
    "影响程度": "Impact",
    "评分雷达展示结构完整度、触发边界、证据、维护和迁移的相对强弱。": "The radar chart compares completeness, trigger clarity, evidence, maintainability, and portability.",
    "交付流程把用户输入、生成的包体和可复用能力放在一条线上。": "The delivery flow places user input, generated package, and reusable capability on one path.",
    "能力矩阵说明这个 Skill 更偏知识密集还是执行确定。": "The capability matrix shows whether the skill leans toward knowledge density or execution certainty.",
    "分层结构展示入口、参考、脚本、评估和报告如何各司其职。": "The layered structure shows how entrypoint, references, scripts, evals, and reports each carry a distinct role.",
    "风险热力图用影响程度和发生概率标出当前治理重点。": "The risk heatmap marks governance priorities by impact and probability.",
    "资产分布图展示当前包体的文件和目录重心。": "The asset distribution chart shows where files and directories are concentrated.",
    "迭代时间线把下一步升级收束成少数可执行动作。": "The iteration timeline narrows the next upgrade into a few executable moves.",
    "只需要一次性回答、没有复用价值的临时请求。": "One-off requests that do not need reusable skill behavior.",
    "要求直接执行相邻任务，而不是沉淀或使用这个 Skill。": "Requests to perform an adjacent task directly rather than create or use this skill.",
    "缺少必要事实且用户不允许澄清的场景。": "Cases that lack required facts and do not allow clarification.",
    "相邻任务需要先确认是否应转为独立 Skill。": "Adjacent tasks should first be checked for whether they need a separate skill.",
    "不替代人工事实核查，也不静默扩大职责。": "Does not replace human fact checking or silently expand responsibility.",
    "先改触发边界，再扩展工作流。": "Tighten trigger boundaries before expanding the workflow.",
    "只把重复且稳定的步骤沉淀为脚本。": "Turn only repeated and stable steps into scripts.",
    "每次升级后重新生成报告并检查分数原因。": "Regenerate the report after each upgrade and inspect score reasons.",
    "先补证据和边界，再增加包体复杂度。": "Improve evidence and boundaries before adding package complexity.",
    "补齐世界证据": "Close world-class evidence",
    "提交有效 intake packet，并让 ledger 通过 artifact SHA-256 校验。": "Submit valid intake packets and let the ledger verify artifact SHA-256 digests.",
    "全部外部/人工证据被 ledger 接受后，才能进入公开 world-class claim 复核。": "Only after the ledger accepts all external and human evidence should the public world-class claim move to review.",
    "缺少真实 provider 模型运行和 token metadata。": "Missing a real provider model run and token metadata.",
    "盲评 pair 仍待真实 reviewer 决策。": "Blind-review pairs still need real reviewer decisions.",
    "原生 runtime enforcement 仍待目标客户端或外部安装器证明。": "Native runtime enforcement still needs target-client or external-installer proof.",
    "真实外部客户端 metadata-only 事件仍未导入。": "Real external-client metadata-only events have not been imported yet.",
}

MODE_ZH = {
    "scaffold": "脚手架",
    "production": "生产",
    "library": "库级",
    "governed": "治理",
    "manual": "手动",
    "inline": "内联",
    "agent-skills": "Agent Skills",
}

PACKAGE_LABEL_ZH = {
    "SKILL.md": "Skill 入口文件",
    "README.md": "人类可读使用说明",
    "agents/interface.yaml": "跨平台接口元数据",
    "manifest.json": "生命周期与打包元数据",
    "references": "扩展指导与复用资料",
    "scripts": "确定性脚本或本地工具",
    "evals": "触发与质量检查",
    "reports": "生成的证据与总结报告",
}

KIND_ZH = {"file": "文件", "folder": "目录"}

LABEL_EN = {
    "强项": "Strength",
    "缺口": "Gap",
    "保留并复用": "Keep",
    "纳入下一轮修复": "Fix next",
    "误触发风险": "Trigger risk",
    "输出漂移风险": "Output drift risk",
    "证据不足风险": "Evidence gap risk",
    "包体膨胀风险": "Package bloat risk",
    "跨平台迁移风险": "Portability risk",
}

METRIC_LABEL_EN = {
    "完整度": "Completeness",
    "触发清晰": "Trigger clarity",
    "证据充分": "Evidence depth",
    "可维护性": "Maintainability",
    "可迁移性": "Portability",
    "上下文成本": "Context cost",
}

WORLD_CLASS_LABEL_EN = {
    "提供商留出": "provider holdout",
    "人工盲评": "human adjudication",
    "原生权限": "native permission",
    "原生遥测": "native telemetry",
}


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in str(text))


def zh_for(text: str) -> str:
    value = str(text).strip()
    if not value:
        return ""
    if value in TEXT_ZH:
        return TEXT_ZH[value]
    if value in TEXT_EN or contains_cjk(value):
        return value
    if value.startswith("Use this skill when the request matches:"):
        return "当用户请求与该 Skill 的触发描述匹配时使用。"
    if value.startswith("用户说出类似需求时："):
        return "当用户提出与该 Skill 触发描述相近的请求时使用。"
    if value.startswith("Use $") and " when you need to " in value:
        skill, need = value.removeprefix("Use ").split(" when you need to ", 1)
        return f"当你需要{zh_for(need).rstrip('。')}时使用 `{skill}`。"
    if value.startswith("Read the strongest pattern from "):
        repo = value.removeprefix("Read the strongest pattern from ").rstrip(".")
        return f"阅读 `{repo}` 中最值得借鉴的模式。"
    if value.startswith("Primary prompt task family:"):
        return "主要提示任务类型已记录在 prompt quality profile 中。"
    if value.startswith("Complexity:"):
        return "复杂度判断已记录在 prompt quality profile 中。"
    if value.startswith("Stability:"):
        return "系统稳定性评分已记录在 system model 中。"
    if value.startswith("Owned job:"):
        return "负责的核心任务已在 system model 中说明。"
    if value.startswith("Leverage:"):
        return "关键杠杆点已在 system model 中说明。"
    return "原始说明可切换到英文查看；默认中文报告保留结论与结构说明。"


def en_for(text: str) -> str:
    value = str(text).strip()
    if not value:
        return ""
    if value in TEXT_EN:
        return TEXT_EN[value]
    if value in METRIC_LABEL_EN:
        return METRIC_LABEL_EN[value]
    if value.startswith("创建完成后建议先打开 ") and value.endswith("，再继续扩展包体。"):
        path = value.removeprefix("创建完成后建议先打开 ").removesuffix("，再继续扩展包体。")
        return f"After creation, open {path} before expanding the package further."
    if value.startswith("交付结果："):
        return "Deliverables: " + value.removeprefix("交付结果：")
    if value.startswith("能力类型："):
        return "Capability type: " + value.removeprefix("能力类型：")
    if value.startswith("成熟度："):
        return "Maturity: " + value.removeprefix("成熟度：")
    if value.startswith("触发强度："):
        return "Trigger strength: " + en_for(value.removeprefix("触发强度："))
    if value.startswith("复用范围："):
        return "Reuse scope: " + en_for(value.removeprefix("复用范围："))
    if value.startswith("评审进度："):
        return "Review progress: " + value.removeprefix("评审进度：")
    if value.startswith("待评审："):
        return "Pending review: " + value.removeprefix("待评审：")
    if value.startswith("一致率："):
        tail = value.removeprefix("一致率：")
        return "Agreement rate: " + ("not available yet" if tail == "暂无" else tail)
    if value.startswith("非法决策："):
        return "Invalid decisions: " + value.removeprefix("非法决策：")
    if value.startswith("变体运行："):
        return "Variant runs: " + value.removeprefix("变体运行：")
    if value.startswith("模型执行："):
        return "Model executions: " + value.removeprefix("模型执行：")
    if value.startswith("记录样本："):
        return "Recorded fixtures: " + value.removeprefix("记录样本：")
    if value.startswith("Token 估算："):
        return "Token estimates: " + value.removeprefix("Token 估算：")
    match = re.match(r"^世界级证据仍有\s+(\d+)\s+项待补；公开完成态 claim 必须继续保持阻塞。$", value)
    if match:
        return f"World-class evidence still has {match.group(1)} pending item(s); public completion claims must stay blocked."
    match = re.match(r"^补齐(.+?)证据：(.+)$", value)
    if match:
        label = WORLD_CLASS_LABEL_EN.get(match.group(1), match.group(1))
        return f"Close {label} evidence: {en_for(match.group(2))}"
    match = re.match(r"^继续补齐剩余\s+(\d+)\s+项外部/人工证据，并保持 claim guard 为 pending 状态。$", value)
    if match:
        return f"Close the remaining {match.group(1)} external or human evidence item(s) and keep the claim guard pending."
    match = re.match(r"^已生成\s+(\d+)\s+/\s+(\d+)\s+类报告证据。$", value)
    if match:
        return f"Generated {match.group(1)} / {match.group(2)} evidence report types."
    match = re.match(r"^SKILL\.md 约\s+(.+?)\s+个词/字。$", value)
    if match:
        return f"SKILL.md is about {match.group(1)} words/characters."
    match = re.match(r"^入口约\s+(.+?)\s+个词/字，references 约\s+(.+?)\s+个词/字。$", value)
    if match:
        return f"Entrypoint is about {match.group(1)} words/characters; references are about {match.group(2)}."
    match = re.match(r"^结构化 Skill 目录，共\s+(.+?)\s+类关键资产。$", value)
    if match:
        return f"Structured skill directory with {match.group(1)} key asset groups."
    if value.startswith("证据不足：缺少 "):
        return "Evidence gap: missing " + value.removeprefix("证据不足：缺少 ").rstrip("。") + "."
    for metric_label in METRIC_LABEL_EN:
        prefix = metric_label + "需要补强："
        if value.startswith(prefix):
            return f"{METRIC_LABEL_EN[metric_label]} needs improvement: {en_for(value.removeprefix(prefix))}"
    if value.startswith("Use this skill when the request matches:"):
        return "Use this skill when the request matches the frontmatter description."
    if value.startswith("用户说出类似需求时："):
        return "Use this skill when the user asks for a matching scenario."
    if value.startswith("当你需要") and "时使用" in value:
        return "Use this skill when the request matches its stated scenario."
    if contains_cjk(value):
        return "Skill-specific source text is authored in Chinese; switch to Simplified Chinese for the exact wording."
    return value


def bi_span(zh: str, en: str | None = None) -> str:
    english = en_for(en) if en is not None else en_for(zh)
    return (
        f'<span data-lang="zh-CN">{html.escape(str(zh))}</span>'
        f'<span data-lang="en">{html.escape(str(english))}</span>'
    )


def bi_item(text: str) -> str:
    return bi_span(zh_for(text), en_for(text))


def mode_zh(value: str) -> str:
    return MODE_ZH.get(str(value), str(value))


def readable_description_zh(description: str) -> str:
    if contains_cjk(description):
        return description
    return "该 Skill 的触发描述来自 SKILL.md frontmatter；默认中文报告先呈现能力边界，原始英文描述可切换到英文查看。"
