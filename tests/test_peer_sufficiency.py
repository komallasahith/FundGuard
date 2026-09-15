import unittest
import numpy as np
import pandas as pd

def check_peer_sufficiency(df: pd.DataFrame, min_peers=10) -> pd.DataFrame:
    df = df.copy()
    peer_col = "PEER_COUNT" if "PEER_COUNT" in df.columns else ("STAT_PEER_COUNT" if "STAT_PEER_COUNT" in df.columns else None)
    if peer_col:
        df["PEER_DATA_SUFFICIENT"] = (pd.to_numeric(df[peer_col], errors="coerce").fillna(0) >= min_peers).astype(int)
    else:
        df["PEER_DATA_SUFFICIENT"] = 1
    return df

class TestPeerSufficiency(unittest.TestCase):
    def test_peer_sufficiency_flag(self):
        data = pd.DataFrame([
            {"WORK_ID": "1", "PEER_COUNT": 15},
            {"WORK_ID": "2", "PEER_COUNT": 10},
            {"WORK_ID": "3", "PEER_COUNT": 9},
            {"WORK_ID": "4", "PEER_COUNT": 0},
            {"WORK_ID": "5", "PEER_COUNT": np.nan},
        ])
        
        result = check_peer_sufficiency(data)
        self.assertEqual(result.loc[result["WORK_ID"] == "1", "PEER_DATA_SUFFICIENT"].values[0], 1)
        self.assertEqual(result.loc[result["WORK_ID"] == "2", "PEER_DATA_SUFFICIENT"].values[0], 1)
        self.assertEqual(result.loc[result["WORK_ID"] == "3", "PEER_DATA_SUFFICIENT"].values[0], 0)
        self.assertEqual(result.loc[result["WORK_ID"] == "4", "PEER_DATA_SUFFICIENT"].values[0], 0)
        self.assertEqual(result.loc[result["WORK_ID"] == "5", "PEER_DATA_SUFFICIENT"].values[0], 0)

    def test_peer_sufficiency_missing_column(self):
        data = pd.DataFrame([{"WORK_ID": "1"}])
        result = check_peer_sufficiency(data)
        self.assertEqual(result["PEER_DATA_SUFFICIENT"].values[0], 1)

if __name__ == "__main__":
    unittest.main()
