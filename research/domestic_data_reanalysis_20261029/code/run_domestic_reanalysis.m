function run_domestic_reanalysis(sourceFile,outDir)
% Reanalyse archived Chinese participant responses; base MATLAB, no new behavior.
if nargin<2,error('Supply the fixed author CSV and an output directory.');end
if ~isfolder(outDir),mkdir(outDir);end
opts=detectImportOptions(sourceFile,'TextType','string');d=readtable(sourceFile,opts);
assert(height(d)==516 && width(d)==11,'Unexpected source version.');
assert(numel(unique(d.Participant_ID))==516,'Duplicate participant identifier.');
assert(all(d.Age>=18 & d.Age<=62),'Unexpected age.');
items=[d.Trust_Item1 d.Trust_Item2 d.Trust_Item3];
assert(all(ismember(items(:),1:7)) && all(d.MBF>=1 & d.MBF<=7),'Invalid scale.');
mem=["No Memory","Relevant Memory","Intrusive Memory"];
ctrl=["No Control","Editable Dashboard"];
assert(all(ismember(d.Memory_Type,mem)) && all(ismember(d.Control_Interface,ctrl)),'Unexpected factor.');
g=zeros(height(d),1);for m=1:3,for c=1:2,g(d.Memory_Type==mem(m) & d.Control_Interface==ctrl(c))=2*(m-1)+c;end,end
counts=accumarray(g,1,[6 1]);assert(isequal(counts',[88 88 84 84 86 86]),'Unexpected cell size.');
campus=ismember(d.Testing_Channel,["Campus session","Campus resident session"]);
assert(sum(campus)==403 && sum(~campus)==113,'Unexpected recruitment channels.');
Y=[mean(items,2) items d.MBF];
metrics=["trust_mean","trust_item1","trust_item2","trust_item3","mbf_author_composite"];
eligible=true(6,5);eligible(1:2,5)=false;
weights_memory=[176 168 172]/516;
W=[1 -1 0 0 -1 1; ... % primary difference in differences
   -weights_memory(1) weights_memory(1) -weights_memory(2) weights_memory(2) -weights_memory(3) weights_memory(3); ...
   -1 1 0 0 0 0;0 0 -1 1 0 0;0 0 0 0 -1 1; ...
   1 -1 -1 1 0 0;1 0 0 0 -1 0;0 1 0 0 0 -1; ...
   -1 0 1 0 0 0;0 -1 0 1 0 0];
cnames=["primary_intrusive_gap_change","dashboard_average_standardized","dashboard_with_no_memory","dashboard_with_relevant","dashboard_with_intrusive","relevant_gap_change","intrusive_penalty_no_dashboard","intrusive_penalty_dashboard","relevant_vs_none_no_dashboard","relevant_vs_none_dashboard"];
cellnames=["none_no_control","none_dashboard","relevant_no_control","relevant_dashboard","intrusive_no_control","intrusive_dashboard"];
samples=["all_516","campus_403"];B=5000;seeds=[20261029 20261030];
arm=table();contrast=table();model=table();fitrows=table();freq=table();boot_all=cell(2,1);point_all=cell(2,1);
for s=1:2
    mask=true(height(d),1);if s==2,mask=campus;end
    yy=Y(mask,:);gg=g(mask);rng(seeds(s),'twister');
    mu=zeros(6,5);boot=zeros(B,5,6);n=zeros(6,1);sd=mu;
    for a=1:6
        x=yy(gg==a,:);n(a)=size(x,1);mu(a,:)=mean(x,1);sd(a,:)=std(x,0,1);
        for st=1:100:B
            nb=min(100,B-st+1);idx=randi(n(a),n(a),nb);z=reshape(x(idx(:),:),[n(a) nb 5]);
            boot(st:st+nb-1,:,a)=reshape(mean(z,1),[nb 5]);
        end
        for k=1:5
            if ~eligible(a,k),continue;end
            q=pct(boot(:,k,a),[.025 .975]);
            row=table(samples(s),cellnames(a),metrics(k),n(a),mu(a,k),sd(a,k),q(1),q(2),'VariableNames',{'sample','cell','metric','participants','estimate','sd','ci_low','ci_high'});arm=[arm;row]; %#ok<AGROW>
        end
        for k=1:3
            for v=1:7
                row=table(samples(s),cellnames(a),metrics(k+1),v,sum(yy(gg==a,k+1)==v),'VariableNames',{'sample','cell','item','value','participants'});freq=[freq;row]; %#ok<AGROW>
            end
        end
    end
    for j=1:size(W,1)
        for k=1:5
            if k==5 && ~ismember(j,[4 5]),continue;end
            est=W(j,:)*mu(:,k);bb=reshape(boot(:,k,:),[B 6])*W(j,:)';q=pct(bb,[.025 .975]);
            row=table(samples(s),cnames(j),metrics(k),est,q(1),q(2),string(j==1 && k==1),'VariableNames',{'sample','contrast','metric','estimate','ci_low','ci_high','primary_in_full_sample'});
            if s~=1,row.primary_in_full_sample="false";end
            contrast=[contrast;row]; %#ok<AGROW>
        end
    end
    c=double(mod(gg,2)==0);r=double(ismember(gg,[3 4]));i=double(ismember(gg,[5 6]));
    X=[ones(sum(mask),1) r i c r.*c i.*c];b=X\yy(:,1);res=yy(:,1)-X*b;sse=sum(res.^2);df=sum(mask)-6;mse=sse/df;
    add=X(:,1:4);sseadd=sum((yy(:,1)-add*(add\yy(:,1))).^2);F=max(0,(sseadd-sse)/2/mse);p=1-betainc(2*F/(2*F+df),1,df/2);
    model=[model;table(samples(s),sum(mask),sse,df,F,p,'VariableNames',{'sample','participants','full_sse','residual_df','interaction_F_2df','interaction_p'})]; %#ok<AGROW>
    terms=["intercept_none_no_control","relevant_vs_none_no_control","intrusive_vs_none_no_control","dashboard_with_no_memory","relevant_dashboard_interaction","intrusive_dashboard_interaction"];
    for z=1:6,fitrows=[fitrows;table(samples(s),terms(z),b(z),'VariableNames',{'sample','term','coefficient'})];end %#ok<AGROW>
    boot_all{s}=boot;point_all{s}=mu;
end
writetable(arm,fullfile(outDir,'cell_estimates.csv'));writetable(contrast,fullfile(outDir,'contrasts.csv'));
writetable(model,fullfile(outDir,'model_checks.csv'));writetable(fitrows,fullfile(outDir,'ols_coefficients.csv'));writetable(freq,fullfile(outDir,'trust_item_frequencies.csv'));
% Comparisons to source-reported rounded means do not reproduce its full analysis.
trust=Y(:,1);isDash=d.Control_Interface=="Editable Dashboard";
sourcecheck=table(["dashboard";"no_control"],[sum(isDash);sum(~isDash)],[mean(trust(isDash));mean(trust(~isDash))],[std(trust(isDash));std(trust(~isDash))],[4.49;4.30],[.91;1.00],'VariableNames',{'condition','participants','computed_mean','computed_sd','article_mean_rounded','article_sd_rounded'});
writetable(sourcecheck,fullfile(outDir,'source_summary_comparison.csv'));
assert(all(round(sourcecheck.computed_mean,2)==sourcecheck.article_mean_rounded),'Source mean replication mismatch.');
meta=struct('date','2026-10-29','engine',version,'participants',516,'campus_sensitivity_n',403,'cell_counts',counts','bootstrap_repetitions',B,'seeds',seeds,'primary_metric','trust_mean','primary_contrast','primary_intrusive_gap_change','new_behavior_generated',false,'missing_imputed',false,'sample_origin','Domestic recruitment via Zhejiang Business College course and local campus/community channels; not nationality or national representativeness','scoring','S14 all positive, unweighted mean of three original 1-7 trust items','design','original memory message packages 3 x specific inspect-edit-delete dashboard 2','ci','pointwise percentile bootstrap within original six cells; participants are units','clustering_limit','recruitment/session identifiers not public; session clustering cannot be estimated','mbf_rule','only relevant/intrusive cells interpreted; original composite not reconstructible from unpublished MBF items','source_commit','3a1f72704e8f49fa9bbc3854be56ea0fa90f6d53');
fid=fopen(fullfile(outDir,'run_metadata.json'),'w','n','UTF-8');fprintf(fid,'%s',jsonencode(meta,PrettyPrint=true));fclose(fid);
save(fullfile(outDir,'bootstrap_aggregates.mat'),'boot_all','point_all','samples','cellnames','metrics','W','cnames','weights_memory','B','seeds');
render_domestic_figures(outDir);disp(jsonencode(meta,PrettyPrint=true));
end

function q=pct(x,p)
x=sort(x(:));h=1+(numel(x)-1)*p;lo=floor(h);hi=ceil(h);q=x(lo)'.*(hi-h)+x(hi)'.*(h-lo);ix=lo==hi;q(ix)=x(lo(ix));
end
