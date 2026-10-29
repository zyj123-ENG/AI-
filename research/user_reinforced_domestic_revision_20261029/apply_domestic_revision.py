"""Patch the supplied DOCX package; preserve non-target parts verbatim."""
from pathlib import Path
from copy import deepcopy
import csv, hashlib, json, re, sys, zipfile
from lxml import etree as ET
from PIL import Image

SOURCE=Path(sys.argv[1]); REPO=Path(sys.argv[2]); OUT=Path(sys.argv[3])
OUT.mkdir(parents=True,exist_ok=True)
DATA=REPO/'research/domestic_data_reanalysis_20261029'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def tag(x):p,n=x.split(':');return '{'+NS[p]+'}'+n
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with zipfile.ZipFile(SOURCE) as z:
    infos=z.infolist(); original={i.filename:z.read(i.filename) for i in infos}
root=ET.fromstring(original['word/document.xml']);body=root.find('w:body',NS)
P=body.findall('w:p',NS);T=body.findall('w:tbl',NS)
assert len(P)==140 and len(T)==5
def text(e):return ''.join(e.itertext()) if False else ''.join(e.xpath('.//w:t/text()',namespaces=NS))
def put(e,value):
    rp=e.find('w:r/w:rPr',NS);rp=deepcopy(rp) if rp is not None else None
    for ch in list(e):
        if ch.tag!=tag('w:pPr'):e.remove(ch)
    run=ET.SubElement(e,tag('w:r'))
    if rp is not None:run.append(rp)
    for k,line in enumerate(value.split('\n')):
        if k:ET.SubElement(run,tag('w:br'))
        el=ET.SubElement(run,tag('w:t'));el.set('{http://www.w3.org/XML/1998/namespace}space','preserve');el.text=line
    return e
def newp(value,template=36):return put(deepcopy(P[template]),value)
def replace_range(start,end,elements):
    at=body.index(P[start]);nodes=list(body)[at:body.index(P[end])+1]
    for e in nodes:body.remove(e)
    for e in elements:body.insert(at,e);at+=1
def row_values(table,row_index,values):
    cells=table.findall('w:tr',NS)[row_index].findall('w:tc',NS)
    assert len(cells)==len(values)
    for cell,value in zip(cells,values):
        paras=cell.findall('w:p',NS)
        for p in paras[1:]:cell.remove(p)
        put(paras[0],value)

