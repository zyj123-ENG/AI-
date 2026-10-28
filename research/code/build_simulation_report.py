from pathlib import Path
import csv
import hashlib
import json
import math
import statistics as st
import zipfile

root=Path(__file__).resolve().parents[1]
out=root/'results'
def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
summary=read_csv(out/'all_summary.csv')
contrasts=read_csv(out/'paired_link_contrasts.csv')
diagnostics=read_csv(out/'base_diagnostics.csv')
dx={(r['rule'],r['policy'],int(r['type'])):r for r in diagnostics}
index={(r['scenario'],r['rule'],r['policy'],int(r['type'])):r for r in summary}
cx={(r['scenario'],r['rule'],int(r['control']),int(r['type'])):r for r in contrasts}
def row(sc='base',rule='bounded_default',policy='D1_R1_C1',typ=1):return index[sc,rule,policy,typ]
def num(r,k):return float(r[k])
def pct(r,k):return f'{100*num(r,k):.2f}%'
def fnum(r,k):return f'{num(r,k):.3f}'
def mc(x):
    x=[v for v in x if math.isfinite(v)]
    return (st.fmean(x),st.stdev(x)/math.sqrt(len(x))) if len(x)>1 else (math.nan,math.nan)

# Recompute exported numerical raw data with Python stdlib, independently of MATLAB summaries.
raw=read_csv(out/'independent_validation_slice.csv')
assert len(raw)==40000
checks=[]
policies=['D1_R0_C0','D1_R0_C1','D1_R1_C1']
metrics=['goal_reviewed','dependent_unreviewed_upgrade','quality_regret','processing_load','no_purchase']
for policy in policies:
    target=row(policy=policy)
    for metric in metrics:
        x=[float(r[policy+'__'+metric]) for r in raw]
        mu,se=mc(x)
        # .mat uses single precision for raw continuous quantities; rate fields remain exact.
        err_mu=abs(mu-num(target,metric));err_se=abs(se-num(target,'mcse_'+metric))
        assert err_mu<2e-5 and err_se<2e-6,(policy,metric,err_mu,err_se)
        checks.append({'policy':policy,'metric':metric,'mean_abs_error':err_mu,'mcse_abs_error':err_se})
for metric in metrics:
    d=[float(r['D1_R1_C1__'+metric])-float(r['D1_R0_C1__'+metric]) for r in raw]
    mu,se=mc(d);target=cx['base','bounded_default',1,1]
    assert abs(mu-num(target,'delta_'+metric))<2e-5
    assert abs(se-num(target,'mcse_'+metric))<2e-6
for r in summary:
    if r['policy']=='D1_R1_C1':
        g=index[r['scenario'],r['rule'],'generic_selective',int(r['type'])]
        for key in r:
            if key in ['scenario','rule','policy','type']:continue
            a,b=float(r[key]),float(g[key])
            assert (math.isnan(a) and math.isnan(b)) or a==b
assert len(summary)==54*10*3*4
assert len(contrasts)==54*3*2*4
assert all(float(r['fact_understood'])==1 for r in summary if int(r['type'])==3)
oldfile=root/'work/archive_pre_T3_fix_results/all_summary.csv'
oldrows=read_csv(oldfile) if oldfile.exists() else []
old_index={(r['scenario'],r['rule'],r['policy'],int(r['type'])):r for r in oldrows}
unchanged=0
for r in summary:
    if int(r['type'])==1 and oldrows:
        old=old_index[r['scenario'],r['rule'],r['policy'],1]
        assert r==old,'T1 changed during T3-only correction'
        unchanged+=1
independent={'status':'passed','date':'2026-10-28','raw_profiles':len(raw),
 'scope':'基准有限注意规则的T1，3政策×5指标及5个配对差；其余场景检查结构一致性及表数量',
 'method':'Python stdlib statistics对MATLAB导出的全部40,000条原始配对记录重算；连续值容差考虑MAT单精度',
 'summary_checks':checks,'paired_mean_mcse_checks':5,'strong_baseline_all_rows_equal':True,
 'T3_prior_knowledge_preserved':True,'T1_rows_unchanged_after_T3_fix':unchanged,
 'rows_summary':len(summary),'rows_link_contrasts':len(contrasts)}
