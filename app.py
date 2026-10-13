"""Launch with: python -m streamlit run app.py"""
import hmac
import html
import json
import math
import os
from datetime import datetime, timezone
import streamlit as st
from core import ROOT, settings, prepare, generate, score
from demo import sample_report

st.set_page_config(page_title='AI Strategy Copilot', page_icon='💡', layout='wide')

STRATEGY_BANNER = '''<style>
.strategy-banner{--ink:#0b0b0b;--muted:#898781;--baseline:#c3c2b7;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a}
@media (prefers-color-scheme: dark){.strategy-banner{--ink:#f0efec;--baseline:#383835;--s1:#3987e5;--s2:#d95926;--s3:#199e70}}
.strategy-banner svg{width:100%;height:auto;max-height:112px;display:block;margin-top:10px}
</style>
<div class="strategy-banner" role="img" aria-label="Three strategy options rising toward a shared growth target">
<svg viewBox="0 0 360 96" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <line x1="24" y1="80" x2="252" y2="80" stroke="var(--baseline)" stroke-width="2"/>
  <path d="M48 80 V60 a4 4 0 0 1 4 -4 h18 a4 4 0 0 1 4 4 V80 Z" fill="var(--s1)"/>
  <path d="M104 80 V48 a4 4 0 0 1 4 -4 h18 a4 4 0 0 1 4 4 V80 Z" fill="var(--s2)"/>
  <path d="M160 80 V28 a4 4 0 0 1 4 -4 h18 a4 4 0 0 1 4 4 V80 Z" fill="var(--s3)"/>
  <circle cx="308" cy="44" r="17" fill="none" stroke="var(--muted)" stroke-width="2.5"/>
  <circle cx="308" cy="44" r="9" fill="none" stroke="var(--muted)" stroke-width="2.5"/>
  <path d="M36 70 C 120 62, 210 54, 295 44" fill="none" stroke="var(--ink)" stroke-width="2.5" stroke-linecap="round"/>
  <polygon points="308,44 294,38 294,50" fill="var(--ink)"/>
</svg>
</div>'''

def secret(name, fallback=''):
    try:
        return str(st.secrets.get(name, fallback))
    except FileNotFoundError:
        return fallback

config = settings()
for key in ('OPENAI_API_KEY', 'OPENAI_MODEL'):
    config[key] = secret(key, config[key])
password = secret('APP_PASSWORD', os.environ.get('APP_PASSWORD', ''))

hero_text, hero_graphic = st.columns([2.4, 1])
with hero_text:
    st.title('AI Strategy Copilot')
    st.caption('WHU hackathon practice · Evidence-backed growth experiments')
with hero_graphic:
    st.markdown(STRATEGY_BANNER, unsafe_allow_html=True)
if password:
    with st.sidebar:
        st.text_input('App password', type='password', key='access_password')
    if not hmac.compare_digest(st.session_state.get('access_password', '').encode(), password.encode()):
        st.info('Enter the app password in the sidebar to continue.')
        st.stop()

DEFAULTS = json.loads((ROOT / 'sample_data.json').read_text(encoding='utf-8'))
FIELDS = list(DEFAULTS)
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, float(value) if key == 'budget' else value)
st.session_state.setdefault('runs', [])

def reset():
    for key, value in DEFAULTS.items():
        st.session_state[key] = float(value) if key == 'budget' else value

def show_claims(claims, evidence):
    for claim in claims:
        st.write(f"{claim['kind'].upper()}: {claim['text']}")
        if claim['sources']:
            with st.expander('Sources: ' + ', '.join(claim['sources'])):
                for source in claim['sources']:
                    st.text(f'[{source}] {evidence[source]}')

def bullets(items):
    if not items:
        st.caption('None identified.')
    for item in items:
        st.write('• ' + item)

VIZ_VARS = '''<style>
.svz{--ink:#0b0b0b;--muted:#898781;--grid:#e1e0d9;--gray:#c3c2b7;--red:#d03b3b;
--blue:#2a78d6;--orange:#eb6834;--aqua:#1baf7a}
@media (prefers-color-scheme: dark){.svz{--ink:#f0efec;--grid:#2c2c2a;--gray:#383835;
--blue:#3987e5;--orange:#d95926;--aqua:#199e70}}
.svz svg{width:100%;height:auto;display:block}
.svz text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif}
</style>'''

def nice_step(raw):
    raw = raw or 1.0
    exp = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * exp >= raw:
            return m * exp
    return 10 * exp

def eur_short(v):
    if v >= 1_000_000:
        return f"€{v/1_000_000:.1f}M".replace('.0M', 'M')
    if v >= 10_000:
        return f"€{v/1_000:.0f}k"
    return f"€{v:,.0f}"