updates={
1:'研究报告补强稿国内数据版',
3:'本研究考察中文AI购物助手为成年消费者推荐充电器时，重要购买理由撤回后的预算重审责任。结合文献与概念分析、配对规范案例、元宝给定历史预试和国内真人二手实验复分析，提出以重要性、公开理由使用、可调整性与相称负担为条件的关联说明要求。普通更正已完成功能时无需追加确认，独立理由、知情重申和退出限制重复干预。对国内招募516人的原六臂数据进行分类回归和参与者重抽样，分别检验平均信任差与特定差距变化；这些结果承接控制措施的评价边界。研究以规范推理辩护责任规则，形成触发、完成、停止及验收清单，预算更新仍由消费者有效表达与授权决定。',
8:'本文聚焦中国成年消费者使用中文建议型购物助手，为iPhone 15选择一只日常充电器，已经具有可用连接线。初始预算150元和后来记录的200元用于构造规范比较。手机材料中的现实商品事实、规范案例与国内二手实验分别管理，品牌、协议及价格均按实际取证范围使用。建议型场景保持最终购买在消费者控制之下，自动下单只作为区分交易授权的边界。',
11:'本文回答：重要购买理由撤回后，助手何时应主动说明它与既有预算修订的关联，怎样履行这一责任，何时停止干预？中心判断是，责任以重要性、公开理由使用、可调整性、知识与相称负担为条件；普通更正已完成功能时即可承接选择。最终预算由消费者的有效表达和授权决定。文献与概念分析承担规范辩护，配对规范案例检验判断边界，有限真实系统预试记录条件响应；国内真人二手实验复分析则用于区分平均信任评价与特定差距变化。',
19:'这项增量定位为低额AI导购中责任范围与审计标准的细化，尚无排他性查新结论。较强的依赖跟踪与选择性再确认可以实现同一处理，应依同一功能标准评价；措施名称或提示出现次数不能单独承担创新主张。依照Mathur等从规范目标推导指标、基线与阈值的方法[10]，本文用规范案例辨析误触发、遗漏和负担，将国内二手数据用于评价指标的经验边界，而不据此验证预算修复方案的优越性。',
22:'知情选择要求消费者对本次重要事实、费用和取舍具有足够可用的理解。规范意义的自主性涉及本人评价理由及维持、修改或终止决定的条件；感知自主性是主观体验，满意度是过程或结果评价。国内二手数据中的信任评价，是参与者对特定购物助手的态度，不能替代以上概念。本项目未直接测量感知自主性或满意度。说服可以通过可评价理由改变选择；按照所采用的操纵理论，隐蔽利用决策脆弱性等条件还须分别证成，不能仅由提高预算或一项无据数字直接认定操纵。[1][2][11]',
27:'图1 研究者绘制的责任判断路线。规范前提承担义务推导；国内经验分析约束评价指标的解释，不作为该责任路线已被实证验证的证据。',
32:'手机材料按照原长截图、分段阅读记录和后续转贴分别登记。已有商品页可见E01230，但未证明三轮所有推荐卡片均为同一SKU；0.87%和36℃缺少匹配的原始统计或测试证据，继续从商品比较事实中排除。TI原厂说明可用于核对电子标记的电流条件，不能把“20W必须有E-Marker”作为普遍必要条件。[14]另一个公开专栏虽刊有42.8℃数字，其倍思产品描述为1C1A，不能直接支持待选单C口SKU的温控排名。[15]',
62:'预算内没有满足明确用途的方案时，助手应说明冲突及证据，提供维持预算并降低功能要求、经同意提高预算、暂不购买等可用路径。它可以清楚标注假设条件，说明提高预算后的可选方案；在取得新的有效表达或授权前，不得把提高后的预算当作已生效的执行范围。真实新信息支持消费者自主修改预算，条件性比较与预算更新分别判断。',
65:'限定响应与经验评价边界',
96:'当前证据形成条件判准、限定系统响应与国内二手实验复分析：给定历史的真实回复没有呈现自然错误怎样促成真人提价，国内记忆面板实验测量即时信任，未包含预算修订、实际控件使用或操作负担。校园及社区便利样本的解释范围也有边界。后续可在有同意的匹配任务中比较普通更正、已完成关联说明的更正及追加提示，分别测重要取舍理解、维持或修改预算的理由、执行情况、时间和负担；样本量依目标精度或功效另定。再依具体失败扩展跨平台状态审计与数字能力差异，落实适用伦理审查和隐私安排。增加重抽样次数不能补出这些未测变量。',
99:'这项责任以改善决定条件为目的，预算更新仍须符合消费者的有效表达和授权。必要纠错不自动恢复已拒绝的商业推动，较强的既有再确认也可以实现相同要求。条件规范判准与可核案例承担责任辩护；国内真人实验复分析分别报告平均信任差和特定差距变化，约束措施的验收口径。预算重审对真实理解、决定及净负担的实际效果，留待直接包含这些变量的匹配任务研究。',
123:'N6、C3、S1作者稿为论证正文精读，引用列表未逐项复核。V2读取PDF1—3；R1读取PDF14—15、17—19及原记录片段；V1读取PDF6—7、11—12；V3读取PDF5—8、12—14。Fong保留为消费品纠错近邻文献，沿用已有指定章节读取记录，其国外数据不进入本稿经验分析。C1仅摘要及公开信息，全文缺口限制排他性查新。Hung核读PDF33、印刷2515相关安排；M3读PDF1、9—10；M4沿用arXiv v4 PDF1—4、8—9的读取记录，正式卷期的元数据核对不等于重新精读期刊全文。不同版本页码分别登记。',
124:'Retractions的正式卷期据出版元数据核对为2026年93卷1期、476—516页，早期在线发表与纸本卷期年份分别登记。其理论任务未用于估计本研究的行为概率。Apple官方规格的快充条件和TI线缆电子标记说明已核；EEPW专栏仅作SKU适用性核查，不作为待选产品性能依据。国内数据来源另核Huang等论文方法PDF4—8页、Study4结果PDF9及11页与相关讨论，正式补充S14的计分及信任题位于PDF19—20、22页。[21][23]',
134:'AI辅助用于文献定位、读取记录、论证草拟、构造案例、复分析代码、图表及格式处理。分工复核属于AI内部检查，不等同独立人类编码或外部同行评审。手机材料来自用户，限定预试的前史由研究者给定；国内二手实验的量表回答来自原作者招募的真人。本项目未新招募参与者，原研究报告的伦理安排不能改称本项目已取得新的真人研究审批。',
135:'本稿为用户补强稿的国内数据替换版。答辩PPT、匿名补充包、知网检测及提交状态须按实际材料核对；本次未取得可核验的PPT、真实查重报告或正式提交回执。知网正文全文重复率需严格低于20%，真实查重报告置于附录，正文检测不含附录。团队编号命名、永久分享及最终匿名检查另行完成，加入查重报告和最后修改后重新核验最终文件。',
139:'手机图像核查沿用已取得的原图及分段阅读台账，本次未独立重做逐像素匹配或确认所谓哈希订正，不把原稿自述登记为新增完成项。当前国内数值核验的原始CSV、固定版本、哈希、程序和汇总结果均可定位。全文与独立仿真报告采用同一批已完成的计算输出，没有生成新的消费者记录。',
}
for i,value in updates.items():put(P[i],value)
added_lit=newp('与交互形式更接近的Huang等研究，用夹克购物原型比较三类记忆消息包和特定可编辑记忆面板，记录即时信任评价。[21]本文复用其公开的国内真人记录，分别计算平均面板差和预定的相对差距变化。[22]这一经验来源有助于界定控制工具的评价口径；原研究已有的心理效应不作为本文首次发现，预算重审责任仍须由前述规范推理承担。',template=15)
P[15].addnext(added_lit)

