#!/usr/bin/env python3
"""Render the frozen QA result into a report and demo assets; no model calls."""
import argparse
import html
import json
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from benchmarks.question_accuracy import summarize

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--results',type=Path,default=ROOT/'benchmarks/results/question-accuracy-2026-09-20.json')
a=p.parse_args()
r=json.loads(a.results.read_text()); s=summarize(r['rows']); n=len(r['rows'])
assert s==r['summary']
if any(v['errors'] for v in s['arms'].values()):
    raise SystemExit('Resolve/report infrastructure errors before publishing a completed benchmark')
full=s['arms']['full']; dynamic=s['arms']['dynamic']; no=s['arms']['no_context']
answerable=[row for row in r['rows'] if row['kind']!='unanswerable']
answerable_correct=sum(row['answers']['dynamic']['grade']['correct'] for row in answerable)
context_reduction=100*(1-s['context_tokens_dynamic']/s['context_tokens_full'])
report_url='https://github.com/rohanarun/dynamic-context-engine/blob/main/benchmarks/question-accuracy-2026-09-20.md'
ink='#192322';paper='#fdfef9';colors=['#aab49f','#4d7034','#bcae96']
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False})
for mobile in [False,True]:
    fig,axs=plt.subplots(2,1,figsize=(4.5,8.8) if mobile else (10.5,7.2),facecolor=paper)
    fig.subplots_adjust(left=.26 if mobile else .19,right=.95,top=.93,bottom=.085,hspace=.8)
    for j,ax in enumerate(axs):
        ax.set_facecolor(paper)
        ax.set_yticks([0,1,2],['Full\ncontext','Dynamic\ncontext','No context\ncontrol'],color=ink,fontsize=9 if mobile else 11)
        ax.invert_yaxis();ax.tick_params(axis='y',length=0,pad=12)
        ax.grid(axis='x',color='#e0e5d8',zorder=0)
        ax.tick_params(axis='x',length=0,labelsize=8)
        ax.set_title('Answer accuracy' if j==0 else 'Average answer-model input',loc='left',fontsize=12 if mobile else 15,pad=22,color=ink)
        values=[s['arms'][k]['accuracy_percent'] if j==0 else s['arms'][k]['reference_input_tokens']/n for k in ['full','dynamic','no_context']]
        ax.barh([0,1,2],values,height=.48,color=colors,zorder=3)
        if j==0:
            ax.set_xlim(0,123);ax.set_xticks([0,25,50,75,100],['0%','25%','50%','75%','100%'])
            ax.set_xlabel('Exact question-level correctness',fontsize=8,labelpad=15,color=ink)
        else:
            ax.set_xlim(0,max(values)*1.26);ax.set_xlabel('Tokens · o200k_base',fontsize=9,labelpad=15,color=ink)
        for i,v in enumerate(values):
            label=f'{v:.1f}%' if j==0 else f'{v:,.0f}'
            ax.text(v+(1.5 if j==0 else max(values)*.018),i,label,va='center',fontsize=9 if mobile else 11,color=ink)
    name='benchmark-accuracy-mobile' if mobile else 'benchmark-accuracy'
    for ext in ['svg','png']:
        fig.savefig(ROOT/'demo/static'/f'{name}.{ext}',facecolor=paper,dpi=180)
    plt.close(fig)

