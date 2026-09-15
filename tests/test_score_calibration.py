import unittest
import numpy as np
import pandas as pd

def calculate_hybrid_score(
    rule_score_calibrated: float,
    stat_score_calibrated: float,
    ml_score_calibrated: float,
    peer_data_sufficient: bool = True,
    rule_candidate: bool = False,
    stat_candidate: bool = False,
    ml_candidate: bool = False,
):
    """
    Computes hybrid risk score using percentile-rank calibrated detector scores
    with unbiased uniform weighting (0.35 Rules / 0.35 Stats / 0.30 ML).
    For sparse-peer works, statistical peer comparison is suppressed (0.0) without inflating Rules/ML.
    """
    signal_count = int(rule_candidate) + int(stat_candidate) + int(ml_candidate)

    rule_w = 0.35
    stat_w = 0.35 if peer_data_sufficient else 0.0
    ml_w = 0.30
    bonus = 10.0 if signal_count >= 3 else (5.0 if signal_count == 2 else 0.0)

    rule_comp = rule_score_calibrated * rule_w
    stat_comp = stat_score_calibrated * stat_w
    ml_comp = ml_score_calibrated * ml_w

    hybrid = np.round(rule_comp + stat_comp + ml_comp + bonus, 1)
    return hybrid

def get_priority_level(score: float) -> str:
    if score >= 60.0:
        return "P1"
    if score >= 40.0:
        return "P2"
    if score >= 20.0:
        return "P3"
    if score > 0.0:
        return "P4"
    return "P0"

class TestScoreCalibration(unittest.TestCase):
    def test_percentile_rank_calibration_bounds(self):
        # 0 inputs should yield 0.0
        hybrid_zero = calculate_hybrid_score(0.0, 0.0, 0.0, peer_data_sufficient=True)
        self.assertEqual(hybrid_zero, 0.0)
        self.assertEqual(get_priority_level(hybrid_zero), "P0")

        # 100th percentile across all 3 with consensus bonus
        hybrid_max = calculate_hybrid_score(
            100.0, 100.0, 100.0,
            peer_data_sufficient=True,
            rule_candidate=True,
            stat_candidate=True,
            ml_candidate=True
        )
        self.assertEqual(hybrid_max, 110.0)
        self.assertEqual(get_priority_level(hybrid_max), "P1")

    def test_three_detector_consensus_gets_p1(self):
        # Even with moderate percentile ranks (~60th pct), 3-engine consensus achieves P1
        score = calculate_hybrid_score(
            60.0, 60.0, 60.0,
            peer_data_sufficient=True,
            rule_candidate=True,
            stat_candidate=True,
            ml_candidate=True
        )
        # 60*0.35 + 60*0.35 + 60*0.30 + 10 = 21 + 21 + 18 + 10 = 70.0 -> P1
        self.assertEqual(score, 70.0)
        self.assertEqual(get_priority_level(score), "P1")

    def test_ml_only_lower_than_two_engine_agreement(self):
        # Work where only ML fires (high ML anomaly score 95th pct, no rule or stat flags)
        ml_only_score = calculate_hybrid_score(
            0.0, 0.0, 95.0,
            peer_data_sufficient=True,
            rule_candidate=False,
            stat_candidate=False,
            ml_candidate=True
        )
        # 0.30 * 95 = 28.5 (P3)
        self.assertEqual(ml_only_score, 28.5)
        self.assertEqual(get_priority_level(ml_only_score), "P3")

        # Work where Rule + Stat agree (moderate 70th pct each + 5 agreement bonus)
        two_engine_score = calculate_hybrid_score(
            70.0, 70.0, 0.0,
            peer_data_sufficient=True,
            rule_candidate=True,
            stat_candidate=True,
            ml_candidate=False
        )
        # 0.35 * 70 + 0.35 * 70 + 5.0 = 24.5 + 24.5 + 5 = 54.0 (P2)
        self.assertEqual(two_engine_score, 54.0)
        self.assertEqual(get_priority_level(two_engine_score), "P2")

        # Assert ML-only is lower than 2-engine agreement
        self.assertLess(ml_only_score, two_engine_score)

    def test_unbiased_sparse_peer_treatment(self):
        """
        Verify that sparse-peer works receive identical non-inflated scoring for identical evidence,
        preventing artificial +18.8 point inflation across regional cohorts.
        """
        dense_rule_score = calculate_hybrid_score(
            100.0, 0.0, 0.0,
            peer_data_sufficient=True,
            rule_candidate=True,
            stat_candidate=False,
            ml_candidate=False
        )
        sparse_rule_score = calculate_hybrid_score(
            100.0, 0.0, 0.0,
            peer_data_sufficient=False,
            rule_candidate=True,
            stat_candidate=False,
            ml_candidate=False
        )
        # Both must produce identical 35.0 score
        self.assertEqual(dense_rule_score, 35.0)
        self.assertEqual(sparse_rule_score, 35.0)

if __name__ == "__main__":
    unittest.main()
