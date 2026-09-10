# 三组累计触发实验 · 2026-09-10

实现：time/text/hybrid共享一个partial Builder在途、一个最新pending。legacy保留。CLI公开窗口、变化量、partial请求预算和EOT接管等待参数。具体契约见../../INTERFACE-AND-SCHEDULING.md末节。

验证：旧功能与新增8项调度测试共55通过；随后增加等长替换、请求预算、取消抵抗任务3项，新调度11项全部通过。共58个不同测试有通过记录。包含实际DockerDB/LiveKit SDK，语言响应为脚本的测试不算真实模型质量证据。只读独立审查未发现当前调度范围缺陷。

真实实验：相同3轮，先长问题问Chai价格，再短问题问Chang价格，再Stock?追问。time/text/hybrid按固定顺序单次运行，150ms、3变化单元、6次partial预算、50ms同输入接管。Builder/Answer/LLMChecker均真实DeepSeek；真实SQL；脚本STT，无真实音频。参数见各result.trigger_config。

结果不支持排序策略优劣：
- time：前两轮正确，第三轮错答Chai库存39，预期沿最近实体Chang回答17。
- text：检索发生TimeoutError，前两轮未取得答案；第三轮也未完成有效查询。不应把故障导致少调用当作节省。
- hybrid：前两轮正确，第三轮同样错答Chai库存39。

错实体路径为final Builder返回wait（path=no_query），Answerer发起重写时选错实体；上下文记录确实包含较近的Chang问答，不是Checker错误接受候选。所有组本轮没有成功复用路径，不能声称调度改进带来加速。三条CLI命令exit0只是程序完成，不等于答案正确。

数据库观察：额外docker stats时容器仍运行，CPU21.40%、内存60.55MiB/7.654GiB；这是单次状态，不能定位超时根因。查询timeout需单独复现，未扩大deadline隐藏失败。本轮未改LLM提示词或Checker以保持实验变量清晰。

后续优先处理：无query/歧义与Answer重写的边界；最近实体指代失败；DB超时。待功能正确且服务稳定后，再增加重复/随机化时间组与文本组对照。保持false-positive优先，不用hit-rate或速度掩盖错误答案。

文件：turns.json输入；time/text/hybrid.json完整输出；对应.jsonl分步骤日志；summary.json计数与路径。没有密钥/公司数据。
