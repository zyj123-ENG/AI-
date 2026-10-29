function outTable = run_paired_simulation_v2()
%RUN_PAIRED_SIMULATION_V2 Independent MATLAB v2 bridge.
% Keeps the frozen Python v2 assets unchanged. Outputs a separate CSV for
% structural and numerical comparison after desktop MATLAB execution.

    bridgeDir = fileparts(mfilename('fullpath'));
    simDir = fileparts(bridgeDir);
    cfg = jsondecode(fileread(fullfile(simDir, 'config', 'parameters.json')));
    outPath = fullfile(bridgeDir, 'matlab_results.csv');
    logPath = fullfile(bridgeDir, 'matlab_run_log.txt');
    diary(logPath);
    cleanup = onCleanup(@() diary('off')); %#ok<NASGU>

    N = cfg.simulation_setup.standard_n;
    seed = cfg.simulation_setup.random_seed;
    rng(seed, 'twister');

    gInit = cfg.parameter_levels.researcher_hypotheses.budgets.initial_budget;
    gElev = cfg.parameter_levels.researcher_hypotheses.budgets.elevated_budget;
    deltaG = cfg.parameter_levels.researcher_hypotheses.budgets.delta_g;
    alpha = cfg.parameter_levels.researcher_hypotheses.reason_budget_influence.default;
    epsSD = cfg.parameter_levels.researcher_hypotheses.noise.epsilon_noise_sd;
    cUnit = cfg.parameter_levels.researcher_hypotheses.costs.cost_single_prompt;
    cCumb = cfg.parameter_levels.researcher_hypotheses.costs.cost_cumbersome_confirm;
    maxCost = cfg.parameter_levels.researcher_hypotheses.costs.max_possible_cost;
    rw = cfg.parameter_levels.researcher_hypotheses.strategy_D_reconsider_weights;

    epsDraws = randn(N,1) * epsSD;
    choiceDraws = rand(N,1);

    histories = {
        'H1_connected', 1, 0, 0, 0, '撤回重要理由且公开相连';
        'H2_independent', 1, 1, 0, 0, '撤回理由但有独立偏好';
        'H3_reaffirmed', 1, 0, 1, 0, '撤回理由但已知情重申';
        'H4_exit', 1, 0, 0, 1, '撤回理由但用户明确退出'
    };
    burdens = {
        'B1_low', 0.90, 0.90, 0.10, 0.00, '低认知负担';
        'B2_mid', 0.90, 0.67, 0.20, 0.05, '中认知负担';
        'B3_high', 0.75, 0.40, 0.30, 0.15, '高认知负担'
    };
    strategies = {'A','B','C','D'};

    rows = cell(48, 19);
    rowIdx = 0;
    for h = 1:size(histories,1)
        hId = histories{h,1}; r = histories{h,2}; u = histories{h,3};
        q = histories{h,4}; exitReq = histories{h,5}; hDesc = histories{h,6};
        for b = 1:size(burdens,1)
            bId = burdens{b,1}; etaDirect = burdens{b,2}; rho = burdens{b,3};
            kappa = burdens{b,4}; burdenPenalty = burdens{b,5}; bDesc = burdens{b,6};
            for s = 1:numel(strategies)
                strat = strategies{s};
                goalDev = zeros(N,1); overwrite = zeros(N,1); postInt = zeros(N,1);
                choiceRet = zeros(N,1); reasonRec = zeros(N,1); costs = zeros(N,1);
                exitVals = [];
                hasExpl = strcmp(strat,'C') || strcmp(strat,'D');
                [~, etaEff] = localBelief(1, etaDirect, rho, kappa, hasExpl);
                [~,~,~,~,~,~,promptCost,exitSuccess] = localState(strat, true, true, r>0, true, u==1, q==1, exitReq==1, cUnit, cCumb);
                for i = 1:N
                    [gFinal,gUser,ow,pi,cr,rr] = localGoal(gInit,gElev,r,0,u,q,exitReq,strat,etaEff,alpha,epsDraws(i),choiceDraws(i),rw,burdenPenalty);
                    goalDev(i) = abs(gFinal-gUser); overwrite(i)=double(ow); postInt(i)=double(pi);
                    choiceRet(i)=double(cr); reasonRec(i)=double(rr); costs(i)=promptCost;
                    if ~isnan(exitSuccess), exitVals(end+1)=double(exitSuccess); end %#ok<AGROW>
                end
                dNorm = mean(goalDev)/deltaG; cNorm = mean(costs)/maxCost;
                rowIdx = rowIdx + 1;
                rows(rowIdx,:) = {hId,hDesc,bId,bDesc,strat,N,mean(goalDev),std(goalDev),mean(overwrite),mean(postInt),mean(choiceRet),mean(reasonRec),localMean(exitVals),mean(costs),dNorm+mean(overwrite)+mean(postInt)+cNorm,dNorm+3*mean(overwrite)+2*mean(postInt)+cNorm,dNorm+2*mean(overwrite)+2*mean(postInt)+2*cNorm,seed,cfg.parameter_version};
            end
        end
    end
    names = {'history_id','history_desc','burden_id','burden_desc','strategy','n_trials','mean_goal_deviation','sd_goal_deviation','incorrect_goal_rewrite_rate','post_exemption_intervention_rate','choice_retention_rate','reason_link_recognition_rate','exit_success_rate','mean_prompt_cost','composite_loss_w1','composite_loss_w2','composite_loss_w3','seed','parameter_version'};
    outTable = cell2table(rows,'VariableNames',names);
    writetable(outTable,outPath);
    fprintf('MATLAB v2 bridge complete: %s\n', outPath);
