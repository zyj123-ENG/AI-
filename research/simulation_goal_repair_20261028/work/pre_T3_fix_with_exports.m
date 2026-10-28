function run_goal_repair_simulation(mode)
% Transparent synthetic mechanism experiment. Base MATLAB only, R2023b.
% Every quantitative behavioral parameter is an uncalibrated assumption.
if nargin < 1, mode = 'full'; end
root = fileparts(fileparts(mfilename('fullpath')));
if strcmp(mode,'cue_contrasts')
 out=fullfile(root,'results'); z=load(fullfile(out,'paired_inputs.mat'));
 a=load(fullfile(out,'base_outcomes.mat'),'P','S','rules','metrics');
 head={'scenario','rule','control','type','n'}; rows={};
 for m=1:numel(a.metrics),head=[head strcat('delta_',a.metrics(m)) strcat('mcse_',a.metrics(m))];end
 for s=1:numel(a.S)
  if s==1,q=z.Q;else,q=subset_inputs(z.Q,z.nGrid,z.nType);end
  for b=1:numel(a.rules),for c=0:1
   i0=find(strcmp({a.P.id},sprintf('D1_R0_C%d',c)));i1=find(strcmp({a.P.id},sprintf('D1_R1_C%d',c)));
   delta=simulate(q,a.S(s),a.P(i1),a.rules{b})-simulate(q,a.S(s),a.P(i0),a.rules{b});
   for typ=0:3
    mask=true(size(q.type));if typ>0,mask=q.type==typ;end
    row={a.S(s).id,a.rules{b},c,typ,sum(mask)};
    for m=1:numel(a.metrics),[mu,se]=mc_stats(delta(mask,m));row=[row {mu,se}];end
    rows(end+1,:)=row;
   end
  end,end
 end
 writetable(cell2table(rows,'VariableNames',head),fullfile(out,'paired_link_contrasts.csv'));
 fprintf('Exported %d prespecified paired link contrasts from unchanged inputs\n',size(rows,1));return;
end
if strcmp(mode,'figures')
 out=fullfile(root,'results'); T=readtable(fullfile(out,'all_summary.csv'));
 TP=readtable(fullfile(out,'paired_differences.csv')); a=load(fullfile(out,'base_outcomes.mat'),'P');
 make_figures(T,TP,root,[],a.P); fprintf('Figures regenerated from unchanged CSV results\n'); return;
end
if strcmp(mode,'smoke'), nType=200; nGrid=100; out=fullfile(root,'results_smoke');
else, nType=40000; nGrid=10000; out=fullfile(root,'results'); end
if ~exist(out,'dir'), mkdir(out); end
diary(fullfile(out,'run.log')); clean=onCleanup(@()diary('off')); %#ok<NASGU>
fprintf('START %s\nMATLAB %s\nMODE %s\n',datestr(now,30),version,mode);
tStart=tic; rng(20261028,'twister'); Q=make_inputs(nType); rngAfter=rng;
save(fullfile(out,'paired_inputs.mat'),'Q','rngAfter','nType','nGrid');
price=[79 109 149 179 69]; compatible=[true true true true false];
catalog=table((1:5)',price',compatible',[0;0;0;1;0],[0;1;0;0;0],[0;0;1;0;0],...
 'VariableNames',{'product','synthetic_price','compatible','blue','compact','folding'});
writetable(catalog,fullfile(out,'synthetic_catalog.csv'));
P=make_policies(); writetable(struct2table(P),fullfile(out,'policies.csv'));
S=make_scenarios(strcmp(mode,'smoke')); writetable(struct2table(S),fullfile(out,'scenarios.csv'));
rules={'full_information','bounded_default','satisficing'};
metrics={'fact_understood','goal_reviewed','dependent_unreviewed_upgrade',...
 'budget_violation_after_request','compatible_purchase','noncompatible_purchase',...
 'valid_alternatives_visible','independent_upgrade_retained','quality_regret',...
 'processing_load','unnecessary_prompt','goal_request','update_failure',...
 'decline_action_cost','no_purchase'};
