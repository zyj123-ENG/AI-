"""Assemble the complete report from source-accounted parts and existing results."""
from pathlib import Path
import re,json,hashlib,csv,shutil

ROOT=Path(__file__).resolve().parent
RESEARCH=ROOT.parent
SIM=RESEARCH/'simulation_goal_repair_20261028'

REFERENCES={
 'N6':'PRUNKL C. Human autonomy at risk? An analysis of the challenges from AI[J]. Minds and Machines, 2024, 34: 26. DOI: 10.1007/s11023-024-09665-1.',
 'V2':'ASHTON H, FRANKLIN M. Solutions to preference manipulation in recommender systems require knowledge of meta-preferences[EB/OL]. arXiv:2209.11801v1, 2022. https://arxiv.org/abs/2209.11801.',
 'I4':'SUSSER D, ROESSLER B, NISSENBAUM H. Technology, autonomy, and manipulation[J]. Internet Policy Review, 2019, 8(2). DOI: 10.14763/2019.2.1410.',
 'C3':'丁晓东. 基于信任的自动化决策：算法解释权的原理反思与制度重构[J]. 中国法学, 2022(1): 99—118. DOI: 10.14111/j.cnki.zgfx.20211230.001.',
 'C2':'刘颖, 刘佳璇. 数字经济中黑暗模式的法律规制：基本原理、域外方案与本土路径[J]. 上海财经大学学报, 2024, 26(5): 122—138. DOI: 10.16538/j.cnki.jsufe.2024.05.009.',
 'R1':'LARA F, DEL VALLE J I. Are you sure this is what you really want? Conversational recommender systems for enhancing human autonomy[J]. Science and Engineering Ethics, 2026, 32: 44. DOI: 10.1007/s11948-026-00619-7.',
 'V3':'FISCHLI R, FRANKLIN M, MANZINI A, et al. Agents, alignment, and the many faces of autonomy[J]. Minds and Machines, 2026, 36: 34. DOI: 10.1007/s11023-026-09786-9.',
 'V1':'ALFRINK K, KELLER I, KORTUEM G, et al. Contestable AI by design: Towards a framework[J]. Minds and Machines, 2023, 33: 613—639. DOI: 10.1007/s11023-022-09611-z.',
 'Fong':'FONG J, GUO T, RAO A. Debunking misinformation about consumer products: Effects on beliefs and purchase behavior[J]. Journal of Marketing Research, 2024, 61(4): 659—681. DOI: 10.1177/00222437221147088.',
 'C1':'李术平. 人机交互中的消费者自主选择权[J]. 东方法学, 2026(4): 161—173. DOI: 10.19404/j.cnki.dffx.2026.04.009. 本研究按摘要及公开信息使用.',
 'Hung':'HUNG A. Keeping consumers in the dark: Addressing “nagging” concerns and injury[J]. Columbia Law Review, 2021, 121(8): 2483—2520. https://columbialawreview.org/content/keeping-consumers-in-the-dark-addressing-nagging-concerns-and-injury/.',
 'S1':'MATHUR A, MAYER J, KSHIRSAGAR M. What makes a dark pattern... dark? Design attributes, normative considerations, and measurement methods[C]//Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems. 2021. DOI: 10.1145/3411764.3445610. 本研究读取作者稿.',
 'M4':'GONÇALVES D, LIBGOBER J, WILLIS J. Retractions: Updating from complex information[EB/OL]. arXiv:2106.11433v4, 2025. https://arxiv.org/abs/2106.11433v4.',
 'M3':'SCHEIBEHENNE B, GREIFENEDER R, TODD P M. Can there ever be too many options? A meta-analytic review of choice overload[J]. Journal of Consumer Research, 2010, 37(3): 409—425. DOI: 10.1086/651235.',
 'LAW1':'全国人民代表大会常务委员会. 中华人民共和国消费者权益保护法[Z/OL]. 2013-10-25修正[2026-10-29]. https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_0a323e046fba43f0b6e9e977f1e8d5fc.html.',
 'LAW2':'国务院. 中华人民共和国消费者权益保护法实施条例[Z/OL]. 2024-03-15公布，2024-07-01施行[2026-10-29]. https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2024/art_0aea188276a44f0baf940ab95ee00e0a.html.',
 'LAW3':'全国人民代表大会常务委员会. 中华人民共和国个人信息保护法[Z/OL]. 2021-08-20[2026-10-29]. https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm.',
}

