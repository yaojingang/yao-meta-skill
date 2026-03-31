# Yao Meta Skill 中文介绍

`yao-meta-skill` 是一个用于构建其他 agent skill 的元 skill。

它把粗糙的 workflow、transcript、prompt、notes 和 runbook 转成可复用的 skill 包，并具备：

- 清晰的触发面
- 精简的 `SKILL.md`
- 可选的 references、scripts 和 evals
- 中性的源元数据以及面向不同客户端的适配层

## Quick Start

1. 先描述你想沉淀成 skill 的 workflow、prompt 集合或重复任务。
2. 使用 `yao-meta-skill` 以 scaffold、production 或 library 模式生成或改进 skill 包。
3. 按需要运行 `context_sizer.py`、`trigger_eval.py` 和 `cross_packager.py` 来检查并导出结果。

## Results

- 当前 `make test` 可通过
- 当前回归集下 trigger eval 为 `0` 误触发、`0` 漏触发
- train / dev / holdout 三层评测均通过
- `openai`、`claude`、`generic` 三个目标的 packaging contract 校验通过

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

- **默认中性**：源码保持厂商中立，适配层只在需要时生成
- **上下文高效**：明确把细节从主 skill 文件中剥离出去
- **评估友好**：workflow 内置 trigger 和体积检查
- **可复用**：输出的是完整包，而不是一段 prompt 文本
- **可移植**：兼容性通过打包处理，而不是为每个客户端复制一套源码

## 最适合谁

这个项目尤其适合：

- agent 构建者
- 内部工具团队
- 正在从 prompt engineering 转向 skill engineering 的人
- 想构建可复用 skill 库的组织

## 许可证

MIT。见 [LICENSE](../LICENSE)。
