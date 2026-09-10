# DeepSeek 真实 API 首轮测试 · 2026-09-10

结论：链路跑通，六个成对测试回答都符合 Northwind 样例数据；本轮没有证明提前检索加速。额外的一次已完成旧查询改口测试也正确回退。AI 执行的 smoke test，不代表用户独立掌握或生产正确率。

## 条件和边界

本机 Python LiveKit Agents 1.8.0、Docker PostgreSQL 77 条公开 Northwind 产品数据、真实 DeepSeek API，deepseek-v4-flash，thinking disabled。一个脚本 STT provider，没有真实识别、麦克风、TTS或音频延迟测量。常规先跑、投机后跑，各一个三轮 session，没有随机化或统计显著性。partial 到 final 人工间隔 500ms（库存追问无 partial）。

| 用户输入 | 正确内容 | 常规 final→完整文本 | 提前检索 final→完整文本 | 投机路径 |
|---|---|---:|---:|---|
| What is the price of Chai? | 18 | 1955.5ms | 2312.6ms | reuse_ready |
| Stock? | Chai 库存39 | 1354.9ms | 1715.5ms | demand |
| Actually, what is the price of Chang? | 19 | 1785.1ms | 1614.3ms | demand |

常规6次 endpoint 请求、3次 DB 查询、API 报告2734 tokens；投机12次 endpoint 请求、3次 DB 查询、已返回usage共4173 tokens。投机旧版日志中有2次 status=error 的 Builder，没有足够错误类型信息区分取消和接口失败；不能算作确定的 API 故障，也不能将没有usage的请求视作零计费。后续已补 cancelled/error_type 指标。Token 数不是账单金额。

数据库查询在这两个 session 为4.8–24.9ms。首次独立 smoke 的一次 DB 查询518.7ms，说明本机也有启动/运行抖动；不等价于 Cloud SQL 基准。首次 smoke 正确回答后，数据库关闭抛 TimeoutError，命令退出1；增加5秒关闭上限、超时终止连接池并告警，CLI保证关闭endpoint，后续两个session及补测均退出0。

## 从 trace 得到的调度问题

1. 投机session第1轮，final在572ms收到；partial Builder在726ms附近才完成。检索虽最终命中，不能称为用户说完前知识已准备好。
2. 最终 FINAL_TRANSCRIPT 仍会调用 observe，在 final路径外再建一个投机Builder。Stock? 没有partial也触发投机请求，存在无效重复开销。
3. 第1轮 final query Builder 和Checker仍在最终文本之后执行；Checker约635ms，本例省掉的DB工作仅约25ms。
4. “reuse_ready”只表示Checker选择时检索已完成，不表示说完前完成，更不意味着总体加速。

这些发现支持下一轮先修终点附近的重复调度、完善候选时序和角色成本指标，再评估Checker策略。此轮未修改查询判定/调度语义，保留可比较的原始行为。语义相似度准确率实验仍待另行设计。

## 已完成旧查询的纠正补测

独立session先发 Chai partial，人工等待2000ms，再最终问Chang。Chai Builder约961ms返回；Checker被实际调用并成功返回；最终path=demand、仅向Answer交付Chang证据、回答19。证明本样例未复用旧实体，不能推广成一般纠错准确率。5次endpoint调用、2次DB查询（以raw记录为准）。final→完整答案约8466ms，存在明显调度/运行抖动，不与上述单样本拼接为稳定延迟估计。

## 保存的证据

`baseline-smoke.json`（首次退出失败但已生成答案）、`baseline.json`、`speculative.json`、`correction.json`、`turns.json`、`summary.json`。文件只含公开样例数据与测量，不含 API key。

修复后的离线测试37项通过，包括超时清理及取消分类。没有进行生产部署或Jetson实验。
