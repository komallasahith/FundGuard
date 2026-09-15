import unittest
import pandas as pd

def deduplicate_transactions(df: pd.DataFrame, subset=None) -> pd.DataFrame:
    if subset is None:
        subset = [c for c in ["WORK_ID", "VENDOR_ID", "FUND_DISBURSED_AMT", "PAYMENT_DATE"] if c in df.columns]
    if not subset:
        subset = ["WORK_ID"]
    return df.drop_duplicates(subset=subset, keep="first")

class TestDeduplication(unittest.TestCase):
    def test_deduplicate_transactions_general(self):
        data = pd.DataFrame([
            {"WORK_ID": 101, "VENDOR_ID": 501, "FUND_DISBURSED_AMT": 500000, "PAYMENT_DATE": "2025-01-10"},
            {"WORK_ID": 101, "VENDOR_ID": 501, "FUND_DISBURSED_AMT": 500000, "PAYMENT_DATE": "2025-01-10"},
            {"WORK_ID": 101, "VENDOR_ID": 501, "FUND_DISBURSED_AMT": 300000, "PAYMENT_DATE": "2025-02-15"},
            {"WORK_ID": 102, "VENDOR_ID": 502, "FUND_DISBURSED_AMT": 500000, "PAYMENT_DATE": "2025-01-10"},
        ])
        
        deduped = deduplicate_transactions(data)
        self.assertEqual(len(deduped), 3)
        self.assertEqual(len(deduped[deduped["WORK_ID"] == 101]), 2)
        self.assertEqual(len(deduped[deduped["WORK_ID"] == 102]), 1)

    def test_deduplicate_no_duplicates(self):
        data = pd.DataFrame([
            {"WORK_ID": 101, "VENDOR_ID": 501, "FUND_DISBURSED_AMT": 100000},
            {"WORK_ID": 102, "VENDOR_ID": 502, "FUND_DISBURSED_AMT": 200000},
        ])
        deduped = deduplicate_transactions(data)
        self.assertEqual(len(deduped), 2)

if __name__ == "__main__":
    unittest.main()
