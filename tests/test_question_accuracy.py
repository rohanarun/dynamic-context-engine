import unittest
from benchmarks.question_accuracy import grade, wilson, messages

class QuestionAccuracyScoringTests(unittest.TestCase):
    def test_null_requires_explicit_abstention(self):
        self.assertTrue(grade({'unknown':None},{'unknown':None})['correct'])
        self.assertFalse(grade({'unknown':None},{})['correct'])
        self.assertFalse(grade({'unknown':None},{'unknown':'unknown'})['correct'])

    def test_types_fields_and_all_or_nothing(self):
        gold={'count':1,'permission':False}
        self.assertTrue(grade(gold,{'count':1.0,'permission':False})['correct'])
        self.assertFalse(grade(gold,{'count':True,'permission':False})['correct'])
        self.assertFalse(grade(gold,{'count':1,'permission':True})['correct'])
        self.assertFalse(grade(gold,{'count':1,'permission':False,'extra':1})['correct'])

    def test_rounding_and_string_normalization(self):
        self.assertTrue(grade({'result':.03},{'result':.030000000000001})['correct'])
        self.assertFalse(grade({'result':1.59},{'result':1.6})['correct'])
        self.assertTrue(grade({'city':'Lisbon'},{'city':' LISBON '})['correct'])

    def test_perfect_small_sample_is_not_proof(self):
        low,high=wilson(32,32)
        self.assertLess(low,90)
        self.assertAlmostEqual(high,100)

    def test_gold_never_enters_messages(self):
        msg=messages('reference','question')
        self.assertEqual(msg[1]['content'],'Reference paragraphs (JSON Lines):\nreference\n\nQuestion:\nquestion')
        self.assertEqual(len(msg),2)
