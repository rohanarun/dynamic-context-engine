#!/usr/bin/env python3
"""Measure real Jev batch overlap and paired time to a complete answer.
Raw private archive text is never written to the public report.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jev_context.engine import Engine, Store, assemble, token_count
from benchmarks.question_accuracy import answer_call

ROOT=Path(__file__).resolve().parents[1]

def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def quantile(values,p):
    values=sorted(values);index=(len(values)-1)*p;lo=int(index);hi=min(lo+1,len(values)-1)
    return values[lo]+(values[hi]-values[lo])*(index-lo)
def stats(values):
    return {'n':len(values),'median_ms':round(statistics.median(values),3),'p95_ms':round(quantile(values,.95),3),'min_ms':round(min(values),3),'max_ms':round(max(values),3)} if values else None

def compact(result):
    return {k:result[k] for k in ['timing_ms','execution','usage','models','cached','context_tokens','selected_count','total_count']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,help='Optional authorized private website-replay cases.json')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repetitions',type=int,default=3)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    sample=json.loads((ROOT/'demo/sample.json').read_text())
    fixture=json.loads((ROOT/'benchmarks/fixtures/question-answering-2026-09-20.json').read_text())
    datasets=[{'id':'sample-12','documents':sample['documents'],'queries':[{'id':f'sample-{i}','question':q} for i,q in enumerate(sample['requests'][:3])]},
              {'id':'qa-71','documents':fixture['documents'],'queries':[c for c in fixture['cases'] if c['id'] in ['trade-fact','vehicle-multi','orbit-refund']]}]
    if args.archive:
        cases=json.loads(args.archive.read_text())['cases'][:3]
        assert len({sha(c['system']) for c in cases})==1
        datasets.append({'id':'website-prompt-78','documents':[{'source':'website-generation-prompt','text':cases[0]['system']}],
                         'queries':[{'id':c['slug'],'question':c['request']} for c in cases]})
    token_count('Tokenizer initialized outside timed queries.')
    protocol={'seed':20260920,'batch_size':12,'workers':[1,3,8],'repetitions':args.repetitions,'threshold':.5,'max_tokens':1_000_000,
              'model':'google/gemini-3.8-flash','timing_clock':'time.perf_counter','location':'user Mac -> provider HTTP APIs',
              'engine_sha256':sha((ROOT/'jev_context/engine.py').read_text()),'harness_sha256':sha(Path(__file__).read_text()),
              'policy_sha256':sha((ROOT/'jev_context/policy.json').read_text()),
              'qa_fixture_sha256':sha((ROOT/'benchmarks/fixtures/question-answering-2026-09-20.json').read_text()),
              'sample_sha256':sha((ROOT/'demo/sample.json').read_text()),'end_to_end_rounds':1,
              'cache':'Local score cache bypassed for cold measurements; immediate warm repetitions use saved scores. Provider caches cannot be forced off.'}
    report_path=args.output/'report.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else {'observed_at':datetime.now(timezone.utc).isoformat(),'protocol':protocol,'datasets':[],'retrieval':[],'answers':[]}
    if report['protocol']!=protocol:raise SystemExit('Protocol changed; choose a new output directory')
    def save():report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    stores={}
    for dataset in datasets:
        store=Store(args.output/(dataset['id']+'.sqlite3'))
        for d in dataset['documents']:store.ingest(d['text'],d['source'])
        stores[dataset['id']]=store
        info={'id':dataset['id'],'paragraphs':len(store.list()),'raw_tokens':token_count('\n\n'.join(d['text'] for d in dataset['documents'])),
              'corpus_sha256':sha(json.dumps(dataset['documents'],sort_keys=True)),
              'queries':[{'id':q['id'],'request_sha256':sha(q['question'])} for q in dataset['queries']]}
        if not any(d['id']==info['id'] for d in report['datasets']):report['datasets'].append(info)
    jobs=[(dataset,q,repeat,workers) for dataset in datasets for q in dataset['queries'] for repeat in range(args.repetitions) for workers in protocol['workers']]
    rng=random.Random(protocol['seed']);rng.shuffle(jobs)
    for dataset,q,repeat,workers in jobs:
        identity=f"{dataset['id']}:{q['id']}:{repeat}:{workers}"
        if any(r['id']==identity for r in report['retrieval']):continue
        store=stores[dataset['id']]
        if workers==8:
            with store.connect() as db:db.execute('DELETE FROM judgments')
        engine=Engine(store,workers=workers,batch_size=12,cache_ttl=3600 if workers==8 else 0)
        started=time.perf_counter()
        result=engine.query(q['question'])
        wall=(time.perf_counter()-started)*1000
        assert not result['cached']
        assert result['execution']['paragraphs_judged']==result['total_count']
        assert len(result['paragraphs'])==len({p['id'] for p in result['paragraphs']})==result['total_count']
        row={'id':identity,'dataset':dataset['id'],'query_id':q['id'],'repeat':repeat,'workers':workers,'wall_ms':round(wall,3),**compact(result)}
        if workers==8:
            started=time.perf_counter();warm=engine.query(q['question']);warm_wall=(time.perf_counter()-started)*1000
            assert warm['cached'] and not warm['usage'] and warm['context']==result['context'] and warm['execution']['batches_dispatched']==0
            row['warm']={'wall_ms':round(warm_wall,3),**compact(warm)}
        report['retrieval'].append(row);save()
        print(json.dumps({'run':identity,'ms':round(wall),'peak':result['execution']['peak_parallel_batches']}),flush=True)
    # Stratified questions fixed before answer calls; no best-of or answer retries.
    rng=random.Random(protocol['seed'])
    chosen=[]
    for kind,count in [('lookup',4),('multi_paragraph',2),('calculation',2),('policy_exception',2),('unanswerable',2)]:
        chosen.extend(rng.sample([c for c in fixture['cases'] if c['kind']==kind],count))
    report['end_to_end_question_ids']=[c['id'] for c in chosen];save()
    store=stores['qa-71'];paragraphs=store.list()
    _,full=assemble(paragraphs,{p['id']:1 for p in paragraphs},0)
    api={'apiKey':os.environ['ANSWER_API_KEY'],'baseUrl':os.environ.get('ANSWER_API_BASE_URL','https://openrouter.ai/api/v1')}
    engine=Engine(store,workers=8,batch_size=12,cache_ttl=0)
    for case in chosen:
        arms=['full','dynamic'];rng.shuffle(arms)
        for arm in arms:
            if any(a['question_id']==case['id'] and a['arm']==arm for a in report['answers']):continue
            start=time.perf_counter()
            selected=engine.query(case['question']) if arm=='dynamic' else None
            context=selected['context'] if selected else full
            answer=answer_call(api,protocol['model'],context,case)
            total_ms=(time.perf_counter()-start)*1000
            if answer.get('error'):raise RuntimeError('Answer provider failure: '+answer['error'])
            assert answer['model']==protocol['model']
            row={'question_id':case['id'],'kind':case['kind'],'arm':arm,'total_ms':round(total_ms,3),'answer':answer}
            if selected:row['selection']=compact(selected)
            report['answers'].append(row);save()
            print(json.dumps({'question':case['id'],'arm':arm,'end_to_end_ms':round(total_ms),'correct':answer['grade']['correct']}),flush=True)
    report['retrieval_summary']={d['id']:{str(w):stats([r['wall_ms'] for r in report['retrieval'] if r['dataset']==d['id'] and r['workers']==w]) for w in protocol['workers']} for d in datasets}
    report['warm_summary']={d['id']:stats([r['warm']['wall_ms'] for r in report['retrieval'] if r['dataset']==d['id'] and 'warm' in r]) for d in datasets}
    report['answer_summary']={arm:{'total':stats([r['total_ms'] for r in report['answers'] if r['arm']==arm]),
                                     'generation':stats([r['answer']['elapsed_ms'] for r in report['answers'] if r['arm']==arm]),
                                     'correct':sum(r['answer']['grade']['correct'] for r in report['answers'] if r['arm']==arm)} for arm in ['full','dynamic']}
    report['paired_delta_ms']=[next(a['total_ms'] for a in report['answers'] if a['question_id']==c['id'] and a['arm']=='dynamic')-next(a['total_ms'] for a in report['answers'] if a['question_id']==c['id'] and a['arm']=='full') for c in chosen]
    save();print(json.dumps({k:report[k] for k in ['retrieval_summary','warm_summary','answer_summary']},indent=2))

if __name__=='__main__':main()
