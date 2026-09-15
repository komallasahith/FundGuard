import unittest
import numpy as np
import pandas as pd

def calibrate_detector_scores(rule_score, stat_score, ml_percentile, agreement_count=1):
    rule_cal = np.clip((rule_score / 35.0) * 100.0, 0, 100.0)
    stat_cal = np.clip((stat_score / 35.0) * 100.0, 0, 100.0)
    ml_cal = np.clip(ml_percentile, 0, 100.0)
    
    bonus = 10.0 if agreement_count >= 3 else (5.0 if agreement_count == 2 else 0.0)
    
    hybrid = np.round(0.35 * rule_cal + 0.35 * stat_cal + 0.30 * ml_cal + bonus, 1)
    return hybrid, rule_cal, stat_cal, ml_cal

class TestScoreCalibration(unittest.TestCase):
    def test_score_calibration_bounds(self):
        hybrid, r, s, m = calibrate_detector_scores(0, 0, 0, 0)
        self.assertEqual(hybrid, 0.0)
        self.assertEqual(r, 0.0)
        self.assertEqual(s, 0.0)
        self.assertEqual(m, 0.0)
        
        hybrid, r, s, m = calibrate_detector_scores(35, 35, 100, 3)
        self.assertEqual(r, 100.0)
        self.assertEqual(s, 100.0)
        self.assertEqual(m, 100.0)
        self.assertEqual(hybrid, 110.0)

    def test_score_calibration_weights(self):
        hybrid_rule, _, _, _ = calibrate_detector_scores(35, 0, 0, 1)
        self.assertAlmostEqual(hybrid_rule, 35.0, delta=0.1)
        
        hybrid_stat, _, _, _ = calibrate_detector_scores(0, 35, 0, 1)
        self.assertAlmostEqual(hybrid_stat, 35.0, delta=0.1)
        
        hybrid_ml, _, _, _ = calibrate_detector_scores(0, 0, 100, 1)
        self.assertAlmostEqual(hybrid_ml, 30.0, delta=0.1)

    def test_risk_level_assignment(self):
        def get_risk_level(score):
            if score >= 60: return "CRITICAL"
            if score >= 40: return "HIGH"
            if score >= 20: return "MEDIUM"
            if score > 0: return "LOW"
            return "NONE"

        self.assertEqual(get_risk_level(105.0), "CRITICAL")
        self.assertEqual(get_risk_level(65.0), "CRITICAL")
        self.assertEqual(get_risk_level(45.0), "HIGH")
        self.assertEqual(get_risk_level(25.0), "MEDIUM")
        self.assertEqual(get_risk_level(10.0), "LOW")
        self.assertEqual(get_risk_level(0.0), "NONE")

if __name__ == "__main__":
    unittest.main()
