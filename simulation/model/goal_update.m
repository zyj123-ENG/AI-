function [g_final, user_recognized_goal, incorrect_rewrite, post_exemption_interv, ...
          choice_retention, reason_link_recognition] = ...
    goal_update(g_init, g_elevated, r_t, s_t, u_t, q_t, is_exit_req, strategy_id, ...
                eta_effective, alpha, epsilon, rand_choice_draw, ...
                p_0, beta_reason, beta_residual, beta_explanation, beta_cost, burden_penalty)
% GOAL_UPDATE 修正版预算目标更新、概率选择与机制指标判定
% 输入:
%   g_init              - 初始预算 (如 150)
%   g_elevated          - 提价后预算 (如 200)
%   r_t                 - 理由与预算公开关联强度 [0, 1]
%   s_t                 - 理由证据支持状态 (撤回为 0)
%   u_t                 - 是否有独立理由 (1 为是，0 为否)
%   q_t                 - 是否已知情重申 (1 为是，0 为否)
%   is_exit_req         - 用户是否明确要求退出 (1 为是，0 为否)
%   strategy_id         - 策略类别 ('A', 'B', 'C', 'D')
%   eta_effective       - 生效信念更新效率
%   alpha               - 理由对预算的影响权重
%   epsilon             - 独立扰动噪声
%   rand_choice_draw    - 策略D下的随机抽样值 [0, 1]
%   p_0, beta_*         - 概率重选模型的连接参数 (研究者假设)
%
% 输出:
%   g_final                 - AI 系统最终生效预算
%   user_recognized_goal    - 用户心理上真实认可的知情目标
%   incorrect_rewrite       - 是否发生错误目标改写 (有独立理由/重申/退出时擅自改变)
%   post_exemption_interv   - 是否发生豁免后干预 (满足豁免条件但系统仍追问)
%   choice_retention        - 是否实际提供了保留、修改、结束三项选择入口 (机制产生)
%   reason_link_recognition - 是否实际获得了理由撤回与预算关联说明 (机制产生)

    delta_g = g_elevated - g_init;
    residual_belief = 1.0 - eta_effective;
    
    % 1. 用户真实认可的目标 (Normative Target)
    if is_exit_req == 1
        % 用户明确要求退出：目标冻结于退出前的决定状态
        user_recognized_goal = g_elevated;
    elseif s_t == 0
        if u_t == 1 || q_t == 1
            user_recognized_goal = g_elevated;
        elseif r_t > 0
            user_recognized_goal = g_init + alpha * r_t * residual_belief * delta_g + epsilon;
            user_recognized_goal = max(g_init, min(g_elevated, user_recognized_goal));
        else
            user_recognized_goal = g_elevated;
        end
    else
        user_recognized_goal = g_elevated;
    end

    % 2. 状态驱动的机制指标与系统最终生效预算判定
    incorrect_rewrite = false;
    post_exemption_interv = false;
    choice_retention = false;
    reason_link_recognition = false;
    is_exempt = (u_t == 1 || q_t == 1 || is_exit_req == 1);

    switch strategy_id
        case 'A' % 弱基线：仅改事实，不碰预算，维持 200，无重选入口
            g_final = g_elevated;
            incorrect_rewrite = false;
            post_exemption_interv = false;
            choice_retention = false;
            reason_link_recognition = false;

        case 'B' % 家长主义基线：自动回滚到 150，剥夺选择
            g_final = g_init;
            if is_exempt
                incorrect_rewrite = true; % 用户有独立理由/已重申/要求退出，系统越权改写
            end
            post_exemption_interv = false;
            choice_retention = false;
            reason_link_recognition = false;

        case 'C' % 繁琐基线：无差别追问，提供说明但强迫反思
            if is_exempt
                g_final = g_elevated;
                post_exemption_interv = true; % 满足豁免条件后仍强行追问
            else
                g_final = g_init;
                post_exemption_interv = false;
            end
            incorrect_rewrite = false;
            choice_retention = true;  % 提供了重选入口，但伴随负摩擦
            reason_link_recognition = true;

        case 'D' % 本方案：依据状态机严格门控触发
            if is_exempt
                % 满足豁免条件：不触发 S5，不改写，不追问
                g_final = g_elevated;
                incorrect_rewrite = false;
                post_exemption_interv = false;
                choice_retention = false;       % 豁免场景无需重开选择，直接停止
                reason_link_recognition = false; % 未触发 S5，故不重复说明关联
            else
                % H1 纯关联情境：触发 S5 说明关联并赋予三项选择权
                choice_retention = true;
                reason_link_recognition = true;
                incorrect_rewrite = false;
                post_exemption_interv = false;
                
                % D 策略重新考虑概率真实连接认知更新变量:
                % p_reconsider = clip(p_0 + beta_r*r + beta_b*b_res + beta_e*I_expl - beta_c*c_t, 0, 1)
                p_reconsider = min(1.0, max(0.0, ...
                    p_0 + beta_reason * r_t + beta_residual * residual_belief + ...
                    beta_explanation * 1.0 - beta_cost * burden_penalty));
                    
                if rand_choice_draw < p_reconsider
                    g_final = g_init;     % 用户知情后决定恢复 150
                else
                    g_final = g_elevated; % 用户知情后决定保留 200
                end
            end
    end
end