abstract='本研究考察中文AI购物助手为成年消费者推荐充电器时，重要购买理由撤回后的预算重审责任。研究结合文献与概念分析、配对规范案例、元宝给定历史预试和MATLAB合成机制仿真，提出基于重要性、公开理由使用、可调整性、知识与负担的关联说明要求。普通更正已使关联可理解并保留调整机会时，无需追加确认；独立理由、知情重申和退出限制重复干预。给定假设下的仿真表明，关联说明与重选操作可影响预算重评，也可能因成本失效或反转，并与同构的选择性再确认等价。研究形成责任判准和设计审计清单，将修复决定条件与替消费者改写预算分别评价。'

def assemble():
    intro=(ROOT/'parts/00_引言与设计.md').read_text(encoding='utf-8')
    lit=(ROOT/'parts/01_近邻与定位.md').read_text(encoding='utf-8')
    lit=lit[lit.index('\n')+1:];lit=lit.split('\n读取依据沿用原记录：')[0].strip()
    intro=intro.replace('{{LITERATURE}}',lit)
    # Add a transparent ranking equation; all coefficients remain declared assumptions.
    intro=intro.replace('理解、注意关联、愿意重评与系统执行分别处理，', '排序按价格、属性简化估值、公开颜色理由及商业权重组成，超出工作预算及已识别不适配项被过滤。理解、注意关联、愿意重评与系统执行分别处理，')
    intro=intro.replace('蒙特卡洛标准误MCSE','蒙特卡洛标准误（Monte Carlo standard error，MCSE）')
    intro=intro.replace('正式运行使用MATLAB', '40,000个基准条件是执行前固定的积分规模，使用配对MCSE报告数值精度，未作为真人功效计算。正式运行使用MATLAB')
    intro=intro.replace('这一前提连接事实与规范：', '既有本土研究通过暗黑模式类型与权利影响的分析提出分层治理，提示措施要对应机制和主体条件。[C2]本文则围绕一次重要理由撤回组织责任判断。这一前提连接事实与规范：')
    theory=(ROOT/'parts/03_规范论证.md').read_text(encoding='utf-8').replace('## 三 理由撤回后的预算修复责任','## 三 理由撤回后的预算重审责任')
    outcomes=(ROOT/'parts/04_案例与机制.md').read_text(encoding='utf-8')
    results,conclusion=outcomes.split('### 结论',1)
    # Source-part figures use local parent paths; assembled draft lives one level up.
    results=results.replace('](../figures/','](figures/')
    governance=(ROOT/'parts/05_治理反思.md').read_text(encoding='utf-8').replace('## 五、','## 四 ').replace('### 5.','### 4.')
    after_theory='\n\n![图1 规范前提与纠错责任的逻辑](figures/图1_论证框架.png)\n\n图1 研究者绘制的责任判断路线。规范前提进入责任判断；机制结果约束实施后果，不替代义务推导。\n'
    intro=intro.replace('### 2.2 材料身份',after_theory+'\n### 2.2 材料身份')
    body='\n\n'.join([intro.strip(),theory.strip(),results.strip(),governance.strip(),'## 结论\n'+conclusion.strip()])
    order=[]
    def cite(m):
        key=m.group(1)
        if key not in REFERENCES:return m.group(0)
        if key not in order:order.append(key)
        return '['+str(order.index(key)+1)+']'
    body=re.sub(r'\[([A-Za-z][A-Za-z0-9]*)\]',cite,body)
    refs='\n\n'.join('['+str(i+1)+'] '+REFERENCES[k] for i,k in enumerate(order))
    appendix='''## 附录

### 附录一 来源与读取范围

N6、C3、S1作者稿为论证正文精读，引用列表未逐项复核。V2读取PDF1—3；R1读取PDF14—15、17—19及原记录片段；V1读取PDF6—7、11—12；V3读取PDF5—8、12—14。Fong排版镜像读取PDF1—6、8、17—21，未精读全文及在线附录；正式书目采用2024年卷期，引用定位保留镜像PDF页码，不转换成最终印刷页。C1仅摘要及公开信息，全文缺口限制查新排他性。Hung核读PDF33、印刷2515相关安排；M3读PDF1、9—10，M4读arXiv v4 PDF1—4、8—9。其他早期材料的具体范围保存在文献卡和方法矩阵。

第一阶段《AI导购中拒绝后的再建议边界》共15页已读；扩展坞、200/239元和设置K均为构造材料，未与充电器案例合并。该稿自述的枚举程序未取得，计数未由本研究独立复跑。

定向检索包括论文题名、DOI、纠错与支付意愿、推荐自主性、元偏好、拒绝与预算等中英文词；日期、平台、获取失败及实际范围随来源表保存。Fong后续检索于2026-10-29进行，使用公开网页及机构/期刊入口，未宣称检索了订阅数据库。合法取得与允许公开再分发分别核对；许可未核实全文留在本地，公开副本提供题录、来源与原件SHA256。

### 附录二 复现材料与参数

正式模型目录为research/simulation_goal_repair_20261028。code/run_goal_repair_simulation.m为主代码，results/all_summary.csv为分组结果，paired_link_contrasts.csv为关联说明的配对差，base_diagnostics.csv报告请求、适配与条件分母，validation.json及independent_validation.json记录计算检查。paired_inputs.mat和base_outcomes.mat保留配对输入与基准输出。结果、变量及参数身份文档、54场景、图表和修复前档案分别保存；归档不是独立样本。

排序公式如下，其中属性项a和收益权重m分别取[0,0.15,0.2,0,0]和[0.1,0.2,0.3,1,0.1]，商业权重λ基准1.2，边界含0。简化颜色估值来自公开理由，未经真实平台估计。

$$S_{ij}=-p_j/100+a_j+\\widehat b_i Blue_j/100+\\lambda m_j.$$

基准不适配识别率0.98，跨政策共用识别事件。剩余注意决定可见项，至多5件；有限注意规则含排序位置与旧推荐默认效应；满意即止按顺序选择达到合成门槛的可见项。完整理解、关联注意和行动概率见参数文档及代码，所有行为数值均为假设。固定种子及配对输入支持重算，MCSE只量化模拟精度。

运行smoke输出results_smoke，full重建正式results；应在独立副本运行。PDF和Word中的图表来自已经核验的正式CSV，本轮写作不改变模拟选择或参数。题目、简介和匿名检查另有验包记录。

### 附录三 AI辅助与研究状态

AI辅助用于文献定位、读取记录、论证草拟、构造案例、代码和图表及格式处理。分工复核属于AI内部检查，不等同独立人类编码或外部同行评审。手机材料来自用户；限定预试由工具操作真实系统，但前史由研究者给定。未进行真人问卷、访谈或购买实验，不提供未经实施的伦理审批或受试者同意文件。

本稿为匿名研究报告初稿。知网全文查重尚未执行，真实查重报告需在检测正文不含附录且重复率低于20%后置入附录。答辩PPT及最终匿名提交包另按实际进度准备；本稿没有制作替代性的查重证明。
'''
    draft='# AI导购理由撤回后的预算重审\n\n研究报告初稿\n\n## 摘要\n\n'+abstract+'\n\n关键词：AI购物助手；预算重审；消费者自主性；纠错责任\n\n'+body+'\n\n## 参考文献\n\n'+refs+'\n\n'+appendix
    (ROOT/'draft.md').write_text(draft,encoding='utf-8')
    (ROOT/'reference_index.json').write_text(json.dumps({k:i+1 for i,k in enumerate(order)},ensure_ascii=False,indent=2),encoding='utf-8')
    fig=ROOT/'figures';fig.mkdir(exist_ok=True)
    old=RESEARCH/'phase4_simulation_sections_20261028/figures'
    shutil.copy2(old/'图1_基准机制比较.png',fig/'图2_主机制比较.png')
    shutil.copy2(old/'图2_条件与反转边界.png',fig/'图3_成本边界.png')
    # Record the exact data and source visual versions used by this draft.
    tracked=['all_summary.csv','paired_link_contrasts.csv','base_diagnostics.csv','validation.json']
    evidence={n:hashlib.sha256((SIM/'results'/n).read_bytes()).hexdigest() for n in tracked}
    counts={'body_cjk':len(re.findall(r'[\u4e00-\u9fff]',body)),'body_characters':len(body),'full_characters':len(draft),'title_characters':len('AI导购理由撤回后的预算重审'),'references':len(order),'abstract_characters':len(abstract)}
    record={'date':'2026-10-29','author_direction':'user delegated title/outline adjustment to assistant according to formal scoring; not described as line-by-line author approval','outline':'planning/提纲调整_v2_按评分.md','scope':'complete report draft with evidence, references and reproducibility appendices','simulation_rerun_this_stage':False,'source_data_sha256':evidence,'counts':counts,'human_study':False,'cnki_report':'not completed','ppt':'not completed'}
    (ROOT/'写作与证据记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':assemble()
