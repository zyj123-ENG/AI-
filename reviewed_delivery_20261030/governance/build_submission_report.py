"""Issue-3/4-only package patch. Scientific chapters and original data are frozen."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,zipfile
from lxml import etree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'submission';OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'research/user_reinforced_domestic_revision_20261029/AI导购理由撤回后的预算重审_补强稿国内数据版.docx'
TARGET=OUT/'AI导购理由撤回后的预算重审_参赛修复稿.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};W='{'+NS['w']+'}'
def text(e):return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(elements):return digest(b'\n'.join(ET.tostring(e,method='c14n') for e in elements))

with zipfile.ZipFile(SOURCE) as z:
    infos=z.infolist();original={n:z.read(n) for n in z.namelist()}
root=ET.fromstring(original['word/document.xml']);body=root.find('w:body',NS)
blocks=list(body)
gov=next(i for i,e in enumerate(blocks) if text(e)=='四 治理设计与伦理反思')
conclusion=next(i for i,e in enumerate(blocks) if text(e)=='结论')
refs=next(i for i,e in enumerate(blocks) if text(e)=='参考文献')
appendix=next(i for i,e in enumerate(blocks) if text(e)=='附录')
frozen_prefix=canonical(blocks[:gov]);frozen_conclusion=canonical(blocks[conclusion:refs]);frozen_refs=canonical(blocks[refs:appendix])
normal=next(e for e in blocks[gov:] if e.tag==W+'p' and text(e).startswith('预算重审的治理重点'))
caption=next(e for e in blocks if text(e).startswith('表4 分主体'))
template_table=body[body.index(caption)+1]
assert template_table.tag==W+'tbl'

def put(p,value,size=None,bold=False):
    r=deepcopy(p.find('w:r',NS)) if p.find('w:r',NS) is not None else ET.Element(W+'r')
    for ch in list(r):
        if ch.tag!=W+'rPr':r.remove(ch)
    if size:
        pr=r.find('w:rPr',NS)
        if pr is None:pr=ET.SubElement(r,W+'rPr')
        for k in ['sz','szCs']:
            n=pr.find('w:'+k,NS)
            if n is None:n=ET.SubElement(pr,W+k)
            n.set(W+'val',str(round(size*2)))
        if bold:
            b=ET.SubElement(pr,W+'b');b.set(W+'val','1')
    t=ET.SubElement(r,W+'t');t.text=value
    t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    for ch in list(p):
        if ch.tag!=W+'pPr':p.remove(ch)
    p.append(r)

def para(value,kind='normal'):
    p=deepcopy(caption if kind=='caption' else normal);put(p,value)
    return p

def table(values,widths):
    tbl=deepcopy(template_table)
    row_template=deepcopy(tbl.findall('w:tr',NS)[1])
    header_template=deepcopy(tbl.findall('w:tr',NS)[0])
    for row in tbl.findall('w:tr',NS):tbl.remove(row)
    grid=tbl.find('w:tblGrid',NS)
    for ch in list(grid):grid.remove(ch)
    for width in widths:
        ET.SubElement(grid,W+'gridCol').set(W+'w',str(round(width*1440)))
    for ri,values_row in enumerate(values):
        row=deepcopy(header_template if ri==0 else row_template)
        cells=row.findall('w:tc',NS)
        while len(cells)<len(values_row):row.append(deepcopy(cells[-1]));cells=row.findall('w:tc',NS)
        for cell in cells[len(values_row):]:row.remove(cell)
        for cell,value,width in zip(row.findall('w:tc',NS),values_row,widths):
            props=cell.find('w:tcPr',NS);props.find('w:tcW',NS).set(W+'w',str(round(width*1440)))
            paragraphs=cell.findall('w:p',NS)
            p=paragraphs[0]
            for other in paragraphs[1:]:cell.remove(other)
            put(p,value,10,ri==0)
        tbl.append(row)
    return tbl

rows=[
 ['责任主体与触发','具体措施','可观察验收','停止或重新判断'],
 ['产品团队：重要依据撤回，存在已核公开预算关联，决定仍可调整且沟通相称','在原更正中说明依据状态及关联，开放维持、修改、降用途和暂不买','理由ID、来源版本、用户原话及轮次可回溯；不以点击或提价猜动机','普通更正已充分完成时不追加；关联不明则保留当前约束'],
 ['推荐团队：用户拒绝该升级方向','关闭同一商业推动；相关新事实仅作必要说明','拒绝范围、同一理由语义及来源更新有记录；事实通知与促销分别编码','同一旧理由不再推；新实质事实或用户主动请求才重新判断'],
 ['交互团队：同一依据版本仍需预算关联提示','默认至多一次主动预算邀请，无强制弹窗；回答用户主动问题另记','按理由及实质事实版本计数；改措辞不得重置；记录字符与新增步骤','首次充分提示后停止主动重复；知情重申或结束立即停止'],
 ['状态与执行团队：用户表达维持或修改','当前预算持续有效；更新须有明确表达或可核预先委托','保存前后预算、授权表达与轮次；筛选实参及候选总支付可比对','无新授权不改写；可撤回、恢复或结束'],
 ['产品团队：收到更正后的维持表达','关联先前告知版本，保存用户重申原话；不强制理解测验','可核告知先于重申，记录本人是否另给理由；不宣称已测心理理解','已知情重申、独立理由充分或明确结束后不重复重开'],
 ['推荐团队：预算内没有满足用途的方案','如实解释冲突，保留降功能、暂不买及本人主动改预算','可行性与必要条件来源明确；不隐藏预算内可行候选','拒绝后维持关闭；不得将不可行直接当作提价许可'],
 ['分析与隐私团队：记录沟通及可选评价','分别记录主动提醒次数、字符、新增操作与任务时间；自报负担需另取同意','各指标单列，不合成自主性总分；不得填入原数据未测的负担值','用户跳过或退出即停止可选追问；不以完成评价为继续条件'],
 ['审计团队：发现预算状态或筛选变化','独立比较授权日志、前后预算及实际候选，不只看“尊重预算”措辞','无匹配授权的目标变更、超有效上限筛选分别记异常，条件预览另标','修复错误状态并开放纠正渠道；新变更再次核授权'],
 ['平台：保存纠错关联及触发紧急风险告知','仅存任务必要关联与版本；严重新安全风险另审最少通知','留存目的、访问和删除规则明确；紧急事实不夹带替代品营销','任务结束停止营销；风险通知依必要性、时效与适当渠道另判'],
]
put(caption,'表4 触发措施验收与停止条件')
body.replace(template_table,table(rows,[1.55,1.85,1.85,1.6]))
put(normal,'预算重审的治理重点，是让重要更正触及已知用途，并保留消费者维持、修改或结束选择的能力。表4把第三章既有判准转成拟议工程要求，验收对象为可见输出和执行记录。以下配置尚未经过真实平台部署或负担研究检验。[14]')
after=body.index(caption)+2
details=[
 '公开关联采用可回溯的最低证据：用户明确把某项理由用于预算变更的原话、会话轮次和对应理由ID。匹配器只能提交待核候选；仅凭预算上升、停留或点击不得建立动机关系。用户否认关联时更正记录，不要求收入、资产或跨平台画像。',
 '每个实质依据版本默认至多一次主动预算邀请，这是本实现的防重复配置，不是已验证的最佳伦理次数。普通更正已经充分时为零次。用户主动追问的必要答复单独记录；“新版本”必须对应可核实的重要事实变化，不能靠改措辞、换商品标题或刷新任务编号重置计数。',
 '“知情重申”的可审计记录包括已发送的更正版本、其后的用户维持表达和轮次。该记录表明系统提供过信息且用户作出表达，不宣称证明真实理解。未收到有效预算更新前继续按当前预算执行；条件性预览必须显式标注并与实际筛选状态分开。',
 '信息负担分项记录：主动提示次数、提示字符、额外选择步骤、完成时间和可选自报负担。前四项需真实交互日志及适当告知，主观负担需另行研究。本项目未据此报告消费者负担效果，也未设经验证的负担阈值。',
 'governance/budget_guard.py提供预算状态守卫和独立日志检查器的参考实现。16项构造输入的工程断言检查授权、重复提示、停止和筛选越限；它们不新增消费者观察，也不改动原六臂统计分析。真实系统仍需接入可信会话记录、商品总价和授权来源，不能仅凭模型自报日志认定合规。',
]
for value in details:
    body.insert(after,para(value));after+=1
mapping=[['既有结果或命题','正文中的既有含义','治理实现','验收记录'],
 ['平均信任差与主δ分别报告','平均评价与特定问题缓解分别判断','按具体修复目标验收，不用平均信任替代预算执行审计','告知、预算状态、筛选及停止分别编码'],
 ['主δ区间跨零，403人为子样本','既有结果保留不确定性及样本边界','保留失败与未决记录，不把16项协议检查当消费者效果','工程检查与原统计结果分栏存档'],
 ['第三章的关联、完成及停止判准','责任由既有规范论证承担','仅在条件齐备时提示；充分更正、重申或结束后停止','原话定位、事实版本、提示次数及结束事件'],
]
body.insert(after,para('表5 既有结果命题与治理验收的对应','caption'));after+=1
body.insert(after,table(mapping,[1.6,1.65,1.9,1.7]))

for p in body.findall('w:p',NS):
    if text(p)=='表5 关键材料的可复核结论':put(p,'表6 关键材料的可复核结论')
    if text(p).startswith('本稿为用户补强稿的国内数据替换版。'):
        put(p,'本稿为仅修复复审第三、第四项的参赛整合版，第一至第三章、摘要、结论及参考文献沿用基准。配套答辩PPT、匿名复现材料及材料状态见submission。真实知网正文检测与报告尚未取得，不能登记为已完成；正文检测不含附录，重复率需严格低于20%，真实报告取得并作匿名检查后附入。永久百度网盘分享、团队编号命名及正式提交仍按实际完成状态核对。')
end=next(i for i,e in enumerate(body) if e.tag==W+'sectPr')
appendix_parts=[para('附录五 产品验收与复现说明','caption'),
 para('governance目录保存规则说明、预算状态参考实现、独立事件审计和16项工程断言。运行python governance/check_protocol.py可重现协议检查；原统计复现命令及数据继续按附录二执行。协议输入为研究者构造，不代表实际模型响应或消费者心理。'),
 para('submission目录提供完整研究报告、答辩PPT、匿名复现包及查重正文导出。README逐项列已生成、待真实检测和待外部提交的状态。复现入口在仓库当前版本，匿名包只保留必要研究材料及正常学术出处，剔除本机路径、参赛者账号与未核许可全文。'),
 para('本轮采用academic-research-suite的定向修订原则、anti-defensive-writing和文档及演示排版检查；同一AI助手完成自审。保护范围的XML及文件哈希见submission/revision_scope.json，不把自审写成外部同行评审。'),
]
for e in appendix_parts:body.insert(end,e);end+=1

package=dict(original);package['word/document.xml']=ET.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with zipfile.ZipFile(TARGET,'w') as z:
    for info in infos:z.writestr(info,package[info.filename])
with zipfile.ZipFile(TARGET) as z:reopened=ET.fromstring(z.read('word/document.xml')).find('w:body',NS)
new=list(reopened);ng=next(i for i,e in enumerate(new) if text(e)=='四 治理设计与伦理反思');nc=next(i for i,e in enumerate(new) if text(e)=='结论');nr=next(i for i,e in enumerate(new) if text(e)=='参考文献');na=next(i for i,e in enumerate(new) if text(e)=='附录')
assert canonical(new[:ng])==frozen_prefix
assert canonical(new[nc:nr])==frozen_conclusion
assert canonical(new[nr:na])==frozen_refs
full='\n\n'.join(text(e) for e in reopened).rstrip()+'\n'
(OUT/'报告核对文本.txt').write_text(full,encoding='utf-8')
(OUT/'知网检测正文_不含附录.txt').write_text('\n\n'.join(text(e) for e in new[:na]).rstrip()+'\n',encoding='utf-8')
rules={'status':'Proposed operational design, not validated consumer intervention',
 'max_proactive_budget_invites_per_material_revision':1,'ordinary_correction_complete_invites':0,
 'table_columns':rows[0],'rules':rows[1:],
 'burden_indicators':['proactive_invite_count','message_characters','extra_required_steps','task_completion_time','optional_self_report'],
 'no_autonomy_composite_score':True,'new_budget_requires_effective_user_authorization':True}
(ROOT/'governance/rules.json').write_text(json.dumps(rules,ensure_ascii=False,indent=2),encoding='utf-8')
scope={'base_commit':'ed7bbd7b5de2ed483b7b8f2b82b24ab59307ec94','authorized_review_issues':[3,4],
 'issues_1_2_changed':False,'protected_chapters_1_to_3_c14n_sha256':frozen_prefix,
 'protected_chapters_1_to_3_identical':True,'conclusion_unchanged':True,'references_unchanged':True,
 'abstract_regenerated':False,'original_source_docx_sha256':digest(SOURCE.read_bytes()),
 'output_docx_sha256':digest(TARGET.read_bytes()),'changed_package_parts':['word/document.xml'],
 'original_domestic_analysis_files_modified':False,'new_governance_assertions':16,
 'new_consumer_data_or_efficacy_claims':False}
(OUT/'revision_scope.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'output':TARGET.name,'protected_scientific_chapters_unchanged':True,'governance_rows':len(rows)-1},ensure_ascii=False))
