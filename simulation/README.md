# 机制仿真方案 (v2 稳定版)：AI导购理由撤回后的预算重审

## 一、方案核心原则与定位

1. **文献角色**：文献作为参数范围和理论边界来源（如 M4 提供撤回信息更新滞后的相对效率经验锚点，W1 提供信念—偏好区分视角），伦理规则作为待检验的系统策略；不把任何文献或模型结果直接当成算法结论。
2. **规范边界与客观定位**：
   > 在预设的信念更新、理由依赖、目标修订概率和交互成本范围内，条件触发并及时停止的策略（策略 D）在部分参数区域能够有效降低目标偏离和事后干预成本；在高认知固执度、低解释增益或高提示成本条件下，弱基线可能更优。该结论是对规则机制和参数后果的计算分析，不是对真人自主性效果的直接测量。
   >
  > 本仿真不声称“证明策略 D 提高了消费者自主性”，亦不声称“策略 D 在所有指标或所有情境下总体最优”；仿真显示策略 D 是在保护目标修订机会、避免错误改写和控制交互成本之间提供条件性折中，为未来验证研究和系统审计提供可检验假设。本项目不开展真人实验。

## 二、模型方程与三级参数

### 1. 变量定义
- $b_t \in [0, 1]$：用户对理由真实性的信念；
- $g_t \in \mathbb{R}^+$：当前预算目标（初始 $g_{\text{init}}=150$，提价后 $g_{\text{elev}}=200$，$\Delta g = 50$）；
- $r_t \in [0, 1]$：理由与预算调整的公开关联度；
- $s_t \in \{0, 1\}$：理由证据支持状态（撤回后 $s_t=0$）；
- $u_t \in \{0, 1\}$：是否具备独立理由（如外观偏好）；
- $q_t \in \{0, 1\}$：是否已经知情重申；
- $\text{exit}_t \in \{0, 1\}$：是否明确要求退出；
- $c_t \ge 0$：交互提醒成本。

### 2. 统一信念更新方程
$$ \eta_{\text{retraction}} = \eta_{\text{direct}} \times \rho_{\text{retraction}} $$
$$ \eta_{\text{effective}} = \min(1.0, \eta_{\text{retraction}} + \kappa) \quad (\text{若有说明，否则 } \eta_{\text{effective}} = \eta_{\text{retraction}}) $$
$$ b_{\text{next}} = \max(0.0, min(1.0, b_t - \eta_{\text{effective}} \cdot b_t)) $$
- $\rho_{\text{retraction}} \in [0.40, 0.67, 0.90]$：**文献锚定参数**（M4 Gonçalves et al. 2026 实证比率锚点）；
- $\eta_{\text{direct}} \in [0.60, 0.90]$（默认 0.90）：**研究者假设参数**；
- $\kappa \in [0.10, 0.30]$（默认 0.20）：**研究者假设参数**。

### 3. 统一预算目标更新方程
$$ g_{\text{recognized}} = g_{\text{init}} + \alpha \cdot r_t \cdot b_{\text{residual}} \cdot \Delta g + \epsilon $$
- $b_{\text{residual}} = 1.0 - \eta_{\text{effective}}$：残余错误信念；
- $\alpha \in [0.50, 1.00]$（默认 0.80）：**研究者假设参数**；
- $\epsilon \sim \mathcal{N}(0, \sigma^2)$，$\sigma = 0.15$。

### 4. 消除硬编码的策略 D 认知连接重选概率
策略 D 的重新考虑概率真实连接认知更新变量与成本项：
$$ p_{\text{reconsider}} = \text{clip}\left(p_0 + \beta_r \cdot r_t + \beta_b \cdot b_{\text{residual}} + \beta_e \cdot I_{\text{explanation}} - \beta_c \cdot c_t, 0.0, 1.0\right) $$
以概率 $p_{\text{reconsider}}$ 采纳 150 元，以 $1 - p_{\text{reconsider}}$ 保留 200 元，彻底消除了写死结果的伪阳性问题。

## 三、策略与状态机语义明确化

| 策略代码与名称 | 进入 S6 | 静默结束 | 豁免后停止 | 重审后完成 | 目标处理规则 | 交互成本 |
|---|:---:|:---:|:---:|:---:|---|:---:|
| **A 弱基线** | 0 | 1 | 0 | 0 | 仅更正事实，不说明关联，不碰预算，维持 200 | 0.0 |
| **B 家长主义基线** | 0 | 1 | 0 | 0 | 自动回滚至 150；若 $u=1$、$q=1$ 或退出则记为错误改写 | 0.5 |
| **C 繁琐基线** | 0 | 0 | 0 | 0 | 无差别全轮次追问；在豁免后仍追问（记为豁免后干预） | 3.5 |
| **D 本方案 (H1)** | 1 | 0 | 0 | 1 | 触发并完成重审流程，依概率采纳目标 | 1.0 |
| **D 本方案 (H2/H3/H4)**| 1 | 0 | 1 | 0 | 识别豁免条件（独立理由/知情重申/退出），合规即时停止 | 0.0 |

