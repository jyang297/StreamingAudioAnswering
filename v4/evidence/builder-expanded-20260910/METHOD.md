# 扩展Builder诊断：方法与解释边界

2026-09-10。用户接受wait不送Checker/跳过，不要求把保守wait视为故障；要求扩大原10条用例。v1/v2提示词冻结，不新增v3、不在本轮按结果调参。当前Pipeline仅将有plan.query和有效retrieval的候选送Checker；final plan无query时直接返回no_query，Checker不运行。Answerer后续重写行为未改变。

## 范围

100条新开发样例，10个参数化场景族各10条：最近相关实体追问、显式切换、显式回指旧实体、多实体歧义、不支持的业务、短显式实体、相同query在partial/final阶段的不同契约、显式多条件、历史约束修订、长历史中的最新焦点。包括中文和英文。不是100种独立语义机制，不是公司数据或独立人工标注的holdout；原10条不并入这个分母。

每组首条作为sentinel，在每个版本下共采样3次；其余每版本1次。100×2+10×2额外次数×2版本=240次真实DeepSeek请求。报告主结果仅repeat0的100条/版本，重复不扩充独立样本量。随机种子20260910固定打乱240个任务，最多2并发；每请求独立HTTP client/metrics。报告延迟仅适用于这个运行方式，不能直接和上轮串行共享client延迟比较。

## 判定

- correct_retrieve：action、实体/价格/布尔/分类等明确约束符合预设；未指定排序/limit保持默认。
- appropriate_wait：歧义、unsupported或partial重复的保守wait。
- missed_retrieve：标签认为可构建query，但模型wait；是安全地放弃机会，不是错误复用。
- wrong_query：模型生成的实体/显式约束不符合标签，优先关注；具体差异逐例保存。并非每种差异都已证明会导致最终错误答案。
- unjustified_retrieve：标签要求wait，模型仍生成query，优先审查。
- query_variant_review：核心字段符合，但用户未规定的排序/limit偏离默认；可能无害或改变覆盖，单列待复核，既不算证明正确也不混作危险实体错误。
- api_or_contract_error：接口/JSON/schema问题，和语义问题分开。

名称大小写与数字int/float按SQL等价处理。所有retrieve标签显式覆盖name/category/min/max/in_stock/discontinued（未要求的字段为null），防止偷偷加过滤条件仍算正确。对于明确指定排序/limit的请求也严格检查这两项。

开发样例没有以公司语料抽样；按族报告而不是只报总体accuracy。置信区间或“零错误”都不能把这些相关的人工模板转换为生产保证。新版更多retrieve不自动更好；尤其重视歧义时的擅自查询。

源文件cases.json、prompts.json，逐调用results.jsonl，summary.json。实际模型与thinking记录在每条结果，所有请求都是任务公开测试文本，不含key。比较器不会将模型输出用于SQL执行，本轮无数据库测试或改动。

复现：`python builder_expanded_eval.py --cases evidence/builder-expanded-20260910/cases.json --output-dir runs/new-expanded-eval`。输出目录必须不存在，防止覆盖；共240次付费API请求，v4/.env供本地读取。评分单元测试与既有接口/调度回归39项通过。