end

function [bNext, etaEff] = localBelief(b, etaDirect, rho, kappa, explain)
    etaEff = etaDirect*rho;
    if explain, etaEff = min(1,etaEff+kappa); end
    bNext = max(0,min(1,b-etaEff*b));
end

function [states,trigger,entered,terminal,stopped,completed,cost,exitSuccess] = localState(strat,important,retracted,publicRel,adjustable,indep,reaffirm,exitReq,cUnit,cCumb)
    exempt = indep || reaffirm || exitReq;
    qualifies = important && retracted && publicRel && adjustable && ~exempt;
    states = [0 1 2 3 4]; trigger=false; entered=false; terminal=false; stopped=false; completed=false; cost=0; exitSuccess=NaN;
    switch strat
        case 'A', terminal=true; if exitReq, exitSuccess=false; end
        case 'B', terminal=true; cost=.5; if exitReq, exitSuccess=false; end
        case 'C', trigger=true; cost=cUnit+cCumb; if exitReq, exitSuccess=false; end
        case 'D'
            entered=true;
            if qualifies, states=[states 5 6]; trigger=true; completed=true; cost=cUnit;
            else, states=[states 6]; stopped=exempt; if exitReq, exitSuccess=true; end, end
    end
end

function [gFinal,gUser,ow,postInt,choiceRet,reasonRec] = localGoal(g0,ge,r,s,u,q,exitReq,strat,eta,alpha,eps,draw,rw,burden)
    dg=ge-g0; residual=1-eta; exempt=u||q||exitReq;
    if exitReq, gUser=ge; elseif s==0 && ~exempt && r>0, gUser=max(g0,min(ge,g0+alpha*r*residual*dg+eps)); else, gUser=ge; end
    ow=false; postInt=false; choiceRet=false; reasonRec=false;
    switch strat
        case 'A', gFinal=ge;
        case 'B', gFinal=g0; ow=exempt;
        case 'C'
            if exempt, gFinal=ge; else, gFinal=g0; end
            postInt=exempt; choiceRet=true; reasonRec=true;
        case 'D'
            if exempt, gFinal=ge;
            else, choiceRet=true; reasonRec=true; p=min(1,max(0,rw.p_0+rw.beta_reason*r+rw.beta_residual*residual+rw.beta_explanation-rw.beta_cost*burden)); if draw<p, gFinal=g0; else, gFinal=ge; end, end
    end
end

function m = localMean(x)
    if isempty(x), m=NaN; else, m=mean(x); end
end
