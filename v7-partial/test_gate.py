import unittest
from replay_gated import length_gate, payload, expanded_cases


class GateTests(unittest.TestCase):
    def test_short_partial_skips_but_final_survives(self):
        for text in ('who', 'and', 'And Batman?', '...'):
            self.assertFalse(length_gate(text, False)['allow'])
            self.assertTrue(length_gate(text, True)['allow'])

    def test_punctuation_is_not_length(self):
        self.assertFalse(length_gate('who ? ! ,', False)['allow'])
        self.assertTrue(length_gate('Who is Batman?', False)['allow'])

    def test_compound_future_is_not_injected(self):
        c = {'snapshots': ['Who?', 'Who? Also why?'], 'context': [],
             'expected_questions': ['Who?', 'why?']}
        self.assertNotIn('expected_questions', payload(c, 0))
        self.assertEqual(payload(c, 0)['text'], 'Who?')


if __name__ == '__main__':
    unittest.main()
