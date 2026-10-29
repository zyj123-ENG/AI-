function [b_next, eta_effective] = belief_update(...
    b_t, eta_direct, rho_retraction, kappa, has_explanation)
% BELIEF_UPDATE 修正版撤回信念更新函数
% 输入:
%   b_t            - 当前对推荐理由真实性的信念强度 [0, 1]
%   eta_direct     - 直接新信息下的基准认知更新效率 (研究者假设)
%   rho_retraction - 撤回信息相对于直接信息的相对更新效率 (M4文献锚点)
%   kappa          - 关联说明带来的认知减负增益 (研究者假设)
%   has_explanation - 是否提供了"撤回与预算关联"的说明 (布尔值)
% 输出:
%   b_next         - 更新后的残余错误信念强度 [0, 1]
%   eta_effective  - 实际生效的信念更新效率

    eta_retraction = eta_direct * rho_retraction;
    if has_explanation
        eta_effective = min(1.0, eta_retraction + kappa);
    else
        eta_effective = eta_retraction;
    end
    delta_b = -b_t;
    b_next = max(0.0, min(1.0, b_t + eta_effective * delta_b));
end
