"""Build evidence/status records from existing completed research; no new simulation."""
from pathlib import Path
import csv, json, hashlib, shutil

ROOT=Path(__file__).resolve().parent
RESEARCH=ROOT.parent
REPO=RESEARCH.parent

def write_csv(name,header,rows):
    with (ROOT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)

rows=[
 ('EV01','NORM','角色责任与公开理由依赖','review/规范桥梁_反方复核.md','2026-10-29','已完成条件性规范论证','决定地位、邀请依赖、控制与比例性','不由模拟结果推出义务；前提待作者审阅'),
 ('EV02','EXP','用户手机三次探索','../三次试跑_关键断言与纠错证据表.md','2026-10-28既有核对','已有记录，非受控重复','无据断言及后来撤回的具体线索','不证明造成真实预算上调，不是3名参与者'),
 ('EV03','PILOT','元宝给定历史T1—T3','../evidence/元宝桌面版预试_匿名会话.json','2026-10-28','3会话×3条发送及回应已执行','T1建议便宜款且保留乙入口；T2/T3支持独立理由；后续接受重申并停止新增推荐','自然生成错误、后台目标和真实理解未知'),
 ('EV04','CASE','公开理由、独立理由及重申','参赛报告蓝图_可审阅.md#d1-情形判断证据','2026-10-29','构造规范对照，部分有给定历史响应','比较应说明或停止的理由','不同类型不是心理因果实验'),
 ('EV05','CASE','普通更正功能已充分的正例','参赛报告蓝图_可审阅.md#c3-子论点二责任是否完成取决于功能而非追加确认','2026-10-29','新规范正例，未新增交互测试','无额外确认也可完成修复','实际理解未测'),
 ('EV06','CASE','自身无据／当时有据后撤回／第三方转述','参赛报告蓝图_可审阅.md#c4-子论点三责任来源与当前能力分别审查','2026-10-29','新规范对照','区分先前过错、特别责任与当前责任','不能写作3项已完成实验'),
 ('EV07','SIM','正式纠错后机制模型','../simulation_goal_repair_20261028/results/validation.json','2026-10-28','已运行并复核；本轮不重跑','54场景、10策略、3规则；基准每类40000，三类120000合成条件','行为参数假设；不是参与者或现实发生率'),
 ('EV08','SIM','固定D的R×C及原D×C','../simulation_goal_repair_20261028/results/all_summary.csv','2026-10-28','有正式原始表','同输入比较关联说明、操作及成本后果','两个2×2分开；不能称元宝商业偏向实验'),
 ('EV09','SIM','强基线及反转','../simulation_goal_repair_20261028/results/paired_link_contrasts.csv','2026-10-28','实际结果已保留','无效、负担及反转、强选择性再确认等价','不证明新算法优势或伦理规则正确'),
 ('EV10','DESIGN','原E2 MATLAB机制设计','../E2_MATLAB机制仿真设计.md','2026-10-28历史阶段','原设计未独立运行','方法设计和与新模型的历史关系','不能把原设计未运行误写成当前没有任何SIM'),
 ('EV11','STAGE1','拒绝边界初稿','../../stage1/拒绝后的再建议边界_研究报告初稿.pdf','2026-10-28取得','15页已读，配套代码未取得','概念、权限边界、前期报告自述','16格及探针计数未独立复跑；不与SIM合并'),
 ('EV12','LIT','Fong等直接近邻','review/近邻补证_读取与增量.md','2026-10-29','取得PDF并精读指定章节','信念/固有偏好、纠错WTP、行动后果及企业均衡仿真已有覆盖','非全文精读；局部未见不能证明领域空白'),
 ('EV13','LIT','C1李术平','review/近邻补证_读取与增量.md','2026-10-29','仍仅摘要、题录及公开注释','形成过程的保护已有本土研究','正文缺口限制创新排他性，不评其全文方法缺陷'),
 ('EV14','FACT','现实商品及型号','../evidence/商品核验002_E01230_参数及来源核对.md','2026-10-28既有核对','部分可核，部分待证','页面型号和条件性价格等材料','CCC商家标注非独立认证核验，构造目录不当真实规格'),
 ('EV15','GOV','设计与审计清单','参赛报告蓝图_可审阅.md#e2-可实施设计审计清单','2026-10-29','设计已形成，未部署','责任主体、触发、措施、验收及代价','不是现有平台已实现效果，不把伦理要求统一当法定义务'),
 ('EV16','DOC','仿真方法结果讨论章节','../phase4_simulation_sections_20261028/draft.md','2026-10-28','已完成可编辑Word及6页排版核验','可复用的方法、结果、讨论和图表','不是完整报告或完成查重证明'),
]
write_csv('证据与版本台账.csv',['证据ID','身份','对象','来源及定位','日期','实际状态','可支持内容','成立边界'],rows)

