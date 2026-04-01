# Yao Meta Skill 中文介绍

`yao-meta-skill` 是一套轻量但严谨的系统，用来创建、评估、打包和治理可复用的 agent skill。

它把粗糙的 workflow、transcript、prompt、notes 和 runbook 转成可复用的 skill 包，并具备：

- 清晰的触发面
- 精简的 `SKILL.md`
- 可选的 references、scripts 和 evals
- 中性的源元数据以及面向不同客户端的适配层
- 内建的治理、晋升和 portability 检查

## Quick Start

1. 先描述你想沉淀成 skill 的 workflow、prompt 集合或重复任务。
2. 使用 `yao-meta-skill` 以 scaffold、production 或 library 模式生成或改进 skill 包。
3. 按需要运行 `context_sizer.py`、`trigger_eval.py` 和 `cross_packager.py` 来检查并导出结果。

## Results

- 当前 `make test` 可通过
- 当前回归集下 trigger eval 为 `0` 误触发、`0` 漏触发
- train / dev / holdout 三层评测均通过
- `openai`、`claude`、`generic` 三个目标的 packaging contract 校验通过

## 当前优势

根据最近一轮加权评测，Yao 当前最强的优势主要集中在真正决定 meta-skill 质量的几个维度：

- **方法论完整性 `9.8`**：已经形成正式的 skill engineering doctrine，覆盖 gate selection、non-skill decision、governance 和 resource boundary。
- **工程化工具链 `9.8`**：初始化、校验、优化、报告、晋升检查、打包和 CI 已经串成一条完整工具链。
- **治理 / 维护 / 安全 `9.8`**：重要 skill 可以声明生命周期、review cadence、maturity score、trust boundary 和 promotion evidence。
- **评测闭环 `9.7`**：触发评测已经覆盖 train/dev/holdout、blind holdout、adversarial holdout、judge-backed blind eval、drift history 和 promotion gate。
- **跨环境复用 / 打包 `9.6`**：源码保持中性，adapter、degradation rule 和 packaging contract 负责保留跨环境可移植语义。
- **触发与边界设计 `9.5`**：route confusion、anti-pattern regression 和 promotion policy 把 trigger 质量变成可审计的路由问题。
- **上下文效率 `9.4`**：入口文件保持紧凑，context budget 分层治理，quality density 也被量化跟踪。

整体方向很明确：入口尽量轻，评测尽量硬，治理成为 skill 质量的一部分。

## 它能做什么

这个项目帮助你把 skill 从一次性 prompt，升级成可创建、可重构、可评估、可打包的长期能力包。

它的设计逻辑很简单：

1. 识别用户请求背后真正重复发生的工作
2. 划清 skill 边界，让一个包只做一个连贯的任务
3. 优先优化触发 description，而不是先把正文写长
4. 保持主 skill 文件精简，把细节移到 references 或 scripts
5. 只在值得时加入质量门槛
6. 只为真正需要的客户端导出兼容产物

## 为什么要做它

大多数团队的重要操作知识都散落在聊天记录、个人 prompt、口头习惯和未成文 workflow 中。这个项目的作用，是把这些隐性流程知识转成：

- 可发现的 skill 包
- 可重复的执行流程
- 更低上下文负担的指令
- 可复用的团队资产
- 可兼容分发的产物

## 仓库结构

```text
yao-meta-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── .gitignore
├── agents/
│   └── interface.yaml
├── references/
├── scripts/
└── templates/
```

## 核心组成

### `SKILL.md`

主 skill 入口，定义触发面、工作模式、压缩后的工作流和输出契约。

### `agents/interface.yaml`

中性的元数据单一来源。它保存显示信息和兼容性信息，不把源码树锁定到某一家厂商的专属路径。

### `references/`

用于存放不应该塞进主 skill 文件的长文档，包括设计规则、评估方法、兼容策略和质量 rubric。

### `scripts/`

让这个元 skill 具备工程化能力的辅助脚本：

- `trigger_eval.py`：检查 trigger description 是否过宽或过弱
- `context_sizer.py`：估算上下文体积，并在初始加载过大时给出警告
- `cross_packager.py`：从中性的源码包生成客户端特定的导出产物

### `templates/`

用于生成简单 skill 和更复杂 skill 的起步模板。

## 如何使用

### 1. 直接使用这个 skill

当你想做以下事情时，可以调用 `yao-meta-skill`：

- 创建新 skill
- 改进已有 skill
- 给 skill 增加 eval
- 把 workflow 变成可复用包
- 为更广泛的团队使用准备 skill

### 2. 生成一个新的 skill 包

典型流程是：

1. 描述 workflow 或能力
2. 识别触发语句和目标输出
3. 选择 scaffold、production 或 library 模式
4. 生成 skill 包
5. 在需要时运行体积检查和触发检查
6. 导出面向目标客户端的兼容产物

### 3. 导出兼容产物

示例：

```bash
python3 scripts/cross_packager.py ./yao-meta-skill --platform openai --platform claude --zip
python3 scripts/context_sizer.py ./yao-meta-skill
python3 scripts/trigger_eval.py --description "Create and improve agent skills..." --cases ./cases.json
```

## 优势

- **方法论优先，不是 prompt 优先**：skill creation 被当成正式工程流程，而不是只写一段说明文字
- **天生面向触发优化**：description 会经过 route confusion、blind holdout、adversarial family 和 promotion policy 的检查
- **入口轻量**：`SKILL.md` 保持克制，references、scripts、evals 只在真正值得时加入
- **工具链完整**：初始化、校验、优化、报告、打包、测试，都能走统一 CLI 和 CI 路径
- **治理化资产**：重要 skill 可以带 owner、lifecycle、maturity expectation 和 review cadence
- **默认可移植**：源码中立，兼容性通过 adapter 和 degradation rule 处理
- **证据密度高**：route scorecard、regression history、context budget、portability score、promotion decision 都是公开产物，而不是隐藏实现

## 最适合谁

这个项目尤其适合：

- agent 构建者
- 内部工具团队
- 正在从 prompt engineering 转向 skill engineering 的人
- 想构建可复用 skill 库的组织

## 许可证

MIT。见 [LICENSE](../LICENSE)。
