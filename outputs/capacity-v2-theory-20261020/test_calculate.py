import unittest,copy
import calculate as c

class Tests(unittest.TestCase):
 def setUp(self):
  self.q,self.m,self.conf,self.a=[c.read(n) for n in ['request.json','model-input.json','config.json','assumptions.json']]
 def test_hand_arithmetic_and_cache(self):
  r=c.calculate(self.q,self.m,self.conf,self.a)
  self.assertEqual(r['inputWorkTopPerRequest'],128)
  self.assertEqual(r['cache']['logicalBytesPerRequest'],17375064)
  self.assertAlmostEqual(r['central']['meanTtftBudgetMs'],1442.857142857143)
  self.assertAlmostEqual(r['central']['busyDecodeStepBudgetMs'],16.285714285714285)
 def test_spare_does_not_add_work_capacity(self):
  before=c.calculate(self.q,self.m,self.conf,self.a);self.q['spareGroups']=1
  after=c.calculate(self.q,self.m,self.conf,self.a)
  self.assertEqual(after['budgetCards']['totalCards'],32)
  self.assertEqual(before['central'],after['central'])
 def test_stricter_goal_and_cache_growth(self):
  self.q['ttftMs']=1000
  self.assertIsNone(c.calculate(self.q,self.m,self.conf,self.a)['budgetCards'])
  self.q['inputTokens']=16000
  self.assertEqual(c.calculate(self.q,self.m,self.conf,self.a)['cache']['logicalBytesPerRequest'],30295064)
if __name__=='__main__':unittest.main()
