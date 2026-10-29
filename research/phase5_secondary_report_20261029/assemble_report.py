"""Assemble the revised report using observed secondary data and derived results."""
from pathlib import Path
import csv,json,re,hashlib,shutil,importlib.util

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'phase4_full_report_20261029'
DATA=ROOT.parent/'secondary_data_reanalysis_20261029'
spec=importlib.util.spec_from_file_location('previous_references',OLD/'assemble_report.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
REFS=dict(old.REFERENCES)
REFS['DATA']='FONG J, GUO T, RAO A. Replication files for Debunking Misinformation About Consumer Products: Effects on Beliefs and Purchase Behavior[DS/OL]. [2026-10-29]. https://people.duke.edu/~tg64/. 作者主页链接的复现目录；原件SHA256见补充材料.'
REFS['PRE']='GUO T, RAO A, FONG J. Debunking Misinformation in Advertisements - By Beliefs - Fluoride[EB/OL]. AsPredicted #99,328, 2022-06-07[2026-10-29]. https://aspredicted.org/6vw3m.pdf.'

abstract='本研究考察中文AI购物助手为成年消费者推荐充电器时，重要购买理由撤回后的预算重审责任。结合文献与概念分析、规范案例、元宝给定历史预试及真实二手实验数据，提出基于重要性、公开理由使用、可调整性与相称负担的关联说明要求。普通更正已完成功能时无需追加确认；独立理由、知情重申和退出限制重复干预。对既有5,050人牙膏实验进行原观测复分析及参与者重抽样，分别报告信念、选择、标价和不购买。二手结果明确测量边界，预算责任由规范推理辩护。研究形成触发、完成、停止及验收规则，预算更新仍由消费者有效表达决定。'

def assemble():
    with (DATA/'results/arm_estimates.csv').open(encoding='utf-8-sig',newline='') as f:armrows=list(csv.DictReader(f))
    with (DATA/'results/contrasts.csv').open(encoding='utf-8-sig',newline='') as f:contrasts=list(csv.DictReader(f))
    A={(x['arm'],x['metric']):x for x in armrows}
    C={(x['contrast'],x['metric']):x for x in contrasts}
    def mean(a,k):return float(A[(a,k)]['estimate'])
    def comp(k,scale=100,digits=2):
        x=C[('debunk_with_misinfo',k)]
        return [f'{float(x[n])*scale:.{digits}f}' for n in ['estimate','ci_low','ci_high']]
    labels={'regular_control':'普通广告＋控制','regular_regulator':'普通广告＋监管纠错','treat_control':'误导广告＋控制','treat_regulator':'误导广告＋监管纠错'}
    tab=['|原处理臂|人数|含氟选择比例|后测有害4—5档|不购买比例|每题所选标价|','|---|---:|---:|---:|---:|---:|']
    for a,label in labels.items():
        n=int(float(A[(a,'ingredient_choice_share')]['participants']))
        vals=[f'{mean(a,k)*100:.2f}%' for k in ['ingredient_choice_share','post_harmful_bin_share','no_purchase_share']]
        tab.append('|'+ '|'.join([label,str(n),*vals,f"{mean(a,'selected_price_unconditional_usd'):.4f}美元"] )+'|')
    e,lo,hi=comp('ingredient_choice_share');h,hl,hh=comp('post_harmful_bin_share')
    primary=f'在误导广告条件下，监管纠错组的含氟选择比例为{100*mean("treat_regulator","ingredient_choice_share"):.2f}%，控制消息组为{100*mean("treat_control","ingredient_choice_share"):.2f}%，主差值为{e}个百分点，95%重抽样区间为[{lo}, {hi}]。后测有害概率4—5档的比例分别为{100*mean("treat_regulator","post_harmful_bin_share"):.2f}%与{100*mean("treat_control","post_harmful_bin_share"):.2f}%，差值{h}个百分点，探索性逐项区间为[{hl}, {hh}]。信念后测位于选择之后，以上不是“先理解、再改变选择”的个体路径证据。'
    e,lo,hi=comp('selected_price_unconditional_usd',1,4);n,nl,nh=comp('no_purchase_share');q,ql,qh=comp('selected_price_purchase_conditional_usd',1,4)
    price=f'所选标价需要核对分母。误导广告下，纠错组含不购买的每题均值为{mean("treat_regulator","selected_price_unconditional_usd"):.4f}美元，控制组为{mean("treat_control","selected_price_unconditional_usd"):.4f}美元，差值{e}美元，探索性逐项区间[{lo}, {hi}]。与此同时，不购买比例差为{n}个百分点，区间[{nl}, {nh}]。若只看购买题，标价差为{q}美元，区间[{ql}, {qh}]。不能把前一个均值降低直接解读为用户调低预算；购买与不购买的构成不同，实际购买题中的价格差也有不确定性。'
    with (DATA/'results/joint_belief_choice.csv').open(encoding='utf-8-sig',newline='') as f:joint=list(csv.DictReader(f))
    J={x['observed_choice_pattern']:int(float(x['participants'])) for x in joint if x['arm']=='treat_regulator' and x['belief_direction']=='lower'}
    jointtext=f'个体联合统计进一步保留结果差异。误导广告加监管纠错组有{sum(J.values())}人后测风险档位低于先验；其中{J["never_ingredient"]}人十题都未选含氟商品，{J["mixed"]}人有时选择，{J["always_ingredient"]}人十题均选择含氟商品。这些是同一组真实记录的分类，非模拟新类型。十题菜单不同，其他偏好也可能支持不同商品；这种组合不能直接标为理解失败、非理性或操纵。'
    intro=(ROOT/'parts/00_引言与设计.md').read_text(encoding='utf-8')
    lit=(ROOT/'parts/01_近邻与定位.md').read_text(encoding='utf-8').split('\n',1)[1].strip()
    intro=intro.replace('{{LITERATURE}}',lit)
    intro=intro.replace('这一前提连接事实与规范：','本土暗黑模式研究从行为类型与权利影响推导分层治理，提示措施应对应机制和主体条件。[C2]本文围绕一次重要理由撤回组织责任判断。这一前提连接事实与规范：')
    diagram='\n\n![图1 规范前提与纠错责任的逻辑](figures/图1_论证框架.png)\n\n图1 责任判断路线。规范前提进入责任推导；经验材料核对测量与可见表现，不由统计差值推出义务。\n\n'
    intro=intro.replace('### 2.2 材料身份',diagram+'### 2.2 材料身份')
    method=(ROOT/'parts/02_二手数据方法.md').read_text(encoding='utf-8')
    theory=(ROOT/'parts/03_规范论证.md').read_text(encoding='utf-8').replace('## 三 理由撤回后的预算修复责任','## 三 理由撤回后的预算重审责任')
    pilot=(OLD/'parts/04_案例与机制.md').read_text(encoding='utf-8').split('实施后果由模型作条件分析。')[0].strip()
    pilot=pilot.replace('### 3.5 条件响应与实施成本','### 3.5 限定真实系统响应与反例')
    if '固定商业披露' in pilot or '表3 基准' in pilot:raise ValueError('Old numerical section retained')
    results=(ROOT/'parts/04_二手数据结果.md').read_text(encoding='utf-8').replace('### 3.5','### 3.6').replace('{{ARM_TABLE}}','\n'.join(tab)).replace('{{PRIMARY_RESULTS}}',primary).replace('{{PRICE_RESULTS}}',price).replace('{{JOINT_RESULTS}}',jointtext)
    results=results.replace('](../figures/','](figures/')
    resultbody,conclusion=results.split('### 结论',1)
    gov=(ROOT/'parts/05_治理反思.md').read_text(encoding='utf-8').replace('## 五、','## 四 ').replace('### 5.','### 4.')
    body='\n\n'.join([intro.strip(),method.strip(),theory.strip(),pilot.strip(),resultbody.strip(),gov.strip(),'## 结论\n'+conclusion.strip()])
    order=[]
    def cite(m):
        k=m.group(1)
        if k not in REFS:return m.group(0)
        if k not in order:order.append(k)
        return '['+str(order.index(k)+1)+']'
    body=re.sub(r'\[([A-Za-z][A-Za-z0-9]*)\]',cite,body)
    refs='\n\n'.join(f'[{i+1}] '+REFS[k] for i,k in enumerate(order))
    appendix='''## 附录

### 附录一 文献、来源及读取范围

N6、C3、S1作者稿为论证正文精读。V2读取PDF1—3；R1读取PDF14—15、17—19及原记录片段；V1读取PDF6—7、11—12；V3读取PDF5—8、12—14。Fong累计实际读取PDF1—10、13—14、17—21，未精读全文及在线附录；本轮补核实验条件、选择激励与信念时点。C1仍仅摘要及公开信息，全文缺口限制排他性查新。Hung核读PDF33、印刷2515；M3读PDF1、9—10，M4读arXiv v4 PDF1—4、8—9。定向检索词、日期、平台与失败获取分别留存。

Fong数据通过Tong Guo的Duke作者主页进入Replication Files，2026-10-29实际取得34,473,604字节ZIP并校验。原ZIP的SHA256为92b44b0ec96ac32e68afdb8a86019697798c116d76f307af81f884a4bcf2e4f3；两份CSV、说明和代码各有原件哈希。原始包含标识与人口字段，且未取得明确再分发许可，留本地不上传。公开附件提供获取入口、必要列规则、分析代码及汇总，不含原参与者标识。

第一阶段《AI导购中拒绝后的再建议边界》共15页已读，扩展坞和设置K等为构造案例；其程序未取得，计数未独立复跑。用户充电器截图、规范案例、真实系统给定历史响应和真实二手实验，按生成方式分开使用。

### 附录二 复分析与重抽样复现

正式目录为research/secondary_data_reanalysis_20261029。01_数据与执行前方案.md记录结构读取后、效果计算前的本地方案，不称外部预注册。code/run_secondary_data.m读取作者原CSV必要列，运行基础MATLAB；调用时分别指定原replication目录与结果目录。种子20261029，5,000次臂内参与者整簇重抽样。每次保留原臂人数及一人全部十题，不模拟新选择，也不插补缺失。

results/arm_estimates.csv为40项臂内指标及区间，contrasts.csv为50项组差及区间，belief_transitions.csv和joint_belief_choice.csv保留类别计数，offered_menu_balance.csv记录菜单均值。run_metadata.json保存实际运行版本；bootstrap_aggregates.mat只含重抽样汇总，不含个体标识。validation/独立复算.json与方法审读.md记录Python点估计、计数复核和11类统计误读检查，不声称独立重跑MATLAB区间。

主指标是含氟选择比例，主比较是误导广告下纠错减控制。其余按探索报告；95%区间为逐项百分位区间，非多指标同时区间。指标保留各自含义，不合成自主性总分。先前12万个合成条件及其图表仅保留在研究历史，本修订稿没有沿用其效应数字、行为参数或R×C优胜结论。

### 附录三 AI辅助与提交状态

AI辅助用于文献和数据定位、概念与论证草拟、代码、复核和排版。真实二手选择由原研究参与者提供；本研究没有自行招募消费者，没有生成新的消费者行为记录。分工复核属于AI内部检查，不等同独立人类编码或外部同行评审。原手机材料由用户提供，元宝预试的前史由研究者给定。

本稿为匿名二手数据修订稿。知网正文检测尚未执行，重复率低于20%的真实报告需收入附录；PPT、匿名补充材料、永久分享与最终提交另行验收。加入查重报告或作最终修改后，重新核验PDF体积、版面及所有提交文件。
'''
    draft='# AI导购理由撤回后的预算重审\n\n研究报告二手数据修订稿\n\n## 摘要\n\n'+abstract+'\n\n关键词：AI购物助手；预算重审；消费者自主性；二手数据复分析\n\n'+body+'\n\n## 参考文献\n\n'+refs+'\n\n'+appendix
    (ROOT/'draft.md').write_text(draft,encoding='utf-8')
    (ROOT/'作品简介_300字内.txt').write_text(abstract+'\n',encoding='utf-8')
    (ROOT/'reference_index.json').write_text(json.dumps({k:i+1 for i,k in enumerate(order)},ensure_ascii=False,indent=2),encoding='utf-8')
    for n in ['图2_真实观测与信念.png','图3_真实选择价格与不购买.png']:shutil.copy2(DATA/'results'/n,ROOT/'figures'/n)
    tracked=['arm_estimates.csv','contrasts.csv','belief_transitions.csv','joint_belief_choice.csv','offered_menu_balance.csv','run_metadata.json']
    record={'date':'2026-10-29','direction':'User requires actual existing secondary data; synthetic behavior dataset removed from current evidential analysis','previous_report':'research/phase4_full_report_20261029','data_analysis':'research/secondary_data_reanalysis_20261029','counts':{'body_cjk':len(re.findall(r'[\u4e00-\u9fff]',body)),'title_characters':14,'abstract_characters':len(abstract),'references':len(order)},'source_results_sha256':{n:hashlib.sha256((DATA/'results'/n).read_bytes()).hexdigest() for n in tracked},'real_secondary_participants':5050,'bootstrap_repetitions':5000,'new_consumer_behavior_generated':False,'cnki':'not completed','ppt':'not completed'}
    (ROOT/'写作与证据记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':assemble()
