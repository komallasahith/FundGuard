import unittest
import numpy as np
import pandas as pd

class TestEdgeCases(unittest.TestCase):
    def test_empty_dataframe_pipeline(self):
        empty_df = pd.DataFrame(columns=["WORK_ID", "RULE_SCORE", "STAT_SCORE", "ML_PERCENTILE"])
        self.assertEqual(len(empty_df), 0)
        rule_cal = np.clip((empty_df["RULE_SCORE"] / 35.0) * 100.0, 0, 100.0)
        self.assertEqual(len(rule_cal), 0)

    def test_single_row_dataframe(self):
        single_df = pd.DataFrame([{
            "WORK_ID": "999999",
            "RULE_SCORE": 10.0,
            "STAT_SCORE": 15.0,
            "ML_PERCENTILE": 80.0,
            "PEER_COUNT": 25,
            "MISSING_FIELD_COUNT": 0
        }])
        
        rule_cal = np.clip((single_df["RULE_SCORE"] / 35.0) * 100.0, 0, 100.0)
        stat_cal = np.clip((single_df["STAT_SCORE"] / 35.0) * 100.0, 0, 100.0)
        ml_cal = single_df["ML_PERCENTILE"]
        
        hybrid = np.round(0.35 * rule_cal + 0.35 * stat_cal + 0.30 * ml_cal, 1)
        self.assertTrue(hybrid.values[0] > 0)
        self.assertTrue(hybrid.values[0] <= 100)

    def test_nan_handling(self):
        nan_df = pd.DataFrame([{
            "WORK_ID": "1",
            "RULE_SCORE": np.nan,
            "STAT_SCORE": None,
            "ML_PERCENTILE": np.nan
        }])
        
        r = pd.to_numeric(nan_df["RULE_SCORE"], errors="coerce").fillna(0)
        s = pd.to_numeric(nan_df["STAT_SCORE"], errors="coerce").fillna(0)
        m = pd.to_numeric(nan_df["ML_PERCENTILE"], errors="coerce").fillna(0)
        
        hybrid = 0.35 * r + 0.35 * s + 0.30 * m
        self.assertEqual(hybrid.values[0], 0.0)

if __name__ == "__main__":
    unittest.main()
