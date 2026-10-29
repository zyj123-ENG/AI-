function results = run_paired_simulation()
% RUN_PAIRED_SIMULATION 执行36单元配对机制仿真与敏感性分析
% 3 理由历史 x 4 AI 策略 x 3 认知负担水平 = 36 条件

    fprintf('=== 开始执行机制仿真 (36单元配对设计) ===\n');
    
    % 加载配置
    cfg_text = fileread(fullfile('..', 'config', 'parameters.json'));
    cfg = jsondecode(cfg_text);
    
    N = cfg.simulation_setup.num_trials_per_cell;
    rng(cfg.simulation_setup.random_seed);
    
    g_init = cfg.parameter_levels.researcher_hypotheses.initial_budget;
    g_elev = cfg.parameter_levels.researcher_hypotheses.elevated_budget;
    c_unit = cfg.parameter_levels.researcher_hypotheses.cost_single_prompt;
    c_cumb = cfg.parameter_levels.researcher_hypotheses.cost_cumbersome_confirm;
    alpha = cfg.parameter_levels.researcher_hypotheses.alpha_reason_influence.default;
    eps_sd = cfg.parameter_levels.researcher_hypotheses.epsilon_noise_sd;

    % 维度设置
    histories = {'H1_connected', 'H2_independent', 'H3_reaffirmed'};
    strategies = {'A', 'B', 'C', 'D'};
    burdens = {'B1_low', 'B2_mid', 'B3_high'};
    
    % 预设配对随机扰动 (消除策略间的随机抽样噪声)
    epsilon_paired = eps_sd * randn(N, 1);
    
    results = [];
    
    for h_idx = 1:length(histories)
        h_id = histories{h_idx};
        switch h_id
            case 'H1_connected'
                r = 1.0; u = 0.0; q = 0.0;
            case 'H2_independent'
                r = 1.0; u = 1.0; q = 0.0;
            case 'H3_reaffirmed'
                r = 1.0; u = 0.0; q = 1.0;
        end
        
        for b_idx = 1:length(burdens)
            b_id = burdens{b_idx};
            switch b_id
                case 'B1_low'
                    lambda_base = 0.90; kappa = 0.10;
                case 'B2_mid'
                    lambda_base = 0.67; kappa = 0.20;
                case 'B3_high'
                    lambda_base = 0.40; kappa = 0.30;
            end
            
            for s_idx = 1:length(strategies)
                strat = strategies{s_idx};
                has_expl = (strat == 'C' || strat == 'D');
                
                % 记录 N 次配对模拟
                goal_devs = zeros(N, 1);
                overwrites = zeros(N, 1);
                choice_retentions = zeros(N, 1);
                reason_recognitions = zeros(N, 1);
                costs = zeros(N, 1);
                over_interventions = zeros(N, 1);
                exit_successes = zeros(N, 1);
                
                for i = 1:N
                    eps_i = epsilon_paired(i);
                    
                    % 1. 信念更新
                    [~, lam_eff] = belief_update(1.0, -1.0, lambda_base, kappa, has_expl);
                    
                    % 2. 状态机
                    [~, trig_S5, stop_S6, p_cost, over_int] = state_machine(...
                        strat, true, true, (r > 0), true, (u == 1), (q == 1), false, c_unit, c_cumb);
                    
                    % 3. 目标更新与偏离
                    [g_final, g_user, overwrite_flag] = goal_update(...
                        g_init, g_elev, r, 0, u, q, strat, lam_eff, alpha, eps_i);
                    
                    goal_devs(i) = abs(g_final - g_user);
                    overwrites(i) = double(overwrite_flag);
                    costs(i) = p_cost;
                    over_interventions(i) = double(over_int);
                    
                    % 4. 选择保留与识别代理
                    if strat == 'D'
                        choice_retentions(i) = 1.0; % 保留保留/修改/结束
                        reason_recognitions(i) = 1.0;
                        exit_successes(i) = 1.0;
                    elseif strat == 'C'
                        choice_retentions(i) = 0.8; % 强迫反思削弱自主结束意愿
                        reason_recognitions(i) = 1.0;
                        exit_successes(i) = 0.5;
                    elseif strat == 'B'
                        choice_retentions(i) = 0.0; % 系统剥夺保留高预算选项
                        reason_recognitions(i) = 0.2;
                        exit_successes(i) = 1.0;
                    else % 'A'
                        choice_retentions(i) = 0.0; % 未开辟重审通道
                        reason_recognitions(i) = 0.0;
                        exit_successes(i) = 1.0;
                    end
                end
                
                % 汇总该单元统计量
                row = struct();
                row.history = h_id;
                row.burden_level = b_id;
                row.strategy = strat;
                row.mean_goal_deviation = mean(goal_devs);
                row.incorrect_overwrite_rate = mean(overwrites);
                row.choice_retention_rate = mean(choice_retentions);
                row.reason_recognition_rate = mean(reason_recognitions);
                row.mean_prompt_cost = mean(costs);
                row.over_intervention_rate = mean(over_interventions);
                row.exit_success_rate = mean(exit_successes);
                
                % 综合权衡损失 (Loss = GoalDev + 50*Overwrite + 10*OverInt + Cost)
                row.composite_tradeoff_loss = row.mean_goal_deviation + ...
                    50.0 * row.incorrect_overwrite_rate + ...
                    10.0 * row.over_intervention_rate + ...
                    row.mean_prompt_cost;
                
                results = [results; row];
            end
        end
    end
    
    fprintf('=== 仿真完成，共计 %d 个实验条件 ===\n', length(results));
end
