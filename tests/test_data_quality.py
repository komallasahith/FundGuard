import unittest
import numpy as np
import pandas as pd

def assign_data_quality_tier(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    missing_cnt = pd.to_numeric(df.get("MISSING_FIELD_COUNT", 0), errors="coerce").fillna(0)
    
    conditions = [
        missing_cnt == 0,
        missing_cnt == 1,
        missing_cnt >= 2
    ]
    choices = ["HIGH", "MEDIUM", "LOW"]
    df["DATA_QUALITY_TIER"] = np.select(conditions, choices, default="MEDIUM")
    
    if "SANCTION_AMOUNT" in df.columns:
        is_missing_sanction = df["SANCTION_AMOUNT"].isna() | (df["SANCTION_AMOUNT"] <= 0)
        df.loc[is_missing_sanction, "DATA_QUALITY_TIER"] = "VERIFICATION_ONLY"
        
    return df

class TestDataQuality(unittest.TestCase):
    def test_data_quality_tier_assignment(self):
        data = pd.DataFrame([
            {"WORK_ID": "1", "MISSING_FIELD_COUNT": 0, "SANCTION_AMOUNT": 500000},
            {"WORK_ID": "2", "MISSING_FIELD_COUNT": 1, "SANCTION_AMOUNT": 500000},
            {"WORK_ID": "3", "MISSING_FIELD_COUNT": 4, "SANCTION_AMOUNT": 500000},
            {"WORK_ID": "4", "MISSING_FIELD_COUNT": 0, "SANCTION_AMOUNT": np.nan},
        ])
        
        result = assign_data_quality_tier(data)
        self.assertEqual(result.loc[result["WORK_ID"] == "1", "DATA_QUALITY_TIER"].values[0], "HIGH")
        self.assertEqual(result.loc[result["WORK_ID"] == "2", "DATA_QUALITY_TIER"].values[0], "MEDIUM")
        self.assertEqual(result.loc[result["WORK_ID"] == "3", "DATA_QUALITY_TIER"].values[0], "LOW")
        self.assertEqual(result.loc[result["WORK_ID"] == "4", "DATA_QUALITY_TIER"].values[0], "VERIFICATION_ONLY")

if __name__ == "__main__":
    unittest.main()
