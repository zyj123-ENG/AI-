"""Deterministic engineering acceptance checks on explicitly constructed inputs.

No human sample, shopping outcome, efficacy estimate, or autonomy score is generated.
"""
from pathlib import Path
import json
from budget_guard import BudgetGuard,audit_events

results=[]
def check(name,condition):
    assert condition,name
    results.append({'check':name,'observed':bool(condition)})
def blocked(fn):
    try:fn()
    except ValueError:return True
    return False
def prepared(**kwargs):
    g=BudgetGuard(20000)
    g.associate('safety','user:2','主要因此提高到200元',True)
    g.withdraw('safety','revision:1','source:withdrawal',material_change=True,**kwargs)
    return g

g=prepared();check('eligible_correction_can_invite',g.can_invite('safety','revision:1'))
check('withdrawal_keeps_effective_budget',g.effective_budget_cents==20000)
check('missing_authorization_rejected',blocked(lambda:g.set_budget(15000)))
g.invite('safety','revision:1','安全优势缺少支持。可维持、调整预算或先不买。')
check('same_episode_second_invitation_rejected',blocked(lambda:g.invite('safety','revision:1','换一种说法再问。')))
g.withdraw('safety','revision:1','source:same')
check('rewording_cannot_reset_episode',not g.can_invite('safety','revision:1'))
g.set_budget(15000,user_turn='user:3',quote='恢复150元',explicit_authorization=True)
check('explicit_authorization_changes_budget',g.effective_budget_cents==15000)
check('filter_obeys_budget',g.candidates([7900,14900,17900])==[7900,14900])
g.candidates([17900],conditional_preview=True)
check('conditional_preview_does_not_change_budget',g.effective_budget_cents==15000)
check('authorized_trace_has_no_budget_errors',audit_events(g.events,20000)==[])
g=prepared();g.correct_association('safety')
check('user_correction_removes_trigger',not g.can_invite('safety','revision:1'))
check('ordinary_complete_correction_needs_no_extra_invite',not prepared(gap=False).can_invite('safety','revision:1'))
check('minor_change_does_not_trigger',not prepared(important=False).can_invite('safety','revision:1'))
g=prepared();g.invite('safety','revision:1','已说明依据变化和预算关联。');g.reaffirm('safety','revision:1','user:4','仍按200元，主要喜欢颜色。',after_notice_reviewed=True)
check('later_user_reaffirmation_stops_same_invite',not g.can_invite('safety','revision:1'))
g=prepared();g.end();check('ending_stops_proactive_budget_invite',not g.can_invite('safety','revision:1'))
g=prepared();g.close_marketing();check('correction_does_not_reopen_marketing',g.marketing_closed and g.can_invite('safety','revision:1'))
bad=[{'event_id':1,'kind':'budget_changed','before_cents':20000,'after_cents':25000,'authorization_event':99},
     {'event_id':2,'kind':'filter_applied','budget_cents':30000,'prices_cents':[29000]}]
check('independent_auditor_detects_target_rewrite_and_filter_breach',len(audit_events(bad,20000))==2)
report={'input_identity':'Researcher-constructed protocol fixtures','scope':'Engineering acceptance only; not an experiment on consumers or ethical efficacy',
        'checks':results,'check_count':len(results),'new_human_data':False,'autonomy_score_created':False,
        'limits':['Association semantics and genuine user authorization require transcript review.','Trace authenticity and live platform integration are outside this reference implementation.','The one-invitation default is a design setting, not an empirically optimal threshold.']}
(Path(__file__).resolve().parent/'protocol_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'engineering_assertions':len(results),'human_experiment':False,'all_recorded_conditions_met':True},ensure_ascii=False))