(out/'independent_validation.json').write_text(json.dumps(independent,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
history_note=(f'T1的{unchanged:,}行主指标及边界结果与修正前一致。旧结果及代码留在本地归档。'
              if oldrows else '当前源代码保留修正说明；复现包不包含旧结果，本次不作历史版本比较。')

# Export the full prespecified grid; extrema are descriptive, not population estimates.
grid=[]
for r in contrasts:
    if r['scenario'].startswith('grid_') and r['rule']!='full_information' and int(r['type'])==1 and int(r['control'])==1:
        bits=r['scenario'].split('_');A=float(bits[1][1:]);g=float(bits[2][1:]);cost=float(bits[3][1:])
        grid.append({'scenario':r['scenario'],'rule':r['rule'],'attention':A,'cue_gain':g,'cue_cost':cost,
          'reduction_pp':-100*num(r,'delta_dependent_unreviewed_upgrade'),
          'paired_mcse_pp':100*num(r,'mcse_dependent_unreviewed_upgrade')})
with (out/'all_grid_effects.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(grid[0]));w.writeheader();w.writerows(grid)
assert len(grid)==80
best=max(grid,key=lambda r:r['reduction_pp']);worst=min(grid,key=lambda r:r['reduction_pp'])
positive=sum(r['reduction_pp']>0 for r in grid);negative=sum(r['reduction_pp']<0 for r in grid)
near=sum(abs(r['reduction_pp'])<=1.96*r['paired_mcse_pp'] for r in grid)
base0=row(policy='D1_R0_C0');baseC=row(policy='D1_R0_C1');baseNew=row()
delta=cx['base','bounded_default',1,1]
drop=-100*num(delta,'delta_dependent_unreviewed_upgrade')
err=100*num(delta,'mcse_dependent_unreviewed_upgrade')
zero0=row(sc='zero_commercial_bias',policy='D1_R0_C1');zero1=row(sc='zero_commercial_bias')
over0=row(sc='information_overload',policy='D1_R0_C1');over1=row(sc='information_overload')

core=['D1_R0_C0','D1_R1_C0','D1_R0_C1','D1_R1_C1']
labels={'D1_R0_C0':'仅事实更正','D1_R1_C0':'更正＋关联提示','D1_R0_C1':'更正＋重选操作','D1_R1_C1':'更正＋关联提示＋操作',
 'generic_all':'普通全员再确认','generic_selective':'强选择性再确认'}
table='|条件（商业披露均有）|完成重评|未重评仍选升级款|已请求降预算后越限|不适配购买|未购买|合成任务效用差|合成负担|\n|---|---|---|---|---|---|---|---|\n'
for policy in core:
    r=row(policy=policy)
    table+=f"|{labels[policy]}|{pct(r,'goal_reviewed')}|{pct(r,'dependent_unreviewed_upgrade')}|{pct(r,'budget_violation_after_request')}|{pct(r,'noncompatible_purchase')}|{pct(r,'no_purchase')}|{fnum(r,'quality_regret')}|{fnum(r,'processing_load')}|\n"

diag_table='|政策|购买数／40,000|兼容购买数|兼容购买者效用差|修改请求数|请求后条件执行失败率|\n|---|---|---|---|---|---|\n'
pen_table='|政策|惩罚0|惩罚100|惩罚500|惩罚1000（主设定）|\n|---|---|---|---|---|\n'
for policy in ['D1_R0_C1','D1_R1_C1']:
    d=dx['bounded_default',policy,1]
    diag_table+=f"|{labels[policy]}|{int(float(d['n_purchased'])):,}|{int(float(d['n_compatible_purchased'])):,}|{float(d['compatible_purchase_regret']):.3f}|{int(float(d['n_requests'])):,}|{100*float(d['failure_rate_given_request']):.2f}%|\n"
    pen_table+='|'+labels[policy]+'|'+'|'.join(f"{float(d['regret_penalty'+str(v)]):.3f}" for v in [0,100,500,1000])+'|\n'

boundary='|情景|规则／比较|结果|解释|\n|---|---|---|---|\n'
boundary+=f"|完全知情参考|所有政策|选择、预算及适配结果相同，任务效用差为0|新增流程没有选择收益，是预设参考规则下的反例条件|\n"
boundary+='|事实更正未理解|有限注意，R有／无，C=1|未重评仍升级均为100%，配对差0|在本模型中，未理解会阻断重评；不意味着所有现实用户都会如此|\n'
boundary+='|关联线索无额外效力|有限注意，R有／无，C=1|基准成本下该指标配对差0，额外成本仍可能影响其他变量|把效力设0即可消除对应收益；不以模型验证这个未测假设|\n'
boundary+=f"|零商业排序偏向|有限注意，R有／无，C=1|合成任务效用差由{fnum(zero0,'quality_regret')}增至{fnum(zero1,'quality_regret')}|更多重评不保证选择质量改善；效用差也不是自主性总分|\n"
boundary+=f"|信息过载|有限注意，R有／无，C=1|负担由{fnum(over0,'processing_load')}增至{fnum(over1,'processing_load')}；未重评升级{pct(over0,'dependent_unreviewed_upgrade')}→{pct(over1,'dependent_unreviewed_upgrade')}|该项变化小，负担增幅大；不把小数差异解释成真人收益|\n"
boundary+='|强选择性再确认|相同触发、效力、成本|全部54场景及3规则的输出与所提方案相同|结构等价检查表明机制可由既有方法实现，不能声称新算法优势|\n'

report=f'''# 已运行仿真：理由撤回与目标修订

日期2026-10-28。证据身份：**合成机制仿真**。MATLAB R2023b实际运行完成，无额外工具箱调用。54个场景×10个政策×3种行为规则；基准每类40,000个合成条件，共120,000个；边界和网格每类10,000。均使用配对输入和种子20261028。这些数量不是真人样本。

## 1. 先给结论

模型展示了一条有条件的经验桥梁：事实更正、注意到目标关联、决定重评和落实新目标可以分离。低成本且有信息效力的关联提示有帮助；无额外信息效力、原本已能正确处理或成本过高时，收益可消失甚至反转。

**最重要的反证边界是：足够强的普通选择性再确认与本方案完全等效。**本轮支持研究“何时应把纠错延伸到目标、怎样限制负担”，不提供新算法优越性。规范责任仍由程序性自主、理由依赖与反例论证支持。

## 2. 补了哪些材料

新增重点包括撤回信息的复杂性、商品错误信息与反驳、选择过载异质性。取得M3的17页作者公开PDF、M4的111页作者稿，分别读取指定章节；M1/M2及W1使用明确标示的摘要／节选，未取得者保持状态。

M4用信息等价对照区分撤回与新信息处理；其方法提醒我们，证据撤回不等于命题被证伪。M3提醒选项与负担效果具有异质性。M1/W1提供不同更正方式与购买行为的相邻研究。它们不为本题提供数值校准。[材料、页码与检索记录](02_新增材料与模型依据.md)

## 3. 模型承接哪个命题

从“原预算150元，当前记录200元，重要安全理由被撤回”的给定历史开始，分T1理由依赖、T2独立颜色理由、T3知情重申。商品和偏好为合成设定。模型不生成AI如何造成先前预算提高的心理因果过程。

主比较固定商业披露D=1，比较关联说明R有／无×重选操作C有／无。另给原商业披露D×控制C四组（固定R=0）及普通再确认基线。C=0仍可用自然语言修订，C=1也可能昂贵或执行失败。R和D通过线索、阅读及操作过程影响结果，没有自主性加分项。

“未重评仍超原150元”是待重评现象，不直接判成未经授权；只有已经明确发出新预算请求后再越限才记录执行偏离。[执行前方案](01_执行前方案.md)；[全部变量、公式与假设](03_变量公式与参数身份.md)

## 4. 主场景实际结果

以下为**有限注意／默认黏着规则、T1理由依赖类型**。每列数值只对应这些假设；效用差以购买条件计算，负担为合成单位。

{table}

在同样有重选操作时，新增关联提示使“未重评仍升级”从{pct(baseC,'dependent_unreviewed_upgrade')}变为{pct(baseNew,'dependent_unreviewed_upgrade')}，减少{drop:.2f}个百分点；配对蒙特卡洛标准误为{err:.3f}个百分点，约95%的模拟积分误差带为[{drop-1.96*err:.2f}, {drop+1.96*err:.2f}]个百分点。该误差带描述随机模拟精度，不是现实人群效果置信区间。

同一表也显示：预算越限在此规则下均为0，不支持“方案减少明确预算违规”的主场景结论。不适配购买没有随主指标同步改善。新增重评不等于所有选择条件改善，必须分别报告结果。

### 4.1 请求分母、条件样本及惩罚诊断

{diag_table}

全样本执行失败率会随修改请求暴露量变化，因此可靠性应同时看请求数和请求后的条件失败率。控制成功概率0.95本身是模型假设，不能把约5%的条件失败率当成对真实平台的估计。

效用差的单组均值以该政策购买者为条件；配对效用差仅在两政策都购买的交集上计算，不是两组各自条件均值之差。未购买和适配分别报告。初始不适配惩罚为1000，故补下表：保持选择不变，只改变惩罚，观察合成效用结果敏感性。

{pen_table}

这是审查后增加的解释诊断，不是预先检验的行为效应。它说明总效用差高度依赖惩罚假设，不能只用总效用差宣称整体质量提升。[原始诊断与共同样本数](results/base_diagnostics.csv)

![主场景四组机制](figures/fig1_core_mechanisms.png)

图1的误差条为1.96×蒙特卡洛标准误。左下零值面板按该规则真实保留，没有补造违规来突出干预。

## 5. 哪些结果削弱宽泛主张

{boundary}

![完整成本和线索网格](figures/fig2_effect_cost_boundaries.png)

图2比较固定C=1时R有／无，红色表示“未重评仍升级”减少，蓝色表示反转。共80个非完全信息的规则×网格点，其中正向{positive}个、反向{negative}个；{near}个落在0附近的±1.96倍实际配对MC误差带内。它们是预定参数网格上的描述，不是对哪种情景在现实更常见的估计。

最大减少{best['reduction_pp']:.2f}个百分点，发生于{best['rule']}、注意{best['attention']:g}、线索效力{best['cue_gain']:g}、提示成本{best['cue_cost']:g}；最大反转{-worst['reduction_pp']:.2f}个百分点，发生于{worst['rule']}、注意{worst['attention']:g}、效力{worst['cue_gain']:g}、成本{worst['cue_cost']:g}。极值用于定位条件，不能作为方案的典型效果。[全部网格与MC误差](results/all_grid_effects.csv)

![成本和选择质量的权衡](figures/fig3_cost_quality.png)

图3保留核心政策及全员再确认，结构等价的选择性基线合并标签；全部10政策仍在CSV中。负担和合成任务效用分别显示；任务效用变差本身不裁定程序性权利，却削弱“普遍净受益”的经验主张。

## 6. 合理升级与强基线

T2/T3的颜色价值被明确设定足以支持179元。选择保留升级可符合该合成偏好，不把多花钱算作失败。针对性提示正常不在已知情重申类型触发，全员确认则仍显示提示；这首先是政策触发属性，不是实测反感或自主感。

全员确认对T1的未重评升级为{pct(row(policy='generic_all'),'dependent_unreviewed_upgrade')}，所提方案为{pct(baseNew,'dependent_unreviewed_upgrade')}；全员提示也能覆盖被识别器漏掉的T1，因此本方案并非每项结果最优。代价要连同T2/T3的额外提示及负担考虑。

强选择性再确认因同构、等参、同随机输入而与所提方案一致。这说明本模型无法区分两者的技术优势，不能把同一机制重新命名成算法创新。

![原披露四组及强基线](figures/fig4_disclosure_and_strong_baseline.png)

图4左侧为D×C且R=0；右侧为T3的提示触发率，是策略实现属性。两部分不是同一个2×2，也不是元宝的真实商业关系测试。

## 7. 计算验证与复现

MATLAB检查指标范围、任务效用差非负、替代数量、完全知情不变性、预算／兼容边界、强基线等价，以及同输入重算一致。Python另对T1主场景全部40,000条原始记录、3政策×5指标及5个配对差重新计算均值和MC误差，检查通过。[MATLAB验证](results/validation.json)；[独立复核](results/independent_validation.json)

完整表有{len(summary):,}行，含各场景／规则／政策下3类型及等权汇总；汇总不是人口估计。R有／无的实际配对差表{len(contrasts):,}行。原始配对输入及基准输出MAT、CSV、代码、日志、图和文件哈希保留。[复现说明](05_复现与验收.md)

热图最初把不等距成本误画为连续等距轴，视觉检查后改成明确标签的离散列；成本图标签重叠后改为共享图例。仅重绘图表，数值及参数未因方向更改。[变更记录](work/变更日志.md)

并行AI只读复核还发现T3既有知识被本轮阅读概率重置，已修正并正式重跑；T3现在保留先前知情状态。{history_note}该复核不是人工同行评审。

## 8. 这对创新点意味着什么

建议贡献句修订为：**本研究将AI导购的重要理由撤回与其公开支持的目标修订联系起来，提出与重要性及负担相称的说明和重选要求，并区分独立理由、知情重申及可用操作的边界。**

仿真承接的是一个条件性机制：有理解及注意缺口时，仅改事实可能没有触及目标；多加程序也可能损害便利或选择质量。因此，规范要求应允许用已有、低成本的针对性说明完成；用户已知情重申或已有回复充分时，不再附加重复确认。

最强近邻的再确认、元偏好与反思方法可能推导同样判断；当前贡献按明确适用条件的规范推导及审计操作化呈现。仿真不确认首创，也不把设定的线索效力当成已发现的心理事实。

## 9. 证据能力与后续

本轮提供可复现的机制分析。所有行为参数未经中国充电器购物用户校准；完全知情、残留和识别器等都是比较假设；实际退出摩擦、多次重复追问、真实理解及偏好认可未测。元宝3条构造响应、用户手机材料和SIM分别保留，模拟数量不相加为真人样本。

下一步若要主张实际净收益，应做有同意的匹配任务研究，分别测重要取舍理解、重评理由、目标执行、时间／负担及退出。人数按真实研究目标与误差／功效另定，不能沿用40,000个合成条件。

评分方面，本轮补充理论机制与反例、研究过程及复现、可实施设计和反思证据；需求普遍性和真人成效仍需独立资料。不预测分数。
'''
(root/'04_结果报告与创新点修订.md').write_text(report,encoding='utf-8')

reproduce='''# 复现与验收

运行环境：MATLAB 23.2.0.2365128（R2023b）。代码未调用额外工具箱。Python报告脚本只使用标准库。

在MATLAB中把本文件所在目录设为当前目录，执行：

```matlab
addpath('code');
run_goal_repair_simulation('smoke');  % 小规模计算检查，另存results_smoke
run_goal_repair_simulation('full');   % 正式54场景，原始输入及结果存results
run_goal_repair_simulation('cue_contrasts'); % 导出R有/无实际配对误差
export_validation_slice;            % 导出基准T1的全部40,000条配对原始记录
export_simulation_diagnostics;      % 导出请求分母、共同购买样本及惩罚敏感性
```

随后使用Python 3运行 `code/build_simulation_report.py`，以CSV生成报告、独立复核、完整网格、哈希及复现ZIP。`figures`模式仅依据已有CSV重新出图，不改变数值。

固定种子20261028；主场景每类40,000、其余每类10,000；敏感性取相同完整输入的各类前10,000。不要分别重抽政策输入。所有商品和行为参数均合成，CSV可追溯到scenarios.csv与policies.csv。

输出：all_summary.csv为全部条件均值及MC误差；paired_differences.csv为对D1_R0_C0的配对差；paired_link_contrasts.csv固定C比较R；all_grid_effects.csv为完整非完全信息网格；paired_inputs.mat及base_outcomes.mat为完整输入和基准输出。independent_validation_slice.csv为T1主场景3政策×5指标的全部原始记录，供独立重算。

validation.json的elapsed_seconds只计数值计算及写表，run.log的COMPLETE时间还包括出图；不是两个不同试验。图表修改与附加导出见work/变更日志.md，原数值版本副本保留。

复现包不含第三方论文PDF和无关私有会话。sources中原下载记录只反映下载时状态，后来实际阅读范围见02材料记录。报告PNG/PDF均为本轮原创数据图，可另用于报告；正式参赛文件仍需统一匿名、引文及大小检查。

验收：所有数值结果存在；固定输入重算一致；强选择性基线同构等价；完全知情比较不变；独立Python核对通过；图表已视觉检查；结果保留无效、反转与成本条件。复现一致不构成参数真实性或伦理命题的独立证明。
'''
(root/'05_复现与验收.md').write_text(reproduce,encoding='utf-8')

entry=f'''# 先看结果

已实际运行MATLAB：54场景、10政策、3规则。基准每类40,000个合成条件；不是受试者。

在基准有限注意规则中，同有重选操作时，增加理由—目标关联提示后，T1“未重评仍选升级款”从{pct(baseC,'dependent_unreviewed_upgrade')}变为{pct(baseNew,'dependent_unreviewed_upgrade')}。这只是指定机制和参数的模拟结果，不直接等于消费自主性改善。

更重要的边界：用户已能正确处理时，新增提示没有选择收益；提示无信息效力时可无帮助；高成本网格可反转；足够强的选择性再确认与本方案一致。

据此，创新主张应落在“重要理由撤回后，何时有义务说明它与目标变化的关系，以及何时应停止干预”，而不是新算法优势或普遍有效性。

看[结果报告](04_结果报告与创新点修订.md)，其中给出全部主结果、反例和4张图。另有[新增材料](02_新增材料与模型依据.md)、[变量与公式](03_变量公式与参数身份.md)和[复现说明](05_复现与验收.md)。原E2机制设计仍保持未运行历史身份，本文件夹是新建并已执行的针对性模型。
'''
(root/'00_先看结果.md').write_text(entry,encoding='utf-8')

intro='本研究聚焦中文AI购物助手选购充电器的知情选择与消费自主性，考察重要购买理由撤回后，纠错责任是否应延伸到由此形成的预算和目标变化。研究结合文献论证拆解、规范案例、元宝构造情景预试及MATLAB机制仿真，区分事实更正、目标重评与修订执行。仿真比较关联说明、选择控制及普通再确认，显示其效果取决于理解、注意与操作成本。研究据此提出与重要性和负担相称的说明、重选及停止干预判准，形成可追溯记录和设计审计清单。'
assert len(intro)<=300
(root/'研究简介_仿真后草案.txt').write_text(intro+'\n',encoding='utf-8')
reading={'date':'2026-10-28','M3':{'pdfObtained':True,'pdfPages':17,'readPdfPages':[1,9,10],'status':'partial reading'},
 'M4':{'pdfObtained':True,'pdfPages':111,'version':'arXiv2106.11433v4; draft2025-02-27, posted2025-02-28','readPdfPages':[1,2,3,4,8,9],'status':'partial reading'},
 'M1':{'pdfObtained':False,'status':'publisher/institution search excerpts; scope detailed in02'},
 'M2':{'pdfObtained':False,'status':'publisher indexed abstract/first-page and experiment excerpt; scope detailed in02'},
 'W1':{'pdfObtained':False,'status':'publisher abstract and author institution bibliography only'},'introCharacters':len(intro)}
(root/'sources').mkdir(exist_ok=True)
(root/'sources/reading_log.json').write_text(json.dumps(reading,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

selection=[]
for p in sorted(root.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(root)
    if rel.parts[0]=='results_smoke':continue
    if rel.parts[0]=='sources' and p.suffix!='.json':continue
    if rel.parts[0]=='work' and p.name not in ['变更日志.md','并行复核与处理.md','executed_numerical_code_v1.m','executed_numerical_code_v2.m']:continue
    if p.suffix in ['.zip'] or p.name=='文件校验SHA256.json':continue
    selection.append(p)
manifest={str(p.relative_to(root)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in selection}
(root/'文件校验SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=root.parent/'仿真复现包_纠错与目标修订_20261028.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in selection+[root/'文件校验SHA256.json']:z.write(p,p.relative_to(root))
print(json.dumps({'report':'04_结果报告与创新点修订.md','base_drop_pp':drop,'paired_mcse_pp':err,
 'grid_positive':positive,'grid_negative':negative,'grid_near_mc_error':near,
 'best_grid':best,'worst_grid':worst,'independent_validation':'passed',
 'archive_bytes':archive.stat().st_size,'files_in_archive':len(selection)+1},ensure_ascii=False,indent=2))
