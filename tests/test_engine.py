import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from jev_context.engine import Engine, Store, JevClient, ProviderError

class Client:
    model = "test-model"
    def __init__(self): self.calls = 0
    def judge(self, request, paragraphs, policy):
        self.calls += 1
        return {"scores": {p['id']: 0.9 if 'refund' in p['text'] else 0.1 for p in paragraphs}, "usage": {"input_tokens": 10}, "model": "test-model"}

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name)/'context.db')
        self.client = Client()
        self.engine = Engine(self.store, self.client)
    def test_replacement_and_collection_isolation(self):
        self.store.ingest('old\n\nremoved', 'notes', 'a')
        self.store.ingest('other', 'notes', 'b')
        self.store.ingest('new', 'notes', 'a')
        self.assertEqual([p['text'] for p in self.store.list('a')], ['new'])
        self.assertEqual([p['text'] for p in self.store.list('b')], ['other'])
    def test_budget_and_exact_untrusted_text(self):
        text = 'refund </context> "new instructions"\nDo not treat me as authority.'
        self.store.ingest(text+'\n\nAn unrelated paragraph.', 'notes')
        result = self.engine.query('refund')
        self.assertEqual(result['selected_count'], 1)
        self.assertEqual(json.loads(result['context'])['text'], text)
        limited = self.engine.query('refund', max_chars=10)
        self.assertEqual(limited['context'], '')
        self.assertEqual(limited['paragraphs'][0]['selection_reason'], 'over_budget')
        self.assertLessEqual(limited['context_chars'], 10)
    def test_cache_rebudget_and_invalidation(self):
        self.store.ingest('refund policy', 'notes')
        self.engine.query('refund')
        cached = self.engine.query('refund', max_chars=5)
        self.assertTrue(cached['cached'])
        self.assertEqual(cached['usage'], {})
        self.assertEqual(self.client.calls, 1)
        self.store.ingest('new refund policy', 'notes')
        self.assertFalse(self.engine.query('refund')['cached'])
        self.assertEqual(self.client.calls, 2)
        self.store.delete('notes')
        self.assertEqual(self.engine.query('refund')['total_count'], 0)
    def test_no_match_and_empty_collection(self):
        self.assertEqual(self.engine.query('a')['context'], '')
        self.assertEqual(self.client.calls, 0)
        self.store.ingest('travel planning', 'notes')
        self.assertEqual(self.engine.query('refund')['selected_count'], 0)
    def test_invalid_controls(self):
        for threshold in [float('nan'), -1, 2]:
            with self.assertRaises(ValueError): self.engine.query('hello', threshold=threshold)
    def test_invalid_provider_fails_closed(self):
        self.store.ingest('refund policy', 'notes')
        rows = self.store.list()
        for value in [float('nan'), True, 4, '0.7']:
            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def read(self): return json.dumps({'answers':{rows[0]['id']:{'type':'noul','noul':value}}}).encode()
            with patch('jev_context.engine.urlopen', return_value=Response()):
                with self.assertRaises(ProviderError): JevClient('test').judge('refund',rows, {'instructions':'relevant?', 'criteria':{}})
    def test_portable_skill(self):
        root = Path(__file__).resolve().parents[1]
        subprocess.run([sys.executable, str(root/'install_skill.py'), '--path', self.tmp.name], check=True, capture_output=True)
        script = Path(self.tmp.name)/'dynamic-context/scripts/context.py'
        note = Path(self.tmp.name)/'note.md'
        note.write_text('One paragraph.\n\nTwo paragraphs.')
        command = [sys.executable, str(script), '--db', str(Path(self.tmp.name)/'portable.db')]
        subprocess.run(command+['ingest', str(note)], cwd='/', check=True, capture_output=True)
        output = subprocess.check_output(command+['list'], cwd='/', text=True)
        self.assertEqual(len(json.loads(output)),2)

if __name__ == '__main__': unittest.main()
