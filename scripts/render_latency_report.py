#!/usr/bin/env python3
"""Render measured latency JSON; never issue provider requests."""
import hashlib
import argparse
import json
from pathlib import Path
import statistics
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from benchmarks.latency import stats
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--results',type=Path,default=ROOT/'benchmarks/results/latency-2026-09-20.json')
a=p.parse_args();r=json.loads(a.results.read_text())
summary=r['retrieval_summary'];warm=r['warm_summary'];answers=r['answer_summary']
labels={'sample-12':'Demo memory · 12 paragraphs','qa-71':'Question corpus · 71 paragraphs','website-prompt-78':'Website prompt · 78 paragraphs'}
ink='#192322';paper='#fdfef9';palette=['#c6ccbf','#90a37a','#4d7034']
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False})
seq=summary['website-prompt-78']['1']['median_ms'];new=summary['website-prompt-78']['8']['median_ms']
for mobile in [False,True]:
 fig,ax=plt.subplots(figsize=(4.5,8.9) if mobile else (11,6.8),facecolor=paper);ax.set_facecolor(paper)
 fig.suptitle(f'{seq/new:.0f}× faster context retrieval\n{seq/1000:.2f}s → {new/1000:.2f}s median', fontsize=13 if mobile else 22, fontweight='bold', color=ink, y=.98)
 fig.text(.5,.89 if mobile else .845,'Website prompt · 1 versus 8 workers\nAll 78 paragraphs judged · complete-answer latency was mixed',ha='center',va='top',fontsize=7.5 if mobile else 10,color=ink)
 fig.subplots_adjust(left=.09 if mobile else .31,right=.96,top=.73 if mobile else .70,bottom=.13)
 positions=[];names=[];maximum=max(v['p95_ms'] for d in summary.values() for v in d.values())/1000
 for i,(dataset,values) in enumerate(summary.items()):
  center=i*(2.6 if mobile else 1.6)
  if mobile:ax.text(0,center-.95,labels[dataset],fontsize=9,color=ink,fontweight='bold')
  for j,w in enumerate([1,3,8]):
   y=center+(j-1)*.36;v=values[str(w)];median=v['median_ms']/1000;p95=v['p95_ms']/1000
   ax.barh(y,median,height=.25,color=palette[j],zorder=3,label=f'{w} worker'+('' if w==1 else 's') if i==0 else None)
   ax.plot([median,p95],[y,y],color=palette[j],linewidth=1.5,zorder=4)
   ax.plot(p95,y,'o',color=palette[j],markersize=3,zorder=4)
   ax.text(p95+maximum*.025,y,f'{median:.2f}s',va='center',fontsize=8 if mobile else 10,color=ink)
  positions.append(center);names.append(labels[dataset].replace(' · ','\n'))
 ax.set_yticks([] if mobile else positions,[] if mobile else names,fontsize=10,color=ink)
 ax.tick_params(axis='y',length=0,pad=15);ax.tick_params(axis='x',length=0,labelsize=9)
 ax.invert_yaxis();ax.set_xlim(0,maximum*1.24);ax.grid(axis='x',color='#e0e5d8',zorder=0)
 ax.set_xlabel('Retrieval seconds · lower is faster',labelpad=18,fontsize=9,color=ink)
 fig.legend(*ax.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.09 if mobile else .31,.815 if mobile else .775),ncol=3,frameon=False,fontsize=8 if mobile else 9)
 if mobile:ax.set_ylim(positions[-1]+.85,-1.2)
 name='benchmark-latency-mobile' if mobile else 'benchmark-latency'
 for ext in ['svg','png']:
  path=ROOT/'demo/static'/f'{name}.{ext}'
  fig.savefig(path,facecolor=paper,dpi=180)
  if ext=='svg':path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
 plt.close(fig)

