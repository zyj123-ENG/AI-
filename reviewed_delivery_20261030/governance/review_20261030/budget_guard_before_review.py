"""Reference budget-state guard, not a consumer-behaviour model or deployed AI.

Input associations require transcript-grounded review by the integrating system.
Money uses integer cents. No latent psychological state is inferred.
"""
from dataclasses import dataclass, field
import json

@dataclass
class BudgetGuard:
    effective_budget_cents: int
    max_proactive_invites: int = 1
    ended: bool = False
    marketing_closed: bool = False
    associations: dict = field(default_factory=dict)
    revisions: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

    def _record(self, kind, **data):
        item={'event_id':len(self.events)+1,'kind':kind,**data}
        self.events.append(item)
        return item['event_id']

    def associate(self, reason_id, user_turn, quote, reviewed_explicit):
        if not user_turn or not quote or not reviewed_explicit:
            raise ValueError('An association requires reviewed explicit user wording and a turn locator.')
        self.associations[reason_id]={'user_turn':user_turn,'quote':quote}
        self._record('association_recorded',reason_id=reason_id,user_turn=user_turn)

    def correct_association(self, reason_id):
        self.associations.pop(reason_id,None)
        self._record('association_corrected',reason_id=reason_id)

    def withdraw(self, reason_id, revision, source_ref, *, important=True, adjustable=True, gap=True, proportionate=True, material_change=True):
        key=(reason_id,revision)
        if key in self.revisions:
            return  # Rephrasing cannot reset the same episode's invitation counter.
        if not source_ref or not material_change:
            raise ValueError('A new episode requires a material evidence change and a source locator.')
        self.revisions[key]={'source_ref':source_ref,'important':important,'adjustable':adjustable,
            'gap':gap,'proportionate':proportionate,'invites':0,'notice_event':None,'reaffirmation':None}
        self._record('reason_withdrawn',reason_id=reason_id,revision=revision,budget_cents=self.effective_budget_cents)

    def can_invite(self, reason_id, revision):
        r=self.revisions[(reason_id,revision)]
        return (not self.ended and reason_id in self.associations and r['important'] and
            r['adjustable'] and r['gap'] and r['proportionate'] and r['reaffirmation'] is None and
            r['invites']<self.max_proactive_invites)

    def invite(self, reason_id, revision, message):
        if not self.can_invite(reason_id,revision):raise ValueError('No remaining basis for this proactive budget invitation.')
        r=self.revisions[(reason_id,revision)];r['invites']+=1
        r['notice_event']=self._record('budget_invitation',reason_id=reason_id,revision=revision,
            message_characters=len(message),effective_budget_cents=self.effective_budget_cents)
        return r['notice_event']

    def reaffirm(self, reason_id, revision, user_turn, quote):
        r=self.revisions[(reason_id,revision)]
        if not r['notice_event'] or not user_turn or not quote:raise ValueError('Record the prior notice and explicit later user expression.')
        r['reaffirmation']={'user_turn':user_turn,'quote':quote,'notice_event':r['notice_event']}
        self._record('user_reaffirmed',reason_id=reason_id,revision=revision,user_turn=user_turn,
            notice_event=r['notice_event'])

    def set_budget(self, cents, *, user_turn=None, quote=None, explicit_authorization=False):
        if not isinstance(cents,int) or cents<0:raise ValueError('Budget must be nonnegative integer cents.')
        if not explicit_authorization or not user_turn or not quote:raise ValueError('No effective budget update without explicit user authorization.')
        auth=self._record('user_budget_authorization',user_turn=user_turn,quote=quote,new_budget_cents=cents)
        before=self.effective_budget_cents;self.effective_budget_cents=cents
        self._record('budget_changed',before_cents=before,after_cents=cents,authorization_event=auth)

    def candidates(self, prices_cents, *, conditional_preview=False):
        if conditional_preview:
            self._record('conditional_preview',effective_budget_cents=self.effective_budget_cents)
            return list(prices_cents)
        selected=[x for x in prices_cents if x<=self.effective_budget_cents]
        self._record('filter_applied',budget_cents=self.effective_budget_cents,prices_cents=selected)
        return selected

    def close_marketing(self):
        self.marketing_closed=True;self._record('marketing_closed')

    def end(self):
        self.ended=True;self._record('task_ended')

def audit_events(events,initial_budget_cents):
    """Check observable budget transitions; correctness also requires authentic logs."""
    budget=initial_budget_cents;authorizations={};errors=[]
    for e in events:
        if e['kind']=='user_budget_authorization':authorizations[e['event_id']]=e
        elif e['kind']=='budget_changed':
            auth=authorizations.get(e.get('authorization_event'))
            if not auth or auth.get('new_budget_cents')!=e['after_cents'] or not auth.get('user_turn'):
                errors.append({'event_id':e['event_id'],'issue':'budget_changed_without_matching_user_authorization'})
            if e['before_cents']!=budget:errors.append({'event_id':e['event_id'],'issue':'budget_history_inconsistent'})
            budget=e['after_cents']
        elif e['kind']=='filter_applied':
            if e['budget_cents']!=budget or any(p>budget for p in e['prices_cents']):
                errors.append({'event_id':e['event_id'],'issue':'filter_exceeds_effective_budget'})
    return errors

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('trace');ap.add_argument('--initial-budget-cents',type=int,required=True)
    a=ap.parse_args()
    with open(a.trace,encoding='utf-8') as f:events=json.load(f)
    errors=audit_events(events,a.initial_budget_cents)
    print(json.dumps({'errors':errors,'scope':'Observable budget-state audit only'},ensure_ascii=False))
    raise SystemExit(bool(errors))
