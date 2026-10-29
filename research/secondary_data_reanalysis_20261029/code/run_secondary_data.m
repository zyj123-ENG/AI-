function run_secondary_data(dataRoot,outDir)
% Reanalyse author-observed consumer data; resample existing subject clusters.
% Base MATLAB only. dataRoot must point to the original replication folder.
if nargin<2,error('Supply original replication folder and an output folder.');end
if ~isfolder(outDir),mkdir(outDir);end
inDir=fullfile(dataRoot,'data_for_cbc_est','toothpaste_beliefs');
demFile=fullfile(inDir,'cleaned_demographics.csv');cbcFile=fullfile(inDir,'cleaned_cbc.csv');
opt=detectImportOptions(demFile,'TextType','string');
opt.SelectedVariableNames={'user','adtreatment','debunktreatment','belieffl','postbelieffl'};
d=readtable(demFile,opt);
opt=detectImportOptions(cbcFile,'TextType','string');
opt.SelectedVariableNames={'user','question','option','price_numeric','has_ingredient','selected'};
c=readtable(cbcFile,opt);
assert(height(d)==5050 && height(c)==202000,'Unexpected source version.');
assert(numel(unique(d.user))==height(d),'Duplicate participant key.');
[ok,u]=ismember(c.user,d.user);assert(all(ok),'Unmatched participant.');
assert(size(unique([c.user c.question c.option],'rows'),1)==height(c),'Duplicate option key.');
[~,~,task]=unique([c.user c.question],'rows');
assert(all(accumarray(task,1)==4) && all(accumarray(task,c.selected)==1),'Invalid task.');
assert(all(accumarray(u,1)==40) && all(accumarray(u,c.selected)==10),'Incomplete cluster.');
assert(all(ismember(c.selected,[0 1])) && all(ismember(c.has_ingredient,[0 1])),'Invalid binary field.');
assert(all(c.price_numeric(c.option==4)==0),'Invalid no-purchase price.');
assert(all(ismember(c.price_numeric(c.option~=4),[.99 1.99 2.99])),'Unexpected price.');
assert(all(ismember(d.belieffl,1:5)) && all(ismember(d.postbelieffl,1:5)),'Missing or invalid belief.');
assert(all(ismember(d.adtreatment,["regular","treat"])) && all(ismember(d.debunktreatment,["control","regulator"])),'Unexpected arm.');
n=height(d);sel=c.selected==1;
ing=accumarray(u,double(sel & c.has_ingredient==1),[n 1])/10;
none=accumarray(u,double(sel & c.option==4),[n 1])/10;
price=accumarray(u,c.price_numeric.*double(sel),[n 1])/10;
purchase=1-none;
pre=double(d.belieffl>=4);post=double(d.postbelieffl>=4);
lower=double(d.postbelieffl<d.belieffl);same=double(d.postbelieffl==d.belieffl);higher=1-lower-same;
X=[ing none price pre post lower same higher purchase];
names=["ingredient_choice_share","no_purchase_share","selected_price_unconditional_usd","pre_harmful_bin_share","post_harmful_bin_share","belief_lower_share","belief_same_share","belief_higher_share","purchase_share","selected_price_purchase_conditional_usd"];
arms=["regular_control","regular_regulator","treat_control","treat_regulator"];
group=zeros(n,1);
group(d.adtreatment=="regular" & d.debunktreatment=="control")=1;
group(d.adtreatment=="regular" & d.debunktreatment=="regulator")=2;
group(d.adtreatment=="treat" & d.debunktreatment=="control")=3;
group(d.adtreatment=="treat" & d.debunktreatment=="regulator")=4;
assert(all(group>0),'Unclassified arm.');
B=5000;seed=20261029;rng(seed,'twister');
mu=zeros(4,10);boot=zeros(B,10,4);counts=zeros(4,1);
for a=1:4
    x=X(group==a,:);na=size(x,1);counts(a)=na;
    mu(a,1:9)=mean(x,1);mu(a,10)=sum(x(:,3))/sum(x(:,9));
    for start=1:100:B
        nb=min(100,B-start+1);idx=randi(na,na,nb);
        vals=reshape(x(idx(:),:),[na nb 9]);m=reshape(mean(vals,1),[nb 9]);
        boot(start:start+nb-1,1:9,a)=m;
        boot(start:start+nb-1,10,a)=m(:,3)./m(:,9);
    end