methods=[
newp('国内二手实验与重抽样方法',35),
newp('经验分析使用Huang、Huang与Guo的Study4。原方法说明，2026年3—6月通过浙江商业职业技术学院课程及校园社区渠道招募18岁以上、中文流利的参与者。公开清洗后保留516份记录，学生316人、居民200人；校园现场203人、居民现场200人、网络测试113人。国内依据是招募方法，不能扩写为逐人国籍核定或全国代表性。另保留403份现场记录作预定敏感性分析。[21][22]'),
newp('原任务为夹克购物原型，三种记忆消息包为无记忆、相关记忆与侵入记忆，另交叉设置无面板与可查看、编辑、删除记忆的面板，形成原生3×2六臂。记忆陈述是研究者构造的刺激，量表回答来自真人。各臂人数依次88、88、84、84、86、86。消息包包含相关性、敏感性及信息来源等差异，不能视为单个特征的纯净操纵；该设计也不是商业披露×预算控制实验。'),
newp('主终点为Trust_Item1至Trust_Item3的原值不加权均值，取值1—7。正式补充S14确认三题全部正向，无反向计分。另保存逐题结果与频数；MBF仅采用作者已计算的构念均值，Study4未公开单题，且只在相关和侵入记忆组作次要分析。[23]'),
newp('令μ_m,c表示记忆条件m及面板条件c下的信任均值，c=1为有面板、c=0为无面板。主比较预定为侵入记忆组的面板增量减去无记忆组的面板增量：'),
newp('δ = (μ侵入,1 − μ侵入,0) − (μ无记忆,1 − μ无记忆,0)'),
newp('δ为正表示侵入组相对获得更大的面板增量。这里比较不同实验臂的参与者，不是同一人的前后测。次要平均差A按全样本原记忆人数比例加权，权重为(176,168,172)/516；主样本与现场子样本都用同一权重。平均差和相对差距对应不同问题，不能相互替代。'),
newp('分类OLS以无记忆且无面板为参照，包含相关记忆R、侵入记忆I、面板C及两个交互项，拟合饱和六臂模型；侵入×面板系数等于δ。将六臂模型与去掉交互的加性模型比较，以残差平方和计算两自由度整体交互F，作为模型复核。主要推断呈现δ的重抽样区间。'),
newp('基础MATLAB R2023b在各原臂内按参与者整行有放回抽取原人数，保留同一人的题间关系，每个人群各5,000轮，种子为20261029和20261030。每轮从六臂均值计算相同差值，采用逐项95%百分位区间。5,000轮的每侧2.5%尾部约125项，仅用于计算不确定性，不新增真人。未另做改变重复次数的收敛实验，末位小数不作为稳定性保证。'),
newp('计算方案在本项目求处理差值前保存，但此前已读到原文结果，因此是有记录的复核性二手分析。原CSV不修改、不插补预算或未观测干预反应。公开排除日志和场次标识缺失，无法重建完整意向处理分析或修正场次内相关。独立Python从原CSV核对点估计、频数、OLS及F/p，未独立重跑bootstrap区间。探索比较的逐项区间不保证多项同时覆盖。'),
newp('本模块不包含理由撤回、预算重审、实际控件使用或操作成本，承接的是平均评价与特定问题缓解应分别检验的要求。撤回信息与直接提供相反信息的区分[16]、选择负担的情境差异[17]继续作为规范讨论的文献背景，不为本数据补入未测参数。'),
]
replace_range(35,44,methods)

