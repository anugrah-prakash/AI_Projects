"""Launch with: python -m streamlit run app.py"""
import hmac
import json
import os
from datetime import datetime, timezone
import streamlit as st
from core import ROOT, settings, prepare, generate, score
from demo import sample_report

st.set_page_config(page_title='AI Strategy Copilot', page_icon='💡', layout='wide')

def secret(name, fallback=''):
    try:
        return str(st.secrets.get(name, fallback))
    except FileNotFoundError:
        return fallback

config = settings()
for key in ('OPENAI_API_KEY', 'OPENAI_MODEL'):
    config[key] = secret(key, config[key])
password = secret('APP_PASSWORD', os.environ.get('APP_PASSWORD', ''))

st.title('AI Strategy Copilot')
st.caption('WHU hackathon practice · Evidence-backed growth experiments')
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
    overview, experiment_tab, evidence_tab, history_tab = st.tabs(['Strategy comparison', '30-day experiment', 'Evidence and uncertainty', 'Compare runs'])
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
