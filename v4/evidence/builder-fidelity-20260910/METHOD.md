---
ai_contribution: authored
date: 2026-09-10
---
# Builder v3 实验契约与方法

## 本轮问题

Builder 可能输出语法正确、可执行的 Query，却删掉或错误转换用户的筛选条件。Checker 即使发现它与 final Query 一致，也不能由此证明两者忠实表达用户需求。此实验只改变 Builder 指令，不把另一层 LLM 叫作确定性保证。

v3 = 冻结 v2 + 通用约束保真规则；无商品名或测试句样例。默认 v1、原 v1/v2 字节内容、retrieve/wait 结构、STT 调度、Checker、Answerer 均不改变。

## 行为契约

| 情形 | 本轮约定 |
|---|---|
| 当前接口能表达已明确的条件 | 输出 Query，保留条件、运算方向、数值和用户指定的数量/顺序 |
| 用户取消条件 | 删除此筛选，不把 true 改 false 或把上限改下限 |
| 询问属性值 | 查询相关记录，不能自动筛掉可能给出“否/零”的记录 |
| 需要不支持的运算或字段筛选 | wait；不擅自只查一个分支、删掉条件或取第一页后声称足够 |
| 用户要求完整列举、接口却只能限量返回且无已知覆盖保证 | wait；不能用 limit 调大到上限代替完整性 |
| 普通有界浏览／支持的 lookup | 可以 retrieve；不能替用户凭空加入“必须穷尽所有结果”的要求 |
| partial 尚未说出的条件 | 不猜测；只按当前可观察文本判断，后续变更仍交 final 决策 |

这是一种严格 schema 实验策略，不是所有 RAG 的通用规则。普通文档 RAG 可以故意宽检索，再由 reranker/Answerer 筛选；但当前 PoC 没有表达被省略约束、分页/覆盖保证或残余过滤的契约。本轮不新增 type，也不把 SQL schema 的限制外推到 GCP 全文/向量检索。

wait 不携带原因，因此下游仍无法区分歧义、等待更多输入与 schema 不支持。final wait 后现有 Answerer 仍能重写；已有错实体失败不因本实验而自动解决。本轮观察边界止于 Builder 输出。

## 预先冻结的比较

- 基线 v2，候选 v3；两版在同一批输入上重新调用，不拿旧运行的 v2 当同时期对照。
- 已见的 24 条挑战（known_challenge）：回归/开发集，直接影响设计动机，不能叫 holdout。
- 新写的 12 条探针（new_development_probe）：有界正例、覆盖负例、上下文修订各 4；仍为 AI 作者按当前假设编写，不是独立公司语料或真正盲测。
- 每条每版一次主采样；9 个场景族首条每版各加两次重复，共 108 次请求。两并发，seed=20260910，独立 HTTP client，单次 15 s，无隐式重试。
- 运行前冻结 cases.json、prompts.json；返回后不改 prompt、标签或挑选成功重跑。重复采样单列，不扩大主样本分母。
- judge 沿用既有字段比较：安全 wait、missed_retrieve、wrong_query、unjustified_retrieve、order/limit 变体待复核、严格命中、API/契约错误。unjustified_retrieve 需按输入审计，区分重复 Query 与丢约束，不能直接叫 Checker FP。
- 原来未指定 --versions 的 evaluator 仍比较 v1/v2；新参数只选择实验组，输出只保存被选版本的实际 prompt。旧证据文件不更新。

## 接受与退出条件

记录所有失败与正例覆盖，不从此有限开发集选生产默认。若负例改善但正例 wait 增多，明确报告权衡。即使全部通过，也只支持继续独立验证；prompt 遵循不是确定性执行保证。下一步涉及宽检索/残余条件表达时需要单独设计，不在本轮隐式实现。

本地测试覆盖版本路由、旧 prompt 不变、评测版本校验及全部既有控制流程；这些测试不证明自然语言语义正确。本轮不运行 PostgreSQL/Answerer/真实 STT。
