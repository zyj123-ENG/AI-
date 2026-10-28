function export_simulation_diagnostics()
% Descriptive diagnostics with fixed choices; no behavioral retuning.
root=fileparts(fileparts(mfilename('fullpath')));out=fullfile(root,'results');
a=load(fullfile(out,'base_outcomes.mat'));z=load(fullfile(out,'paired_inputs.mat'),'Q');
head={'rule','policy','type','n','n_purchased','n_compatible_purchased','n_requests',...
 'compatible_purchase_regret','request_rate','failure_rate_all','failure_rate_given_request',...
 'n_common_purchases_vs_tools','regret_diff_common_vs_tools','mcse_regret_diff_common_vs_tools',...
 'regret_penalty0','regret_penalty100','regret_penalty500','regret_penalty1000'};
rows={};ic=find(strcmp({a.P.id},'D1_R0_C1'));
for b=1:numel(a.rules),for p=1:numel(a.P),for typ=0:3
 mask=true(size(z.Q.type));if typ>0,mask=z.Q.type==typ;end
 Y=double(a.baseOut{b,p}(mask,:));ref=double(a.baseOut{b,ic}(mask,:));
 bought=Y(:,15)==0;comp=Y(:,5)==1;req=Y(:,12)==1;
 condFail=NaN;if any(req),condFail=mean(Y(req,13));end
 both=isfinite(Y(:,9))&isfinite(ref(:,9));dd=Y(both,9)-ref(both,9);
 if numel(dd)>1,dm=mean(dd);ds=std(dd)/sqrt(numel(dd));else,dm=NaN;ds=NaN;end
 penalties=zeros(1,4);plist=[0 100 500 1000];
 for k=1:4
  v=Y(:,9)-(1000-plist(k))*Y(:,6);penalties(k)=mean(v,'omitnan');
 end
 rows(end+1,:)=[{a.rules{b},a.P(p).id,typ,sum(mask),sum(bought),sum(comp),sum(req),...
  mean(Y(comp,9),'omitnan'),mean(req),mean(Y(:,13)),condFail,sum(both),dm,ds},num2cell(penalties)]; %#ok<AGROW>
end,end,end
writetable(cell2table(rows,'VariableNames',head),fullfile(out,'base_diagnostics.csv'));
assert(all(double(a.baseOut{2,ic}(z.Q.type==3,1))==1),'T3 knowledge reset');
fprintf('Diagnostic rows=%d; T3 prior knowledge preserved\n',size(rows,1));
end