def short_name(text, limit=26):
    return html.escape(text if len(text) <= limit else text[:limit-1] + '…')

def svg_row_chart(rows, max_x, ticks, fmt=lambda v: f'{v:g}', budget=None, budget_label=''):
    top = 26 if budget is not None else 10
    row_h, x0, plot_w, bottom = 46, 196, 384, 24
    h = top + row_h * len(rows) + bottom
    p = [f'<svg viewBox="0 0 640 {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    for t in ticks:
        x = x0 + t / max_x * plot_w
        p.append(f'<line x1="{x:.0f}" y1="{top}" x2="{x:.0f}" y2="{h-bottom}" stroke="var(--grid)" stroke-width="1"/>')
        p.append(f'<text x="{x:.0f}" y="{h-7}" text-anchor="middle" font-size="11" fill="var(--muted)">{fmt(t)}</text>')
    for i, row in enumerate(rows):
        cy = top + i * row_h + 23
        w = max(row['value'] / max_x * plot_w, 8)
        lx = x0 + w + 8
        weight = 600 if row.get('bold') else 400
        p.append(f'<text x="8" y="{cy+4}" font-size="13" font-weight="{weight}" fill="var(--ink)">{short_name(row["name"])}</text>')
        p.append(f'<path d="M{x0} {cy-9} h{w-4:.1f} a4 4 0 0 1 4 4 v10 a4 4 0 0 1 -4 4 h-{w-4:.1f} z" fill="var(--{row["color"]})"/>')
        p.append(f'<text x="{lx:.0f}" y="{cy+4}" font-size="12" font-weight="600" fill="var(--ink)">{row["label"]}</text>')
        if row.get('tag'):
            p.append(f'<text x="{lx:.0f}" y="{cy-9}" font-size="10" fill="var(--muted)">{row["tag"]}</text>')
    if budget is not None:
        bx = x0 + min(budget, max_x) / max_x * plot_w
        anchor = 'start' if bx < 480 else 'end'
        px = bx + 4 if anchor == 'start' else bx - 4
        p.append(f'<line x1="{bx:.0f}" y1="{top-4}" x2="{bx:.0f}" y2="{h-bottom}" stroke="var(--ink)" stroke-width="1.5" stroke-dasharray="5 4"/>')
        p.append(f'<text x="{px:.0f}" y="{top-8}" text-anchor="{anchor}" font-size="11" font-weight="600" fill="var(--ink)">{html.escape(budget_label)}</text>')
    p.append('</svg>')
    return ''.join(p)

def svg_component_chart(options, rec_id):
    x0, plot_w, max_x = 8, 500, 5
    top, name_h, row_h, gap = 26, 24, 17, 14
    h = top + len(options) * (name_h + 3 * row_h + gap)
    p = [f'<svg viewBox="0 0 640 {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    for j, (label, color) in enumerate((('Impact', 'blue'), ('Feasibility', 'orange'), ('Evidence', 'aqua'))):
        p.append(f'<rect x="{8 + j*140}" y="2" width="11" height="11" rx="3" fill="var(--{color})"/>')
        p.append(f'<text x="{24 + j*140}" y="12" font-size="11" fill="var(--muted)">{label}</text>')
    y = top
    for o in options:
        weight = 600 if o['id'] == rec_id else 400
        p.append(f'<text x="8" y="{y+14}" font-size="13" font-weight="{weight}" fill="var(--ink)">{short_name(o["name"])}</text>')
        y += name_h
        for key, color in (('impact_score', 'blue'), ('feasibility_score', 'orange'), ('evidence_score', 'aqua')):
            v = float(o[key])
            w = max(v / max_x * plot_w, 6)
            p.append(f'<path d="M{x0} {y} h{w-4:.1f} a4 4 0 0 1 4 4 v2 a4 4 0 0 1 -4 4 h-{w-4:.1f} z" fill="var(--{color})"/>')
            p.append(f'<text x="{x0+w+7:.0f}" y="{y+9}" font-size="11" font-weight="600" fill="var(--ink)">{v:g}</text>')
            y += row_h
        y += gap
    p.append('</svg>')
    return ''.join(p)

with st.sidebar:
    st.header('Analysis settings')
    demo = st.checkbox('Offline sample mode', value=False)
    st.caption('Offline mode uses the original scenario with editable budget. Live AI analyses all edits.')
    st.write('Model: ' + config['OPENAI_MODEL'])
    st.caption('API key configured' if config['OPENAI_API_KEY'].strip() else 'No API key: use offline mode or configure secrets.')
    st.button('Reset fictional example', on_click=reset)
    st.caption('Live mode sends the entered evidence to OpenAI. History is kept only in your current session.')

st.subheader('1. Define the decision')
st.text_area('Business goal', key='goal', max_chars=16000, height=90)
a, b = st.columns([1, 2])
with a:
    st.number_input('Available pilot budget (€)', min_value=0.0, max_value=10000000.0, step=50.0, key='budget')
with b:
    st.text_area('Operational constraints', key='constraints', max_chars=16000, height=100)
st.subheader('2. Edit your evidence')
st.caption('All defaults are fictional. Each nonempty line receives a source ID: B = brief, F = feedback, C = competitors, U = constraints.')
with st.expander('Company brief', expanded=True):
    st.text_area('Edit company brief', key='brief', height=260, max_chars=16000)
with st.expander('Customer feedback', expanded=True):
    st.text_area('One customer comment per line', key='feedback', height=240, max_chars=16000)
with st.expander('Competitor notes', expanded=True):
    st.text_area('One observation per line', key='competitors', height=150, max_chars=16000)
inputs = {key: st.session_state[key] for key in FIELDS}
if st.button('Compare strategies', type='primary'):
    try:
        context = prepare(inputs)
        if demo and any(inputs[k] != DEFAULTS[k] for k in FIELDS if k != 'budget'):
            raise ValueError('Offline mode supports the original fictional scenario and budget changes only. Reset the example or use live AI.')
        with st.spinner('Comparing options and building the experiment. Live mode uses two API calls; allow up to four minutes.'):
            report = sample_report(context) if demo else generate(context, config)
        run = dict(report=report, context=context, inputs=inputs.copy(), demo=demo,
                   model='Offline sample' if demo else config['OPENAI_MODEL'],
                   time=datetime.now(timezone.utc).isoformat())
        st.session_state.runs = (st.session_state.runs + [run])[-5:]
        st.session_state.selected_run = len(st.session_state.runs) - 1
        st.success('Report ready. Source IDs and budget arithmetic passed validation.')
    except ValueError as error:
        st.error(str(error))
    except Exception:
        st.error('Unexpected analysis error. Check your configuration and retry. Previous reports are retained.')

runs = st.session_state.runs
if runs:
    st.divider()
    st.subheader('3. Decision brief')
    def run_label(i):
        r = runs[i]
        winner = next(o for o in r['report']['options'] if o['id'] == r['report']['recommended_id'])
        return f"Run {i+1} · €{r['context']['budget']:,.2f} · {winner['name']} · {r['time']}"
    selected = st.selectbox('View a report', range(len(runs)), format_func=run_label, key='selected_run')
    run = runs[selected]
    r, evidence = run['report'], run['context']['evidence']
    if inputs != run['inputs']:
        st.warning('Inputs have changed since this report. Click Compare strategies to generate an updated report.')
    st.caption(('OFFLINE SCRIPTED SAMPLE — not AI analysis' if run['demo'] else 'LIVE AI · '+run['model']) + ' · ' + run['time'])
    st.write('Goal for this report: ' + run['inputs']['goal'])
    st.download_button('Download report (.json)', data=json.dumps(run, ensure_ascii=False, indent=2),
                       file_name='strategy-report.json', mime='application/json')
    overview, visuals_tab, experiment_tab, evidence_tab, history_tab = st.tabs(['Strategy comparison', 'Strategy visuals', '30-day experiment', 'Evidence and uncertainty', 'Compare runs'])
    winner = next(o for o in r['options'] if o['id'] == r['recommended_id'])
    with overview:
        st.subheader('Situation')
        show_claims(r['situation'], evidence)
        st.subheader('Three strategies')
        st.caption('Scores 1–5. Weighted score: 40% impact + 35% feasibility + 25% evidence. Python selects the highest-scoring affordable option; original order breaks ties.')
        st.dataframe([{'Strategy':o['name'], 'Pilot cost estimate (€)':o['cost_eur'],
                       'Staff hours estimate':o['effort_hours'], 'Impact':o['impact_score'],
                       'Feasibility':o['feasibility_score'], 'Evidence':o['evidence_score'],
                       'Weighted score':score(o), 'Within budget':o['cost_eur'] <= run['context']['budget'],
                       'Recommended':o['id'] == r['recommended_id']} for o in r['options']], use_container_width=True, hide_index=True)
        st.subheader('Recommendation: ' + winner['name'])
        st.write(r['recommendation'])
        for o in r['options']:
            with st.expander(o['name'] + ' — details'):
                st.write(o['action'])
                show_claims(o['evidence'], evidence)
                st.write('Estimated cost basis: ' + o['cost_basis'])
                st.write('Potential impact (estimate): ' + o['impact_estimate'])
                st.write('Score rationale: ' + o['score_rationale'])
                st.write('Trade-offs'); bullets(o['tradeoffs'])
                st.write('Risks'); bullets(o['risks'])
    with visuals_tab:
        st.caption('The comparison table drawn as charts. Bars start at zero; the recommended strategy is highlighted.')
        st.subheader('Weighted score by strategy')
        st.markdown(VIZ_VARS + '<div class="svz">' + svg_row_chart(
            [{'name':o['name'], 'value':score(o), 'label':f'{score(o):.2f}',
              'color':'blue' if o['id']==r['recommended_id'] else 'gray',
              'bold':o['id']==r['recommended_id'],
              'tag':'recommended' if o['id']==r['recommended_id'] else ''} for o in r['options']],
            5, [0,1,2,3,4,5]) + '</div>', unsafe_allow_html=True)
        st.subheader('Pilot cost vs available budget')
        budget_val = run['context']['budget']
        step = nice_step(max([o['cost_eur'] for o in r['options']] + [budget_val]) / 4)
        st.markdown('<div class="svz">' + svg_row_chart(
            [{'name':o['name'], 'value':o['cost_eur'], 'label':eur_short(o['cost_eur']),
              'color':'aqua' if o['cost_eur'] <= budget_val else 'red',
              'bold':o['id']==r['recommended_id'],
              'tag':'within budget' if o['cost_eur'] <= budget_val else 'over budget'} for o in r['options']],
            step*4, [step*i for i in range(5)], fmt=eur_short,
            budget=budget_val, budget_label='Budget ' + eur_short(budget_val)) + '</div>', unsafe_allow_html=True)
        st.subheader('What drives the score')
        st.caption('Component scores 1–5. Weighted score = 40% impact + 35% feasibility + 25% evidence.')
        st.markdown('<div class="svz">' + svg_component_chart(r['options'], r['recommended_id']) + '</div>', unsafe_allow_html=True)
    with experiment_tab:
        exp = r['experiment']
        total = round(sum(c['amount_eur'] for c in exp['costs']), 2)
        cols = st.columns(3)
        cols[0].metric('Available budget', f"€{run['context']['budget']:,.2f}")
        cols[1].metric('Experiment cost estimate', f'€{total:,.2f}')
        cols[2].metric('Unallocated budget', f"€{run['context']['budget']-total:,.2f}")
        st.subheader(exp['title']); st.write('Hypothesis: ' + exp['hypothesis'])
        st.dataframe(exp['steps'], use_container_width=True, hide_index=True)
        st.write('Itemised estimated spending')
        st.dataframe(exp['costs'], use_container_width=True, hide_index=True)
        for label, key in [('Metric','metric'),('Baseline','baseline'),('Success threshold','success_threshold'),('Measurement method','measurement_method')]:
            st.write(label + ': ' + exp[key])
        st.warning('Stop condition: ' + exp['stop_condition'])
    with evidence_tab:
        st.subheader('Missing information'); bullets(r['missing_information'])
        st.subheader('Conflicting evidence')
        show_claims(r['contradictions'], evidence)
        if not r['contradictions']: st.caption('No contradictions identified by the model.')
        st.subheader('What could change the decision?'); bullets(r['decision_changes'])
        st.subheader('Source snapshot')
        st.caption('IDs are checked automatically, but semantic support and feasibility still need human review.')
        for source, text in evidence.items(): st.text(f'[{source}] {text}')
    with history_tab:
        st.caption('Last five runs in this session. Download reports to preserve them before closing or refreshing.')
        st.dataframe([{'Run':i+1, 'Budget (€)':x['context']['budget'], 'Goal':x['inputs']['goal'],
                       'Recommended':next(o['name'] for o in x['report']['options'] if o['id']==x['report']['recommended_id'])}
                      for i,x in enumerate(runs)], use_container_width=True, hide_index=True)
        if len(runs)>1:
            left=st.selectbox('Compare from',range(len(runs)),index=len(runs)-2,format_func=run_label)
            right=st.selectbox('Compare to',range(len(runs)),index=len(runs)-1,format_func=run_label)
            changed=[k for k in FIELDS if runs[left]['inputs'][k]!=runs[right]['inputs'][k]]
            st.write('Changed inputs: ' + (', '.join(changed) or 'None. AI responses can vary between runs.'))
            for k in changed:
                with st.expander(k):
                    st.write('Before'); st.text(str(runs[left]['inputs'][k]))
                    st.write('After'); st.text(str(runs[right]['inputs'][k]))

st.divider()
st.caption('Practice decision support. Costs, scores and outcomes are estimates. Review evidence and feasibility before acting.')
