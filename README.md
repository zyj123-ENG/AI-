# AI导购理由撤回后的预算重审

第八届AIC算法大赛“AI伦理”研究工作库。2026-10-29依用户最新要求，只交付国内二手数据的仿真分析部分；此前虚拟数据和国外数据仿真已从仓库当前版本删除。

后续用户另提供补强稿并明确要求替换其中数值部分，已完成[用户补强稿的国内数据替换版](research/user_reinforced_domestic_revision_20261029/README.md)。这是对所给文件的定向修改，独立仿真报告仍保留，不恢复旧数据模块。

## 当前交付

- [v2 机制仿真与三层锁定验证包](simulation/README.md)：48 单元全因子配对机制仿真（4 历史情境 × 3 负担水平 × 4 策略）、14 项数学不变量与 Manifest 校验全通过（14/14 ALL PASSED）、Python 与 MATLAB 桌面端双向对齐验证（详见 [MATLAB Bridge 比对报告](simulation/matlab_bridge_v2/matlab_python_comparison.md)）。
- [机制证据链与合规边界包](evidence_package/README.md)：包含证据身份表、参数谱系表、TAAS生命周期控制矩阵、iPhone 15 配对案例矩阵与法规核验台账（双 Manifest 独立哈希锁定）。
- [核心创新论证补强](research/direct_argument_validation_20261030/README.md)：2026-10-30完成强近邻比较、15项定向反例、原9轮元宝回复复核及直接比较设计；说明与操作缺口分型，相关修订已写回用户补强稿。真人预算修复效果尚未取得匹配资料。
- [独立报告 Word PDF 源稿](research/domestic_simulation_report_20261029/README.md)：6页、4表2图，含数据来源、变量与公式、回归、实际结果、稳健性和论文可摘用段落。
- [国内真人数据与实际分析代码](research/domestic_data_reanalysis_20261029/README.md)：516名国内渠道招募参与者，原六臂、分类OLS及每个人群5,000轮参与者重抽样；403人现场子样本作敏感性分析。
- [国内数据阶段续接提示词](planning/国内数据阶段续接提示词.md)与[后续任务](planning/下一阶段任务清单.md)：后续默认只维护仿真部分。
- [来源、许可与公开范围](provenance/PUBLICATION_SCOPE.md)及[旧仿真删除记录](provenance/removed_simulations_20261029.json)。

数据来自Huang等Study4的国内招募记录。实验模拟的是记忆陈述，回答来自真人；数据测即时信任，不能直接验证预算重审措施效果。[正式论文](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2026.1934857/full) · [作者固定数据版本](https://github.com/RunhuaHuang/aimemory/tree/3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53)

## 保留的研究材料

[literature 文献卡与读取记录](literature/) · [核心论文方法矩阵](research/B_核心论文论证方法矩阵.md) · [规范创新命题](research/创新点_可主张的具体命题.md) · [第一阶段基础](stage1/README.md)。国外理论文献保留正常引文身份，不作为国外数据仿真。

此前已生成的[国内全文前稿](research/phase6_domestic_report_20261029/README.md)仅供存档；用户要求当前只交付仿真部分，本轮不继续扩写全文。知网检测、PPT及正式提交均未在本轮执行。

## 核验与复现

国内模块README及独立报告给出可直接运行的MATLAB命令，基础MATLAB无需额外工具箱，独立输出目录避免覆盖已验证结果。仓库完整性核验使用Python标准库：

```text
python tools/verify_repository.py
```

原CSV、原件哈希、数据许可、固定版本、实际运行信息和独立复核保留；报告与图表不生成新的消费者回答。仓库删除通过常规Git提交完成，未改写既有提交历史。
