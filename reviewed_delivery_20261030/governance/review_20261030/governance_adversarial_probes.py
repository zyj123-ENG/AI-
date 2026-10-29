"""Read-only governance boundary probes; fixtures are constructed, not consumers.

Default audits the frozen pre-review source snapshot beside this script.
Optional --module path can point to the corrected implementation for re-check.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--module',type=Path,default=HERE/'budget_guard_before_review.py')
ap.add_argument('--output',type=Path,default=HERE/'governance_adversarial_observations_before.json')
args=ap.parse_args()
spec=importlib.util.spec_from_file_location('guard_under_review',args.module)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

def prepared():
    g=m.BudgetGuard(20000)
    g.associate('safety','user:2','主要因此提高到200元',True)
    g.withdraw('safety','revision:1','source:withdrawal',material_change=True)
    return g

def outcome(fn):
    try:return {'accepted':True,'return':fn()}
    except (ValueError,TypeError,KeyError) as e:return {'accepted':False,'exception':type(e).__name__,'message':str(e)}

observations=[]
g=prepared();g.invite('safety','revision:1','已说明依据变化和预算关联。')
r=outcome(lambda:g.withdraw('safety','revision:2','source:withdrawal',material_change=True))
observations.append({'id':'P1','condition':'Same reason and source locator, only revision label changed after one invitation',
    'expected':'Reject reset, or carry previous invitation counter; source version/evidence identity must be reviewed outside the guard',
    'withdraw':r,'second_can_invite':g.can_invite('safety','revision:2') if ('safety','revision:2') in g.revisions else False})

g=prepared();g.set_budget(25000,user_turn='user:3',quote='提高到250元',explicit_authorization=True)
g.set_budget(15000,user_turn='user:4',quote='现在恢复150元',explicit_authorization=True)
r=outcome(lambda:g.set_budget(25000,user_turn='user:3',quote='提高到250元',explicit_authorization=True))
observations.append({'id':'P2','condition':'Replay an already used explicit user turn after a later different budget authorization',
    'expected':'Old turn must not override the later command without new authorization',
    'replayed_call':r,'effective_budget_cents':g.effective_budget_cents})

replay_trace=[
 {'event_id':1,'kind':'user_budget_authorization','user_turn':'user:3','quote':'提高到250元','new_budget_cents':25000},
 {'event_id':2,'kind':'budget_changed','before_cents':20000,'after_cents':25000,'authorization_event':1},
 {'event_id':3,'kind':'user_budget_authorization','user_turn':'user:4','quote':'恢复150元','new_budget_cents':15000},
 {'event_id':4,'kind':'budget_changed','before_cents':25000,'after_cents':15000,'authorization_event':3},
 {'event_id':5,'kind':'budget_changed','before_cents':15000,'after_cents':25000,'authorization_event':1},
]
observations.append({'id':'P3','condition':'External trace reuses consumed authorization_event to restore a superseded target',
    'expected':'Flag consumed/stale authorization at event 5','input_trace':replay_trace,
    'auditor_result':m.audit_events(replay_trace,20000)})

g=prepared();notice=g.invite('safety','revision:1','已说明依据变化和预算关联。')
r=outcome(lambda:g.reaffirm('safety','revision:1','user:1','仍按200元'))
observations.append({'id':'P4','condition':'Call reaffirm after sending notice, but reference an earlier transcript user turn',
    'expected':'Canonical transcript order is needed to prove a later expression; function-call order alone is insufficient',
    'reaffirm_call':r,'notice_event':notice,'recorded_reaffirmation':g.revisions[('safety','revision:1')]['reaffirmation'],
    'interpretation':'This is a documented upstream transcript-validation boundary unless the interface claims to enforce source chronology.'})

g=prepared();g.end()
mut=outcome(lambda:g.set_budget(25000,user_turn='user:5',quote='提高250元',explicit_authorization=True))
filtered=outcome(lambda:g.candidates([24000]))
observations.append({'id':'P5','condition':'Request normal budget update/filter after end in the same guard instance',
    'expected':'Either reject closed-task operations or clearly require the integrating controller to block them; renewed user request belongs to a separately opened task',
    'ended':g.ended,'can_invite':g.can_invite('safety','revision:1'),'marketing_closed':g.marketing_closed,
    'budget_update':mut,'candidate_filter':filtered,
    'interpretation':('Proactive invitation stops; broader closure is not enforced by these methods.'
        if mut['accepted'] or filtered['accepted'] else
        'Closed-task budget/filter gates are enforced; risk notification handling remains separate.')})

missing_quote=[
 {'event_id':1,'kind':'user_budget_authorization','user_turn':'user:3','new_budget_cents':25000},
 {'event_id':2,'kind':'budget_changed','before_cents':20000,'after_cents':25000,'authorization_event':1},
]
observations.append({'id':'P6','condition':'External authorization record has turn label but no quote or source pointer to verify scope',
    'expected':'Flag insufficient authorization evidence rather than treating the trace as affirmatively compliant',
    'input_trace':missing_quote,'auditor_result':m.audit_events(missing_quote,20000),
    'interpretation':'Trace authenticity stays external, but required evidence-field completeness can be checked mechanically.'})

g=prepared();g.invite('safety','revision:1','一次提示')
observations.append({'id':'C1','condition':'Positive control: unchanged key after first invitation','second_invite':outcome(lambda:g.invite('safety','revision:1','重复'))})
g=prepared();g.end()
observations.append({'id':'C2','condition':'Positive control: task ended','can_invite':g.can_invite('safety','revision:1')})
g=m.BudgetGuard(20000);g.associate('safety','user:2','主要因此提高到200元',True)
g.withdraw('safety','revision:1','source:withdrawal',material_change=True,gap=False)
observations.append({'id':'C3','condition':'Positive control: ordinary correction already sufficient','can_invite':g.can_invite('safety','revision:1')})

report={'input_identity':'Researcher-constructed adversarial fixtures; no consumer response or autonomy score',
 'source_name':args.module.name,'source_sha256':hashlib.sha256(args.module.read_bytes()).hexdigest(),
 'scope':'Read-only issue-3 reference implementation audit; statistical analysis and manuscript chapters 1-3 untouched',
 'observations':observations}
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'source':args.module.name,'source_sha256':report['source_sha256'],'observations':len(observations),'output':args.output.name},ensure_ascii=False))