full=answers['full'];dynamic=answers['dynamic'];pair_delta=statistics.median(r['paired_delta_ms'])
seq=summary['website-prompt-78']['1']['median_ms'];new=summary['website-prompt-78']['8']['median_ms'];old=summary['website-prompt-78']['3']['median_ms']
retrieval_rows='';html_rows=''
for dataset,arms in summary.items():
 for w,v in arms.items():
  peak=max(q['execution']['peak_parallel_batches'] for q in r['retrieval'] if q['dataset']==dataset and q['workers']==int(w))
  retrieval_rows+=f"| {labels[dataset]} | {w} | {v['n']} | {v['median_ms']:.0f} ms | {v['p95_ms']:.0f} ms | {peak} |\n"
  html_rows+=f'<tr><th scope="row">{labels[dataset]}</th><td>{w}</td><td>{v["median_ms"]:.0f} ms</td><td>{v["p95_ms"]:.0f} ms</td></tr>'
text=f'''# Parallel Jev and request latency — September 20, 2026

**Eight workers reduced the website-prompt median cold retrieval from {seq:.0f} ms sequential to {new:.0f} ms ({seq/new:.2f}× faster), and from {old:.0f} ms with the previous three-worker default ({old/new:.2f}× faster).**

The default is now eight concurrent Jev HTTP batches per query, with 12 independent paragraph questions per batch. Every paragraph in the selected collection is judged. The worker bound is configurable from 1 to 32. A six-batch corpus reaches six simultaneous calls; seven batches reach seven. The 12-paragraph demo only needs one call, so raising its worker limit cannot create useful additional concurrency.

![Cold retrieval latency by corpus and worker count: median bars and P95 dots.](../demo/static/benchmark-latency.png)

## Cold retrieval measurements

Bars show medians. Thin extensions and dots show the empirical 95th percentile. Nine runs per corpus/configuration: three fixed requests × three repetitions. This is an exploratory latency sample, not a production SLA.

| Corpus | Worker limit | Runs | Median | P95 | Observed peak overlapping calls |
| --- | ---: | ---: | ---: | ---: | ---: |
{retrieval_rows}
## Immediate local-cache repeats

Each of the 27 eight-worker cold queries was immediately repeated. Every repeat returned the same context, zero dispatched provider calls, and zero new Jev usage. Cache lookup and assembly still take time.

| Corpus | Repeats | Median | P95 |
| --- | ---: | ---: | ---: |
'''
for dataset,v in warm.items():text+=f"| {labels[dataset]} | {v['n']} | {v['median_ms']:.2f} ms | {v['p95_ms']:.2f} ms |\n"
text+=f'''
## Time to a complete answer

A separate paired experiment used 12 questions stratified before inference across lookups, multi-paragraph questions, calculations, policy exceptions, and missing-information checks. It reused the public QA corpus and frozen gold answers, with Gemini 3.8 Flash in both arms. Each question has one full-context answer and one answer preceded by fresh eight-worker Jev retrieval. Arm order was randomized within pairs. Requests ran serially to avoid benchmark-generated contention. This measures complete responses, not time to first token; reasoning/output length and remote routing can affect it.

| Arm | Complete answers | Median total | P95 total | Median generation portion | Exact accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full context | {full['total']['n']} | {full['total']['median_ms']/1000:.2f} s | {full['total']['p95_ms']/1000:.2f} s | {full['generation']['median_ms']/1000:.2f} s | {full['correct']}/{full['total']['n']} |
| Dynamic, including cold Jev | {dynamic['total']['n']} | {dynamic['total']['median_ms']/1000:.2f} s | {dynamic['total']['p95_ms']/1000:.2f} s | {dynamic['generation']['median_ms']/1000:.2f} s | {dynamic['correct']}/{dynamic['total']['n']} |

The **median paired dynamic-minus-full difference is {pair_delta/1000:+.2f} seconds**. This differs from subtracting the two arm medians. {sum(v>0 for v in r['paired_delta_ms'])} of the 12 dynamic requests took longer than their full-context partner. Parallel selection reduces retrieval overhead; it does not establish that requests never slow down. No retrieval can overlap an answer that depends on its result. These questions are a small latency subset, not a replacement for the [32-question accuracy benchmark](question-accuracy-2026-09-20.md). Current subset accuracy and every returned answer are included to avoid presenting faster but incorrect answers as an equivalent-quality win.

## Protocol, instrumentation, and limits

- Cold retrieval run order was shuffled with seed 20260920 across all three corpora, three requests, three repetitions, and worker counts 1/3/8: **81 cold queries**. No other experiment ran concurrently. Eight-worker cold queries also enabled cache writing, as production does, before the immediate warm repeat; other configurations disabled local caching. This minor extra write overhead counts against the new default.
- All cold runs checked that the number of unique judged paragraph IDs exactly equals the collection size. Individual requests contain independent Noul questions. A bounded thread pool runs batches concurrently; timestamps and observed peak overlapping calls demonstrate client-side overlap. They do not prove provider-internal scheduling.
- The batch size, relevance policy, threshold (0.50), full request text, and 1,000,000-token budget are unchanged between configurations. Model scoring can vary across fresh calls; changing worker count is not intended to change selection semantics. Required coverage means every paragraph was judged, not that every necessary paragraph was selected.
- Corpus sizes: 12 sample paragraphs, 71 public QA paragraphs, and 78 original website-generation prompt paragraphs. The website prompt is roughly 27k reference tokens and includes one very large paragraph; it is not a synthetic small-text stand-in. The three original website requests remain private; hashes and public site slugs identify them. No private prompt or request text appears in this report or its JSON.
- Benchmarks ran on the user's Mac against public provider APIs. HTTP/TLS, network transit, provider scheduling/inference, SQLite lookup, JSON work, and exact token-budget assembly are included in retrieval wall time. Tokenizer initialization was performed once outside the measurements. No forced provider-cache bypass or guarantees about remote load. These are warm-process measurements, not fresh process startup or first-ever tokenizer download.
- `timing_ms` separates setup, inference, cache writes, assembly, and total time. `execution` includes configured workers, planned/dispatched batches, paragraphs judged, observed peak in-flight batches, and each batch's start/end/duration. The timer covers each complete HTTP provider call, not just model compute. Live demo round-trip measurements additionally include browser-to-demo network transit.
- The engine's concurrency limit is per query. The hosted demo permits three simultaneous queries, so its aggregate ceiling is 24 calls with eight workers. It does not expose worker controls publicly. CLI users can configure `--workers`, `--batch-size`, `JEV_CONTEXT_WORKERS`, and `JEV_CONTEXT_BATCH_SIZE` according to provider quota.
- An error from any batch fails the query without emitting or caching partial scores. No speculative partial context, timeout fallback, or dropped paragraphs is used to achieve faster measurements. No relevance policy was tuned during this experiment.
- P95 uses linear interpolation between ordered samples. Nine cold samples per cell and 12 answer pairs are small; tail estimates are unstable and should not be treated as a guarantee. There is no representative concurrent-user load test or statistical equivalence claim.

## Reproduce

```sh
# Set TYPESAFE_API_KEY and ANSWER_API_KEY privately.
export ANSWER_API_BASE_URL=https://openrouter.ai/api/v1
python3 benchmarks/latency.py \\
  --archive /private/website-replay-cases.json \\
  --output artifacts/latency-reproduction
```

Omit `--archive` to run only the two fully public corpora. Use a new output directory for an independent run. An existing output directory resumes recorded completed calls and rejects changed protocols. The report checkpoints after each measured query. The plotting/report script is tailored to the published three-corpus run.

- [Raw measurements, batch intervals, answer receipts, and source hashes](results/latency-2026-09-20.json)
- [Benchmark harness](latency.py)
- [Public QA fixture](fixtures/question-answering-2026-09-20.json)
- [Model selection policy](../jev_context/policy.json)

## Per-question complete-answer times

| Question | Full | Dynamic including Jev | Delta | Full correct | Dynamic correct |
| --- | ---: | ---: | ---: | ---: | ---: |
'''
for q in r['end_to_end_question_ids']:
 f=next(x for x in r['answers'] if x['question_id']==q and x['arm']=='full');d=next(x for x in r['answers'] if x['question_id']==q and x['arm']=='dynamic')
 text+=f"| {q} | {f['total_ms']/1000:.2f} s | {d['total_ms']/1000:.2f} s | {(d['total_ms']-f['total_ms'])/1000:+.2f} s | {f['answer']['grade']['correct']} | {d['answer']['grade']['correct']} |\n"