end
ga=strings(40,1);gm=ga;gn=zeros(40,1);point=gn;lo=gn;hi=gn;r=0;
for a=1:4
    for k=1:10
        r=r+1;ga(r)=arms(a);gm(r)=names(k);gn(r)=counts(a);point(r)=mu(a,k);
        q=percentiles(boot(:,k,a),[.025 .975]);lo(r)=q(1);hi(r)=q(2);
    end
end
writetable(table(ga,gm,gn,point,lo,hi,'VariableNames',{'arm','metric','participants','estimate','ci_low','ci_high'}),fullfile(outDir,'arm_estimates.csv'));
weights=[0 0 -1 1;-1 1 0 0;-1 0 1 0;0 -1 0 1;1 -1 -1 1];
contrasts=["debunk_with_misinfo","debunk_with_regular","misinfo_without_debunk","misinfo_with_debunk","interaction_debunk_differences"];
cn=strings(50,1);cm=cn;cp=zeros(50,1);cl=cp;ch=cp;r=0;
for j=1:5
    for k=1:10
        r=r+1;cn(r)=contrasts(j);cm(r)=names(k);cp(r)=weights(j,:)*mu(:,k);
        b=reshape(boot(:,k,:),[B 4])*weights(j,:)';q=percentiles(b,[.025 .975]);cl(r)=q(1);ch(r)=q(2);
    end
end
writetable(table(cn,cm,cp,cl,ch,'VariableNames',{'contrast','metric','estimate','ci_low','ci_high'}),fullfile(outDir,'contrasts.csv'));
aa=strings(100,1);pb=zeros(100,1);qb=pb;nn=pb;r=0;
for a=1:4
    for p=1:5
        for q=1:5
            r=r+1;aa(r)=arms(a);pb(r)=p;qb(r)=q;nn(r)=sum(group==a & d.belieffl==p & d.postbelieffl==q);
        end
    end
end
writetable(table(aa,pb,qb,nn,'VariableNames',{'arm','pre_bin','post_bin','participants'}),fullfile(outDir,'belief_transitions.csv'));
% Joint distributions are descriptive; they do not identify mediation or autonomy.
ja=strings(36,1);jd=ja;jc=ja;jn=zeros(36,1);r=0;
direction=["lower","same","higher"];choice=["never_ingredient","mixed","always_ingredient"];
for a=1:4
    for p=1:3
        di=[lower same higher];
        for q=1:3
            ci=[ing==0 ing>0 & ing<1 ing==1];r=r+1;
            ja(r)=arms(a);jd(r)=direction(p);jc(r)=choice(q);jn(r)=sum(group==a & di(:,p)==1 & ci(:,q));
        end
    end
end
writetable(table(ja,jd,jc,jn,'VariableNames',{'arm','belief_direction','observed_choice_pattern','participants'}),fullfile(outDir,'joint_belief_choice.csv'));
% Record randomized menu balance separately from consumer choices.
armOption=group(u);isproduct=c.option~=4;ma=strings(4,1);mi=zeros(4,1);mp=mi;
for a=1:4
    ma(a)=arms(a);mask=armOption==a & isproduct;mi(a)=mean(c.has_ingredient(mask));mp(a)=mean(c.price_numeric(mask));
