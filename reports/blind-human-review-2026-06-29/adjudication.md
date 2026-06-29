# 人工盲测 Adjudication

生成时间：`2026-06-29T03:04:34Z`

## 结论

在 5 个真实常见 skill 创建场景的单人盲测中，评审者在揭晓来源前完成判断，5/5 选择了 `yao-meta-skill` 输出。

| 案例 | 评审选择 | 揭晓来源 |
| --- | --- | --- |
| `case-01-support-triage` | B | `yao-meta-skill` |
| `case-02-monthly-revenue-reconciliation` | A | `yao-meta-skill` |
| `case-03-webinar-repurposing` | B | `yao-meta-skill` |
| `case-04-incident-postmortem` | A | `yao-meta-skill` |
| `case-05-pr-review-followup` | B | `yao-meta-skill` |

## 统计

- `yao-meta-skill`：5
- 官方 `skill-creator`：0
- 平局：0
- 评审人数：1
- 信心程度：5 个判断均为 `1.0`

## 盲审确认

评审者确认：

> 确认：我是在完成五个判断之后才让你打开答案钥匙的，评审前没有看来源。以上 5 个判断都是揭晓来源前完成的。

## 证据边界

这可以作为单人独立盲测偏好证据。它不等同于 provider-backed 独立模型执行证据，因为两个输出是本地按两份 skill 说明生成的。

当前缺口：

- 每个案例的 `reason` 字段为空，缺少逐案 rationale。
- 评审人数为 1，尚未形成多评审者一致性证据。
- 尚未加入外部冻结 holdout 任务集。
