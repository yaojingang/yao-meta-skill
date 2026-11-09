# WorkBuddy Compatibility

Use the existing generic Skill package for Tencent WorkBuddy. Keep the same authoring workflow, Skill IR, CLI, and evidence gates.

## Install and Update

In WorkBuddy's Skill page, choose **Add Skill → Upload Skill** and import the generated yao-meta-skill.zip. Check that the installed name is yao-meta-skill and its version matches the supplied package. A project may also use .codebuddy/skills/yao-meta-skill/ with a complete extracted package; project Skills take precedence over user Skills with the same name.

For updates, import the verified replacement ZIP using WorkBuddy's Skill management flow. Start a fresh conversation when checking enable/disable state or newly loaded instructions. Existing managed Agent Skills/Codex updater commands apply to their own supported installation channels.

## Runtime and Targets

Locate this loaded Skill's actual installation directory before invoking scripts/yao.py. Resolve scripts and references from that directory, then pass the task's explicit target path. Store generated Skills and reports in the selected workspace, outside this installed Skill. Editing Yao itself still requires --self.

The engineering CLI requires Python 3.11+ and PyYAML. Check the interpreter and dependency inside WorkBuddy's command environment before invoking it. A CLI Connector can declare a managed Python runtime; an ordinary uploaded Skill still needs its own runtime check. If prerequisites are missing, complete intent and boundary analysis, report the missing prerequisite, and use the CLI once the environment is ready.

Use WorkBuddy's current permissions and workspace-trust state. When execution is blocked, identify the operation, target and required capability. Keep generated artifacts in the selected workspace and preserve any completed output.

## Create a WorkBuddy Skill

1. Capture the recurring job, real input, output, exclusions and an explicit target directory.
2. Initialize through the existing yao.py init or quickstart workflow. Keep authoring scoped to that target.
3. Fill the target Skill's frontmatter using the table below. Write actual Chinese and English descriptions from the target's job; retain the routing meaning in description.
4. Resolve referenced files from the Skill directory. WorkBuddy documents @references/file.md for supplemental context. Declare script commands and parameters clearly, including the interpreter prerequisite.
5. Run the target's normal structure and risk-appropriate checks. Package through the existing generic target and inspect the delivered ZIP.

| Field | Source |
| --- | --- |
| name | Stable Skill identifier, aligned with the directory name. |
| display_name | Chinese display name. |
| display_name_en | English display name. |
| description | Existing trigger and exclusion contract. |
| description_zh | Chinese introduction for the Skill detail page. |
| description_en | English introduction for the Skill detail page. |
| version | Skill version, consistent with its manifest when present. |
| author | Actual owner or author. |
| examples_zh / examples_en | Optional concrete usage prompts in each language. |
| allowed-tools | Optional comma-separated tools, using names verified in the target WorkBuddy client. |

Keep SKILL.md lean and place durable instructions in references/, executable logic in scripts/, and reusable templates in templates/. Check the ZIP contains one installable root entrypoint, all required resources, and the intended metadata. Keep private inputs, raw evaluation answers, local telemetry and development caches outside delivery.

## Acceptance

The automated compatibility check exercises the generic archive and an extracted CLI in a workspace with Chinese characters and spaces. It checks the published frontmatter fields, version parity, packaged references, and explicit output isolation.

For native acceptance, record the WorkBuddy version, model, Skill version and ZIP hash. In fresh conversations, verify installation, explicit and automatic triggering, referenced-file reads, one generated Skill, HTML artifact preview, and disable state. Review project-level precedence separately when using project installation. Report only the native checks actually observed.

Check features against the running WorkBuddy version; official documentation may describe newer releases.

## Official References

- [Skill development and required metadata](https://open.workbuddy.cn/docs/skill)
- [Desktop Skill import and management](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)
- [Project configuration and priority](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Project)
- [Permissions and workspace trust](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes)
- [Connector runtime scope](https://open.workbuddy.cn/docs/connector)
