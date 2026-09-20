#!/usr/bin/env python3
"""Render public benchmark data into responsive charts and the demo section.
Run with Python + matplotlib. No provider calls or private prompt data required.
"""
import hashlib
import html
import json
from pathlib import Path
import re
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'benchmarks/results/website-replay-2026-09-20.json'
ASSETS = ROOT/'demo/static'
report=json.loads(REPORT.read_text())
rows=report['rows']
variants=[next(v for v in row['variants'] if v['threshold']==.5) for row in rows]
full=[v['baseline_total_tokens'] for v in variants]
selected=[v['dynamic_total_tokens'] for v in variants]
labels=[re.sub(r'-\d+$','',row['slug']).replace('-',' ').capitalize() for row in rows]
reductions=[100*(a-b)/a for a,b in zip(full,selected)]
total_full=sum(full);total_selected=sum(selected);saved=total_full-total_selected
before=sum(v['comparisons']['uncached']['baseline_usd'] for v in variants)
after=sum(v['comparisons']['uncached']['dynamic_usd'] for v in variants)
ink='#192322'; muted='#687169'; paper='#fdfef9'; baseline='#c6ccbf'; active='#4d7034'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False})

# Both variants preserve a common zero baseline and the same numeric scale.
for mobile in [False,True]:
    fig,ax=plt.subplots(figsize=(4.5,13.8) if mobile else (12.8,7.6),facecolor=paper)
    fig.suptitle(f'{100*saved/total_full:.1f}% less generation input\n{saved:,} tokens removed', fontsize=13 if mobile else 22, fontweight='bold', color=ink, y=.98)
    retained=sum(v['required_retained'] for v in variants); required=sum(v['required_total'] for v in variants)
    fig.text(.5,.935 if mobile else .855,f'{len(rows)} archived requests · {retained}/{required} required paragraphs retained\nAfter Jev: {100*(before-after)/before:.1f}% estimated net input-cost savings',ha='center',va='top',fontsize=8 if mobile else 10,color=ink)
    ax.set_facecolor(paper)
    pitch=1.48 if mobile else 1.0
    y=[i*pitch for i in range(len(rows))]
    height=.23 if mobile else .27
    offset=.16 if mobile else .18
    ax.barh([i-offset for i in y],full,height=height,color=baseline,label='Full prompt + request',zorder=3)
    ax.barh([i+offset for i in y],selected,height=height,color=active,label='Selected context + request',zorder=3)
    for i,(a,b,pct) in enumerate(zip(full,selected,reductions)):
        ax.text(a+450,y[i]-offset,f'{a:,}',va='center',fontsize=9,color=muted)
        ax.text(b+450,y[i]+offset,f'{b:,}',va='center',fontsize=9,color=ink,fontweight='bold')
        if mobile:
            ax.text(0,y[i]-.62,labels[i],fontsize=10,color=ink,va='center')
            ax.text(0,y[i]+.58,f'{pct:.1f}% fewer tokens',fontsize=8.5,color=active,va='center')
        else:
            ax.text(35400,y[i],f'−{pct:.1f}%',va='center',ha='right',fontsize=10,color=active,fontweight='bold')
    ax.set_xlim(0,35500)
    ax.set_ylim(y[-1]+(.85 if mobile else .65),-.95 if mobile else -.7)
    if mobile:
        ax.set_yticks([])
        fig.subplots_adjust(left=.06,right=.98,top=.835,bottom=.065)
    else:
        ax.set_yticks(y,labels=[textwrap.fill(label,26) for label in labels],color=ink,fontsize=10)
        ax.tick_params(axis='y',length=0,pad=15)
        fig.subplots_adjust(left=.23,right=.97,top=.75,bottom=.12)
    ax.set_xticks([0,10000,20000,30000])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{int(x/1000)}k' if x else '0'))
    ax.tick_params(axis='x',length=0,labelcolor=muted,pad=10)
    ax.grid(axis='x',color='#e0e5d8',linewidth=.8,zorder=0)
    ax.set_xlabel('Generation input tokens · o200k_base',color=muted,labelpad=16,fontsize=9)
    fig.legend(*ax.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.06 if mobile else .23,.885 if mobile else .81),ncol=1 if mobile else 2,frameon=False,fontsize=9,labelcolor=ink)
    name='benchmark-context-mobile' if mobile else 'benchmark-context'
    fig.savefig(ASSETS/f'{name}.svg',facecolor=paper)
    fig.savefig(ASSETS/f'{name}.png',dpi=180,facecolor=paper)
    svg_path=ASSETS/f'{name}.svg'
    svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines())+'\n')
    plt.close(fig)

