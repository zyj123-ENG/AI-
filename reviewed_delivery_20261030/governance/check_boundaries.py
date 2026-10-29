"""Nine deterministic boundary checks on constructed protocol fixtures.

Run from any working directory: python <path>/governance/check_boundaries.py
The sibling budget_guard.py is the implementation under review. This script
writes boundary_results.json beside itself. It does not edit check_protocol.py
or protocol_results.json and does not generate consumer responses or scores.
"""
from pathlib import Path
import hashlib
import inspect
import json
import sys
from budget_guard import BudgetGuard, audit_events

HERE = Path(__file__).resolve().parent


def prepared():
    g = BudgetGuard(20000)
    g.associate('safety', 'user:2', '主要因此提高到200元', True)
    g.withdraw('safety', 'revision:1', 'source:withdrawal', material_change=True)
    return g


def outcome(fn):
    try:
        return {'accepted': True, 'return': fn()}
    except (ValueError, TypeError, KeyError) as e:
        return {'accepted': False, 'exception': type(e).__name__, 'message': str(e)}


def main():
    checks = []

    def check(check_id, condition, expected, observed, met):
        checks.append({'id': check_id, 'condition': condition, 'expected': expected,
                       'observed': observed, 'condition_met': bool(met)})

    g = prepared()
    g.invite('safety', 'revision:1', '已说明依据变化和预算关联。')
    reset = outcome(lambda: g.withdraw('safety', 'revision:2', 'source:withdrawal', material_change=True))
    can_repeat = g.can_invite('safety', 'revision:2') if ('safety', 'revision:2') in g.revisions else False
    check('P1', '同一reason/source_ref，仅更换revision标签',
          '不重置同一实质证据的邀请计数', {'withdraw': reset, 'second_can_invite': can_repeat}, not can_repeat)

    g = prepared()
    g.set_budget(25000, user_turn='user:3', quote='提高到250元', explicit_authorization=True)
    g.set_budget(15000, user_turn='user:4', quote='现在恢复150元', explicit_authorization=True)
    replay = outcome(lambda: g.set_budget(25000, user_turn='user:3', quote='提高到250元', explicit_authorization=True))
    check('P2', '在后续不同预算授权后重放已使用的user:3',
          '拒绝旧表达重放，保留后来授权的15000分预算',
          {'replayed_call': replay, 'effective_budget_cents': g.effective_budget_cents},
          not replay['accepted'] and g.effective_budget_cents == 15000)

    replay_trace = [
        {'event_id': 1, 'kind': 'user_budget_authorization', 'user_turn': 'user:3',
         'quote': '提高到250元', 'new_budget_cents': 25000},
        {'event_id': 2, 'kind': 'budget_changed', 'before_cents': 20000,
         'after_cents': 25000, 'authorization_event': 1},
        {'event_id': 3, 'kind': 'user_budget_authorization', 'user_turn': 'user:4',
         'quote': '恢复150元', 'new_budget_cents': 15000},
        {'event_id': 4, 'kind': 'budget_changed', 'before_cents': 25000,
         'after_cents': 15000, 'authorization_event': 3},
        {'event_id': 5, 'kind': 'budget_changed', 'before_cents': 15000,
         'after_cents': 25000, 'authorization_event': 1},
    ]
    errors = audit_events(replay_trace, 20000)
    check('P3', '外部事件日志重用已消费的authorization_event',
          '第5事件记录授权重放', {'input_trace': replay_trace, 'audit_errors': errors},
          any(e.get('event_id') == 5 and e.get('issue') == 'authorization_replayed' for e in errors))

    g = prepared()
    g.invite('safety', 'revision:1', '已说明依据变化和预算关联。')
    reaffirm = outcome(lambda: g.reaffirm('safety', 'revision:1', 'user:1', '仍按200元'))
    recorded = g.revisions[('safety', 'revision:1')]['reaffirmation']
    check('P4', '未提供源会话时序复核即用较早user:1记录重申',
          '默认拒绝未复核的重申；不推断真实会话时序或心理理解',
          {'reaffirm_call': reaffirm, 'recorded_reaffirmation': recorded},
          not reaffirm['accepted'] and recorded is None)

    g = prepared()
    g.end()
    update = outcome(lambda: g.set_budget(25000, user_turn='user:5', quote='提高250元', explicit_authorization=True))
    filtered = outcome(lambda: g.candidates([24000]))
    check('P5', '同一实例end后进行普通预算更新和筛选',
          '关闭营销及主动邀请，拒绝已结束任务的普通更新和筛选',
          {'marketing_closed': g.marketing_closed, 'can_invite': g.can_invite('safety', 'revision:1'),
           'budget_update': update, 'candidate_filter': filtered},
          g.marketing_closed and not g.can_invite('safety', 'revision:1')
          and not update['accepted'] and not filtered['accepted'])

    missing_quote = [
        {'event_id': 1, 'kind': 'user_budget_authorization', 'user_turn': 'user:3', 'new_budget_cents': 25000},
        {'event_id': 2, 'kind': 'budget_changed', 'before_cents': 20000,
         'after_cents': 25000, 'authorization_event': 1},
    ]
    errors = audit_events(missing_quote, 20000)
    check('P6', '外部授权记录缺少原话', '记录无匹配授权证据，不能解释为肯定合规',
          {'input_trace': missing_quote, 'audit_errors': errors},
          any(e.get('event_id') == 2 and e.get('issue') == 'budget_changed_without_matching_user_authorization' for e in errors))

    g = prepared()
    g.invite('safety', 'revision:1', '一次提示')
    second = outcome(lambda: g.invite('safety', 'revision:1', '重复'))
    check('C1', '正对照：同一键的第二次主动邀请', '拒绝重复邀请', second, not second['accepted'])
    g = prepared()
    g.end()
    can_invite = g.can_invite('safety', 'revision:1')
    check('C2', '正对照：任务已经结束', '主动邀请关闭', {'can_invite': can_invite}, not can_invite)
    g = BudgetGuard(20000)
    g.associate('safety', 'user:2', '主要因此提高到200元', True)
    g.withdraw('safety', 'revision:1', 'source:withdrawal', material_change=True, gap=False)
    can_invite = g.can_invite('safety', 'revision:1')
    check('C3', '正对照：普通更正已经充分', '不追加预算邀请', {'can_invite': can_invite}, not can_invite)

    # Additional mechanical field checks are reported separately from the nine
    # boundary fixtures and the original sixteen check_protocol assertions.
    g = prepared()
    g.invite('safety', 'revision:1', '已说明依据变化和预算关联。')
    g.reaffirm('safety', 'revision:1', 'user:4', '已看到更正，仍按200元。', after_notice_reviewed=True)
    field_checks = {
        'material_change_default_false': inspect.signature(BudgetGuard.withdraw).parameters['material_change'].default is False,
        'after_notice_reviewed_default_false': inspect.signature(BudgetGuard.reaffirm).parameters['after_notice_reviewed'].default is False,
        'association_quote_logged': any(e['kind'] == 'association_recorded' and e.get('quote') == '主要因此提高到200元' for e in g.events),
        'withdrawal_source_and_conditions_logged': any(e['kind'] == 'reason_withdrawn' and e.get('source_ref') == 'source:withdrawal'
            and e.get('material_change_reviewed') is True and {'important', 'adjustable', 'gap', 'proportionate'} <= set(e) for e in g.events),
        'invitation_text_logged': any(e['kind'] == 'budget_invitation' and e.get('message') == '已说明依据变化和预算关联。' for e in g.events),
        'reaffirmation_quote_and_review_logged': any(e['kind'] == 'user_reaffirmed' and e.get('quote') == '已看到更正，仍按200元。'
            and e.get('source_order_reviewed') is True for e in g.events),
    }
    failures = [c['id'] for c in checks if not c['condition_met']]
    field_failures = [name for name, met in field_checks.items() if not met]
    report = {
        'input_identity': 'Researcher-constructed boundary fixtures; no consumer observations',
        'scope': 'Issue-3 mechanical regression checks on the reference implementation only',
        'implementation_sha256': hashlib.sha256((HERE / 'budget_guard.py').read_bytes()).hexdigest(),
        'check_count': len(checks), 'checks': checks,
        'field_check_count': len(field_checks), 'field_checks': field_checks,
        'failures': failures, 'field_failures': field_failures,
        'new_human_data': False, 'autonomy_score_created': False,
        'random_process': False,
        'limits': [
            'Immutable evidence identity and canonical user event identifiers require a trusted integrating system.',
            'Review flags are upstream attestations; they do not establish genuine source chronology, material facts or user understanding.',
            'These checks do not test consumer autonomy effects, burden, product feasibility, log authenticity or a deployed shopping system.',
            'The original sixteen check_protocol.py assertions remain a separate result set.',
        ],
    }
    (HERE / 'boundary_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'boundary_checks': len(checks), 'field_checks': len(field_checks),
                      'failures': failures, 'field_failures': field_failures,
                      'human_experiment': False}, ensure_ascii=False))
    return 1 if failures or field_failures else 0


if __name__ == '__main__':
    sys.exit(main())
