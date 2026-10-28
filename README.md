# AI购物助手的纠错与目标重审

第八届AIC算法大赛“AI伦理”研究工作库。更新：2026-10-29。

研究场景：中国成年消费者使用中文建议型AI购物助手，为iPhone 15选购一只充电器。

**主问题：重要购买理由被撤回后，AI何时应说明它与消费者既有目标修订的联系，并重新开放自愿选择？**

例如，用户原预算150元，主要因AI声称某款更安全而提高到200元；后来安全优势失去证据支持。研究区分事实更正、关联说明、自愿重选和替用户改写预算，并给出独立理由、知情重申、退出与信息负担的边界。

## 从这里阅读

1. [当前可主张的创新点](research/%E5%88%9B%E6%96%B0%E7%82%B9_%E5%8F%AF%E4%B8%BB%E5%BC%A0%E7%9A%84%E5%85%B7%E4%BD%93%E5%91%BD%E9%A2%98.md)
2. [整合研究方案](research/%E5%8F%82%E8%B5%9B%E7%A0%94%E7%A9%B6%E6%96%B9%E6%A1%88_%E6%95%B4%E5%90%88%E5%AE%A1%E9%98%85%E7%89%88.md)
3. [核心论文怎样论证](research/B_%E6%A0%B8%E5%BF%83%E8%AE%BA%E6%96%87%E8%AE%BA%E8%AF%81%E6%96%B9%E6%B3%95%E7%9F%A9%E9%98%B5.md)
4. [实际仿真结果入口](research/simulation_goal_repair_20261028/00_%E5%85%88%E7%9C%8B%E7%BB%93%E6%9E%9C.md)
5. [可并入论文的方法、结果与讨论](research/phase4_simulation_sections_20261028/draft.md)
6. [下一阶段任务及验收](planning/%E4%B8%8B%E4%B8%80%E9%98%B6%E6%AE%B5%E4%BB%BB%E5%8A%A1%E6%B8%85%E5%8D%95.md)
7. [下一阶段可直接使用的提示词](planning/%E4%B8%8B%E4%B8%80%E9%98%B6%E6%AE%B5%E6%89%A7%E8%A1%8C%E6%8F%90%E7%A4%BA%E8%AF%8D.md)

## 目录与研究阶段

|目录|用途|
|---|---|
|`research/`|研究方案、近邻检索、论文方法矩阵、预试记录、代码、结果与图表|
|`research/simulation_goal_repair_20261028/`|当前仿真的正式复现目录；优先使用此处的代码和结果|
|`research/phase4_simulation_sections_20261028/`|已完成的仿真章节、可编辑Word、图表与生成/核对代码|
|`literature/`|文献目录、21篇文献卡、BibTeX/RIS、原始汇总及可再分发的全文|
|`stage1/`|“拒绝后的再建议边界”第一阶段报告，作为理论与边界基础|
|`planning/`|主线衔接、七项评分对应、下一阶段任务、执行提示词与材料核对|
|`provenance/`|全部本地来源清单、原件/公开副本哈希、许可、公开处理及仓库校验记录|
|`tools/`|公开副本整理及仓库核验工具|

第一阶段处理已经表达的预算、拒绝与重开范围。当前主线推进到用户尚未主动撤回目标时的纠错责任。第一阶段不作为并列主题，原扩展坞案例不与当前充电器案例拼接为同一实录。[阶段衔接说明](stage1/README.md)

## 复现

在MATLAB R2023b或兼容版本中，进入正式复现目录：

```matlab
cd research/simulation_goal_repair_20261028
addpath('code')
run_goal_repair_simulation('smoke') % 小规模运行，输出results_smoke
run_goal_repair_simulation('full')  % 正式运行，输出results
```

模型使用基础MATLAB函数，无额外工具箱。种子20261028；正式基准每类40,000个合成条件，三类共120,000个；54个参数场景、10种策略、3种行为规则。完整运行会重建结果，建议先在独立副本运行。[公式参数](research/simulation_goal_repair_20261028/03_%E5%8F%98%E9%87%8F%E5%85%AC%E5%BC%8F%E4%B8%8E%E5%8F%82%E6%95%B0%E8%BA%AB%E4%BB%BD.md) · [复现与验收](research/simulation_goal_repair_20261028/05_%E5%A4%8D%E7%8E%B0%E4%B8%8E%E9%AA%8C%E6%94%B6.md)

仓库文件核验仅需Python标准库：

```text
python tools/verify_repository.py
```

## 结果的使用范围

- 全部模拟档案、商品、效用与行为参数为合成设定，参数未经真人校准。MCSE表示模拟积分精度。
- 元宝材料包含用户探索性试跑，以及研究者给定历史的限定预试；不构成真实消费者因果实验。
- 强选择性再确认与方案同构等参时结果完全相同；无效、反转及不适配率上升均保留。
- 规范责任通过独立推理讨论；规则符合、数值复现与消费者效果分别评价。
- `work/archive_pre_T3_fix_results/`为修复前历史结果；根目录的重复代码/结果不是独立实验。当前解释以正式复现目录及最新章节为准。

## 来源与公开副本

本地原件保持原样。公开副本清理个人机器路径和私密会话定位信息；数值输入、策略和结果不因公开整理而改写。已核验Creative Commons许可的第三方PDF保留署名、出处与许可。其余全文及提取缓存提供来源索引、获取入口与SHA256。[完整公开范围](provenance/PUBLICATION_SCOPE.md) · [许可记录](provenance/third_party_licenses.json)

本库记录研究进展，尚未形成完整参赛提交包。知网查重报告、完整答辩PPT与最终匿名验包等状态见[下一阶段任务](planning/%E4%B8%8B%E4%B8%80%E9%98%B6%E6%AE%B5%E4%BB%BB%E5%8A%A1%E6%B8%85%E5%8D%95.md)。GitHub工作库不能替代赛事要求的百度网盘补充材料链接。

赛事依据：[官方通知及两个附件](https://www.aicomp.cn/notice/notice-3/3921.html)，[赛程调整通知](https://www.aicomp.cn/notice/notice-3/5435.html)。AI伦理作品截止为2026-10-30 20:00；提交前再次核对官方更新。
