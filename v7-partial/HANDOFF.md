# 当前实验总结与公司电脑交接

更新：2026-09-14。AI 整理，基于实际代码和两轮原始结果。此文件是当前继续入口；旧实验结果保留，不以新设计覆盖历史实现。

## 结论先行

轻量 Builder 可以把部分转写与上下文整理成自然语言检索问题，但**尚未证明它能让正确答案更早到达用户**。目前成立的是机制观察和调用开销测量，不是语音提速或缓存准确率提升。

长度 gate 能避免明显过短输入触发远程 LLM；复杂 partial 仍经常返回 wait。双问题暴露了单一输出契约的限制。下一步优先验证真实时间线与端到端收益，不应仅为降低 wait 比例持续叠加复杂度。

## 业务条件与版本边界

- 公司目标仍是 Python LiveKit、Vertex AI endpoint、复杂多表查询。
- 约 200 条缓存记录含 question、answer 与对应 SQL/检索语句。公司数据未用于本地实验。
- SQL 执行不是主要瓶颈；另有外部重型 RAG 约 10 秒才开始返回 answer stream 的场景，需在公司实测拆分时间。
- 短独立问题、极短追问、长问题、一次问多个问题均需考虑。错误复用比漏用更严重。无音频缓存，无 Jetson 实验。

| 目录 | 实际用途 | 不代表什么 |
|---|---|---|
| `../complex-data/` | 八个真实 BIRD Mini-Dev SQLite 库；346 条修正后的问题/SQL；200 候选分配 | 不是公司数据，也不是已标注的 cache hit/miss 集 |
| `../v6/` | 多表 SQL adapter 与旧 SQL Builder 管线；历史记录 74 tests、346 条参考 SQL 本地验证 | 不是当前轻量 Builder；其测试不能证明模型语义准确率 |
| `replay.py` | 第一轮：partial → 轻量自然语言 Builder → embedding | 未接 LiveKit/SQL/Answerer |
| `replay_gated.py` | 第二轮：增加长度 gate、长问题和双问题回放 | 未实现多子问题并行状态或实时调度 |

不要把 v6 的 SQL Builder 与 v7 的自然语言 Builder 当成同一个已经完成迁移的组件。

## 当前真实数据流

```text
预设累计文本 snapshot + confirmed_context + final 标志
                    ↓
长度 gate（仅第二轮；默认至少 3 个英文词）
    ├─ 太短且非 final → 本地 gated，不调用 LLM 或 embedding
    └─ 通过 / final 绕过
                    ↓
        原始文本 embedding 检索（诊断对照）
                    ↓
        DeepSeek 轻量 Builder，无 schema / SQL
            ├─ wait → 无规范化检索
            └─ search + question → embedding → 同 DB top-3 候选
                    ↓
              保存输出、token 与分步耗时
```

两条检索分支在脚本中顺序运行；不是生产并行架构。200 个候选分属八个 DB，每次只检索该 DB 子集；没有部署 Chroma 服务。缓存向量在本轮启动时计算一次并留在内存。输出只用于观察，不自动采用答案，不执行 SQL。

**gated 与 wait 不同**：gated 是本地拒绝调用；wait 是已经付出一次 LLM 调用后得到的答案。最终完整输入绕过长度门槛，避免永久丢失 `And Batman?` 之类短追问。

## 两轮实测

| 指标 | 第一轮 | 第二轮 |
|---|---:|---:|
| 场景数 | 24 | 32 |
| 每场景 snapshot | 3 | 4 |
| 注入总数 | 72 | 128 |
| 本地 gate 跳过 | 0 | 36 |
| 实际 LLM 调用 | 72 | 92 |
| LLM wait | 44 | 36 |
| LLM search | 28 | 56 |
| HTTP/输出契约错误 | 0 | 0 |
| 报告 token 总数 | 15,976 | 22,068 |
| Builder 中位耗时 | 988.18ms | 790.31ms |
| Builder p95 | 1467.52ms | 1110.81ms |
| query embedding 中位耗时 | 7.19ms | 14.55ms |