(ROOT/'benchmarks/latency-2026-09-20.md').write_text(text)
url='https://github.com/rohanarun/dynamic-context-engine/blob/main/benchmarks/latency-2026-09-20.md'
section=f'''<section id="latency" class="benchmarks" aria-labelledby="latency-title">
<div class="section-head"><div><p class="eyebrow">MEASURED WITH LIVE JEV CALLS</p><h2 id="latency-title">Parallel selection.<br>Measured overhead.</h2></div><p>81 cold queries. Three corpora. One, three, and eight workers.<br>Same paragraph coverage, request, batch size, and relevance policy.</p></div>
<div class="benchmark-summary"><div><strong>{new/1000:.2f}s</strong><span>median website-prompt retrieval</span></div><p><b>{seq/new:.1f}× faster than sequential</b><br>{seq/1000:.2f}s with one worker → {new/1000:.2f}s with eight.<br>{old/new:.1f}× faster than the previous three-worker default.</p></div>
<figure class="benchmark-figure"><picture><source media="(max-width: 600px)" width="450" height="890" srcset="{{{{ base }}}}/assets/benchmark-latency-mobile.svg"><img src="{{{{ base }}}}/assets/benchmark-latency.svg" width="1100" height="680" loading="lazy" alt="Cold retrieval medians compare one, three and eight workers on 12, 71 and 78 paragraphs. The website prompt drops from {seq:.0f} to {new:.0f} milliseconds; exact medians and P95 values follow."></picture><figcaption>Bars and labels show median wall time; thin extensions and dots show P95. Nine runs per configuration. Eight workers reach six concurrent calls for 71 paragraphs and seven for 78. The 12-paragraph sample needs just one call.</figcaption></figure>
<div class="benchmark-conclusion"><strong>Parallel does not mean zero overhead.</strong><p>Across 12 paired questions, median complete-answer time was <b>{full['total']['median_ms']/1000:.2f}s with full context</b> and <b>{dynamic['total']['median_ms']/1000:.2f}s with dynamic context, including Jev</b>. P95 was {full['total']['p95_ms']/1000:.2f}s versus {dynamic['total']['p95_ms']/1000:.2f}s. The median paired difference was {pair_delta:+.0f} ms; {sum(v>0 for v in r['paired_delta_ms'])}/12 dynamic requests took longer. Exact accuracy was {full['correct']}/12 versus {dynamic['correct']}/12. This is a small measured sample, not a latency guarantee.</p><p>Immediate cache repeats made no new Jev calls: median {warm['qa-71']['median_ms']:.1f} ms on the question corpus and {warm['website-prompt-78']['median_ms']:.1f} ms on the website prompt. Local context assembly still takes time.</p></div>
<details class="benchmark-table"><summary>Inspect median and tail retrieval times</summary><div class="benchmark-table-scroll"><table><thead><tr><th scope="col">Corpus</th><th scope="col">Workers</th><th scope="col">Median</th><th scope="col">P95</th></tr></thead><tbody>{html_rows}</tbody></table></div></details>
<div class="benchmark-links"><a href="{url}" target="_blank" rel="noreferrer">Read timing protocol and every paired result ↗</a><a href="{{{{ base }}}}/assets/benchmark-latency.png" download>Download latency graph ↓</a></div>
</section>'''
asset_version=hashlib.sha256((ROOT/'demo/static/benchmark-latency.svg').read_bytes()).hexdigest()[:12]
section=section.replace('.svg"',f'.svg?v={asset_version}"').replace('.png"',f'.png?v={asset_version}"')
(ROOT/'demo/templates/latency.html').write_text(section+'\n')
print(json.dumps({'website_sequential_ms':seq,'website_default_ms':new,'old_default_ms':old,'end_to_end':answers,'median_paired_delta_ms':pair_delta},indent=2))
