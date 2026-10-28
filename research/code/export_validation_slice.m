function export_validation_slice()
% Export all 40,000 dependent profiles for an independent CSV calculation.
root=fileparts(fileparts(mfilename('fullpath'))); out=fullfile(root,'results');
a=load(fullfile(out,'base_outcomes.mat'),'baseOut','P','metrics');
q=load(fullfile(out,'paired_inputs.mat'),'Q'); mask=q.Q.type==1;
policies={'D1_R0_C0','D1_R0_C1','D1_R1_C1'};
cols=[2 3 9 10 15]; header={'profile'}; X=(1:sum(mask))';
for p=1:numel(policies)
 pi=find(strcmp({a.P.id},policies{p})); raw=double(a.baseOut{2,pi}(mask,cols)); X=[X raw]; %#ok<AGROW>
 for k=1:numel(cols),header{end+1}=[policies{p} '__' a.metrics{cols(k)}];end %#ok<AGROW>
end
writetable(array2table(X,'VariableNames',header),fullfile(out,'independent_validation_slice.csv'));
fprintf('Exported %d matched profiles and %d numeric outcomes\n',size(X,1),size(X,2)-1);
end