materials=[
 ('C1','摘要及公开信息','未取得本地全文','题录、双语摘要及公开注释','review/近邻补证_读取与增量.md'),
 ('C2','精读论证正文','已取得本地PDF','PDF1—17，印刷122—138；参考文献未逐项核验','../evidence/核心精读_C2_C3_I1.md'),
 ('C3','精读论证正文','已取得本地PDF','PDF1—20，印刷99—118；参考文献未逐项核验','../evidence/核心精读_C2_C3_I1.md'),
 ('C4','部分正文','已取得本地PDF','局部读取；具体定位沿既有记录','../B_核心论文论证方法矩阵.md'),
 ('C5','部分正文','已取得本地PDF','局部读取；具体定位沿既有记录','../evidence/核心精读_N6_S1与补充.md'),
 ('I1','精读论证正文','已取得本地PDF','PDF1—16；参考文献未逐项核验','../evidence/核心精读_C2_C3_I1.md'),
 ('I2','部分正文','已取得本地PDF','局部读取；不评价未读全文方法','../evidence/核心精读_N6_S1与补充.md'),
 ('I3','精读论证正文','已取得本地PDF','PDF1—32；参考文献未逐项核验','../evidence/核心精读_I3_I4_N2.md'),
 ('I4','精读论证正文及所记注释','已取得本地PDF','PDF1—14及20—22所记部分','../evidence/核心精读_I3_I4_N2.md'),
 ('I5','部分正文','已取得本地PDF','局部读取；不评价未读全文方法','../evidence/核心精读_N6_S1与补充.md'),
 ('I6','原清单摘要/索引节选','未取得本地全文','未重核全文，按逐篇卡实际范围','../../literature/文献目录与下载状态.md'),
 ('N1','原清单及元数据线索','未取得本地全文','按逐篇卡范围，不扩成全文评价','../../literature/文献目录与下载状态.md'),
 ('N2','精读论证正文','已取得本地PDF','PDF1—41；引用列表未逐项核验','../evidence/核心精读_I3_I4_N2.md'),
 ('N3','部分正文','已取得本地PDF','局部读取，按既有记录','../B_核心论文论证方法矩阵.md'),
 ('N4','网页部分正文','未保存本地全文','网页§1—2及既有局部；按原记录','../../literature/文献目录与下载状态.md'),
 ('N5','在线PDF部分正文','未保存可交付本地全文','在线PDF1—7所记范围','../../literature/文献目录与下载状态.md'),
 ('N6','精读论证正文','已取得本地PDF','PDF1—17；参考文献未逐项核验','../evidence/核心精读_N6_S1与补充.md'),
 ('N7','部分正文','已取得本地PDF','PDF1—2、44—46、49—50、64—67','../evidence/核心精读_N6_S1与补充.md'),
 ('N8','部分正文','已取得本地PDF','局部读取，按既有记录','../evidence/核心精读_N6_S1与补充.md'),
 ('S1','精读论证正文','已取得本地PDF','PDF1—25；参考文献未逐项核验','../evidence/核心精读_N6_S1与补充.md'),
 ('S2','原清单摘要/索引线索','未取得本地全文','按逐篇卡范围，不扩成全文评价','../../literature/文献目录与下载状态.md'),
 ('R1','部分正文','已取得本地PDF','PDF14—15、17—19及原记录片段','../预试后继续分析_创新增量与强基线比较.md'),
 ('V1','部分正文','已取得本地PDF','PDF6—7、11—12','../创新续查_文献方法与读取记录.md'),
 ('V2','精读短文论证主体','已取得本地PDF','PDF1—3；引用列表未逐项核验','../创新续查_文献方法与读取记录.md'),
 ('V3','部分正文','已取得本地PDF','PDF5—8、12—14','../创新续查_文献方法与读取记录.md'),
 ('W1/Fong','精读相关章节','本轮取得本地23页PDF','PDF1—6、8、17—21；非全文精读','review/近邻补证_读取与增量.md'),
 ('M3','部分正文','已取得本地PDF','PDF1、9—10','../simulation_goal_repair_20261028/sources/reading_log.json'),
 ('M4','部分正文','已取得本地111页版本','PDF1—4、8—9；arXiv v4','../simulation_goal_repair_20261028/sources/reading_log.json'),
]
write_csv('主要材料读取状态.csv',['文献编号','阅读等级','全文取得状态','实际范围','详细记录'],materials)

