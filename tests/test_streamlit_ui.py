"""UI tests run when Streamlit is installed; no API calls are made."""
import importlib.util
import unittest
from pathlib import Path

@unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Install requirements.txt to run Streamlit UI tests')
class StreamlitTests(unittest.TestCase):
    def test_offline_flow_and_stale_report(self):
        from streamlit.testing.v1 import AppTest
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
        self.assertFalse(at.exception)
        next(w for w in at.checkbox if w.label=='Offline sample mode').check().run()
        next(w for w in at.button if w.label=='Compare strategies').click().run(timeout=30)
        self.assertFalse(at.exception)
        self.assertEqual(len(at.session_state['runs']),1)
        at.number_input[0].set_value(100.0).run()
        self.assertTrue(any('Inputs have changed' in w.value for w in at.warning))
        next(w for w in at.button if w.label=='Compare strategies').click().run(timeout=30)
        self.assertFalse(at.exception)
        self.assertEqual(len(at.session_state['runs']),2)

if __name__=='__main__':unittest.main()
