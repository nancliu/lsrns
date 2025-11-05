"""
Strategy Ranking Engine for Control Strategy Ranking

Responsibilities:
- Calculate overall scores for all strategies
- Rank strategies by score
- Assign recommendation categories
- Handle tie-breaking
"""

import logging
from typing import Dict, List, Any, Optional

from .multi_criteria_scorer import MultiCriteriaScorer

logger = logging.getLogger(__name__)


class StrategyRankingEngine:
    """Ranks control strategies based on multi-criteria scoring"""

    # Recommendation thresholds
    RECOMMENDATION_THRESHOLDS = {
        "强烈推荐": 75,  # Highly recommended: >=75
        "推荐": 60,      # Recommended: 60-75
        "可选": 45,      # Optional: 45-60
        "不推荐": 0,     # Not recommended: <45
    }

    def __init__(
        self,
        custom_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize ranking engine

        Args:
            custom_weights: Optional custom scoring weights
        """
        self.scorer = MultiCriteriaScorer(custom_weights)
        self.ranked_strategies = []

    def rank_strategies(
        self,
        combined_analysis: Dict[str, Any],
        plan_ids: List[str],
        baseline_plan_id: str,
        plan_names: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Rank control strategies based on multi-criteria scores

        Args:
            combined_analysis: Combined analysis results from orchestrator
            plan_ids: List of plan IDs to rank
            baseline_plan_id: Baseline plan ID
            plan_names: Optional dict mapping plan_id to display name

        Returns:
            Dict with:
                - ranked_strategies: List of ranked strategy dicts
                - ranking_metadata: Metadata about the ranking
        """
        logger.info(
            f"Ranking {len(plan_ids)} strategies, baseline={baseline_plan_id}"
        )

        if plan_names is None:
            plan_names = {plan_id: plan_id for plan_id in plan_ids}

        # Step 1: Score all plans
        plan_scores = {}
        for plan_id in plan_ids:
            scores = self.scorer.score_strategy(combined_analysis, plan_id)
            plan_scores[plan_id] = scores
            logger.debug(f"Scores for {plan_id}: {scores}")

        # Step 2: Identify baseline and test plans
        baseline_scores = plan_scores.get(
            baseline_plan_id, {"overall": 50.0, "effectiveness": 50.0}
        )

        # Step 3: Rank test plans (exclude baseline from ranking)
        test_plans = [p for p in plan_ids if p != baseline_plan_id]
        ranked_list = []

        for plan_id in test_plans:
            scores = plan_scores[plan_id]

            ranked_list.append({
                "plan_id": plan_id,
                "plan_name": plan_names.get(plan_id, plan_id),
                "scores": scores,
                "effectiveness": scores["effectiveness"],
            })

        # Step 4: Sort by overall score (descending), then by effectiveness (tie-breaker)
        ranked_list.sort(
            key=lambda x: (x["scores"]["overall"], x["effectiveness"]),
            reverse=True
        )

        # Step 5: Assign ranks and recommendations
        self.ranked_strategies = []
        for rank, item in enumerate(ranked_list, start=1):
            overall_score = item["scores"]["overall"]
            recommendation = self._get_recommendation(overall_score)

            ranked_strategy = {
                "rank": rank,
                "plan_id": item["plan_id"],
                "plan_name": item["plan_name"],
                "overall_score": overall_score,
                "recommendation": recommendation,
                "scores": {
                    "effectiveness": item["scores"]["effectiveness"],
                    "coverage": item["scores"]["coverage"],
                    "efficiency": item["scores"]["efficiency"],
                    "reliability": item["scores"]["reliability"],
                },
                "improvement_vs_baseline": self._calculate_improvement_vs_baseline(
                    item["scores"], baseline_scores
                ),
            }

            self.ranked_strategies.append(ranked_strategy)
            logger.info(
                f"Rank {rank}: {item['plan_name']} "
                f"(score={overall_score:.1f}, {recommendation})"
            )

        return {
            "ranked_strategies": self.ranked_strategies.copy(),
            "ranking_metadata": {
                "total_strategies": len(test_plans),
                "baseline_plan_id": baseline_plan_id,
                "baseline_plan_name": plan_names.get(baseline_plan_id, baseline_plan_id),
                "baseline_score": baseline_scores["overall"],
                "ranking_weights": self.scorer.weights,
                "output_combination": combined_analysis.get("output_combination", "summary"),
            },
        }

    def _get_recommendation(self, score: float) -> str:
        """
        Get recommendation category based on score

        Args:
            score: Overall score (0-100)

        Returns:
            Recommendation string
        """
        for category in sorted(
            self.RECOMMENDATION_THRESHOLDS.keys(),
            key=lambda x: self.RECOMMENDATION_THRESHOLDS[x],
            reverse=True
        ):
            if score >= self.RECOMMENDATION_THRESHOLDS[category]:
                return category

        return "不推荐"

    def _calculate_improvement_vs_baseline(
        self,
        strategy_scores: Dict[str, float],
        baseline_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate improvement of strategy compared to baseline

        Args:
            strategy_scores: Strategy's scores
            baseline_scores: Baseline's scores

        Returns:
            Dict with improvement percentages
        """
        return {
            "effectiveness": round(
                strategy_scores["effectiveness"] - baseline_scores.get("effectiveness", 50),
                1
            ),
            "coverage": round(
                strategy_scores["coverage"] - baseline_scores.get("coverage", 50),
                1
            ),
            "efficiency": round(
                strategy_scores["efficiency"] - baseline_scores.get("efficiency", 50),
                1
            ),
            "reliability": round(
                strategy_scores["reliability"] - baseline_scores.get("reliability", 50),
                1
            ),
            "overall": round(
                strategy_scores["overall"] - baseline_scores.get("overall", 50),
                1
            ),
        }

    def get_ranked_strategies(self) -> List[Dict[str, Any]]:
        """Get ranked strategies list"""
        return self.ranked_strategies.copy()

    def get_top_strategy(self) -> Optional[Dict[str, Any]]:
        """Get top-ranked strategy"""
        if self.ranked_strategies:
            return self.ranked_strategies[0].copy()
        return None


# Convenience function
def rank_strategies(
    combined_analysis: Dict[str, Any],
    plan_ids: List[str],
    baseline_plan_id: str,
    plan_names: Optional[Dict[str, str]] = None,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Rank control strategies

    Args:
        combined_analysis: Combined analysis data
        plan_ids: List of plan IDs
        baseline_plan_id: Baseline plan ID
        plan_names: Optional plan name mapping
        custom_weights: Optional custom weights

    Returns:
        Dict with ranking results
    """
    engine = StrategyRankingEngine(custom_weights)
    return engine.rank_strategies(combined_analysis, plan_ids, baseline_plan_id, plan_names)
