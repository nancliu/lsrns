"""
Event-Scenario Batch Service

Manages event-scenario batches (one event = one batch with multiple scenarios)
Similar to optimization batches but for event scenarios.

Author: Development Team
Date: 2025-11-15
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
import asyncio

from .base_service import BaseService
from .case_service import CaseService
from .simulation_service import SimulationService
from .analysis_orchestration_service import AnalysisOrchestrationService
from ..models.requests.case_requests import EventScenarioQuickCreateRequest

logger = logging.getLogger(__name__)


class EventBatchService(BaseService):
    """
    Event-Scenario Batch Service

    Treats one event as one batch (similar to optimization batches).
    One event can have multiple scenarios (NO_CONTROL, VSS, TEC, DHS).
    """

    def __init__(self):
        super().__init__()
        self.case_service = CaseService()
        self.simulation_service = SimulationService()
        self.analysis_service = AnalysisOrchestrationService()
        self.scenario_index_file = Path("output/scenarios/scenario_index.json")

    def _load_scenario_index(self) -> Dict[str, Any]:
        """Load scenario index from output/scenarios/scenario_index.json"""
        if not self.scenario_index_file.exists():
            raise FileNotFoundError(f"Scenario index not found: {self.scenario_index_file}")

        with open(self.scenario_index_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _find_scenarios_by_event(self, event_id: str) -> List[Dict[str, Any]]:
        """
        Find all scenarios for a given event ID

        Args:
            event_id: Event ID

        Returns:
            List of scenario metadata for this event
        """
        index_data = self._load_scenario_index()
        scenarios = []

        for scenario in index_data.get("scenarios", []):
            if scenario.get("event_id") == event_id:
                scenarios.append(scenario)

        return scenarios

    def _get_scenario_id_from_metadata(self, scenario_meta: Dict[str, Any]) -> str:
        """
        Generate scenario ID from metadata

        Args:
            scenario_meta: Scenario metadata

        Returns:
            Scenario ID in format: scenario_{event_id}_{strategy}
        """
        event_id = scenario_meta.get("event_id", "unknown")
        strategy = scenario_meta.get("strategy", "NO_CONTROL").lower()
        return f"scenario_{event_id}_{strategy}"

    async def create_event_batch(
        self,
        event_id: str,
        scenario_ids: Optional[List[str]] = None,
        simulation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create event-scenario batch

        Args:
            event_id: Event ID
            scenario_ids: List of scenario IDs (if None, use all scenarios for this event)
            simulation_config: Simulation configuration (optional)

        Returns:
            Batch metadata with case_ids and simulation_ids

        Process:
            1. Find scenarios for this event
            2. Create batch directory
            3. Create cases for each scenario
            4. Prepare simulations for each case
            5. Save batch metadata
        """
        logger.info(f"Creating event batch for event_id={event_id}")

        # Find scenarios for this event
        all_scenarios = self._find_scenarios_by_event(event_id)

        if not all_scenarios:
            raise ValueError(f"No scenarios found for event_id={event_id}")

        # Filter scenarios if scenario_ids provided
        if scenario_ids:
            scenarios_to_use = []
            for scenario_id in scenario_ids:
                scenario_meta = next(
                    (s for s in all_scenarios if self._get_scenario_id_from_metadata(s) == scenario_id),
                    None
                )
                if scenario_meta:
                    scenarios_to_use.append(scenario_meta)
                else:
                    logger.warning(f"Scenario not found: {scenario_id}")
        else:
            scenarios_to_use = all_scenarios

        if not scenarios_to_use:
            raise ValueError(f"No valid scenarios found for event_id={event_id}")

        # Generate batch ID
        batch_id = f"batch_event_{event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        batch_dir = self.cases_dir / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created batch directory: {batch_dir}")

        # Create cases and simulations for each scenario
        case_ids = []
        simulation_ids = []
        scenarios_metadata = []

        # Default simulation config
        if simulation_config is None:
            simulation_config = {}

        for scenario_meta in scenarios_to_use:
            scenario_id = self._get_scenario_id_from_metadata(scenario_meta)
            strategy_type = scenario_meta.get("strategy", "NO_CONTROL")

            logger.info(f"Creating case for scenario: {scenario_id} (strategy={strategy_type})")

            try:
                # Prepare request for case creation
                case_request = EventScenarioQuickCreateRequest(
                    scenario_id=scenario_id,
                    event_id=event_id,
                    duration_hours=simulation_config.get("duration_hours"),
                    random_seed=simulation_config.get("random_seed", 12345),
                    output_config=simulation_config.get("output_config", {
                        "tripinfo": True,
                        "edgedata": True,
                        "summary": True
                    })
                )

                # Create case from scenario
                case_data = await self.case_service.create_case_from_scenario(case_request)
                case_id = case_data["case_id"]
                case_ids.append(case_id)

                logger.info(f"Created case: {case_id}")

                # Get the first simulation ID from the case (should be auto-created)
                simulation_id = case_data.get("simulation_id")

                if not simulation_id:
                    # If no simulation was auto-created, create one manually
                    logger.warning(f"No simulation auto-created for case {case_id}, creating manually")
                    sim_data = await self.simulation_service.prepare_simulation(
                        case_id=case_id,
                        duration_hours=simulation_config.get("duration_hours"),
                        random_seed=simulation_config.get("random_seed", 12345)
                    )
                    simulation_id = sim_data["simulation_id"]

                simulation_ids.append(simulation_id)

                logger.info(f"Simulation ready: {simulation_id}")

                scenarios_metadata.append({
                    "scenario_id": scenario_id,
                    "strategy_type": strategy_type,
                    "case_id": case_id,
                    "simulation_id": simulation_id,
                    "event_type": scenario_meta.get("event_type", "unknown"),
                    "location": scenario_meta.get("location", {})
                })

            except Exception as e:
                logger.error(f"Failed to create case/simulation for scenario {scenario_id}: {e}")
                raise

        # Get event type from first scenario
        event_type = scenarios_to_use[0].get("event_type", "unknown") if scenarios_to_use else "unknown"

        # Save batch metadata
        batch_metadata = {
            "batch_id": batch_id,
            "batch_type": "event_scenario",
            "event_id": event_id,
            "event_type": event_type,
            "created_at": datetime.now().isoformat(),
            "scenarios": scenarios_metadata,
            "status": "created",
            "total_simulations": len(simulation_ids),
            "completed_simulations": 0,
            "running_simulations": 0,
            "failed_simulations": 0,
            "simulation_progress": {
                "started_at": None,
                "completed_at": None,
                "estimated_completion": None
            },
            "analysis_batch_id": None,
            "simulation_config": simulation_config
        }

        batch_metadata_file = batch_dir / "batch_metadata.json"
        with open(batch_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(batch_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Batch created successfully: {batch_id}")

        return {
            "batch_id": batch_id,
            "event_id": event_id,
            "event_type": event_type,
            "total_scenarios": len(scenario_ids) if scenario_ids else len(all_scenarios),
            "case_ids": case_ids,
            "simulation_ids": simulation_ids,
            "status": "created"
        }

    async def list_event_batches(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List event-scenario batches

        Args:
            status: Filter by status (created|running|completed|failed|all)
            limit: Max number of batches to return

        Returns:
            List of batch metadata
        """
        logger.info(f"Listing event batches: status={status}, limit={limit}")
        batches = []

        # Find all batch directories
        for batch_dir in self.cases_dir.glob("batch_event_*"):
            if not batch_dir.is_dir():
                continue

            batch_metadata_file = batch_dir / "batch_metadata.json"
            if not batch_metadata_file.exists():
                continue

            try:
                with open(batch_metadata_file, 'r', encoding='utf-8') as f:
                    batch_meta = json.load(f)

                # Filter by status
                if status and status != "all" and batch_meta.get("status") != status:
                    continue

                batches.append(batch_meta)

            except Exception as e:
                logger.error(f"Failed to load batch metadata from {batch_metadata_file}: {e}")
                continue

        # Sort by created_at (newest first)
        batches.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        logger.info(f"Found {len(batches)} event batches")
        return batches[:limit]

    async def get_event_batch_status(
        self,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Get event-scenario batch status with real-time simulation progress

        Args:
            batch_id: Batch ID

        Returns:
            Batch status with simulation details
        """
        logger.info(f"Getting batch status for: {batch_id}")

        batch_dir = self.cases_dir / batch_id
        batch_metadata_file = batch_dir / "batch_metadata.json"

        if not batch_metadata_file.exists():
            raise ValueError(f"Batch not found: {batch_id}")

        with open(batch_metadata_file, 'r', encoding='utf-8') as f:
            batch_meta = json.load(f)

        # Get real-time simulation status
        simulations = []
        completed = 0
        running = 0
        failed = 0

        for scenario in batch_meta["scenarios"]:
            sim_id = scenario["simulation_id"]

            try:
                sim_status = await self.simulation_service.get_simulation_status(sim_id)

                status = sim_status.get("status", "unknown")
                if status == "completed":
                    completed += 1
                elif status == "running":
                    running += 1
                elif status == "failed":
                    failed += 1

                simulations.append({
                    "simulation_id": sim_id,
                    "scenario_id": scenario["scenario_id"],
                    "strategy_type": scenario["strategy_type"],
                    "case_id": scenario["case_id"],
                    "status": status,
                    "progress": sim_status.get("progress", 0)
                })

            except Exception as e:
                logger.error(f"Failed to get status for simulation {sim_id}: {e}")
                simulations.append({
                    "simulation_id": sim_id,
                    "scenario_id": scenario["scenario_id"],
                    "strategy_type": scenario["strategy_type"],
                    "case_id": scenario["case_id"],
                    "status": "unknown",
                    "progress": 0
                })

        # Calculate progress percentage
        total = batch_meta["total_simulations"]
        progress_percent = int((completed / total * 100)) if total > 0 else 0

        # Update batch metadata with latest counts
        batch_meta["completed_simulations"] = completed
        batch_meta["running_simulations"] = running
        batch_meta["failed_simulations"] = failed

        # Update overall status
        if completed == total:
            batch_meta["status"] = "completed"
        elif failed > 0:
            batch_meta["status"] = "partial_failure"
        elif running > 0:
            batch_meta["status"] = "running"

        # Save updated metadata
        with open(batch_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(batch_meta, f, indent=2, ensure_ascii=False)

        return {
            "batch_id": batch_id,
            "event_id": batch_meta["event_id"],
            "event_type": batch_meta["event_type"],
            "status": batch_meta["status"],
            "total_simulations": total,
            "completed_simulations": completed,
            "running_simulations": running,
            "failed_simulations": failed,
            "progress_percent": progress_percent,
            "estimated_completion": batch_meta["simulation_progress"].get("estimated_completion"),
            "simulations": simulations
        }

    async def start_event_batch(
        self,
        batch_id: str,
        parallel_workers: int = 4,
        auto_run_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Start all simulations in an event-scenario batch

        Args:
            batch_id: Batch ID
            parallel_workers: Number of parallel simulation workers
            auto_run_analysis: Whether to automatically run analysis after completion

        Returns:
            Batch execution status
        """
        logger.info(f"Starting event batch: {batch_id} (workers={parallel_workers})")

        batch_dir = self.cases_dir / batch_id
        batch_metadata_file = batch_dir / "batch_metadata.json"

        if not batch_metadata_file.exists():
            raise ValueError(f"Batch not found: {batch_id}")

        with open(batch_metadata_file, 'r', encoding='utf-8') as f:
            batch_meta = json.load(f)

        simulation_ids = [s["simulation_id"] for s in batch_meta["scenarios"]]

        # Update status to running
        batch_meta["status"] = "running"
        batch_meta["simulation_progress"]["started_at"] = datetime.now().isoformat()

        with open(batch_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(batch_meta, f, indent=2, ensure_ascii=False)

        # Start simulations using simulation service
        # Note: This is a simplified version. In production, use BatchSimulationScheduler
        for sim_id in simulation_ids:
            try:
                await self.simulation_service.start_simulation(sim_id)
                logger.info(f"Started simulation: {sim_id}")
            except Exception as e:
                logger.error(f"Failed to start simulation {sim_id}: {e}")

        return {
            "batch_id": batch_id,
            "status": "running",
            "simulation_ids": simulation_ids,
            "message": f"Started {len(simulation_ids)} simulations"
        }

    async def get_event_batch_results(
        self,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Get aggregated analysis results for an event-scenario batch

        This method aggregates simulation results by strategy type and
        calculates improvement vs baseline (NO_CONTROL).

        Args:
            batch_id: Batch ID

        Returns:
            Batch results with strategy comparison and ranking
        """
        logger.info(f"Getting batch results for: {batch_id}")

        batch_dir = self.cases_dir / batch_id
        batch_metadata_file = batch_dir / "batch_metadata.json"

        if not batch_metadata_file.exists():
            raise ValueError(f"Batch not found: {batch_id}")

        with open(batch_metadata_file, 'r', encoding='utf-8') as f:
            batch_meta = json.load(f)

        # Aggregate results by strategy
        strategy_comparison = {}
        baseline_metrics = None

        for scenario in batch_meta["scenarios"]:
            sim_id = scenario["simulation_id"]
            strategy = scenario["strategy_type"]
            case_id = scenario["case_id"]

            try:
                # Get simulation results (summary.xml metrics)
                metrics = await self._get_simulation_metrics(case_id, sim_id)

                strategy_comparison[strategy] = metrics

                # Store baseline for comparison
                if strategy == "NO_CONTROL":
                    baseline_metrics = metrics

            except Exception as e:
                logger.error(f"Failed to get metrics for simulation {sim_id}: {e}")
                continue

        # Calculate improvements vs baseline
        if baseline_metrics:
            for strategy, metrics in strategy_comparison.items():
                if strategy != "NO_CONTROL":
                    metrics["improvement_vs_baseline"] = self._calculate_improvements(
                        metrics, baseline_metrics
                    )

        # Rank strategies by overall improvement
        strategy_ranking = self._rank_strategies(strategy_comparison, baseline_metrics)

        return {
            "batch_id": batch_id,
            "event_id": batch_meta["event_id"],
            "event_type": batch_meta["event_type"],
            "analysis_batch_id": batch_meta.get("analysis_batch_id"),
            "strategy_comparison": strategy_comparison,
            "strategy_ranking": strategy_ranking
        }

    async def _get_simulation_metrics(
        self,
        case_id: str,
        simulation_id: str
    ) -> Dict[str, float]:
        """
        Get simulation metrics from summary.xml

        Args:
            case_id: Case ID
            simulation_id: Simulation ID

        Returns:
            Dictionary of metrics
        """
        import xml.etree.ElementTree as ET

        # Locate summary.xml file
        case_dir = self.cases_dir / case_id
        sim_dir = case_dir / "simulations" / simulation_id
        summary_file = sim_dir / "output" / "summary.xml"

        if not summary_file.exists():
            logger.warning(f"summary.xml not found for {simulation_id}, using default values")
            return {
                "avg_speed": 0.0,
                "avg_trip_duration": 0.0,
                "completion_rate": 0.0,
                "total_vehicles": 0,
                "total_delay": 0.0,
                "avg_waiting_time": 0.0
            }

        try:
            # Parse summary.xml
            tree = ET.parse(summary_file)
            root = tree.getroot()

            # Extract metrics from last timestep
            timesteps = root.findall("timestep")
            if not timesteps:
                raise ValueError("No timesteps found in summary.xml")

            last_step = timesteps[-1]

            # Get vehicle summary from last step
            vehicle = last_step.find("vehicleSummary")
            if vehicle is None:
                raise ValueError("No vehicleSummary found in last timestep")

            # Extract metrics
            loaded = int(vehicle.get("loaded", 0))
            inserted = int(vehicle.get("inserted", 0))
            ended = int(vehicle.get("ended", 0))
            running = int(vehicle.get("running", 0))
            waiting = int(vehicle.get("waiting", 0))
            teleports = int(vehicle.get("teleports", 0))

            # Calculate derived metrics
            total_vehicles = loaded
            completion_rate = (ended / loaded * 100) if loaded > 0 else 0.0

            # Get average speed (may be in m/s, convert to km/h)
            # Note: Some SUMO versions output speed in m/s, others in km/h
            avg_speed_raw = float(vehicle.get("speed", 0))
            # Assume if speed > 200, it's in m/s and needs conversion
            avg_speed = avg_speed_raw * 3.6 if avg_speed_raw < 200 else avg_speed_raw

            # Calculate average trip duration from tripinfo if available
            # For now, estimate based on running time
            sim_duration = int(last_step.get("time", 0))
            avg_trip_duration = sim_duration / ended if ended > 0 else 0.0

            # Estimate total delay (waiting time * waiting vehicles)
            # This is a rough estimate - actual delay requires tripinfo.xml
            total_delay = waiting * 60.0  # Rough estimate

            # Average waiting time (per vehicle)
            avg_waiting_time = waiting / total_vehicles if total_vehicles > 0 else 0.0

            metrics = {
                "avg_speed": round(avg_speed, 2),
                "avg_trip_duration": round(avg_trip_duration, 2),
                "completion_rate": round(completion_rate, 2),
                "total_vehicles": total_vehicles,
                "total_delay": round(total_delay, 2),
                "avg_waiting_time": round(avg_waiting_time, 2)
            }

            logger.info(f"Extracted metrics for {simulation_id}: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Failed to parse summary.xml for {simulation_id}: {e}")
            return {
                "avg_speed": 0.0,
                "avg_trip_duration": 0.0,
                "completion_rate": 0.0,
                "total_vehicles": 0,
                "total_delay": 0.0,
                "avg_waiting_time": 0.0
            }

    def _calculate_improvements(
        self,
        metrics: Dict[str, float],
        baseline: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate improvement percentages vs baseline

        Args:
            metrics: Strategy metrics
            baseline: Baseline metrics

        Returns:
            Improvement percentages
        """
        improvements = {}

        # For metrics where higher is better
        for key in ["avg_speed", "completion_rate"]:
            if key in metrics and key in baseline and baseline[key] != 0:
                improvements[key] = ((metrics[key] - baseline[key]) / baseline[key]) * 100

        # For metrics where lower is better (negative improvement means better)
        for key in ["avg_trip_duration", "total_delay", "avg_waiting_time"]:
            if key in metrics and key in baseline and baseline[key] != 0:
                improvements[key] = ((metrics[key] - baseline[key]) / baseline[key]) * 100

        return improvements

    def _rank_strategies(
        self,
        strategy_comparison: Dict[str, Dict[str, Any]],
        baseline: Optional[Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Rank strategies by overall improvement

        Args:
            strategy_comparison: Strategy comparison data
            baseline: Baseline metrics

        Returns:
            List of ranked strategies
        """
        if not baseline:
            return []

        rankings = []

        for strategy, metrics in strategy_comparison.items():
            if strategy == "NO_CONTROL":
                continue

            improvements = metrics.get("improvement_vs_baseline", {})

            # Calculate overall improvement (weighted average)
            # Positive improvements for speed/completion, negative for time/delay
            overall = 0.0
            count = 0

            for key, value in improvements.items():
                if key in ["avg_speed", "completion_rate"]:
                    overall += value  # Higher is better
                    count += 1
                elif key in ["avg_trip_duration", "total_delay"]:
                    overall += -value  # Lower is better (negate)
                    count += 1

            overall_improvement = overall / count if count > 0 else 0.0

            rankings.append({
                "strategy": strategy,
                "overall_improvement": round(overall_improvement, 2),
                "rank": 0  # Will be set after sorting
            })

        # Sort by overall improvement (descending)
        rankings.sort(key=lambda x: x["overall_improvement"], reverse=True)

        # Assign ranks
        for i, item in enumerate(rankings):
            item["rank"] = i + 1

        return rankings
