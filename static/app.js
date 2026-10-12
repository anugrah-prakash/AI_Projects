'use strict';
const $ = id => document.getElementById(id);
const fields = ['goal','budget','constraints','brief','feedback','competitors'];
let defaults, runs = [], selected = null;
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const eur = value => new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR'}).format(value);
const score = o => (o.impact_score*.4+o.feasibility_score*.35+o.evidence_score*.25).toFixed(2);
const list = items => items.length ? '<ul>'+items.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>' : '<p class="muted">None identified.</p>';
const read = () => Object.fromEntries(fields.map(k=>[k,k==='budget'?Number($(k).value):$(k).value]));
const claims = items => items.map(c=>`<p><span class="badge ${esc(c.kind)}">${esc(c.kind)}</span>${esc(c.text)} ${c.sources.map(s=>`<a href="#source-${esc(s)}">[${esc(s)}]</a>`).join(' ')}</p>`).join('');
function fill(){fields.forEach(k=>$(k).value=defaults[k]); markStale();}
function markStale(){if(selected) $('stale').hidden=JSON.stringify(read())===JSON.stringify(selected.inputs);}
fields.forEach(k=>$(k).addEventListener('input',markStale));
$('reset').onclick=fill;
function render(run){
 selected=run; const r=run.report, e=r.experiment;
 const winner=r.options.find(o=>o.id===r.recommended_id);
 const total=e.costs.reduce((s,c)=>s+c.amount_eur,0);
 $('results').hidden=false;
 $('runlabel').textContent=`${run.demo?'OFFLINE SAMPLE — scripted illustration, not AI analysis':'LIVE AI · '+run.model} · ${run.time} · Goal: ${run.inputs.goal}`;
 $('report').innerHTML=`<div class="card"><h3>Situation</h3>${claims(r.situation)}</div>
 <div class="card"><h3>Compare three strategies</h3><p class="muted">Scores: 1 = weak, 5 = strong. Weighted score = 40% impact + 35% feasibility + 25% evidence. Only affordable options can win. Scores are model judgments, not measured probabilities.</p><div class="table-wrap"><table><thead><tr><th>Strategy</th><th>Pilot cost (estimate)</th><th>Staff hours (estimate)</th><th>Impact / Feasibility / Evidence</th><th>Weighted score</th><th>Budget fit</th></tr></thead><tbody>${r.options.map(o=>`<tr><td>${o.id===r.recommended_id?'★ ':''}${esc(o.name)}</td><td>${eur(o.cost_eur)}</td><td>${esc(o.effort_hours)}</td><td>${o.impact_score} / ${o.feasibility_score} / ${o.evidence_score}</td><td>${score(o)}</td><td>${o.cost_eur<=run.context.budget?'Within budget':'Over budget'}</td></tr>`).join('')}</tbody></table></div>
 ${r.options.map(o=>`<details><summary>${esc(o.name)} — evidence and trade-offs</summary><p>${esc(o.action)}</p>${claims(o.evidence)}<p><b>Estimated cost basis:</b> ${esc(o.cost_basis)}</p><p><b>Potential impact — estimate:</b> ${esc(o.impact_estimate)}</p><p><b>Score rationale:</b> ${esc(o.score_rationale)}</p><b>Trade-offs</b>${list(o.tradeoffs)}<b>Risks</b>${list(o.risks)}</details>`).join('')}</div>
 <div class="card"><span class="eyebrow">RECOMMENDED EXPERIMENT</span><h2>${esc(winner.name)}</h2><p>${esc(r.recommendation)}</p><div class="metrics"><div class="metric">${eur(run.context.budget)}<small>Available budget</small></div><div class="metric">${eur(total)}<small>Estimated experiment cost</small></div><div class="metric">${eur(run.context.budget-total)}<small>Unallocated budget</small></div></div></div>
 <div class="card"><h3>${esc(e.title)}</h3><p><b>Hypothesis:</b> ${esc(e.hypothesis)}</p><div class="table-wrap"><table><thead><tr><th>Days</th><th>Action</th><th>Owner</th></tr></thead><tbody>${e.steps.map(s=>`<tr><td>${esc(s.days)}</td><td>${esc(s.action)}</td><td>${esc(s.owner)}</td></tr>`).join('')}</tbody></table></div><h3>Estimated pilot spending</h3>${list(e.costs.map(c=>`${c.item}: ${eur(c.amount_eur)}`))}<p><b>Metric:</b> ${esc(e.metric)}</p><p><b>Baseline:</b> ${esc(e.baseline)}</p><p><b>Success threshold:</b> ${esc(e.success_threshold)}</p><p><b>Measurement:</b> ${esc(e.measurement_method)}</p><p class="notice"><b>Stop condition:</b> ${esc(e.stop_condition)}</p></div>
 <div class="card"><h3>Missing information</h3>${list(r.missing_information)}<h3>Conflicting evidence</h3>${r.contradictions.length?claims(r.contradictions):'<p>No contradictions identified by the model.</p>'}<h3>What could change the decision?</h3>${list(r.decision_changes)}</div>
 <div class="card"><h3>Source evidence for this run</h3><p class="muted">IDs refer to the saved input snapshot. A valid ID does not itself prove a claim is supported.</p>${Object.entries(run.context.evidence).map(([id,text])=>`<p id="source-${esc(id)}"><b>[${esc(id)}]</b> ${esc(text)}</p>`).join('')}</div>`;
 markStale();
}
function history(){
 $('historySection').hidden=false;
 $('history').replaceChildren();
 runs.forEach((r,i)=>{const b=document.createElement('button');b.className='secondary';b.textContent=`${i+1}. ${eur(r.context.budget)} · ${r.report.options.find(o=>o.id===r.report.recommended_id).name}`;b.onclick=()=>render(r);$('history').append(b);});
 if(runs.length>1){const a=runs[runs.length-2],b=runs[runs.length-1];const changes=fields.filter(k=>a.inputs[k]!==b.inputs[k]);const name=r=>r.report.options.find(o=>o.id===r.report.recommended_id).name;$('changes').textContent=`Latest comparison — changed inputs: ${changes.join(', ')||'none'}. Budget: ${eur(a.context.budget)} → ${eur(b.context.budget)}. Recommendation: ${name(a)} → ${name(b)}. Inspect both runs for reasoning; AI outputs may vary even with identical inputs.`;}
}
$('compare').onclick=async()=>{
 const inputs=read();
 if(!$('budget').value.trim()||!Number.isFinite(inputs.budget)||inputs.budget<0){$('message').textContent='Enter a valid nonnegative budget.';return;}
 $('compare').disabled=true;$('reset').disabled=true;$('message').className='';$('message').textContent='Comparing evidence and validating the report… Live analysis uses two stages and may take up to four minutes.';
 try{
  const response=await fetch('/api/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...inputs,demo:$('demo').checked})});
  const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed.');
  const run={...data,inputs,time:new Date().toLocaleString()};runs.push(run);runs=runs.slice(-5);render(run);history();$('message').textContent='Report ready. Budget arithmetic and source IDs passed validation.';
 }catch(error){$('message').className='error';$('message').textContent=error.message;}
 finally{$('compare').disabled=false;$('reset').disabled=false;}
};
$('download').onclick=()=>{if(!selected)return;const blob=new Blob([JSON.stringify(selected,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='strategy-report.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
(async()=>{try{const [d,s]=await Promise.all([fetch('/api/defaults').then(r=>r.json()),fetch('/api/status').then(r=>r.json())]);defaults=d;fill();$('status').textContent=s.key_configured?`Live AI ready · ${s.model}`:'API key not configured. Add it to .env, or try offline sample mode.';}catch(e){$('message').textContent='Could not load app configuration. Restart the Python server.';}})();
