"""Small live semantic smoke suite; provider usage is billable, no fake judgments."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jev_context import Engine, Store
sample=json.loads((Path(__file__).resolve().parents[1]/'demo/sample.json').read_text())
with tempfile.TemporaryDirectory() as tmp:
    store=Store(Path(tmp)/'eval.db')
    for doc in sample['documents']: store.ingest(doc['text'],doc['source'])
    engine=Engine(store,cache_ttl=0)
    cases=[
        (sample['requests'][0], {'support.md': [0,1]}, False),
        (sample['requests'][1], {'product.md': [1,2,3]}, False),
        (sample['requests'][2], {'engineering.md': [0,1]}, False),
        (sample['requests'][3], {}, True),
    ]
    failed=[]
    for query, required, empty in cases:
        result=engine.query(query)
        selected={(p['source'],p['position']) for p in result['paragraphs'] if p['selected']}
        passed=(not selected if empty else all((source,pos) in selected for source,positions in required.items() for pos in positions))
        print(json.dumps({'request':query,'passed':passed,'selected':sorted(selected),'elapsed_ms':result['elapsed_ms'],'models':result['models'],'usage':result['usage']}))
        if not passed: failed.append(query)
    if failed: raise SystemExit(f'{len(failed)} live regression cases failed')
