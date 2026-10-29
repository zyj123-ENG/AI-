# 国内真人二手数据：当前经验分析

2026-10-29。按用户要求，主分析改为国内采集的既有真人记录，国外牙膏数据和自创行为模型均退为历史。这里采用**原六臂数据复分析、分类OLS及参与者重抽样**，没有生成新的消费者回答。

## 原始来源

Huang, R., Huang, Y., & Guo, H.（2026），*Remembering or monitoring? Contextual fit of simulated AI memory cues and consumer trust*，Frontiers in Psychology 17:1934857。[正式全文](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2026.1934857/full)；[作者固定版本数据仓库](https://github.com/RunhuaHuang/aimemory/tree/3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53)。

正式方法§2.1说明2026年3—6月从浙江商业职业技术学院课程和校园社区渠道招募18岁以上、中文流利者。主用Study4的516份保留记录：学生316、居民200；现场403、网络113。国内采集依据原方法，不等同中国国籍核验或全国代表性。GitHub是公开托管平台，地点不决定参与者来源。

标题中的“simulated”指原作者构造了记忆提示条件；回答由真人完成。原任务是夹克购物原型，三种记忆消息包×有/无查看、编辑、删除记忆面板，共六臂；不是自然交易日志，也不是商业披露×预算重选。三道信任题按正式S14全部正向、无反向的规则取均值。

## 实际结果与完成状态

基础MATLAB R2023b已运行。主516、现场敏感性403，每个原臂内5,000轮按人重抽样，种子20261029和20261030。没有增加真实人数、插补预算或生成未观测干预反应。

- 主δ＝侵入组面板信任增量−无记忆组面板信任增量：−0.160个量表点，逐项95%重抽样区间[−0.542,0.220]。区间跨0不证明等效、无效或所有控制无用。
- 次要的面板平均差0.186，区间[0.032,0.341]。平均评价与特定差距是不同统计对象，不能相互替代。
- 现场403份δ为−0.199，区间[−0.646,0.250]；平均差0.162，区间[−0.013,0.338]。保留精度变化，不只展示更有利结果。
- 交互F(2,510)=0.538、p=0.584；原两组均值/SD舍入与论文4.49、4.30和0.91、1.00一致。独立Python复算56项组内统计、84项差值、12个OLS系数、252项频数及模型F/p全部一致，未独立重跑bootstrap区间。

这些是原研究记录的复核及计算口径扩展，不作为本文新心理效应发现。信任不是规范自主性；数据没有测预算修订、理由撤回、控件实际使用或操作负担，不能据此声称预算重审方案有效。

## 可追溯材料与复现

- [计算前方案](01_执行前方案.md)
- [国内来源及候选取舍](02_国内来源与数据取舍.md)
- [原件、固定版本、许可和哈希](来源与许可.json)
- [原作者Study4 CSV](source/author_original/data/study4_memory_data.csv)、[原LICENSE](source/author_original/LICENSE)、[字典](source/author_original/data/data_dictionary.md)
- [主程序](code/run_domestic_reanalysis.m)、[独立Python复算](code/independent_validate.py)、[仅重绘图](code/render_domestic_figures.m)
- [组内统计](results/cell_estimates.csv)、[差值及区间](results/contrasts.csv)、[模型复核](results/model_checks.csv)
- [独立验证](validation/独立复算.json)和[方法审读](validation/方法审读.md)
- [当前完整国内数据报告](../phase6_domestic_report_20261029/README.md)

```matlab
addpath('research/domestic_data_reanalysis_20261029/code')
run_domestic_reanalysis('作者原Study4 CSV路径','独立输出目录')
```

先与来源JSON核对SHA256。原作者匿名数据按CC BY4.0署名保留原件；本项目的分析与图表是派生成果，未改原CSV。作者分析脚本、完整刺激协议和排除日志未公开，没有假称取得。`bootstrap_aggregates.mat`只存重抽样统计量，不是新的真人数据集。
