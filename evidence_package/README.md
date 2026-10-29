# 机制证据包：AI导购理由撤回后的预算重审 (Evidence Package v2)

> **定位说明**：本证据包是“AI导购理由撤回后的预算重审”课题的核心底层研究基石，旨在为后续报告撰写、系统算法审计及未来验证研究提供规范统一、认识论清晰、数据可溯源的完整支撑材料。**本项目不开展真人实验，继续暂缓报告正文、网页、PPT及提交材料制作，集中夯实底层证据链。**

---

## 证据包核心组件索引

1. **[证据身份与认知效力分级表 (Evidence Identity Table)](evidence_identity_table.md)**  
   - 严格区分 7 类材料：国内真人二手数据 ($N=516$)、机制仿真 ($48$ 单元)、规范配对案例 ($H_1 \sim H_4$)、文献理论锚点 (M4/W1 等)、法定底线依据、论坛质性线索及未来验证方案；
   - 确立“仿真 $\neq$ 心理实证”、“二手数据 $\neq$ 自身发现”、“法规 $\neq$ 伦理机制”的三大隔离准则。

2. **[机制参数溯源与敏感性分析总表 (Parameter Provenance Table)](parameter_provenance_table.md)**  
   - 逐项明确 11 个核心参数与权重体系的分级属性（文献锚定、国内数据约束、研究者假设）；
   - 详尽记录 $N=1000/5000/10000$ 样本量稳定性检验、400 点反转临界区域扫描（$\rho \le 0.35, \kappa \le 0.12$）以及三套综合损失权重敏感性。

3. **[四类典型交互场景配对案例矩阵 (Paired Case Matrix)](paired_case_matrix.md)**  
   - 完整还原 iPhone 15 充电器选购构造情境下的 $H_1$（撤回相连）、$H_2$（独立偏好）、$H_3$（知情重申）与 $H_4$（明确退出）四种业务场景；
   - 严格界定数据性质：150 元为模型构造基准（当日参考价格），20W/30W/27W 为情境假定，不作为产品事实结论；附录可追溯技术参考台账与降级说明（Apple 官网当日参考价格、官方宽泛技术文本参考及网络社区场景线索 CUE_CASE01）。

4. **[触发—措施—验收—停止矩阵 (TAAS Matrix)](trigger_action_acceptance_stopping_matrix.md)**  
   - 建立全生命周期五维控制架构，明确 S5 触发充要条件与单轮交互强停规则；
   - 确立系统越权判定四道红线（擅自改写、豁免后干预、隐瞒依赖、忽略退出）与异常捕获代码断言。

5. **[关键缺口文献与官方法规专项核验台账](literature_statute_verification.md)**  
   - 逐项核验 C1 李术平、Brenncke 两篇、W2 Oh、W3 Zhang 及网信办第 14 条、消保条例第 24 条适用边界。

---

## 证据包独立校验文件与配套清单索引

- 证据包专属哈希清单：[`evidence_manifest.json`](evidence_manifest.json)（`evidence_manifest.json` 与 `evidence_checksums.sha256` 自身不参与自引用校验，避免哈希死锁）
- 证据包校验哈希条目：[`evidence_checksums.sha256`](evidence_checksums.sha256)
- 机制仿真主目录哈希清单：[`v2_manifest.json`](file:///d:/AI理论/simulation/validation/v2_manifest.json) 与 [`v2_checksums.sha256`](file:///d:/AI理论/simulation/validation/v2_checksums.sha256)
- 14 项模型与数据不变量清单：[`invariant_checks.csv`](file:///d:/AI理论/simulation/validation/invariant_checks.csv)

- 机制仿真配置文件：[`parameters.json`](file:///d:/AI理论/simulation/config/parameters.json)、[`sensitivity_grid.json`](file:///d:/AI理论/simulation/config/sensitivity_grid.json)
- 48 单元全因子模拟数据：[`strategy_comparison.csv`](file:///d:/AI理论/simulation/results/strategy_comparison.csv)
- 12 项模型不变量审计清单：[`invariant_checks.csv`](file:///d:/AI理论/simulation/validation/invariant_checks.csv)
- 参数体系与模型全项审计报告：[`parameter_audit.md`](file:///d:/AI理论/simulation/validation/parameter_audit.md)
- 版本全库 SHA-256 哈希清单：[`v2_manifest.json`](file:///d:/AI理论/simulation/validation/v2_manifest.json)
- 理论基准一致性对比清单：[`python_matlab_comparison.csv`](file:///d:/AI理论/simulation/validation/python_matlab_comparison.csv)
- 样本量收敛性检查数据：[`convergence_check.csv`](file:///d:/AI理论/simulation/validation/convergence_check.csv)
- 损失权重敏感性数据：[`weight_sensitivity.csv`](file:///d:/AI理论/simulation/validation/weight_sensitivity.csv)
- 二维反转边界网格数据：[`parameter_sensitivity.csv`](file:///d:/AI理论/simulation/validation/parameter_sensitivity.csv)
