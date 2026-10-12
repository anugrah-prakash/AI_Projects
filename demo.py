"""Deterministic sample report, explicitly not an AI analysis of arbitrary inputs."""
from core import score, validate

def sample_report(context):
    budget = context['budget']
    def claim(text, kind='assumption', sources=None):
        return dict(text=text, kind=kind, sources=sources or [])
    names = [('pickup', 'Office lunch pickup', 700, 4, 3, 3),
             ('loyalty', 'Paper loyalty pilot', 200, 3, 5, 3),
             ('ads', 'Local advertising test', 500, 3, 3, 2)]
    options = []
    for ident, name, cost, impact, feasibility, evidence in names:
        options.append(dict(id=ident, name=name, action={
            'pickup':'Test preorders with one nearby office, customer collection only; cap orders at spare capacity.',
            'loyalty':'Offer a paper stamp card to a small cohort and record repeat visits.',
            'ads':'Run one locally targeted creative and track redemptions using a unique code.'}[ident],
            evidence=[claim('Some customers ask for rewards.', 'fact', ['F4','F15'])] if ident == 'loyalty' else
                     [claim('Demand needs validation with a small pilot.')],
            cost_eur=cost, cost_basis='Illustrative pilot allowance; validate costs before spending.',
            effort_hours=12, impact_estimate='Unvalidated hypothesis: incremental weekday orders; no forecast supplied.',
            impact_score=impact, feasibility_score=feasibility, evidence_score=evidence,
            score_rationale='Illustrative scores for rehearsal, not model-generated conclusions.',
            tradeoffs=['Consumes existing staff time.'], risks=['Demand may not convert into repeat purchases.']))
    if budget < 200:
        options[1].update(name='No-cash repeat-visit discovery', cost_eur=0,
            action='Interview ten existing customers and manually track repeat visits using existing materials.',
            cost_basis='Zero incremental cash assumed; existing staff and supplies only.', impact_score=2)
    winner = max((o for o in options if o['cost_eur'] <= budget), key=score)
    report = dict(situation=[claim('The café lacks a repeat-customer baseline.', 'fact', ['B9'])], options=options,
        recommended_id=winner['id'], recommendation='Start with the affordable repeat-visit pilot. Validate demand before expanding.',
        missing_information=['Repeat-visit baseline.', 'Actual reward redemption costs and incremental sales.'],
        contradictions=[claim('A customer thinks delivery exists, while the brief says there is no driver or vehicle.', 'fact', ['F18','B7'])],
        decision_changes=['Verified office demand and spare staffing could make pickup catering more attractive.',
                          'Change to live AI mode to analyse arbitrary edits and constraints.'],
        experiment=dict(title=winner['name']+' — 30-day experiment',
            hypothesis='A simple repeat-visit intervention may increase weekday purchase frequency.',
            steps=[dict(days='1–7',action='Record baseline repeat visits and interview ten customers.',owner='Owner'),
                   dict(days='8–21',action=winner['action'],owner='Counter team'),
                   dict(days='22–30',action='Compare repeat visits and contribution after rewards against baseline.',owner='Owner')],
            costs=[dict(item='Illustrative all-in pilot allowance, including rewards and materials', amount_eur=winner['cost_eur'])],
            metric='Repeat purchases per enrolled customer per week',baseline='Unknown; measure on days 1–7.',
            success_threshold='At least 10% more repeat purchases per enrolled customer than baseline, with positive incremental contribution.',
            measurement_method='Keep a pseudonymous tally and subtract incremental ingredient, reward and material costs. Small sample; do not claim causality.',
            stop_condition='Stop at the cash cap, or earlier if service delays increase by more than five minutes for three days.'))
    return validate(report, context)