模型均为 `deepseek-v4-flash`；本地真实 multilingual MiniLM ONNX embedding，FastEmbed 0.7.4 mean pooling。两轮负载和运行时间不同，**不是控制变量 A/B**；不能说 gate 让每次 LLM 变快。第二轮 gate 中位耗时 0.013ms，避免 36/128 次原本逐 snapshot 调用（28.1%），但未测这些被跳过请求的反事实输出或 token 成本。

第一轮：最早单词 24/24 wait，中间输入 20/24 wait，完整文本 24/24 search。第二轮包含 16 个 22–44 词的公开长问题、八个同库双问题拼接场景和八个上下文场景。长问题通过 gate 的 32 次非最终输入中，27 wait、5 search。

## 有判别价值的发现

1. **稳定候选不保证条件一致。** “大于 60 岁”修正为“小于 60 岁”，Builder 保留了修正，但首选 cache ID 不变，相似度从 0.7024 升到 0.7328。该候选实际问的是 1990–1993 年受检的未成年患者，两者都不适用。没有测试或否定某个已校准的高阈值；只是不能用趋势代替适用性。
2. **语法完整不保证范围完整。** 学校“提供的年级范围”片段被改成完整问句，但识别哪所学校的条件尚未出现。
3. **第二问可能阻塞完整的第一问。** 双问题中间阶段有 7/8 返回整体 wait。当前契约只有单个 question 或整体 wait，不能表达第一问 ready、第二问 pending。脚本没有任务管理器，因此这不是已观测的候选清除 bug。
4. **可能提前补造两问的关系。** 第一问查入学人数最多的学校，第二问只到“年级范围”，Builder 补成“这些学校提供什么年级”；后续用户实际指定经度最高的学校。
5. **完整输入可以保留双问文字，但不等于两问均获回答。** 第二轮八个最终双问输出由助手检查，均保留两项请求；仍被编码成一个查询向量，没有独立覆盖判定。
6. **未证明规范化改善 cache hit。** 第一轮八个原始缓存问题在 final 输入时，原文和改写均 top-1 命中自身，仅是 sanity check；held-out 问题没有答案复用标签。

## 已讨论但尚未实现

- 提示词改成“输出已经明确的部分，不让未完整后半句整体阻塞”。**两轮实际运行均用旧的固定提示词**，不能把讨论当作已修改。
- 多子问题输出、每问 readiness、稳定 ID、修订/取消/覆盖状态。
- 基于 similarity 趋势触发重型 SQL/RAG；尚无有效阈值。
- 检索 question＋SQL 示例辅助下游 SQL Generator。
- 真正 LiveKit preemptive generation 对照，见 [必须保留的实验要求](../v6/NEXT-VERSION.md)。

## 公司电脑下一步：优先验证整体收益

1. 检查公司实际 LiveKit Agents 版本、STT final 是片段还是整回合、Vertex 模型和工具调用接口，禁止直接套用最新版文档的接口。
2. 建立完整 STT → cache / SQL / RAG 的基线；cache hit 不应强制先经过 Builder。
3. 先验证 LiveKit preemptive 是否真的提前启动所需后端工作，以及输入未变时能否保留任务。`on_user_turn_completed` 改上下文/工具可能使预生成失效，需按实际 SDK 验证。
4. 再比较 partial Builder 路径：记下有效 partial、最终 STT、回合确认、Builder 完成、后端启动、首个有效答案输出/音频的时刻。按 cache hit、SQL miss、外部 RAG 分组。
5. 记录正确结果到达时间、错误复用、丢弃工作、额外调用和 token；失败必须留在分母中。别用 filler 音频冒充有效答案。
6. 如果 Builder 完成时常规路径已经开始，或无法让正确答案提前，就从该类请求中移除它。长问题和慢 RAG 可单独保留实验资格，不必全流量使用。

例如有效 partial 仅早 300ms、Builder 花 800ms，则该分支反而在最终文本后 500ms 才准备好检索。此例是解释性假设，不是本轮测量。

提示词可做一次限定修改再测，但不以减少 wait 作为最终目标。暂不增加远程 gate、训练模型或优化 similarity 趋势来掩盖尚未证明的端到端收益。

