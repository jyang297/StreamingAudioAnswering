# Builder prompt v2 单轮对照 · 2026-09-10

用户明确担心sandbox过拟合，授权测试一个版本并记录可迁移性限制。接口不变：retrieve/query 或 wait；v1逐字保留，仍为默认。v2需显式 `--builder-prompt v2`。不包含具体商品名、不修改数据库schema、Checker、触发策略或Answerer提示词。实验冻结后只跑一次，不根据结果追加调优。

## 改动假设

在相同catalog schema下，v2说明历史顺序、当前显式实体优先、最近相关问答补全省略、显式回指覆盖单纯近邻规则、历史长短不决定权重；final短句不自动wait，真实歧义仍wait。查询属性值与过滤掉零/false记录应区分。以上是通用任务约束，仍可能对当前模型/任务分布产生适配偏差。

## 实验与结果

真实DeepSeek，配置模型/模式见comparison.json。10条冻结输入×2版本，共20次调用，按样例交替v1/v2执行顺序，每个组合仅一次，无统计显著性结论。保存完整system prompt、user payload、原始JSON返回、解析后query、判定及token/耗时。数据不含公司信息。无DB、无Answerer，因此只测Builder，不是端到端正确率。

| 版本 | 满足预设契约/10 | 耗时中位数 |
|---|---:|---:|
| v1原版 | 8 | 931.94ms |
| v2实验版 | 9 | 978.59ms |

关键样例：
- 原长问题Chai→Chang price?→Stock?：v1返回wait；v2返回retrieve/name=Chang。
- 实体与表述同时替换，Ikura→What about Tofu?→Stock?：两版均wait，预期可沿Tofu查询。本例不是单独控制实体变量，因此不能推断具体失败原因。
- 中文库存追问、明确回指Chai：两版正确。
- 两个候选实体指代歧义、无上下文Stock?、不支持的银行业务：两版wait。
- 最终短实体输入、未完成partial、final重复既有query：两版符合预设契约。

判定只检查action和关键Query字段（实体及不能擅加的过滤条件）；不要求order/limit字符串完全相同。不把局部契约通过称为全面语义等价。预设标签和完整输入见cases.json；它们是AI编写的开发诊断，不是独立人工标注测试集。

## 可迁移性与保留的风险

1. 新版解决已知样例但没有消除同类失败，暂不升为默认，不证明recency规则是唯一原因。
2. 全部支持查询仍使用Northwind schema，替换商品名/中英文表述不等于跨领域、跨schema或GCP真实流量验证。
3. 原失败参与了prompt设计，不能作为holdout。测试集有限、每个组合只采样一次；温度0也不视为绝对可复现。
4. 云部署环境变化本身不会修复指代；需在公司实际STT事件、会话组织、schema和endpoint配置下另做冻结输入验证。
5. 原接口wait仍同时表示partial不足与final无法构建，Answerer对空证据仍可重写；本次没有改变该设计，不能声称消除了下游错误指代。
6. 55项不依赖DB的回归测试通过；旧prompt逐字相等另行验证。本轮按用户优先级不处理本地DB超时。

## 复现

从v4运行：

```sh
python builder_prompt_comparison.py \
  --cases evidence/builder-prompt-20260910/cases.json \
  --output runs/builder-prompt-new-result.json
```

先创建runs目录；不要覆盖本目录已保存的comparison.json。首次运行需要本地.env中的DeepSeek key。此命令会发出20次实际API请求。v2整链路试验可在原CLI加`--builder-prompt v2`，默认仍v1。

结论：保留v2作为一个可选实验版本；在可迁移样本与重复测量前不宣称修复完成，不追着这10条样例继续调prompt。