row_values(T[0],5,['国内真人二手实验','国内招募516份原六臂记录；现场403份为子样本','即时信任的描述、交互与不确定性；未测预算修复效果'])
row_values(T[0],2,['用户手机探索','三张原始长截图及分段阅读记录；后续为转贴文字','初始断言可核图；后续界面未取得，非三名参与者'])

with (DATA/'results/cell_estimates.csv').open(encoding='utf-8-sig',newline='') as f:arms=[x for x in csv.DictReader(f) if x['sample']=='all_516' and x['metric']=='trust_mean']
labels=['无记忆／无面板','无记忆／有面板','相关记忆／无面板','相关记忆／有面板','侵入记忆／无面板','侵入记忆／有面板']
old_rows=T[2].findall('w:tr',NS);header=deepcopy(old_rows[0]);rowtemp=deepcopy(old_rows[1])
for row in old_rows:T[2].remove(row)
T[2].append(header)
for _ in arms:T[2].append(deepcopy(rowtemp))
row_values(T[2],0,['原实验条件','人数','信任均值','样本SD','95%重抽样区间'])
for i,(a,label) in enumerate(zip(arms,labels),1):
    row_values(T[2],i,[label,a['participants'],f"{float(a['estimate']):.3f}",f"{float(a['sd']):.3f}",f"[{float(a['ci_low']):.3f}, {float(a['ci_high']):.3f}]"])
widths=[1.8,.55,.9,.9,2.7]
for col,w in zip(T[2].findall('w:tblGrid/w:gridCol',NS),widths):col.set(tag('w:w'),str(round(w*1440)))
for row in T[2].findall('w:tr',NS):
    for cell,w in zip(row.findall('w:tc',NS),widths):
        e=cell.find('w:tcPr/w:tcW',NS)
        if e is not None:e.set(tag('w:w'),str(round(w*1440)))

results=[
newp('国内原数据用于检验控制工具的评价边界。表3保留原六臂的即时信任均值和人数，图2展示逐项参与者重抽样区间。原实验未包含本研究的预算理由历史，也没有检验预算重审措施。'),
newp('表3 国内原六臂即时信任评价',72),deepcopy(T[2]),
newp('注：516人为原研究保留记录，信任为三道正向七点题均值。区间为原臂内5,000轮参与者bootstrap的逐项95%百分位区间，不表示6项同时覆盖。',74),
deepcopy(P[76]),newp('图2 国内六臂均值及逐项95%重抽样区间。纵轴保留原1—7量表范围，记忆提示为构造刺激，回答来自真人。',77),
newp('全516人的主δ为−0.160个量表点，95%重抽样区间[−0.542,0.220]。无记忆组面板增量约0.299，侵入记忆组约0.140；相对差距区间跨0，仍容许缓解和恶化，未确立该面板对侵入记忆差距的选择性缓解，也不能据此证明等效或普遍无效。'),
newp('次要的标准化面板平均差为0.186，区间[0.032,0.341]，两组直接汇总均值为4.486与4.300。整体交互复算F(2,510)=0.538，p=0.584。平均变化、单个δ及两自由度联合交互各有统计对象；不能通过两个显著性标签不同，替代对效果差异的直接检验。'),
deepcopy(P[81]),newp('图3 面板平均差、各记忆内面板差及相对差距分别检验。主比较为δ，其余为次要或探索比较；逐项区间不保证多项同时覆盖。',82),
newp('预先保留的403份现场子样本中，δ为−0.199，区间[−0.646,0.250]；同权重平均差为0.162，区间[−0.013,0.338]。联合交互F(2,397)=0.582，p=0.559。子样本的精度及解释范围不同，保留其不利于确定结论的区间；它与516份重叠，不是独立重复实验。'),
newp('有面板与无面板各258人的均值和SD，舍入后与原文4.49、4.30及0.91、1.00一致。独立Python从作者原CSV复算56项组内统计、84项差值、12个OLS系数、252项频数及两个F/p，均与MATLAB一致；未独立重跑区间，也未取得原作者全部分析脚本。原研究已报告的心理效应不作为本文的新发现。'),
newp('回到预算重审，控制工具的存在及平均信任评价，不能替代对具体修复功能的验收。仍须分别检查依据状态和已公开理由使用是否交代、维持或修改预算是否可执行、结束是否兑现；实际理解与认可需要直接测量。责任规则由决定地位、协助角色及比例性获得辩护，国内数据既不直接证明预算义务，也不把一种面板证据有限推成另一种提示方案已经充分。'),
]
replace_range(71,84,results)

