const base = location.pathname.replace(/\/$/, '');
const $ = id => document.getElementById(id);
let sample, current = 0, lastResult = null;
const escape = text => String(text).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
function paragraphs(rows, judged=false) {
  $('paragraphs').innerHTML = rows.map(p => `<div class="paragraph ${p.selected ? 'is-selected' : ''}"><div class="paragraph-top"><span>${escape(p.source)} · paragraph ${p.position+1}</span><span>${judged ? `${Math.round(p.relevance*100)}% relevant` : 'Not evaluated'}</span></div><p>${escape(p.text)}</p>${judged ? `<div class="score-track"><span style="width:${p.relevance*100}%"></span></div><span class="badge">${p.selected ? 'Included' : p.selection_reason === 'over_budget' ? 'Relevant · over budget' : 'Below cutoff'}</span>` : ''}</div>`).join('');
}
function result(data) {
  lastResult = data;
  paragraphs(data.paragraphs, true);
  $('empty').hidden = true;
  $('selected').hidden = false;
  $('selected').innerHTML = data.paragraphs.filter(p => p.selected).map(p => `<div class="selected-block"><div class="paragraph-top"><span>${escape(p.source)} · paragraph ${p.position+1}</span><span>${Math.round(p.relevance*100)}%</span></div><p>${escape(p.text)}</p></div>`).join('') || '<div class="empty"><h4>No paragraphs selected.</h4><p>No sample paragraph met both the relevance cutoff and available budget. Try a different request or adjust the controls.</p></div>';
  $('context-size').textContent = data.context_tokens.toLocaleString();
  $('result-caption').textContent = `${data.selected_count} of ${data.total_count} paragraphs selected`;
  $('raw').textContent = data.context || '(Empty context)';
  $('copy').disabled = !data.context;
  $('status').className = 'status';
  $('status').textContent = `${data.cached ? 'Cached Jev judgments' : 'Live Jev judgments'} · ${data.models.join(', ') || 'No model call needed'} · ${data.elapsed_ms.toLocaleString()} ms · ${data.selected_count} selected${data.usage.input_tokens !== undefined ? ` · ${data.usage.input_tokens.toLocaleString()} input tokens` : ''}`;
  if (window.gsap && !matchMedia('(prefers-reduced-motion: reduce)').matches) gsap.from('.selected-block', {y:12,opacity:0,duration:.45,stagger:.08});
}
function install(agent) {
  const paths = {codex:'~/.agents/skills',claude:'~/.claude/skills',hermes:'~/.hermes/skills'};
  $('install-code').textContent = `git clone https://github.com/rohanarun/dynamic-context-engine.git\ncd dynamic-context-engine\npython3 -m pip install .\npython3 install_skill.py --agent ${agent}\n\n# Installs to ${paths[agent]}/dynamic-context`;
  document.querySelectorAll('[data-agent]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.agent===agent)));
}
async function start() {
  try {
    const response = await fetch(`${base}/api/sample`);
    if (!response.ok) throw new Error('Unable to load sample context. Please refresh.');
    sample = await response.json();
    paragraphs(sample.paragraphs);
    $('total-count').textContent = sample.paragraphs.length;
  } catch(error) { $('status').className='status error'; $('status').textContent=error.message; }
}
$('query-form').addEventListener('submit', async event => {
  event.preventDefault();
  $('run').disabled = true;
  $('status').className = 'status';
  $('status').textContent = 'Jev is evaluating each sample paragraph against your request…';
  $('query-form').setAttribute('aria-busy','true');
  try {
    const response = await fetch(`${base}/api/select`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({request:$('request').value,threshold:Number($('threshold').value),max_tokens:Number($('budget').value)})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'The request could not be completed. Please retry.');
    result(data);
  } catch(error) { $('status').className='status error'; $('status').textContent=`${error.message}${lastResult ? ' The panels still show the previous successful result.' : ''}`; }
  finally { $('run').disabled=false; $('query-form').setAttribute('aria-busy','false'); }
});
for (const [id, step] of [['previous',-1],['next',1]]) $(id).addEventListener('click',() => {
  if (!sample) return;
  current=(current+step+sample.requests.length)%sample.requests.length;
  $('request').value=sample.requests[current];
  $('example-index').textContent=`${current+1} / ${sample.requests.length}`;
});
$('threshold').addEventListener('input',()=>{$('threshold-label').textContent=`${Math.round(Number($('threshold').value)*100)}%`;});
$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(lastResult.context);$('copy').textContent='Copied';setTimeout(()=>{$('copy').textContent='Copy context ↗';},1500);}catch{$('raw-details').open=true;$('status').textContent='Clipboard unavailable. Copy the payload below manually.';}});
document.querySelectorAll('[data-agent]').forEach(b=>b.addEventListener('click',()=>install(b.dataset.agent)));
install('codex');start();
if (window.gsap && window.ScrollTrigger && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  gsap.registerPlugin(ScrollTrigger);
  gsap.fromTo('.visual',{scale:.8,opacity:.6},{scale:1,opacity:1,scrollTrigger:{trigger:'.hero',start:'top bottom',end:'top 15%',scrub:true}});
  gsap.to('.visual',{opacity:.2,scrollTrigger:{trigger:'.hero',start:'top top',end:'bottom 10%',scrub:true}});
  const reveal=document.querySelector('.reveal');
  reveal.innerHTML=reveal.innerHTML.split('<br>').map(line=>line.split(' ').map(word=>`<span>${word}</span>`).join(' ')).join('<br>');
  gsap.fromTo('.reveal span',{opacity:.1},{opacity:1,stagger:.15,scrollTrigger:{trigger:'.reveal',start:'top 85%',end:'bottom 45%',scrub:true}});
}
