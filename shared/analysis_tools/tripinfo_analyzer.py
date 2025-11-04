"""
TripInfo.xml Analyzer for Control Strategy Ranking

Responsibilities:
- Parse tripinfo.xml for each plan's simulation
- Extract per-vehicle fields: departure, arrival, duration (travel_time), timeLoss (delay)
- Compute aggregate metrics: avg_travel_time, avg_delay, total_delay
- Identify improved OD pairs vs baseline
- Return independent analysis results
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import statistics

logger = logging.getLogger(__name__)


class TripInfoAnalyzer:
    """Analyzes tripinfo.xml metrics for control strategy ranking"""

    def __init__(self):
        """Initialize tripinfo analyzer"""
        self.baseline_tripinfo = {}
        self.plan_tripinfo = {}

    def analyze(
        self,
        batch_dir: Path,
        plan_ids: List[str],
        baseline_plan_id: str
    ) -> Dict[str, Any]:
        """
        Analyze tripinfo.xml for all plans in batch

        Args:
            batch_dir: Batch directory path
            plan_ids: List of plan IDs to analyze
            baseline_plan_id: Baseline plan ID

        Returns:
            Dict with:
                - baseline_tripinfo: Dict with travel_time, delay, od_pairs metrics
                - plan_tripinfo: Dict[plan_id, Dict with tripinfo metrics]
                - improved_od_pairs: Dict[plan_id, count]
                - metrics_metadata: Dict with metric descriptions
        """
        logger.info(f"Analyzing tripinfo.xml for {len(plan_ids)} plans")

        batch_dir = Path(batch_dir)

        # Parse baseline tripinfo
        baseline_path = batch_dir / baseline_plan_id / "tripinfo.xml"
        if baseline_path.exists():
            self.baseline_tripinfo = self._parse_tripinfo_file(baseline_path)
            logger.info(
                f"Baseline tripinfo: "
                f"avg_travel_time={self.baseline_tripinfo.get('avg_travel_time'):.2f}s, "
                f"avg_delay={self.baseline_tripinfo.get('avg_delay'):.2f}s"
            )
        else:
            logger.warning(f"Baseline tripinfo.xml not found: {baseline_path}")
            return {
                "error": f"Baseline tripinfo.xml not found",
                "baseline_tripinfo": {},
                "plan_tripinfo": {},
                "improved_od_pairs": {},
                "metrics_metadata": self._get_metrics_metadata(),
            }

        # Parse test plan tripinfo
        improved_od_pairs = {}
        for plan_id in plan_ids:
            if plan_id == baseline_plan_id:
                continue

            plan_path = batch_dir / plan_id / "tripinfo.xml"
            if plan_path.exists():
                plan_data = self._parse_tripinfo_file(plan_path)
                self.plan_tripinfo[plan_id] = plan_data
                logger.info(
                    f"Plan {plan_id} tripinfo: "
                    f"avg_travel_time={plan_data.get('avg_travel_time'):.2f}s, "
                    f"avg_delay={plan_data.get('avg_delay'):.2f}s"
                )

                # Compare with baseline to count improved OD pairs
                improved_count = self._count_improved_od_pairs(
                    self.baseline_tripinfo, plan_data
                )
                improved_od_pairs[plan_id] = improved_count
            else:
                logger.debug(f"TripInfo.xml not found for plan {plan_id}: {plan_path}")

        return {
            "baseline_tripinfo": self.baseline_tripinfo.copy(),
            "plan_tripinfo": self.plan_tripinfo.copy(),
            "improved_od_pairs": improved_od_pairs.copy(),
            "metrics_metadata": self._get_metrics_metadata(),
        }

    def _parse_tripinfo_file(self, tripinfo_path: Path) -> Dict[str, Any]:
        """
        Parse tripinfo.xml and extract aggregate metrics

        Args:
            tripinfo_path: Path to tripinfo.xml file

        Returns:
            Dict with metrics:
                - total_trips: Number of trips
                - avg_travel_time: Average duration (seconds)
                - avg_delay: Average timeLoss (seconds)
                - total_delay: Sum of all timeLoss (seconds)
                - total_travel_time: Sum of all durations (seconds)
                - vehicle_count: Number of vehicles
                - od_pairs: Dict of OD pair metrics
        """
        result = {
            "total_trips": 0,
            "total_travel_time": 0.0,
            "total_delay": 0.0,
            "avg_travel_time": 0.0,
            "avg_delay": 0.0,
            "vehicle_count": 0,
            "od_pairs": {},
        }

        try:
            tree = ET.parse(tripinfo_path)
            root = tree.getroot()

            trip_count = 0
            durations = []
            delays = []

            for trip in root.findall("trip"):
                trip_count += 1

                # Extract travel time (duration)
                duration = float(trip.get("duration", 0))
                durations.append(duration)
                result["total_travel_time"] += duration

                # Extract delay (timeLoss)
                delay = float(trip.get("timeLoss", 0))
                delays.append(delay)
                result["total_delay"] += delay

                # Extract OD information (from depart/arrival or route edges)
                origin = trip.get("fromTaz") or trip.get("departLane", "").split("_")[0]
                destination = trip.get("toTaz") or trip.get("arrivalLane", "").split("_")[0]

                if origin and destination:
                    od_key = f"{origin}->{destination}"
                    if od_key not in result["od_pairs"]:
                        result["od_pairs"][od_key] = {
                            "count": 0,
                            "total_duration": 0.0,
                            "total_delay": 0.0,
                            "avg_duration": 0.0,
                            "avg_delay": 0.0,
                        }

                    result["od_pairs"][od_key]["count"] += 1
                    result["od_pairs"][od_key]["total_duration"] += duration
                    result["od_pairs"][od_key]["total_delay"] += delay

            # Calculate averages
            result["total_trips"] = trip_count
            result["vehicle_count"] = trip_count

            if trip_count > 0:
                result["avg_travel_time"] = result["total_travel_time"] / trip_count
                result["avg_delay"] = result["total_delay"] / trip_count

            # Calculate OD pair averages
            for od_key in result["od_pairs"]:
                od_data = result["od_pairs"][od_key]
                if od_data["count"] > 0:
                    od_data["avg_duration"] = od_data["total_duration"] / od_data["count"]
                    od_data["avg_delay"] = od_data["total_delay"] / od_data["count"]

            logger.debug(
                f"Parsed tripinfo: {trip_count} trips, "
                f"avg_travel_time={result['avg_travel_time']:.2f}s, "
                f"avg_delay={result['avg_delay']:.2f}s"
            )

        except Exception as e:
            logger.error(f"Error parsing tripinfo.xml {tripinfo_path}: {e}")
            result["error"] = str(e)

        return result

    def _count_improved_od_pairs(
        self,
        baseline_tripinfo: Dict[str, Any],
        plan_tripinfo: Dict[str, Any]
    ) -> int:
        """
        Count OD pairs with improved travel time vs baseline

        Args:
            baseline_tripinfo: Baseline tripinfo metrics
            plan_tripinfo: Plan tripinfo metrics

        Returns:
            Number of OD pairs with travel time reduction
        """
        baseline_od = baseline_tripinfo.get("od_pairs", {})
        plan_od = plan_tripinfo.get("od_pairs", {})

        improved_count = 0

        for od_key in plan_od:
            if od_key not in baseline_od:
                # New OD pair in test plan, count as "improved"
                improved_count += 1
                continue

            baseline_time = baseline_od[od_key].get("avg_duration", 0)
            plan_time = plan_od[od_key].get("avg_duration", 0)

            if baseline_time > 0 and plan_time < baseline_time:
                improved_count += 1

        return improved_count

    def _get_metrics_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about tripinfo metrics

        Returns:
            Dict mapping metric name to metadata
        """
        return {
            "avg_travel_time": {
                "direction": "lower",
                "description": "平均行程时间",
                "unit": "秒",
                "include_in_scoring": True,
            },
            "avg_delay": {
                "direction": "lower",
                "description": "平均延误时间",
                "unit": "秒",
                "include_in_scoring": True,
            },
            "total_delay": {
                "direction": "lower",
                "description": "总延误时间",
                "unit": "秒",
                "include_in_scoring": False,
            },
            "vehicle_count": {
                "direction": "higher",
                "description": "车辆总数",
                "unit": "辆",
                "include_in_scoring": False,
            },
            "od_pairs": {
                "direction": "higher",
                "description": "OD对覆盖率",
                "unit": "对",
                "include_in_scoring": True,
            },
        }

    def get_baseline_tripinfo(self) -> Dict[str, Any]:
        """Get baseline tripinfo metrics"""
        return self.baseline_tripinfo.copy()

    def get_plan_tripinfo(self, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tripinfo for specific plan or all plans"""
        if plan_id:
            return self.plan_tripinfo.get(plan_id, {})
        return self.plan_tripinfo.copy()


# Convenience function
def analyze_tripinfo(
    batch_dir: str,
    plan_ids: List[str],
    baseline_plan_id: str
) -> Dict[str, Any]:
    """
    Analyze tripinfo.xml for all plans

    Args:
        batch_dir: Batch directory path
        plan_ids: List of plan IDs
        baseline_plan_id: Baseline plan ID

    Returns:
        Dict with analysis results
    """
    analyzer = TripInfoAnalyzer()
    return analyzer.analyze(Path(batch_dir), plan_ids, baseline_plan_id)