appendix=[newp('附录二 国内复分析复现材料',127),
newp('正式目录为research/domestic_data_reanalysis_20261029，source/author_original保留原CSV、字典、README、数据许可、论文与补充材料。来源与许可.json记录固定提交3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53、获取入口、署名及哈希。原CSV为42,200字节，SHA256 dec91f502f9fb40f2f89e9e980e981edcf1670e928a91d911a60464c815b0360；按数据集CC BY4.0许可保留原件。[22]'),
newp('code/run_domestic_reanalysis.m从原记录计算正向三题信任均值，保留原六臂人数；主516与现场403每个人群各5,000轮，种子20261029及20261030。两个人群的标准化平均差使用全样本固定权重。重抽样以参与者整行为单位，未生成新行为、未补预算及未观测处理反应。'),
newp('results/cell_estimates.csv记录组内统计与区间；contrasts.csv记录差值；ols_coefficients.csv和model_checks.csv保存分类回归及F/p；trust_item_frequencies.csv保留逐题频数，run_metadata.json记录实际环境。bootstrap_aggregates.mat仅含重复抽样汇总，不是新增真人数据。render_domestic_figures.m读取汇总重绘。'),
newp('code/independent_validate.py及validation/独立复算.json直接核对原CSV的点估计、人数、差值、OLS、频数及模型统计，未独立重算bootstrap端点。原作者脚本、完整刺激协议、排除日志及场次标识未取得；不能把舍入均值一致称为复制全部Tukey或贝叶斯检验。复现宜另存输出，避免覆盖已核结果。'),
newp('当前独立仿真报告在research/domestic_simulation_report_20261029，采用同一批计算结果。旧虚拟与国外数据仿真已依用户要求从仓库当前文件移除。本次仅替换用户补强稿中相关证据及其上下文，没有重新运行主分析或扩写新的研究主线。'),
]
replace_range(127,132,appendix)
for p in appendix[1:]:
    pr=p.find('w:pPr',NS)
    if pr is None:pr=ET.Element(tag('w:pPr'));p.insert(0,pr)
    jc=pr.find('w:jc',NS)
    if jc is None:jc=ET.SubElement(pr,tag('w:jc'))
    jc.set(tag('w:val'),'left')

row_values(T[4],1,['手机原图与分段阅读','原长截图及分段读取台账已取得；逐像素匹配与哈希订正未在本次独立复做','沿用已有读取范围，不认证隐藏上下文或平台后台'])
row_values(T[4],5,['国内数值输出','原CSV哈希固定；56项组内统计、84项差值、12个OLS系数、252项频数及F/p独立复算一致','未独立重跑bootstrap区间；没有预算修复、面板使用及成本变量'])

# Preserve the three drawing relationships; replace old empirical image bytes.
package=dict(original)
for rid,name in [('rId12','图2_国内六臂信任评价.png'),('rId13','图3_面板差值与交互边界.png')]:
    source=DATA/'results'/name
    target='word/media/image'+('2' if rid=='rId12' else '3')+'.png'
    package[target]=source.read_bytes()
    w,h=Image.open(source).size
    drawing=root.xpath('.//a:blip[@r:embed="'+rid+'"]',namespaces=NS)[0]
    inline=drawing.getparent()
    while inline is not None and inline.tag!=tag('wp:inline'):inline=inline.getparent()
    assert inline is not None
    ext=inline.find('wp:extent',NS);cx=int(ext.get('cx'));cy=round(cx*h/w);ext.set('cy',str(cy))
    for e in inline.findall('.//a:xfrm/a:ext',NS):e.set('cx',str(cx));e.set('cy',str(cy))

