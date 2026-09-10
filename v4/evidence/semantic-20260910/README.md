# Semantic Checker 独立对照 · 2026-09-10

真实模型：sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2，经 qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q 固定 revision faf4aa4225822f3bc6376869cb1164e8e3feedd0，FastEmbed0.7.4、CPU两线程、mean pooling、384维、不加prefix。实际ONNX前向推理后计算cosine；无hash、词频、字符串重合或伪向量fallback。

12条人工标注、冻结结构化query的开发诊断，三个Checker使用同一候选与final query。LLM是真实DeepSeek API。四个应接受、八个应拒绝；没有候选的情况另由单元测试覆盖。输入生成和固定次序详见checker_comparison.py。一般query覆盖标签，独立于当前数据库数据巧合。不是随机抽样、holdout、生产准确率或公平输入token基准。

| Checker | 正确/12 | 误接受 | 误拒绝 | 单次决策耗时中位数 |
|---|---:|---:|---:|---:|
| exact | 10 | 0 | 2 | 0.032ms |
| DeepSeek LLM | 12 | 0 | 0 | 907.604ms |
| 真实cosine，threshold=.99 | 8 | 2 | 2 | 45.212ms |

模型加载5255ms、预热143ms单列；semantic在线28–617ms，未缓存向量。上表只有Checker，不含Builder、数据库、回答；固定顺序的单次数据不能推导稳定p95或端到端收益。

关键真实分数：category 1→2 得0.995850；min_price20→10得0.993008，两者在.99误接受。CHANG→Chang得0.962471，而数据库名称比较不区分大小写；min_price10→10.0得0.986272，但数值条件等价。这也暴露当前query_text模板/数字表示影响，不应归纳为所有embedding模型的固有准确率。

| 阈值 | 误接受/8 | 误拒绝/4 |
|---:|---:|---:|
| .90 | 7 | 0 |
| .95 | 6 | 0 |
| .98 | 4 | 1 |
| .99 | 2 | 2 |
| .995 | 1 | 2 |
| .999 | 0 | 3 |
| .9999 | 0 | 3 |

扫描在同一开发集进行，不选生产阈值。.999在本组0误接受并不意味着安全，且错拒了3/4有效样例。未来可独立增加“结构化约束校验+语义分数”组，但不能偷偷混入本纯cosine组。

完整LiveKit额外smoke：真实DeepSeek Builder/Answerer、真实本地PostgreSQL、脚本STT；Chai partial提前2000ms，final相同，semantic .99选中ready候选，cosine≈1，回答18。语义Checker耗时130.156ms。不是麦克风/ASR/TTS实验。原有重复调度保持不变。

47项本地测试通过（包含真实DB/SDK回归）；cosine数学单元测试明确使用手工二维数字，只验证数学函数，不作语义质量证据。独立只读review未发现当前范围critical issue；单一ONNX worker退出仍可能等待原生推理，生产硬deadline需要进程隔离。

文件：comparison.json（全部分数、判定、LLMusage/耗时和阈值扫描），livekit-result.json，livekit-timing.jsonl。没有密钥或公司数据。

原始模型卡：https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
FastEmbed模型说明：https://qdrant.github.io/fastembed/examples/Supported_Models/