> **注**：H4 用于检验明确退出请求下的停止干预规则；若涉及商业性推送，再与《消保法实施条例》第 24 条进行有限对应。

## 四、八项拆分指标与综合损失体系

1. **目标偏离度 ($D_g$)**：$|g_{\text{final}} - g_{\text{recognized}}|$；
2. **错误目标改写率**：系统改变预算但用户有独立理由、已重申或要求退出的比例（B 在 H2/H3/H4 达 100%）；
3. **豁免后干预率**：已满足豁免条件后系统仍追问的比例（C 达 100%，D 为 0%）；
4. **选择机会保留率**：仅在实际触发 S5 并提供重选时为 1（D 在 H1 为 1，豁免情境不触发为 0）；
5. **理由关联识别率**：仅在实际获得关联说明时为 1（D 在 H1 为 1，豁免情境为 0）；
6. **退出成功率**：仅在存在退出请求的 H4 情境下计算（D 为 100%，A/B/C 为 0%）。**必须说明的是：A、B、C 被预设为不响应退出请求，D 被预设为响应退出请求。因此 H4 的退出成功率用于检查策略规则实现，不代表真实平台的实际行为比例**；
7. **交互提醒成本**：系统提示造成的认知与操作成本；
8. **三套归一化综合损失**：
   - $W_1$ (等权平衡)：$1.0 \times \tilde{D}_g + 1.0 \times \text{Rate}_{\text{ow}} + 1.0 \times \text{Rate}_{\text{int}} + 1.0 \times \tilde{C}$
   - $W_2$ (改写优先)：$1.0 \times \tilde{D}_g + 3.0 \times \text{Rate}_{\text{ow}} + 2.0 \times \text{Rate}_{\text{int}} + 1.0 \times \tilde{C}$
   - $W_3$ (负担平衡)：$1.0 \times \tilde{D}_g + 2.0 \times \text{Rate}_{\text{ow}} + 2.0 \times \text{Rate}_{\text{int}} + 2.0 \times \tilde{C}$

## 五、验证矩阵与核心结论 (详见 validation/)

- **基准情境数值基线 (H1-B2)**：
  - 策略 D 实测指标：目标偏离度为 **17.7819** 元，综合损失 $W_1 = \mathbf{0.6414}$、$W_2 = \mathbf{0.6414}$、$W_3 = \mathbf{0.9271}$；
  - 历史版本结果已废止，当前分析不使用旧版数值；当前结果统一以 `strategy_comparison.csv` 和验证日志中的基准表为准；
- **稳定性检验**：在当前参数配置、随机种子和模型结构下，$N=1,000$ 与 $N=10,000$ 的策略排序保持一致，说明本仿真在该固定设定下具有结果稳定性；
- **反转决策边界**：在 $\rho_{\text{retraction}} \le 0.35$ 且 $\kappa \le 0.12$（用户极端固执且解释无益）时，弱基线 A 的成本优势使其综合损失低于策略 D；
- **版本哈希锁定与自引用说明**：
  - 核心文件哈希锁定于 [`validation/v2_manifest.json`](file:///d:/AI理论/simulation/validation/v2_manifest.json) 与 [`validation/v2_checksums.sha256`](file:///d:/AI理论/simulation/validation/v2_checksums.sha256)；
  - `v2_manifest.json` 与 `v2_checksums.sha256` 自身不参与自引用校验，避免哈希自引用死锁；
  - 证据包文件独立建档锁定于 [`evidence_package/evidence_manifest.json`](file:///d:/AI理论/evidence_package/evidence_manifest.json) 与 [`evidence_package/evidence_checksums.sha256`](file:///d:/AI理论/evidence_package/evidence_checksums.sha256)；
- **执行环境与学术诚实声明**：
  1. Python 仿真已全部完成并生成完整数据；
  2. 单元理论基准检查已全部通过；
  3. MATLAB 脚本已完整对齐，其实机运行仍待桌面端交互会话完成；
  4. 外部 API 连接异常仅为工具调用网络波动，本身不影响本地已生成的仿真数据，且严禁将 API 错误作为任何仿真或实证证据。
