"""Build the domestic-data manuscript from unchanged observed-data outputs."""
from pathlib import Path
import csv,json,re,hashlib,shutil,importlib.util
ROOT=Path(__file__).resolve().parent
HISTORY=ROOT.parent/'phase4_full_report_20261029'
DATA=ROOT.parent/'domestic_data_reanalysis_20261029'
spec=importlib.util.spec_from_file_location('base_refs',HISTORY/'assemble_report.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
REFS=dict(base.REFERENCES)
REFS['Huang']='HUANG R, HUANG Y, GUO H. Remembering or monitoring? Contextual fit of simulated AI memory cues and consumer trust[J]. Frontiers in Psychology, 2026, 17: 1934857. DOI: 10.3389/fpsyg.2026.1934857.'
REFS['DOMDATA']='HUANG R, HUANG Y, GUO H. AI Memory Boundary Fit: de-identified study data[DS/OL]. [2026-10-29]. https://github.com/RunhuaHuang/aimemory/tree/3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53. CC BY 4.0.'
abstract='本研究考察中文AI购物助手为成年消费者推荐充电器时，重要购买理由撤回后的预算重审责任。结合文献与概念分析、规范案例、元宝给定历史预试及国内真人实验二手数据，提出基于重要性、公开理由使用、可调整性与相称负担的关联说明要求。普通更正已完成功能时无需追加确认；独立理由、知情重申和退出限制重复干预。对国内招募516人的记忆提示与面板实验进行六臂复分析及参与者重抽样，分别检验平均信任差和特定差距变化，信任不等于规范自主性。研究以规范推理辩护责任规则，形成触发、完成、停止及验收清单；预算更新仍由消费者有效表达决定。'

def assemble():
    def read(name):
        with (DATA/'results'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    arms=read('cell_estimates.csv');con=read('contrasts.csv');mods=read('model_checks.csv');src=read('source_summary_comparison.csv')
    A={(r['sample'],r['cell'],r['metric']):r for r in arms}
    C={(r['sample'],r['contrast'],r['metric']):r for r in con}
    def fmt(s,k):return [f'{float(C[(s,k,"trust_mean")][x]):.3f}' for x in ['estimate','ci_low','ci_high']]
    table=['|原记忆提示|无面板人数|信任均值|有面板人数|信任均值|','|---|---:|---:|---:|---:|']
    for slug,label in [('none','无记忆提示'),('relevant','相关记忆提示'),('intrusive','侵入记忆提示')]:
        a=A[('all_516',slug+'_no_control','trust_mean')];b=A[('all_516',slug+'_dashboard','trust_mean')]
        table.append(f'|{label}|{int(float(a["participants"]))}|{float(a["estimate"]):.3f}|{int(float(b["participants"]))}|{float(b["estimate"]):.3f}|')
    delta,dl,dh=fmt('all_516','primary_intrusive_gap_change');avg,al,ah=fmt('all_516','dashboard_average_standardized')
    f=next(x for x in mods if x['sample']=='all_516')
    main=f'全516份的主差中之差δ为{delta}个量表点，95%重抽样区间[{dl}, {dh}]。次要的标准化面板平均差为{avg}，逐项区间[{al}, {ah}]；直接两组均值分别为4.486与4.300。两自由度整体交互复算为F(2,510)={float(f["interaction_F_2df"]):.3f}，p={float(f["interaction_p"]):.3f}。这些数字分别对应平均变化与相对差距，不能互相替代。'
    delta,dl,dh=fmt('campus_403','primary_intrusive_gap_change');avg,al,ah=fmt('campus_403','dashboard_average_standardized')
    sens=f'预先保留的403份现场渠道记录中，δ为{delta}，逐项区间[{dl}, {dh}]；同权重面板平均差为{avg}，区间[{al}, {ah}]。现场子样本没有把特定差距缓解确立为已验证效果，其平均差区间也跨0。两个人群的精度与覆盖范围不同，不能只展示全样本中更有利的区间，亦不把它们当两次独立实验。'
    intro=(ROOT/'parts/00_引言与设计.md').read_text(encoding='utf-8')
    lit=(ROOT/'parts/01_近邻与定位.md').read_text(encoding='utf-8').split('\n',1)[1].strip();intro=intro.replace('{{LITERATURE}}',lit)
    intro=intro.replace('这一前提连接事实与规范：','本土暗黑模式研究从行为类型与权利影响推导分层治理，提示措施应对应机制和主体条件。[C2]本文围绕一次重要理由撤回组织责任判断。这一前提连接事实与规范：')
    diagram='\n\n![图1 规范前提与纠错责任的逻辑](figures/图1_论证框架.png)\n\n图1 责任判断路线。规范前提进入责任推导；国内经验材料核对评价与措施边界，不由信任差值推出义务。\n\n'
    intro=intro.replace('### 2.2 材料身份',diagram+'### 2.2 材料身份')
    method=(ROOT/'parts/02_国内数据方法.md').read_text(encoding='utf-8')
    theory=(ROOT/'parts/03_规范论证.md').read_text(encoding='utf-8').replace('## 三 理由撤回后的预算修复责任','## 三 理由撤回后的预算重审责任')
    pilot=(HISTORY/'parts/04_案例与机制.md').read_text(encoding='utf-8').split('实施后果由模型作条件分析。')[0].strip().replace('### 3.5 条件响应与实施成本','### 3.5 限定真实系统响应与反例')
    result=(ROOT/'parts/04_国内数据结果.md').read_text(encoding='utf-8').replace('{{CELL_TABLE}}','\n'.join(table)).replace('{{MAIN_RESULTS}}',main).replace('{{SENSITIVITY_RESULTS}}',sens).replace('](../figures/','](figures/')
    results,conclusion=result.split('### 结论',1)
    gov=(ROOT/'parts/05_治理反思.md').read_text(encoding='utf-8').replace('## 五、','## 四 ').replace('### 5.','### 4.')
    body='\n\n'.join([intro.strip(),method.strip(),theory.strip(),pilot.strip(),results.strip(),gov.strip(),'## 结论\n'+conclusion.strip()])
    order=[]
    def cite(m):
        k=m.group(1)
        if k not in REFS:return m.group(0)
        if k not in order:order.append(k)
        return '['+str(order.index(k)+1)+']'
    body=re.sub(r'\[([A-Za-z][A-Za-z0-9]*)\]',cite,body)
    refs='\n\n'.join(f'[{i+1}] '+REFS[k] for i,k in enumerate(order))
    appendix='''## 附录

### 附录一 来源及实际读取范围

N6、C3、S1作者稿为论证正文精读。V2读取PDF1—3；R1读取PDF14—15、17—19及原记录片段；V1读取PDF6—7、11—12；V3读取PDF5—8、12—14。Fong累计读取PDF1—10、13—14、17—21，保留为消费品纠错近邻文献，其国外数据不进入本稿主分析。C1仅摘要，全文缺口限制排他性查新。Hung核读PDF33、印刷2515；M3读PDF1、9—10，M4读arXiv v4 PDF1—4、8—9。

Huang等原论文共16页，核读方法PDF4—8页、Study4结果PDF9及11页，以及摘要、引言和相关讨论。正式补充材料共27页，S14的计分、信任题及来源位于PDF19—20、22页。补充附件经出版方公开接口实际取得，不将未取得的完整stimulus_protocol.md或作者分析脚本登记为已读。

国内Study4原CSV固定于作者提交3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53，42,200字节，SHA256 dec91f502f9fb40f2f89e9e980e981edcf1670e928a91d911a60464c815b0360。CC BY4.0许可和作者署名随原文件保留，未修改原观测。原README及CITATION仍标投稿状态，书目采用正式发表DOI，历史文件原样留存。国内采集、文件托管地点、作者国籍及全国代表性分别判断。

手机探索、构造规范案例与元宝给定历史响应不作为真人消费者实验。第一阶段《AI导购中拒绝后的再建议边界》15页已读，扩展坞和设置K为构造材料，枚举程序未取得、未独立复跑。国内候选检索、未选数据的编码或采集地缺口，分别保存在来源核验记录。

### 附录二 国内复分析复现材料

正式目录为research/domestic_data_reanalysis_20261029。source/author_original保存作者原CSV、字典、README、许可、论文与补充材料；来源与许可.json记录固定版本、URL、哈希和署名。原有匿名Participant_ID用于辨识记录，不是平台账号；报告仅呈汇总。

code/run_domestic_reanalysis.m使用基础MATLAB读原记录，主终点为三道正向信任题均值；原六臂各保持88/88、84/84、86/86份。主样本516，现场敏感性403属于其子集。各臂内5,000轮按人重抽样，种子分别20261029与20261030；不补预算、控制使用或未观测处理反应。平均差固定全样本记忆权重；δ方向以正文定义为准。

results/cell_estimates.csv为56项组内统计，contrasts.csv为84项差值及逐项区间，ols_coefficients.csv和model_checks.csv记录分类回归与交互F/p，trust_item_frequencies.csv保留252项频数；source_summary_comparison.csv核对原文舍入均值，run_metadata.json保存实际版本。bootstrap_aggregates.mat仅存重复抽样汇总；render_domestic_figures.m独立重绘图，不重新计算数据分析。

code/independent_validate.py与validation/独立复算.json核对点估计、差值、OLS和频数；方法审读明确未独立重跑bootstrap区间。原作者脚本、完整交互记录、排除日志及session标识未公开，本轮没有补造。数据是原实验保留样本，不能写为完整ITT。旧国外牙膏及自创合成结果仅保留研究历史，不进入当前主要结果。

### 附录三 AI辅助与提交状态

AI辅助用于定位文献和公开数据、草拟规范论证、编写复算代码、图表及排版。原研究者构造实验提示，国内真人提供存档回答，本项目没有生成消费者行为数据。AI内部复核不称独立人类编码或外部同行评审；原研究报告的伦理安排不能当作本项目已获得新的真人研究审批。

本稿为匿名国内数据修订稿。真实知网正文查重及报告、答辩PPT、匿名补充包与永久分享、团队编号命名及正式提交仍待完成。正常学术作者和外部数据采集单位保留出处，不作为参赛者身份删除。最后改稿和附入真实查重报告后重新核验PDF及整套提交文件。
'''
    draft='# AI导购理由撤回后的预算重审\n\n研究报告国内数据修订稿\n\n## 摘要\n\n'+abstract+'\n\n关键词：AI购物助手；预算重审；消费者自主性；国内二手数据\n\n'+body+'\n\n## 参考文献\n\n'+refs+'\n\n'+appendix
    (ROOT/'draft.md').write_text(draft,encoding='utf-8');(ROOT/'作品简介_300字内.txt').write_text(abstract+'\n',encoding='utf-8')
    (ROOT/'reference_index.json').write_text(json.dumps({k:i+1 for i,k in enumerate(order)},ensure_ascii=False,indent=2),encoding='utf-8')
    for n in ['图2_国内六臂信任评价.png','图3_面板差值与交互边界.png']:shutil.copy2(DATA/'results'/n,ROOT/'figures'/n)
    tracked=['cell_estimates.csv','contrasts.csv','model_checks.csv','ols_coefficients.csv','trust_item_frequencies.csv','source_summary_comparison.csv','run_metadata.json']
    record={'date':'2026-10-29','direction':'Domestic Chinese recruitment data required; foreign data removed from current empirical analysis','source':'Huang et al. (2026), Study4, DOI10.3389/fpsyg.2026.1934857','analysis':'research/domestic_data_reanalysis_20261029','counts':{'body_cjk':len(re.findall(r'[\u4e00-\u9fff]',body)),'title_characters':14,'abstract_characters':len(abstract),'references':len(order)},'observed_participants':516,'campus_sensitivity':403,'bootstrap_repetitions':5000,'new_behavior_generated':False,'source_results_sha256':{n:hashlib.sha256((DATA/'results'/n).read_bytes()).hexdigest() for n in tracked},'cnki':'not completed','ppt':'not completed'}
    (ROOT/'写作与证据记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':assemble()