summaryHead={'scenario','rule','policy','type','n'};
pairHead=summaryHead;
for m=1:numel(metrics)
 summaryHead=[summaryHead metrics(m) strcat('mcse_',metrics(m))]; %#ok<AGROW>
 pairHead=[pairHead strcat('delta_',metrics(m)) strcat('mcse_',metrics(m))]; %#ok<AGROW>
end
summaryRows={}; pairRows={}; baseOut=cell(numel(rules),numel(P)); checks={};
idxRef=find(strcmp({P.id},'D1_R0_C0')); idxNew=find(strcmp({P.id},'D1_R1_C1'));
idxStrong=find(strcmp({P.id},'generic_selective'));
for s=1:numel(S)
 if s==1, q=Q; else, q=subset_inputs(Q,nGrid,nType); end
 fprintf('SCENARIO %d/%d %s n=%d\n',s,numel(S),S(s).id,numel(q.type));
 for b=1:numel(rules)
  outputs=cell(1,numel(P));
  for p=1:numel(P)
   Y=simulate(q,S(s),P(p),rules{b}); outputs{p}=Y;
   assert(all(Y(:,1:6)>=0 & Y(:,1:6)<=1,'all'),'Rate outside [0,1]');
   assert(all(Y(:,9)>=-1e-9 | isnan(Y(:,9))),'Negative regret');
   assert(all(Y(:,7)>=0 & Y(:,7)<=3),'Invalid alternative count');
   for typ=0:3
    mask=true(size(q.type)); if typ>0, mask=q.type==typ; end
    row={S(s).id,rules{b},P(p).id,typ,sum(mask)};
    for m=1:numel(metrics), [mu,se]=mc_stats(Y(mask,m)); row=[row {mu,se}]; end %#ok<AGROW>
    summaryRows(end+1,:)=row; %#ok<AGROW>
   end
   if s==1, baseOut{b,p}=single(Y); end
  end
  % This is an explicit strong-baseline check, not a claim of algorithm novelty.
  assert(isequaln(outputs{idxNew},outputs{idxStrong}),'Selective baseline differs');
  if strcmp(rules{b},'full_information')
   for p=1:numel(P)
    assert(all(outputs{p}(:,4)==0),'Full-information budget mismatch');
    assert(all(outputs{p}(:,6)==0),'Full-information incompatibility');
    assert(all(outputs{p}(:,9)==0),'Full-information regret');
    assert(isequaln(outputs{p}(:,1:9),outputs{1}(:,1:9)),'Full-information choice effect');
   end
  end
  for p=1:numel(P)
   delta=outputs{p}-outputs{idxRef};
   for typ=0:3
    mask=true(size(q.type)); if typ>0, mask=q.type==typ; end
    row={S(s).id,rules{b},P(p).id,typ,sum(mask)};
    for m=1:numel(metrics), [mu,se]=mc_stats(delta(mask,m)); row=[row {mu,se}]; end %#ok<AGROW>
    pairRows(end+1,:)=row; %#ok<AGROW>
   end
  end
 end
end
T=cell2table(summaryRows,'VariableNames',summaryHead);
TP=cell2table(pairRows,'VariableNames',pairHead);
writetable(T,fullfile(out,'all_summary.csv')); writetable(TP,fullfile(out,'paired_differences.csv'));
save(fullfile(out,'base_outcomes.mat'),'baseOut','metrics','P','S','rules','-v7');
% Deterministic rerun of one full base configuration against saved raw arrays.
rerun=single(simulate(Q,S(1),P(idxNew),'bounded_default'));
assert(isequaln(rerun,baseOut{2,idxNew}),'Deterministic rerun mismatch');
checks={'probabilities_and_rates_in_range','nonnegative_task_regret','valid_alternative_count',...
 'full_information_choice_invariance','full_information_budget_and_compatibility',...
 'strong_selective_reconfirmation_exact_equivalence','same_input_across_policies',...
 'deterministic_base_rerun_exact_match'};
