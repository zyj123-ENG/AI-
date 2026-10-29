# 仿真部分独立报告

用户最新要求仅交付仿真部分，本轮不继续撰写完整比赛报告。这里单独呈现已运行的国内真人二手实验复分析、分类OLS及经验重抽样。

2026-10-30证据定位补充：本计算模块为伦理方案提供经验背景，不直接检验完整预算重审方案。原六臂没有理由撤回、独立理由、知情重申等预算历史条件，也未直接比较普通事实纠错、一般再确认或元偏好反思；核心判准的创新仍由规范推理、配对规范案例和边界条件论证承担。

- [Word独立报告](国内二手数据重抽样分析报告.docx)
- [PDF独立报告](国内二手数据重抽样分析报告.pdf)
- [报告源稿](report.md)
- [报告生成程序](build_report.py)
- [输入结果哈希](生成记录.json)
- [交付核对](交付核对.json)
- [国内原数据、实际分析代码、许可和独立复核](../domestic_data_reanalysis_20261029/README.md)

516名参与者来自原研究的国内招募渠道，403名现场参与者为敏感性子样本。保留原六臂与原回答，每个人群5,000轮原臂内参与者bootstrap；这是计算重复，不增加真人样本。报告包含4表2图、变量和公式、实际结果、核对范围、局限及可用于论文的结果段落。原数据测即时信任，预算重审措施效果留待直接研究。

独立报告6页，约2,950汉字，PDF551,336字节。最终6页已逐页检查；输入结果和图表与正式运行输出哈希一致。交付核对由`verify_report.py`生成。

本目录从已完成的结果CSV生成报告，不重跑主分析、不改写原数据。重新生成Word使用`python build_report.py`，需python-docx；图表直接复制正式MATLAB输出。需重新分析时，在仓库根目录的MATLAB运行：

```matlab
d = fullfile('research','domestic_data_reanalysis_20261029');
addpath(fullfile(d,'code'))
sourceFile = fullfile(d,'source','author_original', ...
    'data','study4_memory_data.csv');
run_domestic_reanalysis(sourceFile,fullfile(d,'results_reproduced'))
```

请先核对原CSV SHA256；独立复现输出另存，勿覆盖已验证结果。已生成的全文前稿保留为历史资料，当前交付入口以本目录为准。
