function export_paper_figures()
root=fileparts(mfilename('fullpath'));
sim=fullfile(fileparts(root),'simulation_goal_repair_20261028');
out=fullfile(root,'figures');if ~exist(out,'dir'),mkdir(out);end
T=readtable(fullfile(sim,'results','all_summary.csv'));
G=readtable(fullfile(sim,'results','all_grid_effects.csv'));
set(groot,'defaultAxesFontName','Microsoft YaHei','defaultTextFontName','Microsoft YaHei');
set(groot,'defaultAxesFontSize',10,'defaultTextInterpreter','none');
pol={'D1_R0_C0','D1_R1_C0','D1_R0_C1','D1_R1_C1'};
lab={'仅事实更正','关联说明','重选操作','说明与操作'};
f=figure('Visible','off','Units','inches','Position',[1 1 7 3.2]);tiledlayout(1,2,'TileSpacing','compact');
metrics={'goal_reviewed','dependent_unreviewed_upgrade'};ttl={'完成目标重评','未重评仍选择升级款'};
for m=1:2
 nexttile;mu=zeros(1,4);se=mu;
 for k=1:4
  r=T(strcmp(T.scenario,'base')&strcmp(T.rule,'bounded_default')&T.type==1&strcmp(T.policy,pol{k}),:);
  mu(k)=100*r.(metrics{m});se(k)=100*r.(['mcse_' metrics{m}]);
 end
 bar(1:4,mu,'FaceColor',[.28 .42 .53]);hold on;errorbar(1:4,mu,1.96*se,'k.','LineWidth',1);
 xticks(1:4);xticklabels(lab);xtickangle(20);ylabel('比例 %');title(ttl{m});grid on;box off;
end
exportgraphics(f,fullfile(out,'图1_基准机制比较.png'),'Resolution',300);
exportgraphics(f,fullfile(out,'图1_基准机制比较.pdf'),'ContentType','vector');close(f);

f=figure('Visible','off','Units','inches','Position',[1 1 7 5.7]);tiledlayout(2,2,'TileSpacing','compact');
gain=[0 .25 .5 .75];cost=[0 .5 1.5 3 6];rules={'bounded_default','satisficing'};names={'有限注意','满意即止'};
lim=max(abs(G.reduction_pp));
for b=1:2,for a=1:2
 A=[2 6];Z=zeros(4,5);
 for g=1:4,for l=1:5
  rr=G(strcmp(G.rule,rules{b})&G.attention==A(a)&G.cue_gain==gain(g)&G.cue_cost==cost(l),:);
  Z(g,l)=rr.reduction_pp;
 end,end
 nexttile;imagesc(Z);axis xy;clim([-lim lim]);cb=colorbar;cb.Label.String='百分点';
 xticks(1:5);xticklabels(string(cost));yticks(1:4);yticklabels(string(gain));
 xlabel('提示处理成本');ylabel('关联线索效力');title(sprintf('%s规则  注意资源 %g',names{b},A(a)));
end,end
x=linspace(-1,1,129)';colormap(f,[min(1,1+x),1-abs(x),min(1,1-x)]);
exportgraphics(f,fullfile(out,'图2_条件与反转边界.png'),'Resolution',300);
exportgraphics(f,fullfile(out,'图2_条件与反转边界.pdf'),'ContentType','vector');close(f);
fprintf('Two publication figures exported from existing corrected CSV data\n');
end
