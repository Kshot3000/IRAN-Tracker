import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('collector', pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'refresh_data.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CollectorTests(unittest.TestCase):
    def test_failed_refresh_preserves_observation_and_original_fetch_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            original = {'ok': True, 'data': [{'name': 'Actual vessel'}], 'fetchedAt': '2026-10-03T10:00:00Z', 'observedAt': '2026-10-03T09:30:00Z'}
            (p / 'ships.json').write_text(json.dumps(original))
            def fail():
                raise ValueError('source unavailable')
            with patch.object(module, 'OUT', p), patch.dict(module.JOBS, {'ships': fail}):
                _, status = module.collect('ships')
            result = json.loads((p / 'ships.json').read_text())
            self.assertEqual(result['observedAt'], original['observedAt'])
            self.assertEqual(result['fetchedAt'], original['fetchedAt'])
            self.assertEqual(result['data'], original['data'])
            self.assertEqual(status['status'], 'cached')
            self.assertIn('lastFailure', result)
    def test_no_snapshot_means_unavailable_not_fake_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fail():
                raise ValueError('source unavailable')
            with patch.object(module, 'OUT', pathlib.Path(tmp)), patch.dict(module.JOBS, {'ships': fail}):
                _, status = module.collect('ships')
            self.assertEqual(status['status'], 'unavailable')
            self.assertIsNone(json.loads((pathlib.Path(tmp) / 'ships.json').read_text())['data'])
    def test_recovery_clears_old_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            (p / 'summary.json').write_text(json.dumps({'ok': True, 'lastFailure': {'message': 'old'}}))
            def success():
                return {'total_ships': 0}, '2026-10-03T12:00:00Z', {'name': 'Test'}
            with patch.object(module, 'OUT', p), patch.dict(module.JOBS, {'summary': success}):
                _, status = module.collect('summary')
            self.assertEqual(status['status'], 'ok')
            self.assertNotIn('lastFailure', json.loads((p / 'summary.json').read_text()))

if __name__ == '__main__':
    unittest.main()
