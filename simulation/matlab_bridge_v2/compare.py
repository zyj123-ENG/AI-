import pandas as pd
p=pd.read_csv('simulation/results/strategy_comparison.csv'); m=pd.read_csv('simulation/matlab_bridge_v2/matlab_results.csv')
x=p.merge(m,on=['history_id','burden_id','strategy'],suffixes=('_py','_ml'))
cols=['mean_goal_deviation','sd_goal_deviation','incorrect_goal_rewrite_rate','post_exemption_intervention_rate','choice_retention_rate','reason_link_recognition_rate','mean_prompt_cost','composite_loss_w1','composite_loss_w2','composite_loss_w3']
for c in cols:
 d=(x[c+'_py']-x[c+'_ml']).abs()
 print(f'{c}: max={d.max():.6f}, mean={d.mean():.6f}')
print('H4 exit python/matlab')
print(x[x.history_id=='H4_exit'][['strategy','exit_success_rate_py','exit_success_rate_ml']].drop_duplicates().to_string(index=False))