trs='\n'.join(f'<tr><th scope="row"><a href="{html.escape(r["url"])}" target="_blank" rel="noreferrer">{html.escape(label)}</a></th><td>{a:,}</td><td>{b:,}</td><td>{pct:.1f}%</td></tr>' for r,label,a,b,pct in zip(rows,labels,full,selected,reductions))
section='''<section id="benchmarks" class="benchmarks" aria-labelledby="benchmark-title">
<div class="section-head"><div><p class="eyebrow">MEASURED ON EIGHT EXISTING SITES</p><h2 id="benchmark-title">Less context.<br>Measured, not assumed.</h2></div><p>Exact archived website requests, replayed through Jev.<br>Default relevance cutoff: 0.50 · September 20, 2026.</p></div>
<div class="benchmark-summary"><div><strong>REDUCTION</strong><span>fewer generation-input tokens</span></div><p><b>FULL → SELECTED</b><br>SAVED tokens removed across eight requests.<br>All 80 required-paragraph checks passed.</p></div>
<figure class="benchmark-figure"><picture><source media="(max-width: 600px)" width="450" height="1380" srcset="{{ base }}/assets/benchmark-context-mobile.svg"><img src="{{ base }}/assets/benchmark-context.svg" width="1280" height="760" loading="lazy" alt="Paired bars compare full and reduced generation-input tokens for eight existing sites. Individual reductions range from MINIMUM to MAXIMUM. Exact values appear in the table below."></picture><figcaption>Both bars include the unchanged request. The selected-context bar also includes source metadata and its instruction wrapper. Jev’s own processing tokens are excluded from these bars.</figcaption></figure>
<div class="benchmark-conclusion"><strong>Fewer generation tokens ≠ the same reduction in cost.</strong><p>After Jev’s selection cost, estimated uncached input cost fell from $BEFORE to $AFTER: <b>NET savings</b>. With cached generation prompts, the dynamic path cost more. This replay did not regenerate sites or establish equivalent output quality.</p></div>
<details class="benchmark-table"><summary>View exact token counts and test sites</summary><div class="benchmark-table-scroll"><table><thead><tr><th scope="col">Test site</th><th scope="col">Full input</th><th scope="col">Dynamic input</th><th scope="col">Reduction</th></tr></thead><tbody>ROWS</tbody><tfoot><tr><th scope="row">All eight sites</th><td>FULL</td><td>SELECTED</td><td>REDUCTION</td></tr></tfoot></table></div></details>
<div class="benchmark-links"><a href="https://github.com/rohanarun/dynamic-context-engine/blob/main/benchmarks/website-replay-2026-09-20.md" target="_blank" rel="noreferrer">Read methodology and cost breakdown ↗</a><a href="{{ base }}/assets/benchmark-context.png" download>Download graph ↓</a></div>
</section>'''
for key,value in {'REDUCTION':f'{100*saved/total_full:.1f}%','FULL':f'{total_full:,}','SELECTED':f'{total_selected:,}','SAVED':f'{saved:,}','MINIMUM':f'{min(reductions):.1f}%','MAXIMUM':f'{max(reductions):.1f}%','BEFORE':f'{before:.5f}','AFTER':f'{after:.5f}','NET':f'{100*(before-after)/before:.1f}%','ROWS':trs}.items():
    section=section.replace(key,value)
asset_version=hashlib.sha256((ASSETS/'benchmark-context.svg').read_bytes()).hexdigest()[:12]
section=section.replace('.svg"',f'.svg?v={asset_version}"').replace('.png"',f'.png?v={asset_version}"')
(ROOT/'demo/templates/benchmark.html').write_text(section+'\n')
print(json.dumps({'cases':len(rows),'full_tokens':total_full,'dynamic_tokens':total_selected,'removed_tokens':saved,'reduction_percent':100*saved/total_full}))
