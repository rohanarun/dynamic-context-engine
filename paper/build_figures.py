"""Rebuild manuscript figures and validate totals from frozen public measurements."""
import json, hashlib, statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
files={k:ROOT/'benchmarks/results'/v for k,v in {
 'website':'website-replay-2026-09-20.json','original':'question-accuracy-2026-09-20.json',
 'revised':'question-accuracy-2026-09-20-revised.json','latency':'latency-2026-09-20.json'}.items()}
data={k:json.loads(p.read_text()) for k,p in files.items()}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors=['#626e7a','#267366','#b29669']
fig,ax=plt.subplots(1,2,figsize=(10,3.3),layout='constrained')
for a,key,title in zip(ax,['original','revised'],['Original evaluation (32 questions)','Post-selected rerun (29 questions)']):
 s=data[key]['summary']; vals=[s['arms'][k]['accuracy_percent'] for k in ['full','dynamic','no_context']]
 a.bar(['Full','Dynamic','No context'],vals,color=colors,width=.6)
 a.set_ylim(0,119);a.set_yticks([0,25,50,75,100]);a.set_ylabel('Exact accuracy (%)');a.set_title(title,fontsize=11)
 for i,k in enumerate(['full','dynamic','no_context']):
  v=s['arms'][k];a.text(i,vals[i]+2,f"{v['correct']}/{v['total']}",ha='center')
fig.savefig(OUT/'figures/accuracy.png',dpi=220);plt.close(fig)
fig,ax=plt.subplots(figsize=(9,3.4),layout='constrained')
rows=data['website']['rows']; variants=[next(v for v in r['variants'] if v['threshold']==.5) for r in rows]
full=sum(v['baseline_total_tokens'] for v in variants);selected=sum(v['dynamic_total_tokens'] for v in variants)
assert (full,selected)==(230057,195953)
labels=['Website prompt replay\n8 requests','Original QA\n32 questions','Revised QA\n29 questions']
reductions=[100*(1-selected/full),data['original']['summary']['input_reduction_percent'],data['revised']['summary']['input_reduction_percent']]
ax.barh(labels,reductions,color=['#626e7a','#267366','#71a299'],height=.5);ax.invert_yaxis();ax.set_xlim(0,112);ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('Downstream input tokens removed (%)')
for i,v in enumerate(reductions):ax.text(v+1,i,f'{v:.1f}%',va='center')
fig.savefig(OUT/'figures/tokens.png',dpi=220);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(10,3.2),layout='constrained')
lat=data['latency']
for ax,ds,title in zip(axs,['sample-12','qa-71','website-prompt-78'],['12 paragraphs','71 paragraphs','78 paragraphs']):
 vals=[]
 for w in [1,3,8]:
  rr=[r['wall_ms'] for r in lat['retrieval'] if r['dataset']==ds and r['workers']==w]
  assert len(rr)==9
  vals.append(statistics.median(rr)/1000)
 ax.bar(['1','3','8'],vals,color=colors,width=.6);ax.set_title(title,fontsize=11);ax.set_xlabel('Concurrent worker limit');ax.set_ylabel('Median retrieval (s)');ax.set_ylim(0,max(vals)*1.22)
 for i,v in enumerate(vals):ax.text(i,v+.025,f'{v:.2f}',ha='center',fontsize=9)
fig.savefig(OUT/'figures/latency.png',dpi=220);plt.close(fig)
manifest={'code_revision':'93f6020','results':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files.values()},'website_full_input':full,'website_dynamic_input':selected,'original_summary':data['original']['summary'],'revised_summary':data['revised']['summary']}
(OUT/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Figures and evidence manifest written; website totals verified.')