validation=struct('checks',{checks},'passed',true,'seed',20261028,...
 'main_profiles_per_type',nType,'sensitivity_profiles_per_type',nGrid,...
 'scenarios',numel(S),'policies',numel(P),'rules',numel(rules),...
 'matlab_version',version,'elapsed_seconds',toc(tStart),'evidence_type','synthetic simulation');
write_json(fullfile(out,'validation.json'),validation);
if strcmp(mode,'full'), make_figures(T,TP,root,idxNew,P); end
fprintf('COMPLETE elapsed=%.3f seconds rows=%d\n',toc(tStart),height(T));
end

function Q=make_inputs(n)
N=3*n; Q.type=repelem((1:3)',n); Q.u=rand(N,14);
Q.blue=110+90*Q.u(:,1); Q.blue(Q.type==1)=80*Q.u(Q.type==1,1);
Q.compact=40*Q.u(:,2); Q.fold=30*Q.u(:,3);
Q.fold(Q.type==1)=90*Q.u(Q.type==1,3);
Q.falseBonus=110+30*Q.u(:,4); Q.falseBonus(Q.type==1)=110-Q.blue(Q.type==1)+30*Q.u(Q.type==1,4);
Q.trueU=250-[79 109 149 179 69]+Q.compact*[0 1 0 0 0]+Q.fold*[0 0 1 0 0]+Q.blue*[0 0 0 1 0];
Q.trueU(:,5)=-1069;
end

function q=subset_inputs(Q,n,nFull)
idx=[1:n,nFull+(1:n),2*nFull+(1:n)]; fields=fieldnames(Q);
for k=1:numel(fields), q.(fields{k})=Q.(fields{k})(idx,:); end
end

function P=make_policies()
P=struct('id',{},'D',{},'R',{},'C',{},'generic',{});
for d=0:1, for r=0:1, for c=0:1
 P(end+1)=struct('id',sprintf('D%d_R%d_C%d',d,r,c),'D',d,'R',r,'C',c,'generic',0); %#ok<AGROW>
end, end, end
P(end+1)=struct('id','generic_all','D',1,'R',0,'C',1,'generic',1);
P(end+1)=struct('id','generic_selective','D',1,'R',0,'C',1,'generic',2);
end

function S=make_scenarios(smoke)
b=struct('id','base','qFact',0.8,'attention',6,'cueGain',0.5,'cueCost',0.5,...
 'menuCost',0.5,'costPlain',3,'costControl',0.8,'successPlain',0.8,...
 'successControl',0.95,'commercialBias',1.2,'noticeBase',0.18,...
 'disclosureEffect',0.08,'sensitivity',0.9,'falsePositive',0,...
 'priorExpansion',1,'residual',0,'compatRecognition',0.98,'cueGrid',0,'loadGrid',0);
S=b;
spec={ 'zero_commercial_bias','commercialBias',0; 'correction_not_understood','qFact',0;...
 'no_extra_cue_effect','cueGain',0; 'spontaneous_goal_review','noticeBase',1;...
 'high_control_cost','costControl',8; 'equal_control_execution','successControl',0.8;...
 'degraded_control_execution','successControl',0.2; 'trigger_misclassification','falsePositive',0.5;...
 'no_prior_budget_expansion','priorExpansion',0; 'residual_old_reason','residual',0.4;...
 'disclosure_licensing','disclosureEffect',-0.2; 'perfect_factual_understanding','qFact',1};
for i=1:size(spec,1), a=b; a.id=spec{i,1}; a.(spec{i,2})=spec{i,3}; S(end+1)=a; end %#ok<AGROW>
a=b; a.id='information_overload'; a.attention=1.5; a.cueCost=3; a.menuCost=3; S(end+1)=a;
if smoke, return; end
for A=[2 6], for gain=[0 0.25 0.5 0.75], for cost=[0 0.5 1.5 3 6]
 a=b; a.id=sprintf('grid_A%g_G%g_L%g',A,gain,cost); a.attention=A;
 a.cueGain=gain; a.cueCost=cost; a.cueGrid=gain; a.loadGrid=cost; S(end+1)=a; %#ok<AGROW>
end, end, end
end

function Y=simulate(Q,s,p,rule)
N=numel(Q.type); typ=Q.type; price=[79 109 149 179 69]; trueNeed=typ==1 & s.priorExpansion==1;
recognized=(trueNeed & Q.u(:,5)<s.sensitivity) | (~trueNeed & Q.u(:,5)<s.falsePositive);
if p.generic==1, prompt=true(N,1); else, prompt=(p.R==1 | p.generic==2) & recognized; end
load=1+p.D*0.4+p.C*s.menuCost+prompt*s.cueCost;
att=min(1,s.attention./load); understood=Q.u(:,6)<s.qFact.*att;
notice=min(1,max(0,s.noticeBase+s.cueGain*prompt+0.05*p.C+...
 p.D*s.disclosureEffect*s.commercialBias/(1+s.commercialBias))).*att;
cost=(1-p.C)*s.costPlain+p.C*s.costControl;
expectedReviewValue=20+80*Q.u(:,13); % hypothetical anticipated value, not oracle regret
probAct=1./(1+exp(-(expectedReviewValue-(5+10*Q.u(:,14))*cost)/20));
review=understood & Q.u(:,7)<notice & Q.u(:,8)<probAct;
resid=(~understood)+understood*s.residual;
perU=Q.trueU+resid.*Q.falseBonus*[0 0 0 1 0];
knownBad=Q.u(:,9)<s.compatRecognition;
perU(~knownBad,5)=181;
perU(knownBad,5)=-Inf;
startB=200*ones(N,1); startB(typ==1 & s.priorExpansion==0)=150;
if ~s.priorExpansion, perU(:,4)=Q.trueU(:,4); end
[~,bestPer]=max(perU,[],2); intendedB=150+50*(price(bestPer)'>150);
declaredB=startB; declaredB(review)=intendedB(review);
request=review & declaredB~=startB;
success=Q.u(:,10)<((1-p.C)*s.successPlain+p.C*s.successControl);
workB=startB; workB(request & success)=declaredB(request & success);
effective=Q.trueU; effective(:,5)=-Inf;
targetB=200*ones(N,1); targetB(typ==1)=150;
effective(price>targetB)=-Inf; [bestTrue,idealChoice]=max(effective,[],2);
if strcmp(rule,'full_information')
 understood=true(N,1); review=trueNeed; request=trueNeed; workB=targetB; declaredB=targetB;
 chosen=idealChoice; visibleCount=3*ones(N,1); k=5*ones(N,1);
else
 estimateBlue=20+120*(typ~=1);
 score=-price/100+[0 0.15 0.2 0 0]+estimateBlue/100*[0 0 0 1 0]+...
  s.commercialBias*[0.1 0.2 0.3 1 0.1];
 score(price>workB)=-Inf; score(knownBad,5)=-Inf;
 [sorted,order]=sort(score,2,'descend');
 remain=max(0,s.attention-load-review*cost);
 k=min(5,max(1,1+floor(remain)));
 visible=false(N,5); rank=zeros(N,5); rr=(1:N)';
 for j=1:5
  ix=sub2ind([N 5],rr,order(:,j)); visible(ix)=k>=j & isfinite(sorted(:,j)); rank(ix)=j;
 end
 veto=review & Q.u(:,11)<min(1,s.attention./(load+cost+1));
 visible(veto,:)=visible(veto,:) & price<=declaredB(veto);
 visibleCount=sum(visible(:,1:3),2);
 if strcmp(rule,'bounded_default')
  decision=perU+12*(6-rank)+40*(~review)*[0 0 0 1 0]; decision(~visible)=-Inf;
  [v,chosen]=max(decision,[],2); chosen(~isfinite(v))=0;
 else
  chosen=zeros(N,1); threshold=60+60*Q.u(:,12);
  for j=1:5
   ix=sub2ind([N 5],rr,order(:,j)); take=chosen==0 & visible(ix) & perU(ix)>=threshold;
   chosen(take)=order(take,j);
  end
 end
end
bought=chosen>0; selectedPrice=zeros(N,1); selectedPrice(bought)=price(chosen(bought));
regret=nan(N,1); rr=find(bought); ix=sub2ind([N 5],rr,chosen(bought));
regret(bought)=bestTrue(bought)-Q.trueU(ix);
retained=nan(N,1); retained(typ~=1)=chosen(typ~=1)==4;
Y=[understood review (typ==1 & ~review & selectedPrice>150 & s.priorExpansion==1),...
 request & selectedPrice>declaredB, bought & chosen~=5,chosen==5,visibleCount,retained,...
 regret,load+review*cost+0.5*k,prompt & ~trueNeed,request,...
 request & workB~=declaredB, repmat(cost+p.C*s.menuCost,N,1),~bought];
end

function [mu,se]=mc_stats(x)
x=x(isfinite(x)); if isempty(x), mu=NaN; se=NaN; else, mu=mean(x); se=std(x)/sqrt(numel(x)); end
end

function write_json(path,obj)
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0); fprintf(fid,'%s\n',jsonencode(obj,'PrettyPrint',true)); fclose(fid);
end

function make_figures(T,TP,root,~,P)
dirFig=fullfile(root,'figures'); if ~exist(dirFig,'dir'),mkdir(dirFig);end
core={'D1_R0_C0','D1_R1_C0','D1_R0_C1','D1_R1_C1'};
labels={'Fact only','Link cue','Choice tools','Link + tools'};
fig=figure('Visible','off','Position',[80 80 1150 700]); tiledlayout(2,2);
ms={'goal_reviewed','dependent_unreviewed_upgrade','budget_violation_after_request','noncompatible_purchase'};
ttl={'Goal review','Unreviewed upgrade (not a violation label)','Over budget AFTER explicit revision','Incompatible purchase'};
for j=1:4
 nexttile; vals=zeros(1,4); se=vals;
 for k=1:4
  row=T(strcmp(T.scenario,'base') & strcmp(T.rule,'bounded_default') & strcmp(T.policy,core{k}) & T.type==1,:);
  vals(k)=100*row.(ms{j}); se(k)=100*row.(['mcse_' ms{j}]);
 end
 bar(vals,'FaceColor',[0.2 0.45 0.65]); hold on; errorbar(1:4,vals,1.96*se,'k.');
 xticks(1:4);xticklabels(labels);xtickangle(15); ylabel('Percent');title(ttl{j});grid on;
 if all(vals==0),ylim([0 1]);text(2.5,0.5,'All four zero under this rule','HorizontalAlignment','center');end
end
sgtitle('Synthetic dependent profiles; base assumptions; 40,000 paired cases per type');
save_figure(fig,dirFig,'fig1_core_mechanisms');

fig=figure('Visible','off','Position',[80 80 1100 750]); tiledlayout(2,2);
gain=[0 .25 .5 .75]; costs=[0 .5 1.5 3 6]; zAll=[];
for b=1:2, for a=1:2
 rule={'bounded_default','satisficing'}; A=[2 6]; Z=zeros(4,5);
 for g=1:4,for l=1:5
  id=sprintf('grid_A%g_G%g_L%g',A(a),gain(g),costs(l));
  nr=T(strcmp(T.scenario,id)&strcmp(T.rule,rule{b})&strcmp(T.policy,'D1_R1_C1')&T.type==1,:);
  br=T(strcmp(T.scenario,id)&strcmp(T.rule,rule{b})&strcmp(T.policy,'D1_R0_C1')&T.type==1,:);
  Z(g,l)=100*(br.dependent_unreviewed_upgrade-nr.dependent_unreviewed_upgrade);
 end,end
 zAll=[zAll;Z(:)]; %#ok<AGROW>
 nexttile;imagesc(1:5,1:4,Z);axis xy;colorbar;
 xticks(1:5);xticklabels(string(costs));yticks(1:4);yticklabels(string(gain));
 xlabel('Link reading cost (discrete grid)');ylabel('Cue effect assumption');
 title(sprintf('%s; attention=%g',rule{b},A(a)),'Interpreter','none');
end,end
lims=max(abs(zAll));if lims==0,lims=1;end
axesList=findall(fig,'Type','axes');for k=1:numel(axesList),clim(axesList(k),[-lims lims]);end
colormap(fig,blue_white_red(129));
sgtitle('Reduction in unreviewed upgrades (percentage points); negative = reversal; N=10,000/type');
save_figure(fig,dirFig,'fig2_effect_cost_boundaries');

fig=figure('Visible','off','Position',[80 80 1100 570]);tiledlayout(1,2);
shown={'D1_R0_C0','D1_R1_C0','D1_R0_C1','D1_R1_C1','generic_all'};
shownLabels={'Fact only','Link cue','Choice tools','Link+tools / targeted generic','Ask everyone'};
colors=lines(5);markers={'o','s','^','d','v'};hh=gobjects(5,1);
for s=1:2
 nexttile;hold on; scen={'base','information_overload'};
 for k=1:numel(shown)
  q=T(strcmp(T.scenario,scen{s})&strcmp(T.rule,'bounded_default')&strcmp(T.policy,shown{k})&T.type==1,:);
  hh(k)=scatter(q.processing_load,q.quality_regret,90,colors(k,:),markers{k},'filled');
 end
 xlabel('Synthetic processing/operation units');ylabel('Synthetic task-utility regret');title(scen{s},'Interpreter','none');grid on;
end
lg=legend(hh,shownLabels,'Orientation','horizontal','NumColumns',3);lg.Layout.Tile='south';
sgtitle('Cost-quality trade-offs; values are not empirical autonomy scores');
save_figure(fig,dirFig,'fig3_cost_quality');

fig=figure('Visible','off','Position',[80 80 1100 480]);tiledlayout(1,2);
nexttile; c={'D0_R0_C0','D1_R0_C0','D0_R0_C1','D1_R0_C1'};vals=zeros(1,4);
for k=1:4,q=T(strcmp(T.scenario,'base')&strcmp(T.rule,'bounded_default')&strcmp(T.policy,c{k})&T.type==1,:);vals(k)=100*q.dependent_unreviewed_upgrade;end
bar(vals);xticklabels({'D0 C0','D1 C0','D0 C1','D1 C1'});ylabel('Percent');title('Original D x C design, R=0');grid on;
nexttile; c={'D1_R1_C1','generic_all','generic_selective'};vals=zeros(1,3);
for k=1:3,q=T(strcmp(T.scenario,'base')&strcmp(T.rule,'bounded_default')&strcmp(T.policy,c{k})&T.type==3,:);vals(k)=100*q.unnecessary_prompt;end
bar(vals);xticklabels({'Targeted link','Ask everyone','Strong targeted baseline'});xtickangle(15);ylabel('Percent');title('Extra prompting after informed reaffirmation');grid on;
sgtitle('Different comparisons: commercial disclosure vs generic reconfirmation');
save_figure(fig,dirFig,'fig4_disclosure_and_strong_baseline');
end

function cm=blue_white_red(n)
x=linspace(-1,1,n)';cm=[min(1,1+x),1-abs(x),min(1,1-x)];
end

function save_figure(fig,folder,name)
exportgraphics(fig,fullfile(folder,[name '.png']),'Resolution',180);
exportgraphics(fig,fullfile(folder,[name '.pdf']),'ContentType','vector');close(fig);
end
