import unittest
from pathlib import Path
import pandas as pd

class TestGoldenRegression(unittest.TestCase):
    """
    Golden regression test suite to ensure future pipeline refactorings
    do not silently alter or corrupt anomaly ranks, candidate volumes, or detector agreements.
    """
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parents[1]
        cls.queue_path = cls.base_dir / "data" / "outputs" / "india_investigation_queue.csv"
        cls.hybrid_path = cls.base_dir / "data" / "outputs" / "india_hybrid_risk.csv"

        if not cls.queue_path.exists():
            raise FileNotFoundError(f"Missing queue file: {cls.queue_path}")
        if not cls.hybrid_path.exists():
            raise FileNotFoundError(f"Missing hybrid file: {cls.hybrid_path}")

        cls.queue = pd.read_csv(cls.queue_path, low_memory=False)
        cls.hybrid = pd.read_csv(cls.hybrid_path, low_memory=False)

    def test_golden_top_10_flagged_works_snapshot(self):
        # Frozen golden snapshot of top 10 work IDs in the national investigation queue
        expected_top_10 = [
            "313337", "312966", "284190", "298370", "300408",
            "290133", "238085", "301697", "298371", "166142"
        ]
        actual_top_10 = self.queue["WORK_ID"].astype(str).head(10).tolist()
        self.assertEqual(
            actual_top_10,
            expected_top_10,
            f"Top 10 flagged works changed from golden snapshot!\nActual: {actual_top_10}\nExpected: {expected_top_10}"
        )

    def test_golden_top_10_priorities_are_p1(self):
        top_priorities = self.queue["INVESTIGATION_PRIORITY"].head(10).tolist()
        for p in top_priorities:
            self.assertEqual(p, "P1", "All top-10 works must be categorized as P1 priority")

    def test_golden_candidate_and_consensus_counts(self):
        # Verify 7,521 total investigation candidates
        self.assertEqual(len(self.queue), 7521)
        
        # Verify exactly 597 3-detector consensus works
        consensus_count = (self.queue["DETECTOR_AGREEMENT"] == "RULE + STATISTICAL + ML").sum()
        self.assertEqual(consensus_count, 597)

    def test_golden_tier_counts_snapshot(self):
        """
        Frozen golden snapshot of investigation priority tier distribution
        across all 7,521 candidates to catch calibration regressions.
        """
        priority_counts = self.queue["INVESTIGATION_PRIORITY"].value_counts().to_dict()
        expected_tiers = {
            "P1": 1818,
            "P2": 2049,
            "P3": 3588,
            "P4": 66
        }
        self.assertEqual(
            priority_counts,
            expected_tiers,
            f"Investigation priority tier distribution shifted!\nActual: {priority_counts}\nExpected: {expected_tiers}"
        )

    def test_metadata_fields_integrity(self):
        self.assertIn("PEER_DATA_SUFFICIENT", self.queue.columns)
        self.assertIn("SCORE_REGIME", self.queue.columns)
        self.assertIn("DATA_QUALITY_TIER", self.queue.columns)

        # Ensure no nulls in critical audit columns
        self.assertEqual(self.queue["PEER_DATA_SUFFICIENT"].isna().sum(), 0)
        self.assertEqual(self.queue["SCORE_REGIME"].isna().sum(), 0)
        self.assertEqual(self.queue["DATA_QUALITY_TIER"].isna().sum(), 0)

        # Ensure regimes and tiers are valid categories
        valid_regimes = {"STANDARD", "SPARSE_PEER"}
        actual_regimes = set(self.queue["SCORE_REGIME"].unique())
        self.assertTrue(actual_regimes.issubset(valid_regimes))

        valid_tiers = {"HIGH", "MEDIUM", "LOW"}
        actual_tiers = set(self.queue["DATA_QUALITY_TIER"].unique())
        self.assertTrue(actual_tiers.issubset(valid_tiers))

if __name__ == "__main__":
    unittest.main()