end
writetable(table(ma,mi,mp,'VariableNames',{'arm','offered_ingredient_share','offered_price_mean_usd'}),fullfile(outDir,'offered_menu_balance.csv'));
meta=struct('date','2026-10-29','engine',version,'seed',seed,'bootstrap_repetitions',B,'participants',n,'choice_tasks',numel(unique(task)),'option_rows',height(c),'actual_arm_sizes',counts','resampling_unit','participant within original arm; all ten observed choices retained','new_behavior_generated',false,'missing_imputed',false,'primary_metric','ingredient_choice_share','primary_contrast','debunk_with_misinfo','conditional_price_denominator','purchased choice tasks','ci','pointwise percentile subject-cluster bootstrap; not simultaneous intervals');
fid=fopen(fullfile(outDir,'run_metadata.json'),'w','n','UTF-8');fprintf(fid,'%s',jsonencode(meta,PrettyPrint=true));fclose(fid);
save(fullfile(outDir,'bootstrap_aggregates.mat'),'boot','mu','counts','names','arms','weights','contrasts','seed','B');
makefigs(outDir,mu,boot,arms);
disp(jsonencode(meta,PrettyPrint=true));
end

function q=percentiles(x,p)
% Linear interpolation of empirical order statistics; no Statistics Toolbox.
x=sort(x(:));h=1+(numel(x)-1)*p;lo=floor(h);hi=ceil(h);q=x(lo)'.*(hi-h)+x(hi)'.*(h-lo);same=lo==hi;q(same)=x(lo(same));
end

function makefigs(outDir,mu,boot,arms)
set(groot,'defaultAxesFontName','Microsoft YaHei');set(groot,'defaultTextFontName','Microsoft YaHei');
labels={'普通广告/控制','普通广告/纠错','误导广告/控制','误导广告/纠错'};
f=figure('Visible','off','Color','w','Position',[50 50 1500 680]);tiledlayout(1,2,'TileSpacing','compact','Padding','compact');
for panel=1:2
    k=[1 5];k=k(panel);nexttile;v=100*mu(:,k);bar(v,.62,'FaceColor',[.23 .42 .57]);hold on;
    bounds=zeros(4,2);for a=1:4,bounds(a,:)=100*percentiles(boot(:,k,a),[.025 .975]);end
    errorbar(1:4,v,v-bounds(:,1),bounds(:,2)-v,'.k','LineWidth',1.4);
    set(gca,'XTick',1:4,'XTickLabel',labels,'XTickLabelRotation',16,'FontSize',14);ylabel('百分比（%）');
    if panel==1,title('每人十题含氟选择比例（主终点）');else,title('报告有害概率在60%—100%档的参与者');end
    ylim([0 max([v;bounds(:,2)])*1.18]);grid on;
    for a=1:4,text(a,bounds(a,2)+.4,sprintf('%.2f',v(a)),'HorizontalAlignment','center','FontSize',13);end
end
sgtitle('原始四臂真实观测：选择与主观信念分别测量','FontSize',18,'FontWeight','bold');
exportgraphics(f,fullfile(outDir,'图2_真实观测与信念.png'),'Resolution',180);close(f);
f=figure('Visible','off','Color','w','Position',[50 50 1500 680]);tiledlayout(1,2,'TileSpacing','compact','Padding','compact');
for panel=1:2
    k=[2 3];k=k(panel);nexttile;scale=1;if k==2,scale=100;end
    v=scale*mu(:,k);bar(v,.62,'FaceColor',[.45 .58 .44]);hold on;
    bounds=zeros(4,2);for a=1:4,bounds(a,:)=scale*percentiles(boot(:,k,a),[.025 .975]);end
    errorbar(1:4,v,v-bounds(:,1),bounds(:,2)-v,'.k','LineWidth',1.4);
    set(gca,'XTick',1:4,'XTickLabel',labels,'XTickLabelRotation',16,'FontSize',14);
    if k==2,ylabel('不购买选择比例（%）');title('不购买是原选择表的一项');else,ylabel('每题所选标价均值（美元）');title('含不购买记0，不等于实际支出或预算');end
    ylim([0 max([v;bounds(:,2)])*1.2]);grid on;
    for a=1:4,text(a,bounds(a,2)+max(v)*.025,sprintf('%.3f',v(a)),'HorizontalAlignment','center','FontSize',13);end
end
sgtitle('次要探索指标：不购买与所选标价','FontSize',18,'FontWeight','bold');
exportgraphics(f,fullfile(outDir,'图3_真实选择价格与不购买.png'),'Resolution',180);close(f);
end
