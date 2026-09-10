---
ai_contribution: authored
updated: 2026-09-10
---
# LiveKit PoC v4：当前运行与验证入口

Company handoff and English standup: [Transfer and demo quick start](TRANSFER-AND-DEMO.md) · [Agent prompt](COMPANY-AGENT-PROMPT.md) · [Migration contract](COMPANY-AGENT-HANDOFF.md) · [Offline presentation](demo/standup.html).


Python LiveKit、一个 STT 流、文本 endpoint Builder/Checker/Answerer、真实本地 PostgreSQL。仅 Mac 实验；v1–v3 和历史 checkpoint 保留。AI demonstration，不是论文复现或生产验收。

## 先看什么

- [文档总导航与续接清单](DOCUMENTATION.md)：设计、论文阅读、历史版本、所有评测的对应关系。
- [接口、STT 分批与三类问题](INTERFACE-AND-SCHEDULING.md)：接入 LiveKit 的位置和迁移必须保持的契约。
- [最新 v2/v3 约束保真实验](evidence/builder-fidelity-20260910/README.md)：36 条输入、108 次调用；仍有合法但漏条件的 Query，默认不变。
- [挑战集结果](evidence/builder-challenge-20260910/README.md)：24 条输入、72 次真实调用，包含新发现的条件遗漏/错误过滤。
- [100 条开发集结果](evidence/builder-expanded-20260910/README.md)：240 次真实调用，不能代替公司语料验证。

## 当前能力和默认值

| 部分 | 当前状态 |
|---|---|
| Builder | DeepSeek 实际联调；query 或 wait；默认 v1，`--builder-prompt v2|v3` 为可选实验组（实际参数选一个版本） |
| Checker | 默认 LLM；exact 和真实 ONNX/cosine semantic 为独立对照，semantic 必须显式给阈值，无生产推荐值 |
| 检索 | Docker PostgreSQL，77 条公开 Northwind 商品；参数化只读 SQL，不由 LLM 编写 SQL |
| 调度 | time/text/hybrid/legacy；候选共享检索、有界等待、过期任务防护；只等待 Checker 选中的任务 |
| Answerer | 用证据生成回答，最多一次重写检索；已有错误追问案例，尚未证明端到端正确 |
| LiveKit | 实际 SDK 1.8.0、脚本 STT、顺序轮次、自定义 PipelineLLM；无真实 ASR/TTS/麦克风/打断验证 |
| 语音收益 | 未测真实语音延迟、TTFT/TTFAT；不能用脚本 gap 或成功复用当作加速证明 |

CLI 默认常规基线，只有加 `--speculate` 才启用提前检索。启用后默认 `time`、150 ms、变化量 3、partial 请求上限 6、有效候选上限 2、同输入 EOT 接管上限 50 ms。text/hybrid 可以由变化量先触发，因此不是一律等待 150 ms。Python `Pipeline()` 构造器仍默认 `speculate=True, trigger_policy='legacy'`，直接调用时应显式传参数。所有阈值都是实验起点。

## 数据流与 wait

```text
单个 STT → 累计文本快照 → partial Builder
                             ├─ wait：不创建检索、不成为 Checker 候选
                             └─ query：创建或共享当前候选的检索 task
SDK 确认 EOT → 取得 final Query（同输入已有有效计划可接管）
                             ├─ wait：no_query，跳过 Checker
                             └─ query → Checker 选候选
                                          ├─ 适用：复用结果／等待选中任务
                                          └─ 不适用：按 final Query 常规检索
Bundle → 当前 hook 中的指针 → 自定义 PipelineLLM → Answerer
                                                   └─ 最多一次普通重写检索
```

`wait` 是允许的保守行为；“有机会却 wait”与“错误 Query/错误复用”分开记录。final wait 不意味着 Answerer 不运行：它仍可能发起重写，旧实验已发生此阶段错选实体，因此不能把跳过 Checker 等同于整轮安全。

Builder 重复输出不等于多执行 SQL：相同结构化 Query 在当前有效候选内共享检索 task。新回归测试验证三种新策略下，两个 Builder 输出仅触发一次检索，旧候选淘汰也不会误杀共享任务。这不是跨轮缓存，也不保证不同结构表示或已淘汰查询去重。

Checker 负责早期 query 是否适用于最终需求，不负责证明 Builder 忠实表达了用户所有约束。两边 Query 若都漏掉约束，单靠两者匹配不足以保证答案正确。

## 本机运行

工作目录为本文件所在 v4；既有 Python 环境 `/private/tmp/livekit-anticipation-poc-venv`。配置已支持固定加载 `v4/.env`，不向上搜索，进程环境变量优先。现有 `DEEPSEEK_API_KEY` 足够选择默认 DeepSeek 地址、`deepseek-v4-flash`、thinking disabled；三个角色是独立请求。不要用模板覆盖已有配置，也不要提交密钥。

