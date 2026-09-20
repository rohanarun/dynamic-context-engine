import os
import tempfile
import unittest
from unittest.mock import patch

class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ['JEV_CONTEXT_DB'] = cls.tmp.name+'/demo.db'
        from demo.app import app
        cls.client = app.test_client()
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
        os.environ.pop('JEV_CONTEXT_DB', None)
    def test_sample_and_no_write_route(self):
        self.assertEqual(len(self.client.get('/demos/context-engine/api/sample').json['paragraphs']),12)
        self.assertEqual(self.client.post('/demos/context-engine/api/ingest',json={}).status_code,404)
    def test_bad_inputs_without_provider(self):
        for payload in [[], {}, {'request':'x','threshold':'nan'}, {'request':'x','max_tokens':None}, {'request':'x','max_tokens':1000001}, {'request':'x','max_tokens':True}, {'request':'x','max_tokens':1.5}]:
            self.assertEqual(self.client.post('/demos/context-engine/api/select',json=payload).status_code,400)
    def test_provider_failure_exposed_without_key(self):
        from jev_context.engine import ProviderError
        with patch('demo.app.engine.query',side_effect=ProviderError('Jev unavailable')):
            response=self.client.post('/demos/context-engine/api/select',json={'request':'unique test request'})
        self.assertEqual(response.status_code,502)
        self.assertEqual(response.json['error'],'Jev unavailable')

    def test_token_budget_defaults_and_maximum(self):
        with patch('demo.app.engine.query', return_value={}) as query:
            for payload in [{'request':'test'}, {'request':'test','max_tokens':1000000}]:
                response = self.client.post('/demos/context-engine/api/select',json=payload)
                self.assertEqual(response.status_code,200)
                self.assertEqual(query.call_args.kwargs['max_tokens'],1000000)
