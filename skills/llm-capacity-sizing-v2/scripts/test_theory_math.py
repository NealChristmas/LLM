import unittest
from theory_math import *

class TheoryMathTests(unittest.TestCase):
    def test_burst_hand_case(self):
        self.assertEqual(linear_work_top(8000,8e9),128)
        self.assertEqual(effective_tops(2,1120,.4),896)
        self.assertAlmostEqual(burst_mean_ttft_ms(60,4,128,896,300),1442.857142857143)
    def test_uneven_and_idle_instances(self):
        self.assertAlmostEqual(mean_fcfs_order(5,2),9/5)
        self.assertEqual(mean_fcfs_order(2,4),1)
        self.assertEqual(planned_concurrency(61,20),74)
    def test_spare_and_validation(self):
        self.assertEqual(card_totals(2,16,1),{'workCards':32,'spareCards':16,'totalCards':48})
        for call in [lambda:effective_tops(1,1120,1.1),lambda:linear_work_top(0,8e9),lambda:mean_fcfs_order(2,0),lambda:card_totals(1,16,-1)]:
            with self.assertRaises(ValueError):call()

if __name__=='__main__':unittest.main()
