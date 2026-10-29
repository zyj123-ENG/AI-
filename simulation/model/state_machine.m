function [states_visited, trigger_S5, entered_S6, terminal_without_intervention, ...
                  stopped_after_exemption, completed_reconsideration, prompt_cost, exit_success] = ...
    state_machine(strategy_id, reason_important, reason_retracted, has_public_rel, ...
                  decision_adjustable, has_indep_reason, is_reaffirmed, is_exit_requested, ...
                  cost_unit, cost_cumbersome)
% STATE_MACHINE 修正版六状态机制状态转移与语义明确判定
% 状态集:
%   S0: 初始预算与目标
%   S1: AI 提供推荐理由
%   S2: 用户因理由改变预算
%   S3: 重要理由失去支持
%   S4: 判断是否存在公开的理由—预算关联
%   S5: 说明关联并开放保留/修改/结束三项选择
%   S6: 停止干预 (知情重申、独立理由或退出)
%
% 输出:
%   states_visited               - 经历的状态序列
%   trigger_S5                   - 是否触发 S5 关联说明
%   entered_S6                   - 是否正式进入 S6 停止状态
%   terminal_without_intervention - 是否属于静默结束（无干预过程，如 A、B）
%   stopped_after_exemption      - 是否属于识别豁免条件后的合规停止 (H2, H3, H4)
%   completed_reconsideration    - 是否属于完成重审流程后的合规停止 (H1)
%   prompt_cost                  - 交互提醒成本
%   exit_success                 - 若存在退出请求时，系统是否成功停止推荐与追问 (非退出情境为 NaN)

    states_visited = [0, 1, 2, 3, 4];
    is_exempt = (has_indep_reason || is_reaffirmed || is_exit_requested);
    qualifies_for_S5 = reason_important && reason_retracted && has_public_rel && ...
                       decision_adjustable && ~is_exempt;

    switch strategy_id
        case 'A' % 弱基线：静默跳过 S5 和 S6，无干预
            trigger_S5 = false;
            entered_S6 = false;
            terminal_without_intervention = true;
            stopped_after_exemption = false;
            completed_reconsideration = false;
            prompt_cost = 0.0;
            if is_exit_requested
                exit_success = false; % 未能响应退出请求，继续默认推荐
            else
                exit_success = NaN;
            end

        case 'B' % 家长主义基线：后台直接改写，静默退出
            trigger_S5 = false;
            entered_S6 = false;
            terminal_without_intervention = true;
            stopped_after_exemption = false;
            completed_reconsideration = false;
            prompt_cost = 0.5;
            if is_exit_requested
                exit_success = false; % 未能响应退出意图，且越权改写目标
            else
                exit_success = NaN;
            end

        case 'C' % 繁琐基线：无差别强行进入 S5，忽视豁免条件，持续追问
            states_visited = [states_visited, 5];
            trigger_S5 = true;
            entered_S6 = false;
            terminal_without_intervention = false;
            stopped_after_exemption = false;
            completed_reconsideration = false;
            prompt_cost = cost_unit + cost_cumbersome;
            if is_exit_requested
                exit_success = false; % 忽视退出请求，继续强行追问
            else
                exit_success = NaN;
            end

        case 'D' % 本方案：严格依条件触发与停止
            if qualifies_for_S5
                % H1 场景：触发重审并合规完成
                states_visited = [states_visited, 5, 6];
                trigger_S5 = true;
                entered_S6 = true;
                terminal_without_intervention = false;
                stopped_after_exemption = false;
                completed_reconsideration = true; % 完成重审后停止
                prompt_cost = cost_unit;
                exit_success = NaN;
            else
                % H2, H3, H4 场景：识别豁免条件，合规即时停止
                states_visited = [states_visited, 6];
                trigger_S5 = false;
                entered_S6 = true;
                terminal_without_intervention = false;
                stopped_after_exemption = is_exempt; % 识别豁免后停止
                completed_reconsideration = false;
                prompt_cost = 0.0;
                if is_exit_requested
                    exit_success = true; % 严格响应退出请求，彻底停止推荐
                else
                    exit_success = NaN;
                end
            end
    end
end
