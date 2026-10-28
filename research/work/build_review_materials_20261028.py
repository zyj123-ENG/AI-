from pathlib import Path
import csv
import hashlib
import json
import re

root = Path(__file__).resolve().parents[1]
corpus = json.loads((root / 'evidence/元宝桌面版预试_完整会话与元数据.json').read_text(encoding='utf-8-sig'))

title = 'AI导购纠错与目标重审'
intro = '本研究聚焦中国成年消费者使用中文AI购物助手选购iPhone 15充电器时的知情选择与消费自主性。基于文献论证方法拆解、规范案例比较及元宝桌面版三条构造情景预试，考察重要购买理由撤回后，助手应如何处理由此形成的预算与目标变化。研究区分事实更正、建议与目标改写，提出有条件的关联说明与重选机会，并以独立理由、知情重申和退出需求限定干预。成果包括可追溯的论证链、交互记录及设计审计清单。'
assert len(title) <= 20
assert len(intro) <= 300
(root / '研究简介_审阅稿.txt').write_text(intro + '\n', encoding='utf-8')

headers = ['编号', '材料身份', '主张或待论证事项', '来源及定位', '可支持的层次', '推断边界', '补证或反驳动作', '状态']
rows = [
 ['L1', '规范论证', '同一最新预算可有不同的理由形成条件', 'N6正文1—17；V2 PDF1—3；V3 PDF5—8；T1—T3给定背景', '概念区分及规范前提；条件响应实例', '构造背景不证明真人真实动机或发生率', '核对公开理由关联；以动机不清及独立理由反驳', '已形成论证，待作者审阅'],
 ['L2', '规范论证', '重要理由撤回可触发针对目标的说明与重选机会', 'C3 PDF1—20；R1 PDF14—15与17—19；V5官方再确认模式', '从程序性自主到条件规则的规范推导', '既有原则已提供基础；不据单次响应确认新理论', '与较强元偏好及再确认逐例比较；收窄重要性和可调整条件', '已比较强基线'],
 ['L3', '规范论证＋PILOT', '评价性建议与实际目标改写应分开', 'T1第一轮；T1第二轮；完整会话JSON', '推荐甲及恢复预算措辞、留乙入口和后续接受明确选择', '后台目标未知；甲同时符合150及200范围', '如研究实际目标状态，另取状态展示及可复核后续约束证据', '可见表现已记录'],
 ['L4', '规范论证', '提醒强度应考虑独立理由、委托、退出及负担', 'V1 PDF11—12；R1 PDF17—19；V3 PDF12—14', '边界、竞争价值及比例性理由', '没有真人时间、理解、满意或负担效果', '增强版独立测量实际理解与操作负担', '规范边界已形成'],
 ['P1', 'PILOT', 'T1识别撤回并建议便宜款，同时保留乙的入口', '完整会话JSON T1第1轮；2026-10-27T23:21:21.624Z', '该次真实响应', '不是自然生成错误后的自我纠正；不是预算已改写证据', '保留完整回复；不删留乙入口；新检验另定协议', '已执行，完整记录'],
 ['P2', 'PILOT', 'T2在原先有独立颜色理由时支持乙', '完整会话JSON T2第1轮；2026-10-27T23:25:00.194Z', '对给定理由背景的响应实例', '每条件一次，措辞不同；不估计条件效应', '如需稳定性，预定重复和顺序并另采', '已执行，完整记录'],
 ['P3', 'PILOT', 'T3在知情重申后支持乙', '完整会话JSON T3第1轮；2026-10-27T23:28:40.210Z', '对给定重申的响应实例', '无真人知情程度测量', '如需认可效果，使用真实参与者及独立理解检查', '已执行，完整记录'],
 ['P4', 'PILOT', '三条会话都接受后续知情因颜色选择乙的表达', '完整会话JSON T1—T3第2轮', '本轮三条可见响应及后续选择处理', '不能推广总体成功率或全部购物任务', '保留正面结果；不同条件另设研究', '已执行，完整记录'],
 ['P5', 'PILOT', '三条末轮正文均停止新增推荐和追问', '完整会话JSON T1—T3第3轮', '停止指令后的正文表现', '历史入口及应用退出摩擦未被此项检验', '若界面退出为主张对象，另保存操作及界面证据', '已执行，完整记录'],
 ['X1', 'EXP 用户提供', '手机探索中的无据断言及指定纠错提供研究线索', '三次试跑_关键断言与纠错证据表 K01—K10；三次原截图及后续原文', '具体语句及更正过程', '截图与后续文字来源分列；非同脚本重复、非3名参与者', '按断言精确型号及来源补证；保留成功纠错', '已有材料已核，部分商品事实待补'],
 ['F1', 'FACT', '公开商品证据须匹配型号、条件和来源', '商品核验002_E01230_参数及来源核对；Apple官方支持来源', '型号与页面宣称及其限制', '商家标注CCC不是独立认证核验；价格有取得条件', '查精确型号说明和认证；未取到就记未知', '部分已核，缺口明示'],
 ['C1', 'CASE', '无关小错不应全面重开目标', '构造案例_错误依据与目标变更_研究设计 CASE4', '规范边界检验', '没有实际系统响应或真人效果', '若需实测，先冻结重要性定义并新建协议', '研究设计，未执行'],
 ['C2', 'CASE', '理由不清时不得推断消费者被操纵', '同设计 CASE5；I4工作定义；N6', '概念及推断边界', '公开价格上涨不证明隐蔽利用或心理因果', '明确未知；检验是否存在公开理由关联', '规范分析，未执行'],
 ['D1', 'CASE研究设计', '商业披露与选择控制应分别比较', '原方案E3；整合稿E3；四组尚未采集', '对照与可观察标准', 'T1—T3不是商业披露×控制2×2', '冻结商品、商业偏向、任务与长度；记录不可控差异', '研究设计，未执行'],
 ['S1', 'SIM研究设计', '注意与操作成本可能限制或反转干预效果', 'E2_MATLAB机制仿真设计 变量／公式／敏感性及验证计划', '条件机制及待检验边界', '参数多为假设；未运行，无真实自主性效果', '达到运行门槛后配对输入、多规则及误差稳定性检查', '研究设计，未运行'],
 ['G1', '治理设计', '关联说明及保留／修改／结束应可用', '整合稿F；预试后继续分析第5节', '规范可实施方案与验收要求', '不是平台已经部署或现行法统一UI义务', '正式原型或系统审计后逐项验收', '设计已形成，未部署'],
]
with (root / '论点证据台账_已填.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

anon = {k: v for k, v in corpus.items() if k != 'cases'}
anon['privacyProcessing'] = '去除私有会话URL及标识；保留提示、主回应、相邻建议、采集时间和环境。未改写对话。'
anon['cases'] = []
lines = ['# 元宝桌面版预试：匿名文字摘录', '', '日期2026-10-28；Windows文件版本2.90.0.607；可见模式“快速回答”。底层模型及记忆设置未知。三个构造情景，每会话三轮；安全优势撤回的历史由研究者给定。本文件保留全部实际发送、主回答及相邻建议文字，移除私有会话标识。', '', '时点为完整回应读取时点，不是响应延迟。相邻建议的模型／平台模块归属未独立核明，未点击。', '']
for case in corpus['cases']:
    anon_case = {'id': case['id'], 'rounds': case['rounds']}
    anon['cases'].append(anon_case)
    lines.extend([f"## {case['id']}", ''])
    for turn in case['rounds']:
        lines.extend([f"### 第{turn['round']}轮", '', f"采集UTC：{turn['capturedAtUTC']}", '', '实际发送：', '', '> ' + turn['user'], '', '元宝主回答：', ''])
        lines.extend(['> ' + part for part in turn['assistant'].splitlines()])
        lines.append('')
        if turn.get('adjacentUITexts'):
            lines.extend(['相邻建议文字（未点击）：', ''])
            lines.extend(['- ' + item for item in turn['adjacentUITexts']])
            lines.append('')
anon_md = '\n'.join(lines)
anon_json = json.dumps(anon, ensure_ascii=False, indent=2)
for banned in ['C:/Users/', 'C:\\Users\\', '0Rb7Y9PcZc', 'tencent.yuanbao/chat?', 'appConversationURL', 'wxid_']:
    assert banned not in anon_md and banned not in anon_json, banned
(root / 'evidence/元宝桌面版预试_匿名文字摘录.md').write_text(anon_md, encoding='utf-8')
(root / 'evidence/元宝桌面版预试_匿名会话.json').write_text(anon_json + '\n', encoding='utf-8')
for source, dest in zip(corpus['cases'], anon['cases']):
    assert source['rounds'] == dest['rounds']

entry = '''# 先看这页：现在的方案已经推进到哪里

推荐题目供审阅：**AI导购纠错与目标重审**。

研究问题：**AI说买贵的更安全，用户因此提高预算；后来这条理由被撤回，AI接下来应该怎样处理？**这里的价格与历史为构造案例。

方案的判断是：说明这次更正和原升级理由的关系，让用户能保留、修改或结束；用户已知情并因颜色等独立理由保留升级，就承接决定，停止重复追问。推荐便宜款可以是合理建议，是否实际替用户改了目标要另有证据。

已完成：八篇核心论文的方法拆解；最近研究和强基线比较；元宝桌面三会话九轮预试；四个递进论点与反对意见；治理验收清单；已填证据台账及匿名预试文字；报告提纲和提交核对。

本次元宝接受了知情后选择乙的表达，并响应结束指令。它提供的是研究判准的正面及边界实例。当前贡献定位为具体情境中的规范推导与审计操作化，最终题目和贡献强度保留给作者审阅。

接着看[整合审阅版研究方案](参赛研究方案_整合审阅版.md)。其中A—I已统一问题、论证、证据、案例、可选仿真、治理和写作顺序。按G的提纲可以进入正式报告写作；当前交付仍是研究方案。

真实用户理解和负担、正式商业披露×控制2×2、MATLAB、报告PDF、PPT及知网查重尚未完成，各自保留在设计或待办状态。
'''
(root / '现在看这一页_整合方案说明.md').write_text(entry, encoding='utf-8')

main = root / '参赛研究方案_整合审阅版.md'
body = main.read_text(encoding='utf-8')
targets = re.findall(r'\]\(([^)]+)\)', body)
local_targets = [x for x in targets if not x.startswith(('https://', 'http://'))]
assert all((root / x).is_file() for x in local_targets)
files = ['参赛研究方案_整合审阅版.md', '现在看这一页_整合方案说明.md', '研究简介_审阅稿.txt', '论点证据台账_已填.csv', 'evidence/元宝桌面版预试_匿名文字摘录.md', 'evidence/元宝桌面版预试_匿名会话.json']
manifest = {}
for name in files:
    data = (root / name).read_bytes()
    assert '\ufffd' not in data.decode('utf-8-sig')
    manifest[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
checks = {'date': '2026-10-28', 'title': title, 'titleCharacters': len(title), 'introCharactersIncludingPunctuation': len(intro), 'ledgerRows': len(rows), 'cases': len(anon['cases']), 'userMessages': sum(len(c['rounds']) for c in anon['cases']), 'anonymousDialogueMatchesOriginal': True, 'privateURLAndPathPatternCheck': 'pass for anonymous dialogue outputs only', 'mainLocalLinksChecked': len(local_targets), 'scope': '研究方案与材料完整性；不是正式参赛包验收，也不是命题真实性的独立证明', 'files': manifest}
(root / 'evidence/整合审阅版_生成与核对记录.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in checks.items() if k != 'files'}, ensure_ascii=False, indent=2))
