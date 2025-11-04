"""
Summary.xml Analyzer for Control Strategy Ranking

Responsibilities:
- Extract 8 metrics from summary.xml for each plan
- Compute improvement rates relative to baseline
- Validate baseline plan presence
- Return independent analysis results
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from batch_result_analyzer import BatchResultAnalyzer

logger = logging.getLogger(__name__)


class SummaryAnalyzer:
    """Analyzes summary.xml metrics for control strategy ranking"""

    # 8 core metrics from summary.xml as per proposal
    CORE_METRICS = [
        "loaded",      # 已加载车数 (辆)
        "inserted",    # 已插入车数 (辆)
        "ended",       # 已完成车数 (辆) ⬆️ higher is better
        "running",     # 当前运行车数 (辆) ⬇️ lower is better
        "waiting",     # 等待车数 (辆) ⬇️ lower is better
        "teleports",   # 传送次数 (次) ⬇️ lower is better
        "collisions",  # 碰撞次数 (次) ⬇️ lower is better
        "avgSpeed",    # 平均速度 (m/s) ⬆️ higher is better
    ]

    # Metrics where higher values are better
    HIGHER_IS_BETTER = {"ended", "avgSpeed"}

    # Metrics where lower values are better
    LOWER_IS_BETTER = {"running", "waiting", "teleports", "collisions"}

    def __init__(self):
        """Initialize summary analyzer"""
        self.batch_analyzer = BatchResultAnalyzer()
        self.baseline_metrics = {}
        self.plan_metrics = {}
        self.improvement_rates = {}

    def analyze(
        self,
        batch_dir: Path,
        plan_ids: List[str],
        baseline_plan_id: str
    ) -> Dict[str, Any]:
        """
        Analyze summary.xml for all plans in batch

        Args:
            batch_dir: Batch directory path
            plan_ids: List of plan IDs to analyze
            baseline_plan_id: Baseline plan ID

        Returns:
            Dict with:
                - baseline_metrics: Dict[str, float] - baseline values
                - plan_metrics: Dict[plan_id, Dict[metric, float]]
                - improvement_rates: Dict[plan_id, Dict[metric, float]]
                - metrics_metadata: Dict[metric, {"direction": "higher"/"lower", ...}]
        """
        logger.info(f"Analyzing summary.xml for {len(plan_ids)} plans")

        batch_dir = Path(batch_dir)

        # Use existing BatchResultAnalyzer to extract metrics
        batch_results = self.batch_analyzer.analyze_batch_results(
            batch_dir=batch_dir,
            plan_ids=plan_ids,
            baseline_plan_id=baseline_plan_id,
        )

        # Extract baseline metrics
        if baseline_plan_id in batch_results.get("plan_results", {}):
            self.baseline_metrics = batch_results["plan_results"][baseline_plan_id].get(
                "metrics", {}
            )
            logger.info(f"Baseline metrics: {self.baseline_metrics}")
        else:
            logger.error(f"Baseline plan {baseline_plan_id} not found in results")
            return {
                "error": f"Baseline plan {baseline_plan_id} not found",
                "baseline_metrics": {},
                "plan_metrics": {},
                "improvement_rates": {},
                "metrics_metadata": self._get_metrics_metadata(),
            }

        # Extract test plan metrics and improvement rates
        for plan_id, plan_data in batch_results.get("plan_results", {}).items():
            if plan_id == baseline_plan_id:
                continue

            metrics = plan_data.get("metrics", {})
            self.plan_metrics[plan_id] = metrics
            logger.info(f"Plan {plan_id} metrics: {metrics}")

        # Store improvement rates from batch analyzer
        self.improvement_rates = batch_results.get("improvement_rates", {})

        return {
            "baseline_metrics": self.baseline_metrics.copy(),
            "plan_metrics": self.plan_metrics.copy(),
            "improvement_rates": self.improvement_rates.copy(),
            "metrics_metadata": self._get_metrics_metadata(),
            "batch_analysis": batch_results,
        }

    def _get_metrics_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about each metric (direction, description, unit)

        Returns:
            Dict mapping metric name to metadata
        """
        return {
            "loaded": {
                "direction": "higher",
                "description": "已加载车数",
                "unit": "辆",
                "include_in_scoring": False,  # typically same as inserted
            },
            "inserted": {
                "direction": "higher",
                "description": "已插入车数",
                "unit": "辆",
                "include_in_scoring": False,  # typically same as loaded
            },
            "ended": {
                "direction": "higher",
                "description": "已完成车数",
                "unit": "辆",
                "include_in_scoring": True,
            },
            "running": {
                "direction": "lower",
                "description": "当前运行车数",
                "unit": "辆",
                "include_in_scoring": True,
            },
            "waiting": {
                "direction": "lower",
                "description": "等待车数",
                "unit": "辆",
                "include_in_scoring": True,
            },
            "teleports": {
                "direction": "lower",
                "description": "传送次数（拥堵指标）",
                "unit": "次",
                "include_in_scoring": True,
            },
            "collisions": {
                "direction": "lower",
                "description": "碰撞次数",
                "unit": "次",
                "include_in_scoring": True,
            },
            "avgSpeed": {
                "direction": "higher",
                "description": "平均速度",
                "unit": "m/s",
                "include_in_scoring": True,
            },
        }

    def get_baseline_metrics(self) -> Dict[str, Any]:
        """Get baseline metrics"""
        return self.baseline_metrics.copy()

    def get_plan_metrics(self, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific plan or all plans"""
        if plan_id:
            return self.plan_metrics.get(plan_id, {})
        return self.plan_metrics.copy()

    def get_improvement_rates(self, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Get improvement rates for specific plan or all plans"""
        if plan_id:
            return self.improvement_rates.get(plan_id, {})
        return self.improvement_rates.copy()


# Convenience function
def analyze_summary(
    batch_dir: str,
    plan_ids: List[str],
    baseline_plan_id: str
) -> Dict[str, Any]:
    """
    Analyze summary.xml for all plans

    Args:
        batch_dir: Batch directory path
        plan_ids: List of plan IDs
        baseline_plan_id: Baseline plan ID

    Returns:
        Dict with analysis results
    """
    analyzer = SummaryAnalyzer()
    return analyzer.analyze(Path(batch_dir), plan_ids, baseline_plan_id)
