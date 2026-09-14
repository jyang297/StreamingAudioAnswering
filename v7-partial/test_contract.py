import unittest
from replay import parse_output, payload


class BoundaryTests(unittest.TestCase):
    def test_no_future_or_gold_in_early_payload(self):
        c = {'snapshots': ['Who', 'Who is Alice?'], 'context': [],
             'SQL': 'SECRET GOLD', 'evidence': 'FUTURE HINT'}
        self.assertEqual(payload(c, 0), {'text': 'Who', 'confirmed_context': [], 'final': False})

    def test_reject_sql_field_and_empty_search(self):
        for obj in ({'action': 'search', 'question': 'Who?', 'sql': 'SELECT 1'},
                    {'action': 'search', 'question': ' '},
                    {'action': 'wait', 'question': 'invented'}):
            with self.assertRaises(ValueError):
                parse_output(obj)

    def test_wait_and_final(self):
        self.assertEqual(parse_output({'action': 'wait', 'question': None})['action'], 'wait')
        self.assertTrue(payload({'snapshots': ['Who?'], 'context': []}, 0)['final'])


if __name__ == '__main__':
    unittest.main()
