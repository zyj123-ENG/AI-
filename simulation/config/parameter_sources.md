# 机制仿真参数来源与分级依据说明 (v2 稳定版)

本版本依据终审意见，消除了硬编码指标，引入 $H_4$ 退出情境（扩展为 48 实验单元），并将策略 D 的重新考虑概率完全连接至实际认知变量。

## 一、参数层级与公式解耦

### 1. 撤回信念更新效率解耦
$$ \eta_{\text{retraction}} = \eta_{\text{direct}} \times \rho_{\text{retraction}} $$
- $\rho_{\text{retraction}} \in [0.40, 0.67, 0.90]$：**文献锚定参数**（M4 *Gonçalves et al., 2026, REStud* 实证比率锚点）；
- $\eta_{\text{direct}} \in [0.60, 0.90]$（默认 0.90）：**研究者假设参数**；
- 说明关联增益：$\eta_{\text{effective}} = \min(1.0, \eta_{\text{retraction}} + \kappa)$，$\kappa \in [0.10, 0.30]$（研究者假设参数）。

### 2. 用户真实认可预算目标统一方程
$$ g_{\text{recognized}} = g_{\text{init}} + \alpha \cdot r_t \cdot b_{\text{residual}} \cdot \Delta g + \epsilon $$
- $b_{\text{residual}} = 1.0 - \eta_{\text{effective}}$：残余错误信念；
- $r_t \in [0, 1]$：公开理由关联强度；
- $\alpha \in [0.50, 1.00]$（默认 0.80）：理由依赖影响权重（研究者假设）；
- $\Delta g = 50.0$ 元；$\epsilon \sim \mathcal{N}(0, \sigma^2)$。

### 3. 策略 D 重新考虑概率方程（真实连接认知更新变量）
$$ p_{\text{reconsider}} = \text{clip}\left(p_0 + \beta_r \cdot r_t + \beta_b \cdot b_{\text{residual}} + \beta_e \cdot I_{\text{explanation}} - \beta_c \cdot c_t, 0.0, 1.0\right) $$
- $p_0 = 0.40$（基准重选倾向）；
- $\beta_r = 0.15$（公开关联敏感度）；
- $\beta_b = 0.15$（残余信念阻尼权重）；
- $\beta_e = 0.15$（关联说明呈现增益）；
- $\beta_c = 0.10$（交互认知负担惩罚）；
- 上述权重均明确标定为**研究者假设参数**，并在敏感性分析中检验。

## 二、四个理由历史情境 ($4 \times 3 \times 4 = 48$ 单元)

1. **$H_1$ (撤回且相连)**：$r=1, u=0, q=0, \text{exit}=0$；触发 S5 说明重审；
2. **$H_2$ (独立偏好)**：$r=1, u=1, q=0, \text{exit}=0$；触发停止条件；
3. **$H_3$ (知情重申)**：$r=1, u=0, q=1, \text{exit}=0$；触发停止条件；
4. **$H_4$ (明确请求退出)**：$r=1, u=0, q=0, \text{exit}=1$；触发停止条件，用于检验明确退出请求下的停止干预规则（若涉及商业性推送，再与《消保法实施条例》第 24 条进行有限对应；A/B/C 预设为不响应退出，D 预设为响应，用于检查策略规则实现，不代表真实平台实际行为比例）。

## 三、三套综合损失权重配置 (Weight Sensitivity)

$$ \text{Loss} = w_{\text{goal}} \cdot \frac{D_g}{\Delta g} + w_{\text{rewrite}} \cdot \text{Rate}_{\text{rewrite}} + w_{\text{intervention}} \cdot \text{Rate}_{\text{intervention}} + w_{\text{cost}} \cdot \frac{C}{\bar{C}} $$
- **W1 (全维等权)**：$w = [1.0, 1.0, 1.0, 1.0]$；
- **W2 (改写与干预优先惩罚)**：$w = [1.0, 3.0, 2.0, 1.0]$；
- **W3 (负担与目标均衡)**：$w = [1.0, 2.0, 2.0, 2.0]$。
