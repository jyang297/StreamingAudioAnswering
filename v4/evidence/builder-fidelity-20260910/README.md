---
ai_contribution: authored
date: 2026-09-10
---
# v2/v3 同批对照：规则更明确，仍不能保证不漏条件

结论：v3 修正部分 schema 不支持需求的近似查询，但两条新负例仍漏掉条件。默认 v1 不变，v3 保持可选。本轮没有继续按失败样例调 prompt；失败保留为下一次设计依据。

契约与采样方法见 [METHOD](METHOD.md)。36 条输入各测 v2/v3，9 个场景族哨兵各加两次重复，共 108 次真实 DeepSeek 请求。主表只统计 repeat=0，各 36 条；24 条已见挑战与 12 条新开发探针分别保存 dataset 标签。它们不是生产 holdout。

| 主采样结果 | v2 | v3 |
|---|---:|---:|
| 符合预设 Query 字段 | 19 | 19 |
| 合理 wait | 8 | 13 |
| 有查询机会却 wait | 0 | 1 |
| 不支持要求被近似成可执行 Query | 5 | 2 |
| partial 重复相同 Query | 1 | 1 |
| 排序变体待复核 | 1 | 0 |
| Query 解析器拒绝非法输出 | 2 | 0 |

v2/v3 的原始 unjustified_retrieve 分别为 6/3；其中各 1 条为 partial 重复，单列以免冒充危险误接受。correct_retrieve 是字段 oracle 通过，不是答案正确或证据覆盖验证。API HTTP/JSON 请求均成功，v2 两条错误发生在 Query.parse：`negative-stock` 的 order=null、`probe-unsupported-followup` 的不支持字段 quantity_per_unit。解析器拒绝没有进入有效 Query，不按漏条件的合法输出计数。

## 哪些改善，哪些没有

- v3 对明确超出最大返回条数、完整列举、后缀匹配、两个名称的 OR，以及旧“库存小于5”输入返回 wait。
- v3 `probe-stock-range`：用户要求库存数量2–7，却返回仅 limit=5；库存条件完全缺失。
- v3 `probe-unsupported-followup`：追问包装12个，保留 category_id=4、limit=5，却删掉包装条件。**v2 同例是非法字段被拒绝，v3 变成合法但不忠实的 Query；不能把少一次解析错误叫作安全改善。**
- v3 `quoted-entity`：引用广告中的 Chai，但明确问 Chang 库存，返回 wait；预期可查询。这是一次保守漏检索机会，不是危险复用。
- 两版 `partial-duplicate` 都重复返回 Chang Query；现有流程已验证同 Query 共享任务，不能推断多一次 SQL。

开发子集拆分：

| 子集 | v2 | v3 |
|---|---|---|
| 已见挑战24条 | 字段命中12、wait8、近似查询1、重复1、排序待核1、解析拒绝1 | 字段命中12、wait10、重复1、miss1 |
| 新开发探针12条 | 字段命中7、近似查询4、解析拒绝1 | 字段命中7、wait3、近似查询2 |

新增探针中的7条正例两版均符合字段预设，5条不支持需求负例中v3仍有2条漏条件；样本小且人为设计，不能推断生产概率。9×2组哨兵三次的结果类别均未变化；这不证明模型确定性。

主采样 Builder 延迟中位数：v2 1137.9 ms，v3 1218.4 ms。两并发、每请求独立client、v3更长prompt，未控制网络/缓存/服务负载；只报告本次测量，不声称稳定延迟差异或性价比。

## 实现与检查

- opt-in `--builder-prompt v3`；默认 v1；v1/v2 文本 SHA-256 不变。
- evaluator 新增 `--versions`，默认仍 v1/v2；选 v2/v3 时仅对这两版调用并保存实际 prompt。重复/未知/空版本在创建结果目录或调用 API 前拒绝。
- 74 passed、3 skipped，3.38 s；3 个真实 DB 项未启用。本轮无 SQL、Answerer、真实 STT 或语音延迟实验。
- 所有108次原始输出、指标和输入标签已保存，无成功挑选重跑。代码中 prompt 与 prompts.json 已核对一致。

## 下一步含义

本轮支持的判断是：通用指令值得保留为实验，但“字段合法”与“条件忠实”之间仍有缺口。更高 semantic threshold 或 early/final Query 相等都不能补出双方共同漏掉的条件。

若继续，应先用目标业务检索接口定义可执行的约束与允许的宽检索策略，再考虑让检索计划显式携带保留/未满足的要求、或独立验证需求到 Query 的映射；这些都是后续设计选项，本轮未增加新 type 或 endpoint。若仍保持当前契约，schema 不支持就 wait，但不能声称 prompt 能强制所有请求遵循它。最终 wait 后的 Answerer 仍可重写，先前错实体路径未解决。

复现（会产生108次API调用，输出目录必须全新）：

```sh
/private/tmp/livekit-anticipation-poc-venv/bin/python builder_expanded_eval.py \
  --versions v2 v3 --cases evidence/builder-fidelity-20260910/cases.json \
  --output-dir /private/tmp/builder-fidelity-new-run
```

证据：cases.json、prompts.json、results.jsonl、summary.json；METHOD.md记录预设契约；local-validation.json记录本地测试。无论文新结论，无生产配置切换。
