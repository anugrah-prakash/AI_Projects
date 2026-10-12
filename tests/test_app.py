import copy
import json
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from core import ROOT, prepare, validate, generate
from demo import sample_report
from app import Handler

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'sample_data.json').read_text())
        self.context=prepare(self.data)
        self.report=sample_report(self.context)
    def test_budget_scenarios(self):
        for budget in [0,50,199,500,2000]:
            c=prepare({**self.data,'budget':budget});r=sample_report(c)
            self.assertLessEqual(sum(x['amount_eur'] for x in r['experiment']['costs']),budget)
    def test_reject_overbudget(self):
        self.report['experiment']['costs'][0]['amount_eur']=3000
        with self.assertRaises(ValueError):validate(self.report,self.context)
    def test_reject_invented_source(self):
        self.report['situation'][0]['sources']=['F999']
        with self.assertRaises(ValueError):validate(self.report,self.context)
    def test_reject_uncited_fact(self):
        self.report['situation'][0]['sources']=[]
        with self.assertRaises(ValueError):validate(self.report,self.context)
    def test_reject_bad_budget(self):
        for bad in [-1,float('nan'),float('inf'),True,'200']:
            with self.assertRaises(ValueError):prepare({**self.data,'budget':bad})
    def test_reject_wrong_winner(self):
        self.report['recommended_id']='ads'
        with self.assertRaises(ValueError):validate(self.report,self.context)
    def test_blank_optional_evidence(self):
        c=prepare({**self.data,'feedback':'','competitors':''})
        self.assertFalse(any(k.startswith('F') for k in c['evidence']))
    def test_no_key(self):
        with self.assertRaises(ValueError):generate(self.context,{'OPENAI_API_KEY':''})
    def test_api_contract_mock(self):
        result={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(self.report)}]}]}
        from io import BytesIO
        with patch('urllib.request.urlopen',return_value=BytesIO(json.dumps(result).encode())) as call:
            actual=generate(self.context,{'OPENAI_API_KEY':'test-key','OPENAI_MODEL':'gpt-4o-mini'})
        self.assertEqual(actual,self.report)
        sent=json.loads(call.call_args.args[0].data)
        self.assertTrue(sent['text']['format']['strict']);self.assertFalse(sent['store'])

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def test_pages_and_secret_is_not_served(self):
        for route in ['/','/app.js','/style.css','/api/status']:
            with urllib.request.urlopen(self.base+route) as r:self.assertEqual(r.status,200)
        with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(self.base+'/.env')
        self.assertEqual(cm.exception.code,404)
    def test_offline_complete_flow(self):
        data=json.loads((ROOT/'sample_data.json').read_text());data['demo']=True
        req=urllib.request.Request(self.base+'/api/compare',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req) as r: result=json.load(r)
        self.assertEqual(len(result['report']['options']),3)
        data['constraints']='No rewards allowed.'
        req.data=json.dumps(data).encode()
        with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code,400)
    def test_cross_origin_rejected(self):
        req=urllib.request.Request(self.base+'/api/compare',data=b'{}',headers={'Content-Type':'application/json','Origin':'https://elsewhere.example'})
        with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code,403)

if __name__=='__main__':unittest.main()