## Clone 后如何复现

只阅读证据、运行边界测试不需要模型或 DB。进入此目录：

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```

跑文本回放需要单独 Python 环境、`requirements.txt`、本地 embedding 模型和自己的 endpoint 配置。**不要复用本机 `/private/tmp/...` 路径**。可从第一轮 `evidence/partial-20260913/runtime-lock.txt` 查看实际版本；它包含本机环境，其他平台安装仍需检查兼容性。

Embedding 来源：`qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q`，revision `faf4aa4225822f3bc6376869cb1164e8e3feedd0`。通过 Hugging Face `snapshot_download` 获取 `*.json` 与 `model_optimized.onnx`，将返回目录传给 `--model-path`。runner 只从指定本地目录加载模型，不能假设 clone 会带模型。

```sh
python replay_gated.py \
  --data-root ../complex-data \
  --model-path /YOUR/LOCAL/MODEL/SNAPSHOT \
  --env-file /YOUR/LOCAL/CONFIG.env \
  --minimum-words 3 \
  --output evidence/company-replay-NEW-ID
```

输出目录必须不存在。`--env-file` 由程序读取，进程环境优先；不要向 agent 展示密钥。现有 DeepSeek 支持 `DEEPSEEK_API_KEY`；覆盖项为 `RAG_LLM_BASE_URL`、`RAG_LLM_MODEL`、`RAG_LLM_API_KEY_ENV`、`RAG_LLM_THINKING`。**当前 HTTP 客户端是 OpenAI-compatible，不是已实现的 Vertex 原生身份认证适配器。** 公司 agent 应先适配实际接口再运行。

这两个 v7 runner 只需 `selected-cases.json` 和 `cache-split-plan.json`，不需要下载 SQLite 实体。若继续测 v6 SQL，再按 [数据 README](../complex-data/README.md) 获取约145MiB DB 和修正描述；遵守 CC BY-SA 4.0 归属声明。

## 推送范围与原始证据

当前新增且未跟踪的目录是 `complex-data/`、`v6/`、`v7-partial/`；仅推送 v7 会漏掉所需 JSON 数据及前置设计。按实际 repo 根路径选择性暂存这三个目录，审阅后自行 commit/push。不要使用工作区配置副本代替 `/Users/codingleo/Documents/LearningVault` 中的真实 repo。

现有忽略规则排除 `.data/`、`.venv/`、`__pycache__/` 和凭据 `.env`。准备时按 Git 可见文件检查：103 个新增文件约3.6MB（本交接文档加入前），未发现待上传的运行时目录或凭据文件名；`.env.example` 是唯一相关模板文件名，未读取其内容。这不是全仓库敏感信息审计。

- [第一轮报告](RESULTS.md) / [原始汇总](evidence/partial-20260913/summary.json)
- [第二轮设计](GATED-DESIGN.md) / [第二轮报告](GATED-RESULTS.md) / [原始汇总](evidence/gated-long-compound-20260913/summary.json)
- 两个 evidence 目录的 `results.jsonl`、`timing.jsonl`、`cases.json`、`manifest.json` 保留逐步输出与提示词/代码哈希。
- [交接索引](vibe-discipline/index.md)

## 给公司 agent 的起始消息

> 请先阅读 `40-Exercises/Sandbox/LiveKitAnticipationPoC/v7-partial/HANDOFF.md` 及两个实验报告。当前 v7 是独立文本回放，不是 LiveKit 集成。先检查公司实际 SDK/STT/Vertex 配置，建立完整 STT 基线和 LiveKit preemptive 对照，再判断 partial Builder 是否值得接入。保留快速 cache 路径；不把单次 embedding 候选或高分当作答案适用性。提示词优化与多子问题契约仍未实现，请先说明最小改动及验证指标。保留所有旧实验与失败记录，不把本地合成时间线当作生产提速证据。公司数据、配置与新日志应按内部 repo 规则存放，不回传公开实验 repo。

交接完成意味着证据和边界可继续使用，不代表生产集成完成或学习掌握度已被验证。
