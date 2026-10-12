import copy
import json
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from core import ROOT, prepare, validate, generate, select_winner, ANALYSIS_SCHEMA, PLAN_SCHEMA
from demo import sample_report

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
        from io import BytesIO
        analysis={k:self.report[k] for k in ANALYSIS_SCHEMA['properties']}
        plan={k:self.report[k] for k in PLAN_SCHEMA['properties']}
        def response(value):
            return BytesIO(json.dumps({'status':'completed','output':[{'content':[
                {'type':'output_text','text':json.dumps(value)}]}]}).encode())
        with patch('urllib.request.urlopen',side_effect=[response(analysis),response(plan)]) as call:
            actual=generate(self.context,{'OPENAI_API_KEY':'test-key','OPENAI_MODEL':'gpt-4o-mini'})
        self.assertEqual(actual,self.report)
        self.assertEqual(call.call_count,2)
        first=json.loads(call.call_args_list[0].args[0].data)
        second=json.loads(call.call_args_list[1].args[0].data)
        self.assertTrue(first['text']['format']['strict']);self.assertFalse(first['store'])
        self.assertNotIn('recommended_id',first['text']['format']['schema']['properties'])
        self.assertNotIn('recommended_id',second['text']['format']['schema']['properties'])
        self.assertEqual(json.loads(second['input'])['selected_option']['id'],actual['recommended_id'])
    def test_ties_follow_original_order(self):
        for o in self.report['options']:
            o.update(impact_score=3,feasibility_score=3,evidence_score=3)
        self.assertEqual(select_winner(self.report,self.context)['id'],'pickup')
    def test_overbudget_high_score_cannot_win(self):
        self.report['options'][0].update(cost_eur=2500,impact_score=5,feasibility_score=5,evidence_score=5)
        self.assertEqual(select_winner(self.report,self.context)['id'],'loyalty')
    def test_second_stage_overbudget_still_rejected(self):
        analysis={k:self.report[k] for k in ANALYSIS_SCHEMA['properties']}
        plan={k:copy.deepcopy(self.report[k]) for k in PLAN_SCHEMA['properties']}
        plan['experiment']['costs'][0]['amount_eur']=99999
        with patch('core.request_structured',side_effect=[analysis,plan]):
            with self.assertRaisesRegex(ValueError,'exceeds the budget'):
                generate(self.context,{'OPENAI_API_KEY':'test-key'})


if __name__ == '__main__': unittest.main()