def count(v):return f"{v['correct']}/{v['total']} ({v['accuracy_percent']:.1f}%)"
def mark(v):return 'Pass' if v['grade']['correct'] else 'Fail'
def js(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
failures=[v for v in r['rows'] if not v['answers']['dynamic']['grade']['correct']]
header=f'''# Question-answer accuracy and context savings — September 20, 2026

**Full context: {count(full)}. Dynamic context: {count(dynamic)}. No context: {count(no)}. Dynamic selection removed {s['input_reduction_percent']:.1f}% of answer-model input tokens.**

This is a separate workload from the 14.8% website-generation-prompt replay: it answers questions about frozen public text from the same eight generated sites plus Orbit's fictional sample memory. It does not rerun the private website-generation prompt or regenerate websites. The source corpus contains 71 coherent paragraphs across 11 documents. Do not extrapolate its compression rate to website generation.

Dynamic accuracy on answerable questions alone was **{answerable_correct}/{len(answerable)} ({100*answerable_correct/len(answerable):.1f}%)**; all nine deliberately unanswerable questions were correctly answered with null in every arm.

## Results

| Arm | Correct answers | Reference input tokens | Provider input tokens | Provider output tokens |
| --- | ---: | ---: | ---: | ---: |
'''
for key,title in [('full','Full context'),('dynamic','Dynamic context'),('no_context','No-context control')]:
    x=s['arms'][key]
    header+=f"| {title} | {count(x)} | {x['reference_input_tokens']:,} | {x['provider_usage']['prompt_tokens']:,} | {x['provider_usage']['completion_tokens']:,} |\n"
header+=f'''
- Input tokens removed: **{s['input_tokens_removed']:,}**, including the same question and answer instructions in both arms.
- Context payload alone: **{s['context_tokens_full']:,} → {s['context_tokens_dynamic']:,} tokens ({context_reduction:.1f}% removed)**. Both arms use the engine's identical JSONL provenance format. The full raw-text corpus without provenance is {r['rows'][0]['full_raw_text_tokens']:,} tokens per question; the full JSONL corpus is {r['rows'][0]['full_context_tokens']:,}. No repeated filler was added.
- Accuracy change: **{s['accuracy_delta_percentage_points']:+.3f} percentage points**. Paired counts: {js(s['paired'])}.
- Correct dynamic answers on answerable questions: **{answerable_correct}/{len(answerable)}**. The no-context control failed all 23 answerable questions and passed all nine abstention cases.
- Gold evidence retained: **{s['evidence']['retained']}/{s['evidence']['total']} paragraph instances**; every required paragraph retained on {s['evidence']['all_required_retained_cases']}/{s['evidence']['answerable_cases']} answerable questions. Unanswerable questions have no gold evidence and are excluded from this denominator.
- Jev processing overhead: **{s['jev_usage']['input_tokens']:,} input and {s['jev_usage']['output_tokens']:,} output tokens**. These are additional provider-native tokens, excluded from the answer-model reduction. Token savings are not cost savings.
- Zero answer-call infrastructure errors in the measured run. Super API preflight calls returned HTTP 404 before the experiment; the measured calls use the direct OpenRouter endpoint with the same frozen answer model in every arm. Those failed preflights are excluded from accuracy.

## Accuracy by question type

| Type | Full | Dynamic | No context | Input reduction |
| --- | ---: | ---: | ---: | ---: |
'''
for kind,x in r['by_kind'].items():
    header+=f"| {kind} | {count(x['arms']['full'])} | {count(x['arms']['dynamic'])} | {count(x['arms']['no_context'])} | {x['input_reduction_percent']:.1f}% |\n"
header+='\n## Failures and omitted evidence\n\n'
if not failures:header+='No dynamic answer failed the frozen exact scorer. This does not establish universal equivalence.\n'
for row in failures:
    header+=f"### {row['id']}\n\n{row['question']}\n\n- Gold: `{js(row['expected'])}`\n- Full: `{js(row['answers']['full'].get('answer'))}` ({mark(row['answers']['full'])})\n- Dynamic: `{js(row['answers']['dynamic'].get('answer'))}` ({mark(row['answers']['dynamic'])})\n- Missing source evidence: `{js(row['missing_evidence'])}`\n\n"
header+='''The tribute failure omitted the speech-limit paragraph and correctly abstained on that field. The prosthetic failure omitted the displayed baseline/optimized values, then used nearby illustrative 6-hour/55-minute prose to answer 305 instead of the requested displayed-value difference of 291. The vehicle failure omitted the numeric CG height and abstained. One additional gold paragraph omission did not cause an answer failure; retention and final correctness are separate measures.

## Frozen protocol and limits

- Gold questions, expected JSON objects, and supporting source quotes were authored and frozen before model calls. Neither gold answers nor evidence annotations are sent to Jev or the answer model. No policies, thresholds, questions, or gold answers were tuned after observing outcomes.
- Answer model: `google/gemini-3.8-flash` via OpenRouter, temperature 0, 4,096 maximum completion tokens, provider-default reasoning. All response model names, finish reasons, token receipts, and answers are published in the JSON. No tools, web search, external knowledge, or previous turns are supplied. Each arm is an independent completion.
- Jev: existing relevance policy v1, cutoff 0.50, 12-paragraph batches, three workers, 1,000,000-token budget, cold queries. The returned actual Jev version is retained per question.
- The first question was a connectivity pilot and its successful responses were retained; remaining calls were shuffled with seed 20260920 and run with four workers. The harness checkpoints results for resumption without rerunning successful answers. No best-of selection or failed-answer retries.
- Primary score is all-fields-correct per question. Numeric tolerance is 0.000001 after requested rounding; strings ignore case and repeated whitespace; booleans require booleans; missing facts require explicit JSON null. Missing, extra, malformed, or incorrect fields fail. There is no subjective AI judge. This tests structured source-grounded answers, not free-form prose quality.
- The no-context control measures what the same model can answer or abstain from without sources. Unanswerable cases are deliberately included; abstention gets credit there but fails answerable questions.
- Counts use o200k_base for exact message content, including instructions, question, JSONL provenance, and separators. Chat-envelope overhead is excluded from reference counts; provider-native token receipts are reported separately. Output/reasoning and Jev tokens are not hidden inside the reported input reduction.
- The public pages are test documents, not verified medical, legal, financial, technical, or historical authority. Questions test faithful reading of their frozen initial HTML text. They do not validate the correctness of the sites or their interactive computations. Static snapshots may contain stale or internally inconsistent display values.
- This is one small, hand-authored run on one answer model. The questions share documents, so observations are correlated. The Wilson intervals below are descriptive single-proportion intervals, not a paired non-inferiority test or proof of deployment-wide equivalence. No held-out validation or repeated-run stability study was performed.
'''
for arm,title in [('full','Full'),('dynamic','Dynamic'),('no_context','No context')]:
    interval=s['arms'][arm]['wilson_95_percent']
    header+=f"- {title} descriptive 95% Wilson accuracy interval: {interval[0]:.1f}%–{interval[1]:.1f}%.\n"
header+='''
## Reproduce

Install the engine, set `TYPESAFE_API_KEY`, and set `ANSWER_API_KEY` plus `ANSWER_API_BASE_URL=https://openrouter.ai/api/v1`. An OpenAI-compatible endpoint is required; the fixture is public. Without answer-specific variables the harness uses the installed Super API configuration. Provider routes can change: verify the returned model. Credentials never belong in fixtures or commits.

```sh
python3 benchmarks/question_accuracy.py \\
  --fixture benchmarks/fixtures/question-answering-2026-09-20.json \\
  --model google/gemini-3.8-flash \\
  --output artifacts/qa-reproduction
python3 scripts/render_accuracy_report.py \\
  --results artifacts/qa-reproduction/report.json
```

The renderer requires matplotlib and writes report/demo artifacts. Keep a reproduction separate until its results are reviewed. Use a fresh output directory for a new independent run; rerunning the same directory resumes saved responses.

- [Frozen source corpus, questions, gold answers, and evidence](fixtures/question-answering-2026-09-20.json)
- [Full measured results, raw answers, usage, and relevance scores](results/question-accuracy-2026-09-20.json)
- [Benchmark harness](question_accuracy.py)
- [Existing website-generation input replay](website-replay-2026-09-20.md)

## Every question

| Question ID | Full | Dynamic | No context | Full input | Dynamic input | Removed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
'''
for row in r['rows']:
    f=row['answers']['full']['input_tokens'];d=row['answers']['dynamic']['input_tokens']
    header+=f"| {row['id']} | {mark(row['answers']['full'])} | {mark(row['answers']['dynamic'])} | {mark(row['answers']['no_context'])} | {f:,} | {d:,} | {100*(f-d)/f:.1f}% |\n"
for row in r['rows']:
    header+=f"\n### {row['id']}\n\n{row['question']}\n\nGold: `{js(row['expected'])}`\n\n"
    for arm in ['full','dynamic','no_context']:
        header+=f"- {arm}: `{js(row['answers'][arm].get('answer'))}`\n"
(ROOT/'benchmarks/question-accuracy-2026-09-20.md').write_text(header)
trs=''.join(f'<tr><th scope="row">{html.escape(group)}</th><td>{count(x["arms"]["full"])}</td><td>{count(x["arms"]["dynamic"])}</td><td>{x["input_reduction_percent"]:.1f}%</td></tr>' for group,x in r['by_group'].items())
failure_note=(f'{len(failures)} dynamic answer(s) failed. See the report for exact missing evidence and answers.' if failures else 'No dynamic answers failed this run; a small sample does not prove equivalence.')
section=f'''<section id="accuracy" class="benchmarks" aria-labelledby="accuracy-title">
<div class="section-head"><div><p class="eyebrow">QUESTIONS, ANSWERS, AND EVIDENCE</p><h2 id="accuracy-title">Does less context<br>keep the answer right?</h2></div><p>{n} frozen questions. One answer model. Three independent arms.<br>Public text from the eight sites plus the demo’s sample memory.</p></div>
<div class="benchmark-summary"><div><strong>{dynamic['correct']}/{n}</strong><span>dynamic-context answers correct</span></div><p><b>{s['input_reduction_percent']:.1f}% less answer-model input</b><br>Full context: {count(full)} · No context: {count(no)}<br>Accuracy change: {s['accuracy_delta_percentage_points']:+.1f} percentage points.<br>Answerable questions: {answerable_correct}/{len(answerable)} · Missing-information checks: 9/9.</p></div>
<figure class="benchmark-figure"><picture><source media="(max-width: 600px)" srcset="{{{{ base }}}}/assets/benchmark-accuracy-mobile.svg"><img src="{{{{ base }}}}/assets/benchmark-accuracy.svg" width="1050" height="720" loading="lazy" alt="Answer accuracy: full {count(full)}, dynamic {count(dynamic)}, no context {count(no)}. Dynamic input tokens decreased {s['input_reduction_percent']:.1f} percent."></picture><figcaption>Gemini 3.8 Flash answers; Jev selects at cutoff 0.50. Exact all-fields-correct scoring against answers frozen before the run. Input includes the question, instructions, and source metadata. Jev processing tokens are additional.</figcaption></figure>
<div class="benchmark-conclusion"><strong>A separate question-answering workload.</strong><p>These questions use 71 paragraphs of published site text and sample memory, not the full website-generation prompt above. The compression rates are not interchangeable. {failure_note} One model, one run, {n} hand-authored questions; this does not establish regenerated-site quality.</p></div>
<details class="benchmark-table"><summary>Compare accuracy and input saved by source</summary><div class="benchmark-table-scroll"><table><thead><tr><th scope="col">Source</th><th scope="col">Full accuracy</th><th scope="col">Dynamic accuracy</th><th scope="col">Input removed</th></tr></thead><tbody>{trs}</tbody></table></div></details>
<div class="benchmark-links"><a href="{report_url}" target="_blank" rel="noreferrer">Inspect every question, answer, and limitation ↗</a><a href="{{{{ base }}}}/assets/benchmark-accuracy.png" download>Download accuracy graph ↓</a></div>
</section>'''
(ROOT/'demo/templates/accuracy.html').write_text(section+'\n')
print(json.dumps({'full':count(full),'dynamic':count(dynamic),'no_context':count(no),'input_reduction':s['input_reduction_percent'],'context_reduction':context_reduction,'failures':[f['id'] for f in failures]},indent=2))
