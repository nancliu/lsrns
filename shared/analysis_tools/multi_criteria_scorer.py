"""
Multi-Criteria Scorer for Control Strategy Ranking

Responsibilities:
- Implement adaptive effectiveness, coverage, efficiency, and reliability scorers
- Calculate weighted scores based on available outputs
- Normalize scores to 0-100 range
- Support custom weights
"""

import logging
import statistics
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class MultiCriteriaScorer:
    """Implements multi-criteria scoring for strategy ranking"""

    # Default weights (can be customized)
    DEFAULT_WEIGHTS = {
        "effectiveness": 0.40,
        "coverage": 0.25,
        "efficiency": 0.20,
        "reliability": 0.15,
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialize scorer with optional custom weights

        Args:
            custom_weights: Optional custom weights dict, must sum to 1.0
        """
        self.weights = self._validate_weights(
            custom_weights or self.DEFAULT_WEIGHTS.copy()
        )
        logger.info(f"Scorer initialized with weights: {self.weights}")

    def score_strategy(
        self,
        combined_analysis: Dict[str, Any],
        plan_id: str
    ) -> Dict[str, float]:
        """
        Calculate all scores for a strategy plan

        Args:
            combined_analysis: Combined analysis results from orchestrator
            plan_id: Plan ID to score

        Returns:
            Dict with scores:
                - effectiveness: 0-100
                - coverage: 0-100
                - efficiency: 0-100
                - reliability: 0-100
                - overall: 0-100 (weighted average)
        """
        output_combination = combined_analysis.get("output_combination", "summary")

        # Calculate individual dimension scores
        effectiveness = self._calculate_effectiveness(combined_analysis, plan_id)
        coverage = self._calculate_coverage(
            combined_analysis, plan_id, output_combination
        )
        efficiency = self._calculate_efficiency(combined_analysis, plan_id)
        reliability = self._calculate_reliability(combined_analysis, plan_id)

        # Calculate overall score
        overall = (
            effectiveness * self.weights["effectiveness"]
            + coverage * self.weights["coverage"]
            + efficiency * self.weights["efficiency"]
            + reliability * self.weights["reliability"]
        )

        return {
            "effectiveness": round(effectiveness, 2),
            "coverage": round(coverage, 2),
            "efficiency": round(efficiency, 2),
            "reliability": round(reliability, 2),
            "overall": round(overall, 2),
        }

    def _calculate_effectiveness(
        self,
        combined_analysis: Dict[str, Any],
        plan_id: str
    ) -> float:
        """
        Calculate effectiveness score (40%) based on improvement rates

        Effectiveness = weighted average of improvement rates for:
        - ended (25%): vehicles that completed
        - avgSpeed (25%): average speed improvement
        - waiting reduction (20%): fewer waiting vehicles
        - teleports reduction (20%): fewer teleports (congestion indicator)
        - running reduction (5%): fewer running vehicles
        - collisions reduction (5%): fewer collisions

        Args:
            combined_analysis: Combined analysis data
            plan_id: Plan ID to score

        Returns:
            Score 0-100
        """
        summary_data = combined_analysis.get("summary", {})
        improvement_rates = summary_data.get("improvement_rates", {}).get(plan_id, {})

        if not improvement_rates:
            logger.warning(f"No improvement rates found for {plan_id}")
            return 0.0

        # Extract improvement rates (already in percentage)
        ended_improvement = improvement_rates.get("ended", 0) or 0
        avgSpeed_improvement = improvement_rates.get("avgSpeed", 0) or 0
        waiting_reduction = improvement_rates.get("waiting", 0) or 0
        teleports_reduction = improvement_rates.get("teleports", 0) or 0
        running_reduction = improvement_rates.get("running", 0) or 0
        collisions_reduction = improvement_rates.get("collisions", 0) or 0

        # Normalize to 0-100 range (improvements can be negative)
        effectiveness = (
            0.25 * self._normalize_score(ended_improvement)
            + 0.25 * self._normalize_score(avgSpeed_improvement)
            + 0.20 * self._normalize_score(waiting_reduction)
            + 0.20 * self._normalize_score(teleports_reduction)
            + 0.05 * self._normalize_score(running_reduction)
            + 0.05 * self._normalize_score(collisions_reduction)
        )

        return max(0, min(100, effectiveness))  # Clamp to 0-100

    def _calculate_coverage(
        self,
        combined_analysis: Dict[str, Any],
        plan_id: str,
        output_combination: str
    ) -> float:
        """
        Calculate adaptive coverage score (25%) based on available outputs

        - Mode 1 (Summary only): Coverage based on completion rate, non-running rate, non-waiting rate
        - Mode 2 (Summary + TripInfo): Add OD pair improvement coverage
        - Mode 3a (Summary + EdgeData): Add road segment coverage
        - Mode 3b (All outputs): Combine segment + OD + vehicle coverage

        Args:
            combined_analysis: Combined analysis data
            plan_id: Plan ID to score
            output_combination: String like "summary" or "summary+tripinfo+edgedata"

        Returns:
            Score 0-100
        """
        summary_data = combined_analysis.get("summary", {})
        plan_metrics = summary_data.get("plan_metrics", {}).get(plan_id, {})
        baseline_metrics = summary_data.get("baseline_metrics", {})

        if not plan_metrics:
            return 0.0

        # Extract coverage metrics
        ended = plan_metrics.get("ended", 0)
        loaded = plan_metrics.get("loaded", 1)  # Avoid division by zero
        running = plan_metrics.get("running", 0)
        waiting = plan_metrics.get("waiting", 0)

        completion_rate = ended / max(loaded, 1)
        non_running_rate = 1 - (running / max(loaded, 1))
        non_waiting_rate = 1 - (waiting / max(loaded, 1))

        # Mode 1: Summary only
        if output_combination == "summary":
            coverage = (
                0.50 * completion_rate
                + 0.30 * non_running_rate
                + 0.20 * non_waiting_rate
            )
            return self._normalize_score(coverage * 100)

        # Mode 2: Summary + TripInfo
        if "tripinfo" in output_combination and combined_analysis.get(
            "tripinfo", {}
        ).get("available"):
            tripinfo_data = combined_analysis.get("tripinfo", {})
            baseline_tripinfo = tripinfo_data.get("baseline_tripinfo", {})
            improved_od = tripinfo_data.get("improved_od_pairs", {}).get(plan_id, 0)
            total_od = len(baseline_tripinfo.get("od_pairs", {}))

            od_coverage = improved_od / max(total_od, 1)

            coverage = (
                0.40 * completion_rate
                + 0.30 * od_coverage
                + 0.30 * non_running_rate
            )
            return self._normalize_score(coverage * 100)

        # Mode 3a: Summary + EdgeData (no tripinfo)
        if "edgedata" in output_combination and combined_analysis.get(
            "edgedata", {}
        ).get("available"):
            edgedata_data = combined_analysis.get("edgedata", {})
            baseline_edgedata = edgedata_data.get("baseline_edgedata", {})
            improved_segments = edgedata_data.get("improved_segments_count", {}).get(
                plan_id, 0
            )
            total_segments = baseline_edgedata.get("total_edges", 1)

            segment_coverage = improved_segments / max(total_segments, 1)

            coverage = (
                0.40 * segment_coverage
                + 0.35 * completion_rate
                + 0.25 * non_running_rate
            )
            return self._normalize_score(coverage * 100)

        # Mode 3b: All outputs
        if (
            "tripinfo" in output_combination
            and "edgedata" in output_combination
            and combined_analysis.get("tripinfo", {}).get("available")
            and combined_analysis.get("edgedata", {}).get("available")
        ):
            tripinfo_data = combined_analysis.get("tripinfo", {})
            edgedata_data = combined_analysis.get("edgedata", {})

            baseline_tripinfo = tripinfo_data.get("baseline_tripinfo", {})
            improved_od = tripinfo_data.get("improved_od_pairs", {}).get(plan_id, 0)
            total_od = len(baseline_tripinfo.get("od_pairs", {}))
            od_coverage = improved_od / max(total_od, 1)

            baseline_edgedata = edgedata_data.get("baseline_edgedata", {})
            improved_segments = edgedata_data.get("improved_segments_count", {}).get(
                plan_id, 0
            )
            total_segments = baseline_edgedata.get("total_edges", 1)
            segment_coverage = improved_segments / max(total_segments, 1)

            coverage = (
                0.35 * segment_coverage
                + 0.35 * od_coverage
                + 0.30 * completion_rate
            )
            return self._normalize_score(coverage * 100)

        # Fallback to Mode 1
        coverage = (
            0.50 * completion_rate
            + 0.30 * non_running_rate
            + 0.20 * non_waiting_rate
        )
        return self._normalize_score(coverage * 100)

    def _calculate_efficiency(
        self,
        combined_analysis: Dict[str, Any],
        plan_id: str
    ) -> float:
        """
        Calculate efficiency score (20%)

        Efficiency = total improvement / control intensity
        where control intensity is estimated from number of affected edges

        Args:
            combined_analysis: Combined analysis data
            plan_id: Plan ID to score

        Returns:
            Score 0-100
        """
        summary_data = combined_analysis.get("summary", {})
        improvement_rates = summary_data.get("improvement_rates", {}).get(plan_id, {})

        if not improvement_rates:
            return 50.0  # Default neutral score

        # Calculate total improvement (weighted average of key metrics)
        avg_speed_improvement = improvement_rates.get("avgSpeed", 0) or 0
        ended_improvement = improvement_rates.get("ended", 0) or 0
        teleports_reduction = improvement_rates.get("teleports", 0) or 0

        total_improvement = (
            0.4 * max(0, avg_speed_improvement)
            + 0.3 * max(0, ended_improvement)
            + 0.3 * max(0, teleports_reduction)
        )

        # For now, use a default control intensity
        # In future, could read from plan metadata if available
        control_intensity = 0.2  # Assume 20% of network edges affected

        if control_intensity == 0:
            control_intensity = 0.1  # Avoid division by zero

        efficiency = total_improvement / control_intensity

        return max(0, min(100, efficiency))  # Clamp to 0-100

    def _calculate_reliability(
        self,
        combined_analysis: Dict[str, Any],
        plan_id: str
    ) -> float:
        """
        Calculate reliability score (15%)

        Reliability = 100 - (std_dev * 10)
        where std_dev is the standard deviation of effectiveness across random seeds

        For single-seed runs, default to 70 (moderate reliability)

        Args:
            combined_analysis: Combined analysis data
            plan_id: Plan ID to score

        Returns:
            Score 0-100
        """
        # Get seed data from combined analysis
        seed_data = combined_analysis.get("summary", {}).get("seed_data", {}).get(plan_id, [])
        batch_metadata = combined_analysis.get("batch_metadata", {})
        num_seeds = batch_metadata.get("num_seeds", 1)

        # If no seed data or only 1 seed, use default
        if not seed_data or len(seed_data) <= 1 or num_seeds <= 1:
            logger.debug(
                f"Reliability score for {plan_id}: using default (num_seeds={num_seeds})"
            )
            return 70.0  # Default for single-seed or missing seed data

        # Calculate effectiveness scores for each seed
        effectiveness_scores = []
        improvement_rates_baseline = combined_analysis.get("summary", {}).get("improvement_rates", {}).get(plan_id, {})

        for seed_metrics in seed_data:
            # Recalculate effectiveness for this seed using its metrics
            effectiveness = self._calculate_effectiveness_from_metrics(seed_metrics, improvement_rates_baseline)
            effectiveness_scores.append(effectiveness)

        if len(effectiveness_scores) < 2:
            logger.debug(f"Not enough seed data for {plan_id}")
            return 70.0

        # Calculate standard deviation
        std_dev = statistics.stdev(effectiveness_scores)
        reliability = max(0, min(100, 100 - (std_dev * 10)))

        logger.info(
            f"Reliability for {plan_id}: std_dev={std_dev:.2f}, "
            f"effectiveness_scores={[round(s, 2) for s in effectiveness_scores]}, "
            f"reliability={reliability:.2f}"
        )

        return round(reliability, 2)

    def _calculate_effectiveness_from_metrics(
        self,
        seed_metrics: Dict[str, float],
        improvement_rates: Dict[str, float]
    ) -> float:
        """
        Calculate effectiveness for a single seed's metrics

        Args:
            seed_metrics: Metrics dict from one seed
            improvement_rates: Pre-calculated improvement rates

        Returns:
            Effectiveness score 0-100
        """
        # Extract improvement rates for this seed
        ended_improvement = improvement_rates.get("ended", 0) or 0
        avgSpeed_improvement = improvement_rates.get("avgSpeed", 0) or 0
        waiting_reduction = improvement_rates.get("waiting", 0) or 0
        teleports_reduction = improvement_rates.get("teleports", 0) or 0
        running_reduction = improvement_rates.get("running", 0) or 0
        collisions_reduction = improvement_rates.get("collisions", 0) or 0

        # Calculate effectiveness
        effectiveness = (
            0.25 * self._normalize_score(ended_improvement)
            + 0.25 * self._normalize_score(avgSpeed_improvement)
            + 0.20 * self._normalize_score(waiting_reduction)
            + 0.20 * self._normalize_score(teleports_reduction)
            + 0.05 * self._normalize_score(running_reduction)
            + 0.05 * self._normalize_score(collisions_reduction)
        )

        return max(0, min(100, effectiveness))

    def _normalize_score(self, value: float) -> float:
        """
        Normalize a value to 0-100 range

        Args:
            value: Input value (can be negative or >100)

        Returns:
            Normalized score 0-100
        """
        # Clamp negative values to 0, values >100 to 100
        return max(0, min(100, value))

    def _validate_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Validate and normalize custom weights

        Args:
            weights: Weight dictionary

        Returns:
            Validated weights dict

        Raises:
            ValueError: If weights don't sum close to 1.0
        """
        total = sum(weights.values())

        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Weights sum to {total}, normalizing to 1.0"
            )
            # Normalize weights
            return {k: v / total for k, v in weights.items()}

        return weights


# Convenience function
def score_strategy(
    combined_analysis: Dict[str, Any],
    plan_id: str,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Score a strategy plan

    Args:
        combined_analysis: Combined analysis data
        plan_id: Plan ID to score
        custom_weights: Optional custom weights

    Returns:
        Dict with all scores
    """
    scorer = MultiCriteriaScorer(custom_weights)
    return scorer.score_strategy(combined_analysis, plan_id)