首次准备参考 [依赖](requirements-v4.txt) 和 [数据库说明](postgres-fixture/README.md)。`setup.sh`/`import.sh` 会重建任务内示例表，已有环境日常测试不需要重新导入。容器名 `livekit-rag-postgres-fixture`，端口 `127.0.0.1:55432`；DB 凭据由显式 `--credential-file` 读取。

```sh
# 常规基线；真实 API 调用。
/private/tmp/livekit-anticipation-poc-venv/bin/python -m rag_poc.cli \
  --credential-file postgres-fixture/.env --text 'What is the price of Chai?'
# 同一 final，加脚本 partial；gap-ms 不是真实说话时长。
/private/tmp/livekit-anticipation-poc-venv/bin/python -m rag_poc.cli \
  --credential-file postgres-fixture/.env --speculate --builder-prompt v1 \
  --partial 'What is the price of Chai?' --gap-ms 2000 \
  --text 'What is the price of Chai?' > result.json 2> timing.jsonl
```

多轮输入 `--turns-file`：`[{"partials":["Chai"],"final":"Chai","gap_ms":150}]`。各组比较时固定 prompt、Checker、转写和人工 gap，只变待研究因素；结果记录 `trigger_config` 和 `builder_prompt`。

通用配置见 [config.example.sh](config.example.sh)，DeepSeek 显式环境变量见 [config.deepseek.example.sh](config.deepseek.example.sh)。未配置真实 endpoint 会失败，不自动回退 scripted endpoint。`scripted_endpoint.py` 和 MockTransport 仅是协议/流程测试替身。Builder/Checker/Answerer token 上限分别 256/128/512，HTTP 单次 15 s，final 与 answer 阶段各 20 s，无隐式 HTTP 重试；预算不是生产 SLA。

## 每步骤日志

CLI stderr 为 start/end JSONL，stdout 为结果 JSON；`time_spent_ms` 是每步 wall-clock，包含内部等待。用 `turn/candidate/span_id/parent_span_id` 关联并发任务，状态区分 ok/error/cancelled。模型等待、队列等待、Checker、选中检索等待、demand/rewrite、Answer 和清理均按实际执行记录；没有发生的步骤不伪造零值。计时日志不含文本或密钥；完整结果与评测原始记录可以包含本次公开测试输入。

父子 span 和并发 span 不可直接相加。`final_to_full_answer` 是脚本 final 到完整文本事件，非 TTFT/TTS；`step_timings` 是 pipeline 内记录，完整初始化/清理日志见 stderr。LLM Checker 无候选会直接返回 null，此时可有 checker span 而无 HTTP 子步骤。

## 独立 semantic 对照

`--checker exact|llm|semantic`；semantic 需要 `--semantic-threshold`，例如 `.99` 仅为诊断参数，已观察到误接受。实现为固定 MiniLM 多语言模型的 384 维 ONNX 向量及真实 cosine，无 hash/词汇重合/伪向量替代，也不混入 exact 或 LLM 二次确认。

模型、revision、输入序列化、阈值、启动/在线延迟和既有结果见 [semantic 证据](evidence/semantic-20260910/README.md) 与 [实现](rag_poc/semantic.py)。依赖单独在 `requirements-semantic.txt`；默认模型缓存 `/private/tmp/livekit-semantic-models`，首次可能下载约 220 MB。无向量缓存；单一后台 worker，取消 await 不保证原生推理停止，硬超时需生产隔离设计。

## 验证与复现

```sh
# v4 控制、协议、日志与调度回归；数据库项默认跳过。
PYTHONDONTWRITEBYTECODE=1 /private/tmp/livekit-anticipation-poc-venv/bin/python \
  -m pytest -q -p no:cacheprovider
# 单独启用真实 DB/SDK 集成测试（需要本地服务可用）。
RUN_POSTGRES_TESTS=1 RAG_DB_CREDENTIAL_FILE=postgres-fixture/.env \
  PYTHONDONTWRITEBYTECODE=1 /private/tmp/livekit-anticipation-poc-venv/bin/python \
  -m pytest -q -p no:cacheprovider test_postgres.py
# 冻结挑战集复现：会产生 72 次真实调用；必须使用全新输出目录。
/private/tmp/livekit-anticipation-poc-venv/bin/python builder_expanded_eval.py \
  --cases evidence/builder-challenge-20260910/cases.json --output-dir /private/tmp/builder-challenge-new-run
```

最新本地回归：**74 passed, 3 skipped in 3.38 s**。3 项是未启用的真实 DB 测试，本轮未重测其可用性。既有 9 项是可控依赖下的并发/边界测试；本轮增加 6 项版本路由/评测回归，不能作模型语义质量证据。

完整各阶段证据与历史数字见 [文档总导航](DOCUMENTATION.md)。默认 prompt 和 Checker 未改变。v3 已按无法表达则 wait 的保守契约做独立实验，但仍漏条件；下一步用目标业务 schema 明确约束表达/覆盖，并以独立标注样本验证；本地 DB 超时按用户决定暂不优先修复。
