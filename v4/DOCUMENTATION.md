---
ai_contribution: authored
updated: 2026-09-10
---
# 文档总导航与 AFK 交接

Company handoff and English standup: [Transfer and demo quick start](TRANSFER-AND-DEMO.md) · [Agent prompt](COMPANY-AGENT-PROMPT.md) · [Migration contract](COMPANY-AGENT-HANDOFF.md) · [Offline presentation](demo/standup.html).


当前代码与实验以本目录 v4 为准。最新为 [v2/v3 约束保真对照](evidence/builder-fidelity-20260910/README.md)，保留失败与默认版本。README 是运行入口，接口文档是设计事实；evidence 保留每次实验当时的输入、输出、失败和限制。历史材料不是当前状态，旧论文导读和学习进度未覆盖。

## 三条阅读路线

| 目的 | 入口 | 状态/边界 |
|---|---|---|
| 接着运行 PoC | [README](README.md) → [最新约束保真实验](evidence/builder-fidelity-20260910/README.md) | 已运行 DeepSeek；默认 v1 不变；本轮未重跑 DB |
| 理解接口和设计 | [INTERFACE-AND-SCHEDULING](INTERFACE-AND-SCHEDULING.md) | 单 STT、Builder 批次、final Checker、hook 注入指针、三种问题、迁移不变量 |
| 继续论文阅读 | [Stream RAG 原有 Zotero 笔记](zotero://select/library/items/V4FWCA2T)、[MoshiRAG](zotero://select/library/items/9L6S5PEZ) | 本轮只整理入口，没有替用户推进阅读进度或追加论文结论 |

## 设计对应的原文／工程选择

以下复用已有阅读和架构记录，不是本轮重新文献检索。

| 当前设计 | 既有原文定位 | 不能混同的部分 |
|---|---|---|
| Builder 与回答分开 | [Stream RAG §3.1](https://arxiv.org/html/2510.02044v1#S3.SS1) | 当前用现成文本 endpoint，不是训练复现 |
| final 时检查早期查询 | [Stream RAG §3.2.1](https://arxiv.org/html/2510.02044v1#S3.SS2.SSS1) | 我们 Checker 的 Query 适用性不等于原 Reflector 的结果一致判据 |
| 渐进输入决定 wait/query | [Stream RAG §3.2.2](https://arxiv.org/html/2510.02044v1#S3.SS2.SSS2) | 当前混合不同方案思路；时间/文本阈值和预算是工程实验参数 |
| 实时交互与异步检索分开 | [MoshiRAG §3.1–3.2](https://arxiv.org/html/2604.12928v3#S3.SS1) | 未使用 Moshi 音频 token/reference encoder，不依赖本机 24 GB 模型 |
| 最终轮次 hook 与证据消费 | [LiveKit nodes](https://docs.livekit.io/agents/logic/nodes/)；本地 [adapter](rag_poc/livekit_adapter.py) | 自定义 PipelineLLM 消费指针，普通插件不能直接替换；native preemptive 关闭 |
| exact/LLM/semantic Checker 对照 | [本地诊断](evidence/semantic-20260910/README.md) | 不是 vCache 实现，不是论文给出的安全阈值 |

已有 [论文—设计 architecture map](/Users/codingleo/ai-generated-tool/LearningVault+/vibe-discipline/what-we-built/livekit-paper-architecture-20260909/architecture-map.md) 保留其旧版本范围，不能直接当作当前 v4 实现清单。

## 所有实验记录

| 阶段 | 证据 | 能说明什么／不能说明什么 |
|---|---|---|
| v4 初次协议/数据库集成 | [validation.json](evidence/validation.json)、[offline demo](evidence/offline-demo.json) | 历史测试数含 v1–v3；脚本语言响应，不是当时的真实模型效果 |
| DeepSeek 初次联调 | [deepseek](evidence/deepseek-20260910/README.md) | 真实 API/DB、脚本 STT；不能推导语音加速 |
| 三种 Checker | [semantic](evidence/semantic-20260910/README.md) | 12 条冻结 Query，真实 cosine .99 有 2 次误接受；未校准生产阈值 |
| time/text/hybrid | [triggers](evidence/triggers-20260910/README.md) | 真实联调出现 Answerer 追问错实体与 DB 超时；不是策略优劣证明 |
| Builder 首次 v1/v2 | [10 条](evidence/builder-prompt-20260910/README.md) | 小样本开发，保留失败与版本；已被更广诊断补充 |
| Builder 扩展 | [100 条 / 240 调用](evidence/builder-expanded-20260910/README.md) | 参数化开发集；wait 减少，但不能估计生产错误率 |
| Builder 约束保真 v3 | [36 条 / 108 调用](evidence/builder-fidelity-20260910/README.md) | 同批 v2/v3；近似查询减少但仍有漏条件，非法输出减少不等于更安全 |
| Builder 挑战与控制边界 | [24 条 / 72 调用](evidence/builder-challenge-20260910/README.md) | 暴露滤条件错误/不支持请求近似查询；另有 9 项调度边界测试 |

Builder-only 数据不能衡量 Checker FP 或答案正确率。100 条与挑战集分开报告，不合并为营销式准确率。每步耗时日志定义与复现命令统一见 README。

## 历史版本与阅读材料

- [v1](../README.md)、[v2](../README-v2.md)、[v3](../README-v3.md)：保留对应实验事实，非当前操作入口。
- [冻结 checkpoint](CHECKPOINT-20260910.md)：绑定 `34e09db` 的状态；后来的触发调度与 prompt 实验不倒写其中。
- [早期专题导读入口](/Users/codingleo/Documents/LearningVault/20-Active/Research/voice-anticipation/00-start.md)、[文献综述与 PoC 路线](/Users/codingleo/Documents/LearningVault/20-Active/Research/voice-anticipation/LiveKit-Literature-and-PoC-2026-09-08.md)：旧阅读包保留；当前共读以 Zotero 为主，读者进度不据代码运行自动更新。
- Krites 仅待读；vCache 仅概念参考；两者均未进入 PoC。详见接口文档第 6 节。
- `postgres-fixture/README.md` 只负责本地公开数据与重建流程。生产 GCP 数据源与凭据配置尚未验证。

## 本次停靠点

1. 完成：冻结 prompt 的挑战测试；wait/共享检索/淘汰边界回归；当前 README 与接口说明统一；历史证据未覆盖。
2. 默认：CLI 常规基线；显式 speculate 后 time；Builder v1；LLM Checker。参数未因开发集结果偷偷调整。
3. 未解决：Builder 对不支持请求的保守处理（v3 实验已有改善，仍不可靠）；no_query 后 Answerer 重写错实体；真实 STT 分段/修订、barge-in、GCP 检索接口；公司数据上的 Checker 校准。
4. 当前实验契约：无法完整表达则 wait，v3 仅为可选 prompt；实验仍有合法但漏条件的 Query。下个设计点是目标业务检索接口的约束表达和允许的宽检索保证，不把自然语言指令当作确定性验证。未引入新 type。
5. 下个可执行实验：从目标业务取得经授权、独立标注的短问/长问/追问和冲突负例，固定版本后分别测 Builder 约束保真、Checker 错误接受、Answerer 错误答案。优先负例，不只追求复用率。

本轮没有生产部署、远程 push、Jetson 实验或新增守候自动化；AFK 授权用于当前有限执行。Implementation：本地控制边界已验证、端到端质量未通过验收。Learning：AI demonstration，用户理解与迁移能力仍未评估。
