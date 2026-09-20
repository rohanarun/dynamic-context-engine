import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from jev_context.engine import Engine, Store, ProviderError

class ParallelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name)/'memory.db')
        self.store.ingest('\n\n'.join(f'Paragraph {i}.' for i in range(7)),'notes')

    def test_batches_overlap_cover_every_paragraph_and_match_serial(self):
        class Client:
            model='parallel-test'
            def __init__(self,barrier=None):self.barrier=barrier;self.seen=[];self.calls=0;self.lock=threading.Lock()
            def judge(self,request,paragraphs,policy):
                with self.lock:
                    self.calls+=1;number=self.calls;self.seen.extend(p['id'] for p in paragraphs)
                if self.barrier and number<=3:self.barrier.wait(timeout=3)
                return {'scores':{p['id']:.9 for p in paragraphs},'usage':{'input_tokens':len(paragraphs)},'model':self.model}
        parallel=Client(threading.Barrier(3))
        a=Engine(self.store,parallel,workers=3,batch_size=2,cache_ttl=0).query('all')
        b=Engine(self.store,Client(),workers=1,batch_size=2,cache_ttl=0).query('all')
        self.assertEqual(a['context'],b['context'])
        self.assertEqual(sorted(parallel.seen),sorted(p['id'] for p in self.store.list()))
        self.assertEqual(a['execution']['peak_parallel_batches'],3)
        self.assertEqual(a['execution']['batches_dispatched'],4)
        self.assertEqual(a['execution']['paragraphs_judged'],7)
        self.assertEqual(a['usage']['input_tokens'],7)
        self.assertEqual(b['execution']['peak_parallel_batches'],1)
        self.assertGreaterEqual(a['timing_ms']['total'],a['timing_ms']['inference'])

    def test_failure_never_caches_partial_context(self):
        class Client:
            model='failure-test'
            def judge(self,request,paragraphs,policy):
                if paragraphs[0]['position']==2:raise ProviderError('one batch failed')
                return {'scores':{p['id']:.9 for p in paragraphs},'usage':{},'model':self.model}
        with self.assertRaises(ProviderError):Engine(self.store,Client(),batch_size=2).query('all')
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM judgments').fetchone()[0],0)

    def test_worker_change_reuses_scores_without_new_provider_calls(self):
        class Client:
            model='cache-test'
            def judge(self,request,paragraphs,policy):
                return {'scores':{p['id']:.9 for p in paragraphs},'usage':{'input_tokens':7},'model':self.model}
        client=Client()
        Engine(self.store,client,workers=1).query('all')
        with patch.object(client,'judge',side_effect=AssertionError('cache must avoid provider')):
            result=Engine(self.store,client,workers=8).query('all')
        self.assertTrue(result['cached']);self.assertEqual(result['usage'],{})
        self.assertEqual(result['execution']['batches_dispatched'],0)
        self.assertEqual(result['execution']['peak_parallel_batches'],0)

    def test_bounded_settings_and_cli(self):
        for n in [0,33,True,1.5]:
            with self.assertRaises(ValueError):Engine(self.store,workers=n)
        with patch.dict(os.environ,{'JEV_CONTEXT_WORKERS':'4','JEV_CONTEXT_BATCH_SIZE':'2'}):
            engine=Engine(self.store);self.assertEqual((engine.workers,engine.batch_size),(4,2))
        root=Path(__file__).resolve().parents[1]
        result=json.loads(subprocess.check_output([sys.executable,'-m','jev_context.cli','--db',str(Path(self.tmp.name)/'empty.db'),'query','test','--workers','2','--batch-size','1','--json'],cwd=root,text=True))
        self.assertEqual(result['execution']['workers_limit'],2)
        self.assertEqual(result['execution']['batch_size'],1)
        self.assertEqual(result['execution']['paragraphs_judged'],0)