# Renumber citations by first body appearance and reorder the bibliography.
refs={i-100:re.sub(r'^\[\d+\]\s*','',text(P[i])) for i in range(101,121)}
refs.update({21:'HUANG R, HUANG Y, GUO H. Remembering or monitoring? Contextual fit of simulated AI memory cues and consumer trust[J]. Frontiers in Psychology, 2026, 17:1934857. DOI:10.3389/fpsyg.2026.1934857.',
22:'HUANG R, HUANG Y, GUO H. AI Memory Boundary Fit: de-identified study data[DS/OL]. 固定提交3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53[2026-10-29]. https://github.com/RunhuaHuang/aimemory/tree/3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53. 数据集CC BY4.0.',
23:'HUANG R, HUANG Y, GUO H. Supplementary File 1 to Remembering or monitoring?[DS/OL]. S14, PDF19—20及22页[2026-10-29]. https://public-pages-files-2025.frontiersin.org/articles/1934857/file/Supplementary_file_1.pdf/1934857_supplementary-file_1/1.'})
order=[]
for e in list(body)[:body.index(P[100])]:
    for n in re.findall(r'\[(\d+)\]',text(e)):
        n=int(n)
        if n not in order:order.append(n)
assert set(order)==set(refs),(order,set(refs)-set(order))
mapping={old:i+1 for i,old in enumerate(order)}
for e in body:
    if e in P[101:121]:continue
    for t in e.findall('.//w:t',NS):
        if t.text:t.text=re.sub(r'\[(\d+)\]',lambda m:'['+str(mapping[int(m.group(1))])+']',t.text)
at=body.index(P[101])
for e in P[101:121]:body.remove(e)
for old in order:
    entry=newp('['+str(mapping[old])+'] '+refs[old],120)
    pr=entry.find('w:pPr',NS)
    if pr is None:pr=ET.Element(tag('w:pPr'));entry.insert(0,pr)
    jc=pr.find('w:jc',NS)
    if jc is None:jc=ET.SubElement(pr,tag('w:jc'))
    jc.set(tag('w:val'),'left')
    body.insert(at,entry);at+=1

package['word/document.xml']=ET.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
core=ET.fromstring(package['docProps/core.xml'])
for t in core:
    if ET.QName(t).localname in ['creator','lastModifiedBy']:t.text=''
package['docProps/core.xml']=ET.tostring(core,encoding='UTF-8',xml_declaration=True,standalone=True)
target=OUT/'AI导购理由撤回后的预算重审_补强稿国内数据版.docx'
with zipfile.ZipFile(target,'w') as z:
    for info in infos:z.writestr(info,package[info.filename])
changed=[k for k in original if original[k]!=package[k]]
allowed=['word/document.xml','word/media/image2.png','word/media/image3.png','docProps/core.xml']
assert set(changed)<=set(allowed)
assert sha(SOURCE)=='ac4e5ffdc717fdfe0c9ed8881a6fdf303a5c562893379076516518e362f39ca8'
final_text='\n\n'.join(text(e) for e in body)
for forbidden in ['合成机制仿真','40,000','120,000','51.70','31.25','MCSE','54场景','all_summary.csv','run_goal_repair_simulation','1,800','388项']:
    assert forbidden not in final_text,forbidden
(OUT/'report_text.txt').write_text(final_text,encoding='utf-8')
trace={'date':'2026-10-29','source_sha256':sha(SOURCE),'source_unchanged':True,'output':target.name,'output_sha256':sha(target),
       'changed_package_parts':changed,'all_other_package_parts_byte_identical':True,'citation_old_to_new':mapping,
       'original_paragraphs_revised':sorted(updates),'replaced_original_ranges':[[35,44],[71,84],[127,132]],'original_tables_revised':[0,2,4],
       'source_results_sha256':{p.name:sha(p) for p in (DATA/'results').glob('*.csv')},
       'normative_scope_fix':'Conditional exploration distinguished from effective budget execution.',
       'unverified_completion_claims_removed':['pixel-matching and hash-correction claims','old numerical validation claims','unprovided PPT and anonymous-package completion claims'],
       'new_behavior_generated':False,'main_analysis_rerun':False,'original_foreign_simulations_not_restored':True}
(OUT/'修订核对.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'docx':target.name,'bytes':target.stat().st_size,'changed_package_parts':changed,'references':len(refs),'original_untouched':True},ensure_ascii=False))
