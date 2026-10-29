import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
const runtimeModules=process.env.RUNTIME_NODE_MODULES;
if(!runtimeModules)throw new Error('Set RUNTIME_NODE_MODULES to the bundled node_modules directory.');
const runtimeRequire=createRequire(path.join(path.resolve(runtimeModules),'..','artifact-runtime-entry.cjs'));
const {Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(runtimeRequire.resolve('@oai/artifact-tool')).href);
const workspace=process.env.TASK_WORKSPACE;
const repo=path.resolve(process.argv[2]);
const skill=process.env.PRESENTATIONS_SKILL_DIR;
const python=process.env.RUNTIME_PYTHON;
if(!workspace||!skill||!python)throw new Error('Set TASK_WORKSPACE, PRESENTATIONS_SKILL_DIR and RUNTIME_PYTHON.');
const build=path.join(workspace,'build');
const out=path.join(repo,'submission');
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const p=Presentation.create({slideSize:{width:1280,height:720}});
const FONT='Microsoft YaHei';const C={ink:'#172B3A',teal:'#007C80',muted:'#536472',pale:'#F2F5F7',line:'#D9E1E5',amber:'#A35128'};
const owners=[];
function text(s,t,x,y,w,h,size=28,color=C.ink,bold=false){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=t;q.text.style={typeface:FONT,fontSize:size,color,bold,verticalAlignment:'top',wrap:'square',autoFit:'none',insets:0};return q;
}
function slide(title,notes){const s=p.slides.add();s.background.fill='#FFFFFF';text(s,title,64,44,1150,90,37,C.ink,true);text(s,String(p.slides.items.length).padStart(2,'0'),1170,670,50,26,17,C.muted);s.speakerNotes.text=notes;return s;}
function para(s,head,body,y){text(s,head,64,y,1152,44,28,C.teal,true);text(s,body,64,y+52,1152,96,27);}
function table(s,values,widths,y=170,height=390,size=23){
 owners.push(p.slides.items.length);
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height,columnWidths:widths,values});
 t.borders.assign({fill:C.line,width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const q=t.getCell(r,c);q.fill=r===0?C.ink:(r%2===0?C.pale:'#FFFFFF');q.text.style={typeface:FONT,fontSize:size,color:r===0?'#FFFFFF':C.ink,bold:r===0,verticalAlignment:'middle',wrap:'square',insets:{left:12,right:12,top:8,bottom:8}};
 }return t;
}
async function image(s,name){const b=await fs.readFile(path.join(repo,'research/domestic_data_reanalysis_20261029/results',name));s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',alt:name,fit:'contain',position:{left:64,top:155,width:850,height:440}});}

let s=slide('AI导购理由撤回后的预算重审','研究报告配套答辩。正文摘要及前三章沿用GitHub基准。本次增加治理执行规则和提交材料，不改动原六臂数据、统计结果、规范论证或创新定位。');
text(s,'重要理由失去支持后\n如何完成相称修复并尊重停止',64,207,1152,170,47,C.ink,true);
text(s,'成年消费者的中文建议型购物助手',64,435,1152,55,29,C.teal);
text(s,'规范判准  国内二手数据复分析  治理验收',64,515,1152,50,27,C.muted);

s=slide('事实更正可能关联先前的预算决定','来源：报告第一章及第三章。以下150元、200元及理由历史为构造案例。真实手机材料未观察到无据说法导致消费者提价。');
para(s,'原有范围','消费者给出150元预算，助手提供商品与功能比较',175);
para(s,'公开使用','消费者明确表示主要因为某项优势，愿提高到200元',330);
para(s,'依据变化','该优势后来失去支持，当前预算仍需由本人决定是否修改',485);

s=slide('材料身份决定它可以支持什么判断','来源：报告表1、第二章及附录。原实验夹克购物任务，模拟的是记忆陈述，516份响应由原研究参与者提供；403人为其子样本。');
table(s,[['材料','用途','证据范围'],['规范论证与构造案例','责任条件与边界','不估计消费者心理效应'],['手机探索与限定系统预试','具体断言及条件响应','后续转贴和原始界面分别登记'],['国内516人原六臂记录','即时信任与统计不确定性','不包含预算重审处理']], [340,390,422],172,365,24);
text(s,'原数据、规范判断和本轮工程验收分别记录',64,575,1150,55,28,C.teal,true);

s=slide('既有研究使增量落在责任条件的细化','来源：报告第一章。Fong等2024，DOI10.1177/00222437221147088；Prunkl2024，DOI10.1007/s11023-024-09665-1；Lara与del Valle2026，DOI10.1007/s11948-026-00619-7。李术平仅摘要及公开信息。沿用原有创新定位。');
para(s,'消费品纠错已有经验研究','事实信念、固有偏好及支付意愿的修复，已有邻近研究',175);
para(s,'自主保护涵盖理由与实际行动','反思、委托和避免过度负担需要一起考察',330);
para(s,'本研究的既有定位','细化预算关联说明的触发、功能完成、停止和审计条件',485);

s=slide('角色责任须满足公开联系和相称条件','来源：报告第二、三章。此页为既有规范主张，不由二手信任差值推出。');
text(s,'消费者保有支出决定地位',64,170,1152,56,32,C.teal,true);
text(s,'理由重要，存在公开可核的预算联系\n决定仍可调整，当前说明还有具体缺口\n助手有知识和可控制的修复机会\n补充沟通的负担相称',64,260,1152,255,31);
text(s,'普通更正已经完成功能时，无须另设确认关卡',64,565,1152,65,29,C.teal,true);

s=slide('限定预试保留了系统的正面响应','来源：报告表2及research/evidence/元宝桌面版预试_完整会话与元数据.json。三条会话、每条三轮；给定历史、固定顺序、每条件一次。不能估计总体成功率。');
table(s,[['给定历史','首轮可见响应','判读'],['主要依赖撤回理由','推荐79元甲，保留乙入口','未见后台预算改写证据'],['有充分独立颜色理由','支持179元蓝色乙','允许合理维持升级'],['更正后已知情重申','支持乙，未再要求确认','符合停止重复重审边界']], [355,410,387],172,360,23);
text(s,'79元同时满足150元与200元上限，推荐便宜款不等于擅改预算',64,575,1152,65,25,C.muted);

s=slide('国内记录保留原六臂与原响应','来源：Huang、Huang与Guo2026，Frontiers in Psychology17:1934857，DOI10.3389/fpsyg.2026.1934857；作者固定数据提交3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53。原MATLAB图未改动。');
await image(s,'图2_国内六臂信任评价.png');
text(s,'516名成年参与者\n原生3×2实验臂\n三题即时信任均值',940,200,280,160,27);
text(s,'按原臂各5,000轮\n参与者bootstrap\n403人现场敏感性',940,410,280,160,27,C.teal);
text(s,'夹克记忆提示与具体面板场景',64,615,1152,36,22,C.muted);

s=slide('平均信任差与相对差距分别报告','来源：报告第三章原结果及research/domestic_data_reanalysis_20261029/results/contrasts.csv。保留原统计口径；没有本轮新增消费者结果。');
await image(s,'图3_面板差值与交互边界.png');
text(s,'主δ = −0.160\n95%区间\n[−0.542, 0.220]',935,200,285,170,27);
text(s,'平均差A = 0.186\n95%区间\n[0.032, 0.341]',935,415,285,160,27,C.teal);
text(s,'两者对应不同问题，沿用原报告的解释边界',64,615,1152,36,22,C.muted);

s=slide('触发提醒需要可回溯的证据','来源：本轮报告表4，拟议治理实现。关系匹配需要会话依据与复核，不据点击或提价推断真实动机。');
table(s,[['要核对的条件','可核查记录'],['重要理由失去支持','理由ID、依据来源与实质版本变化'],['消费者公开用于预算修订','用户原话及会话轮次'],['决定可调整且关联尚有缺口','当前任务与已有更正的完成状态'],['沟通负担相称','提示内容、次数及新增操作']], [440,712],172,390,25);
text(s,'关联不明时保持当前预算，接受用户纠正记录',64,590,1152,50,27,C.teal,true);

s=slide('停止条件进入同一套执行规则','来源：本轮报告表4及governance/rules.json。一次上限是参考实现的配置，不是经验证的最优伦理次数。');
table(s,[['情况','执行约定'],['普通更正已充分完成','不追加预算邀请'],['同一实质依据版本仍需提示','默认至多一次主动预算邀请'],['用户知情重申或明确结束','停止同一提示与商业推动'],['用户主动追问或出现重要新事实','分别审查必要响应，改措辞不重置计数']], [440,712],172,390,24);
text(s,'必要安全通知另审必要性和渠道，并与营销分开',64,590,1152,50,26,C.muted);

s=slide('预算执行与知情重申分别留痕','来源：本轮治理实现。记录告知版本和后续表达，不声称证明真实心理理解，也不强制理解测验。');
para(s,'预算状态','保存变更前后数值、有效授权表达与轮次，条件预览不改生效预算',175);
para(s,'知情重申','关联先前更正版本和用户后续维持表达，保留纠正入口',330);
para(s,'实际执行','核对筛选实参、候选总支付和结束事件，不能只查尊重预算的措辞',485);

s=slide('负担与目标改写采用可观察指标','来源：本轮报告第四章。均为待部署采集与审计指标，原实验没有这些负担变量。');
table(s,[['指标','记录方式','解释边界'],['重复干预','同一依据版本的主动邀请次数','不以换措辞重置'],['信息与操作负担','提示字符、额外步骤、任务时间','无经验证的综合阈值'],['主观负担','可选、自愿的后续评价','不以完成评价为继续条件'],['擅改目标或越限筛选','授权事件与预算状态、筛选实参比对','日志需真实且完整']], [300,460,392],172,390,23);

s=slide('既有结果与治理措施一一对应','来源：本轮报告表5，沿用原统计与第三章规范命题。对应表是工程验收分工，不增加机制有效性结论。');
table(s,[['既有依据','治理安排','验收对象'],['平均评价与特定差距不同','按具体修复问题分别验收','告知、状态、筛选与停止'],['区间及样本边界保持','保留失败和未决记录','工程检查与统计输出分栏'],['关联、完成及停止判准','有缺口才提示，已完成即停止','原话、事实版本及结束事件']], [380,400,372],172,365,24);
text(s,'伦理判准与工程验收共同使用，各自承担原有任务',64,575,1152,60,27,C.teal,true);

s=slide('参考实现已完成16项工程断言','来源：governance/budget_guard.py、check_protocol.py、protocol_results.json。输入全部为构造协议记录，不是模型或消费者实验。');
para(s,'运行入口','python governance/check_protocol.py',175);
para(s,'检查内容','授权变更、重复提示、用户纠正、重申停止、结束与筛选越限',330);
para(s,'实现边界','需要接入真实会话和价格来源，日志真实性及现场部署尚待完成',485);

s=slide('保护措施也需要控制负担和隐私','来源：原报告第四章及本轮执行约定。法律适用限定沿用正文，新增默认配置属于产品设计建议。');
para(s,'避免过度锁定','维持预算、改预算、降低用途和暂不购买均有可用路径',175);
para(s,'避免持续画像','优先使用本任务已有公开表达，记录最少关联与来源版本',330);
para(s,'避免形式性合规','不以弹窗、确认次数或日志自报替代实际可用的控制',485);

s=slide('完整材料已经整合，外部检测据实补入','来源：submission/README.md与material_status.json。知网报告与百度网盘分享按用户要求不在本轮办理；正式上传未执行，不能登记为已经提交。');
para(s,'本次完成','完整报告、答辩PPT、匿名复现包、执行规则和保护范围核对',175);
para(s,'保持不变','摘要、前三章、结论、参考文献及原六臂数据与计算',330);
para(s,'提交前补入','真实知网报告、正式分享入口与提交回执，均按实际状态登记',485);

await fs.mkdir(path.join(build,'slides'),{recursive:true});
const candidate=path.join(build,'defense-candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const scrub=spawnSync(python,['-X','utf8',path.join(repo,'governance/scrub_pptx_core.py'),candidate],{encoding:'utf8',windowsHide:true});if(scrub.status!==0)throw new Error(scrub.stderr);
const finalPath=path.join(out,'AI导购理由撤回后的预算重审_答辩稿.pptx');
const result=await finalizePresentation({workspaceDir:workspace,candidatePath:candidate.replace('.pptx','-metadata.pptx'),finalPath,pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...owners.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:owners,fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,'defense-validation.json')});
await fs.writeFile(path.join(build,'defense-finalizer-result.json'),JSON.stringify(result,null,2));
const final=await PresentationFile.importPptx(await FileBlob.load(finalPath));
for(let i=0;i<final.slides.items.length;i++){const b=await final.export({slide:final.slides.items[i],format:'png',scale:1.2});await fs.writeFile(path.join(build,'slides',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}
await fs.writeFile(path.join(out,'答辩讲稿与来源.md'),p.slides.items.map((s,i)=>`## 第${i+1}页\n\n${s.speakerNotes.text}\n`).join('\n'));
console.log(JSON.stringify({slides:final.slides.items.length,renderedFinal:true,finalPath}));
