---
ai_contribution: authored
date: 2026-09-10
---
# Builder 挑战集：24 条输入，72 次真实调用

用户授权 AFK 后有限推进。沿用冻结 v1/v2 与 builder_expanded_eval.py，24 条新输入各测两版，每族首条再各重复两次，共 72 次 DeepSeek 调用；两并发、固定 shuffle seed。六族为指代、约束修订、schema 不支持、歧义、历史数据边界、partial/final 阶段。每条预先保存 rationale 和预期字段，未按返回结果调 prompt 或换标签。

这是已知开发问题驱动的 AI 编写诊断，不是盲测、公司语料或 24 种独立未知机制。具体英文商品名保留，当前文本主要中文；不能与旧英文样本作受控语言效果比较。

## 主结果（repeat=0，各 24 条）

| 结果 | v1 | v2 |
|---|---:|---:|
| 严格符合预设的 retrieve | 4 | 13 |
| 合理 wait | 11 | 8 |
| 有查询机会但 wait | 3 | 0 |
| 错误过滤条件 | 4 | 0 |
| 不支持需求被近似查询替代 | 0 | 2 |
| partial 冗余相同 query | 0 | 1 |
| 排序变体待复核 | 2 | 0 |

原始 summary 将 v2 后两种共 3 条归为 unjustified_retrieve；这里按输入/输出逐条解释，不覆盖原记录。72 次无 API/解析错误。v1/v2 主样本延迟中位数约 1054/1059 ms，仅为独立 HTTP client、两并发条件下的 Builder 延迟。

## 新暴露的失败

- v1 `drop-stock`：取消库存筛选应移除 in_stock，却输出 false；这会把“全部库存状态”改为“仅无库存”。
- v1 `recent-vs-old` / `correction-final`：问库存值却添加 in_stock=true；v1 `boolean-value`：问是否停产却添加 discontinued=true。三者可能把“没有/否”的证据过滤掉。
- v2 `or-two-names`：要求 Chai 或 Chang 且不能有其他商品，返回只查 Chai、limit=20；不能完整覆盖请求。
- v2 `negative-stock`：要求库存数量小于 5，返回无过滤、limit=10。行内确有库存字段，但只取前 10 行不是完整候选集，不能默认为安全的“检索后过滤”。当前契约没有明确此种降级查询语义，预设为 wait。
- v2 `partial-duplicate`：返回与 previous query 相同的 Chang 查询。这是冗余输出，不是错误实体，也不能推断新增一次 SQL。

**这些是 Builder 对需求的表达问题，不是 Checker false positive 测量。** 即使 final 与 early query 完全一致，也可能共同漏掉用户要求。下一阶段应先确定完整/保守检索的可接受契约；不在本轮擅自添加 type、schema 或新 prompt。

六族首条各版本三次采样：v1 `drop-stock` 的类别为 wrong_query/correct/correct；v2 `history-instruction` 为 correct/排序待复核/correct。温度 0 也不保证输出确定性。其余哨兵类别未变化，不代表分布稳定。

## 控制流程验证

新增 `../../test_candidate_boundaries.py` 共 9 个参数化测试覆盖 time/text/hybrid：

1. 两个 Builder 输出相同 Query、检索仍在途、旧候选被淘汰：仍共享一个检索任务，数据库依赖只调用一次。
2. partial wait 不建检索，不进入 Checker views，但消耗一次 partial Builder 预算。
3. 即使已有早期有效 query，final wait 也在 Checker 前返回 no_query，证据为空。

全部 v4 本地测试：68 passed、3 skipped，14.44 s。3 个 DB 测试未启用；本轮没有运行真实 SQL 或 Answerer。测试依赖是明确标记的流程替身，不代表检索质量。

## 续接

默认仍 v1、v2 可选；保留已知失败，不追着挑战集调 prompt。下一步优先独立标注的业务输入，分别评 Builder 约束保真、Checker 错误复用与 Answerer 证据充分性。wait 可接受，不能因为追求命中率而默许丢条件。现有 no_query 后 Answerer 改写的错实体记录仍未解决。

文件：cases.json（含预先 rationale）、prompts.json、results.jsonl（72 次）、summary.json。复现命令见主 README，输出目录不可复用。两次开发集共 124 条/312 次调用不合并成单一 accuracy，因为采样和场景构成不同。
