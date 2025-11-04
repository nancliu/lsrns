"""
Strategy Ranking Service

Orchestrates control strategy ranking workflow:
1. Data extraction from batch results
2. Multi-criteria scoring
3. Strategy ranking
4. Report generation
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class StrategyRankingService:
    """Service for control strategy ranking"""

    def __init__(self):
        """Initialize ranking service"""
        self.logger = logging.getLogger(__name__)

    def rank_strategies(
        self,
        case_dir: Path,
        batch_id: str,
        plan_ids: List[str],
        baseline_plan_id: str = "baseline_plan",
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Rank control strategies for a batch

        Args:
            case_dir: Case directory path
            batch_id: Batch ID
            plan_ids: List of plan IDs to rank
            baseline_plan_id: Baseline plan ID
            custom_weights: Optional custom scoring weights

        Returns:
            Dict with ranking results
        """
        case_dir = Path(case_dir)
        batch_dir = case_dir / "simulations" / batch_id

        logger.info(
            f"Starting strategy ranking: batch={batch_id}, plans={len(plan_ids)}"
        )

        # Step 1: Import ranking modules (local import to avoid circular deps)
        try:
            from shared.analysis_tools.analysis_orchestrator import (
                AnalysisOrchestrator
            )
            from shared.analysis_tools.strategy_ranking_engine import (
                StrategyRankingEngine
            )
            from shared.analysis_tools.ranking_report_generator import (
                RankingReportGenerator
            )
        except ImportError as e:
            logger.error(f"Failed to import ranking modules: {e}")
            raise

        # Step 2: Orchestrate data analysis
        logger.info("Orchestrating data analysis...")
        orchestrator = AnalysisOrchestrator()
        combined_analysis = orchestrator.analyze_batch(batch_dir, plan_ids, baseline_plan_id)

        if "error" in combined_analysis:
            logger.error(f"Data analysis failed: {combined_analysis['error']}")
            return {
                "error": combined_analysis["error"],
                "batch_id": batch_id
            }

        # Step 3: Rank strategies
        logger.info("Ranking strategies...")
        ranking_engine = StrategyRankingEngine(custom_weights)

        # Get plan names from metadata or use plan IDs
        plan_names = self._get_plan_names(case_dir, batch_dir, plan_ids)

        ranking_results = ranking_engine.rank_strategies(
            combined_analysis=combined_analysis,
            plan_ids=plan_ids,
            baseline_plan_id=baseline_plan_id,
            plan_names=plan_names
        )

        # Step 4: Generate HTML report
        logger.info("Generating HTML report...")
        report_generator = RankingReportGenerator()
        report_file = report_generator.generate_report(
            ranking_results,
            output_dir=Path(__file__).parent.parent.parent / "frontend" / "control"
        )

        # Step 5: Build response
        ranking_id = f"ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        response = {
            "ranking_id": ranking_id,
            "case_id": case_dir.name,
            "batch_id": batch_id,
            "ranked_strategies": ranking_results.get("ranked_strategies", []),
            "ranking_metadata": ranking_results.get("ranking_metadata", {}),
            "report_file": report_file,
            "timestamp": datetime.now().isoformat()
        }

        # Save ranking results to JSON
        ranking_json_path = batch_dir / f"{ranking_id}.json"
        try:
            with open(ranking_json_path, "w", encoding="utf-8") as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
            logger.info(f"Ranking results saved: {ranking_json_path}")
        except Exception as e:
            logger.warning(f"Failed to save ranking JSON: {e}")

        logger.info(f"Strategy ranking complete: {ranking_id}")
        return response

    def _get_plan_names(
        self,
        case_dir: Path,
        batch_dir: Path,
        plan_ids: List[str]
    ) -> Dict[str, str]:
        """
        Get plan names from metadata or batch config

        Args:
            case_dir: Case directory path
            batch_dir: Batch directory path
            plan_ids: List of plan IDs

        Returns:
            Dict mapping plan_id to plan_name
        """
        plan_names = {}

        # Try to read from batch config
        try:
            simulation_config_path = batch_dir / "simulation_config.json"
            if simulation_config_path.exists():
                with open(simulation_config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    plan_configs = config.get("plan_configs", {})
                    for plan_id in plan_ids:
                        plan_data = plan_configs.get(plan_id, {})
                        plan_names[plan_id] = plan_data.get("name", plan_id)
        except Exception as e:
            logger.warning(f"Failed to read plan names from config: {e}")

        # Fill in any missing names with plan IDs
        for plan_id in plan_ids:
            if plan_id not in plan_names:
                plan_names[plan_id] = plan_id

        return plan_names

    def get_ranking_results(self, batch_dir: Path, ranking_id: str) -> Optional[Dict]:
        """
        Retrieve previously generated ranking results

        Args:
            batch_dir: Batch directory path
            ranking_id: Ranking ID

        Returns:
            Dict with ranking results or None if not found
        """
        batch_dir = Path(batch_dir)
        ranking_file = batch_dir / f"{ranking_id}.json"

        try:
            if ranking_file.exists():
                with open(ranking_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read ranking results: {e}")

        return None


# Singleton instance for use in routes
_ranking_service = None


def get_ranking_service() -> StrategyRankingService:
    """Get or create ranking service singleton"""
    global _ranking_service
    if _ranking_service is None:
        _ranking_service = StrategyRankingService()
    return _ranking_service