intro='本研究聚焦中国成年消费者使用中文AI购物助手选购充电器，讨论重要购买理由被撤回后，助手对既有目标变化的纠错责任。研究结合文献与概念分析、配对规范案例、元宝限定预试及MATLAB合成机制仿真，提出依据公开理由关联、重要性、可调整性与负担判断的说明和重选要求，并区分独立理由、知情重申及退出边界。成果包括条件性责任判准、可复现机制分析和设计审计清单，为兼顾便利、知情选择与消费自主性提供治理依据。'
(ROOT/'作品简介_300字内草案.txt').write_text(intro+'\n',encoding='utf-8')

# Preserve the previous snapshot before updating the current ledger.
ledger=RESEARCH/'论点证据台账_已填.csv'
archive=ROOT/'论点证据台账_20261028仿真前快照.csv'
if not archive.exists():shutil.copy2(ledger,archive)
with archive.open(encoding='utf-8-sig',newline='') as f: previous=list(csv.DictReader(f));header=list(previous[0])
for r in previous:
    if r['编号']=='S1':
        r.update({'材料身份':'SIM 已运行新模型','主张或待论证事项':'理解、关联注意、操作及成本可使更正后重评的结果分离，并存在无效和反转','来源及定位':'simulation_goal_repair_20261028/results；phase4_simulation_sections_20261028/draft.md','可支持的层次':'已运行的合成条件机制与复现；强选择性再确认同构等参时等价','推断边界':'假设参数未真人校准；不是完整自主性效果或新算法优势','补证或反驳动作':'以真实理解、认可和负担研究补证；当前数值不因蓝图阶段重跑','状态':'2026-10-28已执行并修复复核；2026-10-29台账更新'})
with ledger.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=header);w.writeheader();w.writerows(previous)

record={'date':'2026-10-29','scope':'P0 A-F blueprint, evidence/version alignment, nearest-literature supplement; no new simulation or human study','intro_characters':len(intro),'intro_limit':300,'title':'AI导购纠错与目标重审','title_characters':len('AI导购纠错与目标重审'),'evidence_rows':len(rows),'material_rows':len(materials),'author_outline_review':'pending','formal_ars_pipeline_passport':False,'criteria_binding':'criteria_binding_unavailable; manual evidence mapping from verified official attachments','sources':{'W1_reading':'PDF1—6,8,17—21; partial body reading','C1':'abstract and public metadata; full text unavailable'},'local_originals_modified':False}
assert len(intro)<=300 and len(record['title'])<=20
(ROOT/'本轮执行记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
