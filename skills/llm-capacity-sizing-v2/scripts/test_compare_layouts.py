import unittest,copy
from compare_layouts import compare_layouts,REQUIRED

def layout(name,p,d,spare=0):return {'id':name,'workGroups':1,'prefillCardsPerGroup':p,'decodeCardsPerGroup':d,'spareGroups':spare}
def good():return {'checks':{k:{'ok':True,'reason':'Synthetic test constraint satisfied','basis':'Synthetic unit test assumption'} for k in REQUIRED}}

class LayoutComparisonTests(unittest.TestCase):
 def test_independent_evaluation_and_failure(self):
  called=[]
  def evaluate(l):
   called.append(l['id']);e=good()
   if l['decodeCardsPerGroup']<8:e['checks']['memory']={'ok':False,'reason':'Expert shards do not fit'}
   return e
  r=compare_layouts([layout('small',4,4),layout('reference',8,8)],evaluate)
  self.assertEqual(called,['small','reference'])
  self.assertEqual(r['results'][0]['state'],'rejected')
  self.assertEqual(r['minimaByEvidenceState']['budget_candidate']['layoutIds'],['reference'])
 def test_unknown_not_ranked_with_complete_candidates(self):
  def evaluate(l):
   e=good()
   if l['id']=='conditional':e['checks']['transfer']={'ok':None,'reason':'No transfer model'}
   if l['id']=='missing':del e['checks']['tpot']
   return e
  r=compare_layouts([layout('conditional',4,4),layout('complete',8,8),layout('missing',2,2)],evaluate)
  self.assertEqual([x['state'] for x in r['results']],['conditional','budget_candidate','incomplete'])
  self.assertEqual(r['minimaByEvidenceState']['conditional']['minimumTotalCardsWithinEvaluatedSet'],8)
  self.assertEqual(r['minimaByEvidenceState']['budget_candidate']['minimumTotalCardsWithinEvaluatedSet'],16)
  self.assertIsNone(r['recommendedLayoutId'])
 def test_spares_and_ties(self):
  r=compare_layouts([layout('a',4,4,1),layout('b',8,8),layout('c',8,16)],lambda l:good())
  self.assertEqual(r['minimaByEvidenceState']['budget_candidate']['layoutIds'],['a','b'])
  self.assertEqual(r['results'][0]['cards']['spareCards'],8)
 def test_bare_flags_do_not_prove_conditions(self):
  r=compare_layouts([layout('a',4,4)],lambda l:{'checks':{k:{'ok':True} for k in REQUIRED}})
  self.assertEqual(r['results'][0]['state'],'incomplete')
 def test_reject_bad_identity_and_values(self):
  for layouts in [[layout('a',4,4),layout('a',8,8)],[layout('bad',0,8)]]:
   with self.assertRaises(ValueError):compare_layouts(layouts,lambda l:good())
  with self.assertRaises(ValueError):compare_layouts([layout('bad',4,4)],lambda l:{'checks':{'memory':{'ok':1}}})

if __name__=='__main__':unittest.main()
