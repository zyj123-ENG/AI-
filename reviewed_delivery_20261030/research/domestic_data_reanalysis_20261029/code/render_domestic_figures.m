function render_domestic_figures(outDir)
% Render only aggregate CSVs; no new data or model computation.
arm=readtable(fullfile(outDir,'cell_estimates.csv'),'TextType','string');
con=readtable(fullfile(outDir,'contrasts.csv'),'TextType','string');
set(groot,'defaultAxesFontName','Microsoft YaHei');set(groot,'defaultTextFontName','Microsoft YaHei');
a=arm(arm.sample=="all_516" & arm.metric=="trust_mean",:);v=reshape(a.estimate,[2 3])';lo=reshape(a.ci_low,[2 3])';hi=reshape(a.ci_high,[2 3])';
f=figure('Visible','off','Color','w','Position',[50 50 1300 700]);b=bar(v,'grouped');b(1).FaceColor=[.35 .49 .60];b(2).FaceColor=[.36 .61 .48];hold on;
for c=1:2
    errorbar(b(c).XEndPoints,v(:,c),v(:,c)-lo(:,c),hi(:,c)-v(:,c),'.k','LineWidth',1.3);
    for m=1:3,text(b(c).XEndPoints(m),hi(m,c)+.08,sprintf('%.3f',v(m,c)),'HorizontalAlignment','center','FontSize',15);end
end
set(gca,'XTick',1:3,'XTickLabel',{'无记忆提示（每臂88人）','相关记忆提示（每臂84人）','侵入记忆提示（每臂86人）'},'FontSize',15);ylim([1 7]);ylabel('存档信任三题均值（1—7）');legend({'无控制面板','可编辑面板'},'Location','northwest');grid on;title('国内原实验六臂：即时信任评价','FontSize',19);
exportgraphics(f,fullfile(outDir,'图2_国内六臂信任评价.png'),'Resolution',180);close(f);
names=["dashboard_average_standardized","dashboard_with_no_memory","dashboard_with_relevant","dashboard_with_intrusive","primary_intrusive_gap_change","relevant_gap_change"];
labels={'面板平均差（次要）','无记忆内面板差','相关记忆内面板差','侵入记忆内面板差','主比较：侵入差距δ','相关差距变化（探索）'};
v=zeros(6,1);lo=v;hi=v;
for j=1:6,r=con(con.sample=="all_516" & con.metric=="trust_mean" & con.contrast==names(j),:);v(j)=r.estimate;lo(j)=r.ci_low;hi(j)=r.ci_high;end
f=figure('Visible','off','Color','w','Position',[50 50 1500 750]);axes('Position',[.30 .15 .66 .78]);errorbar(v,1:6,v-lo,hi-v,'horizontal','o','LineWidth',1.6,'MarkerSize',7,'Color',[.22 .43 .56]);xline(0,'--k');
set(gca,'YTick',1:6,'YTickLabel',labels,'YDir','reverse','FontSize',15);ylim([.4 6.6]);grid on;xlabel('信任量表点数差及逐项95%重抽样区间');title('平均评价变化与特定差距缓解分别检验','FontSize',19);
set(f,'PaperPositionMode','auto');print(f,fullfile(outDir,'图3_面板差值与交互边界.png'),'-dpng','-r180');close(f);
end
