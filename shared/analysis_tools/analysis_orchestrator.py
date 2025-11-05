"""
Analysis Orchestrator for Control Strategy Ranking

Responsibilities:
- Orchestrates output detection and modular analyzers
- Calls appropriate analyzers based on available outputs
- Handles missing data gracefully (continues with available outputs)
- Returns combined results with metadata
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from .output_detector import OutputDetector
from .summary_analyzer import SummaryAnalyzer
from .tripinfo_analyzer import TripInfoAnalyzer
from .edgedata_analyzer import EdgeDataAnalyzer

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """Orchestrates data extraction from various output sources"""

    def __init__(self):
        """Initialize orchestrator"""
        self.output_detector = OutputDetector()
        self.summary_analyzer = SummaryAnalyzer()
        self.tripinfo_analyzer = TripInfoAnalyzer()
        self.edgedata_analyzer = EdgeDataAnalyzer()
        self.results = {}

    def analyze_batch(
        self,
        batch_dir: Path,
        plan_ids: List[str],
        baseline_plan_id: str
    ) -> Dict[str, Any]:
        """
        Orchestrate complete analysis of batch

        Args:
            batch_dir: Batch directory path
            plan_ids: List of plan IDs to analyze
            baseline_plan_id: Baseline plan ID

        Returns:
            Dict with combined analysis results from all available sources
        """
        import json

        batch_dir = Path(batch_dir)
        logger.info(
            f"Starting batch analysis: {len(plan_ids)} plans, "
            f"baseline={baseline_plan_id}"
        )

        # Load batch metadata to get seed information
        batch_metadata = {}
        metadata_path = batch_dir / "batch_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    batch_metadata = json.load(f)
                logger.info(
                    f"Loaded batch metadata: num_seeds={batch_metadata.get('num_seeds')}, "
                    f"base_seed={batch_metadata.get('base_seed')}"
                )
            except Exception as e:
                logger.warning(f"Failed to load batch metadata: {e}")
        else:
            logger.warning(f"Batch metadata not found: {metadata_path}")

        # Step 1: Detect available outputs
        output_detection = self.output_detector.detect_outputs(batch_dir, baseline_plan_id)
        available_outputs = output_detection.get("available_outputs", {})
        output_combination = output_detection.get("output_combination", "summary")

        logger.info(
            f"Output detection: {output_combination} "
            f"({available_outputs})"
        )

        # Step 2: Analyze summary.xml (always required)
        summary_results = self.summary_analyzer.analyze(
            batch_dir, plan_ids, baseline_plan_id
        )

        if "error" in summary_results:
            logger.error(f"Summary analysis failed: {summary_results['error']}")
            return {
                "error": "Cannot analyze batch: baseline plan not found",
                "batch_dir": str(batch_dir),
                "output_combination": output_combination,
            }

        # Step 3: Analyze tripinfo.xml (if available)
        tripinfo_results = {}
        if available_outputs.get("tripinfo"):
            try:
                tripinfo_results = self.tripinfo_analyzer.analyze(
                    batch_dir, plan_ids, baseline_plan_id
                )
                logger.info("TripInfo analysis completed successfully")
            except Exception as e:
                logger.warning(f"TripInfo analysis failed: {e}. Continuing with summary only.")
                tripinfo_results = {}

        # Step 4: Analyze edgedata.xml (if available)
        edgedata_results = {}
        if available_outputs.get("edgedata"):
            try:
                edgedata_results = self.edgedata_analyzer.analyze(
                    batch_dir, plan_ids, baseline_plan_id
                )
                logger.info("EdgeData analysis completed successfully")
            except Exception as e:
                logger.warning(f"EdgeData analysis failed: {e}. Continuing with summary only.")
                edgedata_results = {}

        # Step 5: Combine results
        combined_results = self._combine_results(
            summary_results, tripinfo_results, edgedata_results, output_combination, batch_metadata
        )

        logger.info("Batch analysis completed successfully")
        return combined_results

    def _combine_results(
        self,
        summary_results: Dict[str, Any],
        tripinfo_results: Dict[str, Any],
        edgedata_results: Dict[str, Any],
        output_combination: str,
        batch_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine analysis results from all sources

        Args:
            summary_results: Results from summary analyzer
            tripinfo_results: Results from tripinfo analyzer
            edgedata_results: Results from edgedata analyzer
            output_combination: String indicating which outputs were analyzed
            batch_metadata: Batch metadata including seed information

        Returns:
            Dict with combined results for ranking engine
        """
        return {
            "output_combination": output_combination,
            "batch_metadata": {
                "num_seeds": batch_metadata.get("num_seeds", 1),
                "base_seed": batch_metadata.get("base_seed"),
            },
            "summary": {
                "baseline_metrics": summary_results.get("baseline_metrics", {}),
                "plan_metrics": summary_results.get("plan_metrics", {}),
                "improvement_rates": summary_results.get("improvement_rates", {}),
                "metrics_metadata": summary_results.get("metrics_metadata", {}),
                "seed_data": summary_results.get("seed_data", {}),  # 多种子数据用于可靠性计算
            },
            "tripinfo": {
                "baseline_tripinfo": tripinfo_results.get("baseline_tripinfo", {}),
                "plan_tripinfo": tripinfo_results.get("plan_tripinfo", {}),
                "improved_od_pairs": tripinfo_results.get("improved_od_pairs", {}),
                "metrics_metadata": tripinfo_results.get("metrics_metadata", {}),
                "available": bool(tripinfo_results) and "error" not in tripinfo_results,
            },
            "edgedata": {
                "baseline_edgedata": edgedata_results.get("baseline_edgedata", {}),
                "plan_edgedata": edgedata_results.get("plan_edgedata", {}),
                "improved_segments_count": edgedata_results.get("improved_segments_count", {}),
                "deteriorated_segments_count": edgedata_results.get("deteriorated_segments_count", {}),
                "metrics_metadata": edgedata_results.get("metrics_metadata", {}),
                "available": bool(edgedata_results) and "error" not in edgedata_results,
            },
        }


# Convenience function
def analyze_batch(
    batch_dir: str,
    plan_ids: List[str],
    baseline_plan_id: str
) -> Dict[str, Any]:
    """
    Orchestrate batch analysis

    Args:
        batch_dir: Batch directory path
        plan_ids: List of plan IDs
        baseline_plan_id: Baseline plan ID

    Returns:
        Dict with combined analysis results
    """
    orchestrator = AnalysisOrchestrator()
    return orchestrator.analyze_batch(Path(batch_dir), plan_ids, baseline_plan_id)
