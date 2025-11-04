"""
EdgeData.xml Analyzer for Control Strategy Ranking

Responsibilities:
- Parse edgedata.xml for each plan's simulation
- Extract per-edge-interval metrics: speed, occupancy, density
- Compute edge-level improvements vs baseline
- Identify improved_segments and deteriorated_segments
- Return independent analysis results
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class EdgeDataAnalyzer:
    """Analyzes edgedata.xml metrics for control strategy ranking"""

    def __init__(self):
        """Initialize edgedata analyzer"""
        self.baseline_edgedata = {}
        self.plan_edgedata = {}

    def analyze(
        self,
        batch_dir: Path,
        plan_ids: List[str],
        baseline_plan_id: str
    ) -> Dict[str, Any]:
        """
        Analyze edgedata.xml for all plans in batch

        Args:
            batch_dir: Batch directory path
            plan_ids: List of plan IDs to analyze
            baseline_plan_id: Baseline plan ID

        Returns:
            Dict with:
                - baseline_edgedata: Dict with edge segment metrics
                - plan_edgedata: Dict[plan_id, Dict with edgedata metrics]
                - improved_segments_count: Dict[plan_id, count]
                - deteriorated_segments_count: Dict[plan_id, count]
                - metrics_metadata: Dict with metric descriptions
        """
        logger.info(f"Analyzing edgedata.xml for {len(plan_ids)} plans")

        batch_dir = Path(batch_dir)

        # Parse baseline edgedata
        baseline_path = batch_dir / baseline_plan_id / "edgedata" / "edgedata.xml"
        if baseline_path.exists():
            self.baseline_edgedata = self._parse_edgedata_file(baseline_path)
            logger.info(
                f"Baseline edgedata: "
                f"{len(self.baseline_edgedata.get('edges', {}))} edges, "
                f"avg_speed={self.baseline_edgedata.get('avg_speed', 0):.2f}m/s"
            )
        else:
            logger.warning(f"Baseline edgedata.xml not found: {baseline_path}")
            # Return graceful degradation - edgedata is optional
            return {
                "baseline_edgedata": {},
                "plan_edgedata": {},
                "improved_segments_count": {},
                "deteriorated_segments_count": {},
                "metrics_metadata": self._get_metrics_metadata(),
                "note": "EdgeData analysis not available (output_edgedata=false or file missing)",
            }

        # Parse test plan edgedata
        improved_segments = {}
        deteriorated_segments = {}

        for plan_id in plan_ids:
            if plan_id == baseline_plan_id:
                continue

            plan_path = batch_dir / plan_id / "edgedata" / "edgedata.xml"
            if plan_path.exists():
                plan_data = self._parse_edgedata_file(plan_path)
                self.plan_edgedata[plan_id] = plan_data
                logger.info(
                    f"Plan {plan_id} edgedata: "
                    f"{len(plan_data.get('edges', {}))} edges, "
                    f"avg_speed={plan_data.get('avg_speed', 0):.2f}m/s"
                )

                # Compare with baseline to count improved/deteriorated segments
                improved, deteriorated = self._compare_edge_segments(
                    self.baseline_edgedata, plan_data
                )
                improved_segments[plan_id] = improved
                deteriorated_segments[plan_id] = deteriorated
            else:
                logger.debug(f"EdgeData.xml not found for plan {plan_id}: {plan_path}")

        return {
            "baseline_edgedata": self.baseline_edgedata.copy(),
            "plan_edgedata": self.plan_edgedata.copy(),
            "improved_segments_count": improved_segments.copy(),
            "deteriorated_segments_count": deteriorated_segments.copy(),
            "metrics_metadata": self._get_metrics_metadata(),
        }

    def _parse_edgedata_file(self, edgedata_path: Path) -> Dict[str, Any]:
        """
        Parse edgedata.xml and extract metrics by edge

        Args:
            edgedata_path: Path to edgedata.xml file

        Returns:
            Dict with metrics:
                - total_edges: Number of edges in file
                - edges: Dict[edge_id, {speed, occupancy, density, ...}]
                - avg_speed: Average speed across all edges
                - avg_occupancy: Average occupancy across all edges
        """
        result = {
            "total_edges": 0,
            "edges": {},
            "avg_speed": 0.0,
            "avg_occupancy": 0.0,
            "avg_density": 0.0,
        }

        try:
            tree = ET.parse(edgedata_path)
            root = tree.getroot()

            speeds = []
            occupancies = []
            densities = []
            edge_count = 0

            for edge in root.findall(".//edge"):
                edge_id = edge.get("id")
                if not edge_id:
                    continue

                edge_count += 1

                # Aggregate metrics across all time intervals for this edge
                edge_data = {
                    "id": edge_id,
                    "intervals": [],
                    "total_time": 0.0,
                    "avg_speed": 0.0,
                    "avg_occupancy": 0.0,
                    "avg_density": 0.0,
                }

                interval_speeds = []
                interval_occupancies = []
                interval_densities = []

                for interval in edge.findall("interval"):
                    speed = float(interval.get("speed", 0))
                    occupancy = float(interval.get("occupancy", 0))
                    density = float(interval.get("density", 0))
                    time_value = float(interval.get("time", 0))

                    interval_speeds.append(speed)
                    interval_occupancies.append(occupancy)
                    interval_densities.append(density)

                    edge_data["intervals"].append({
                        "time": time_value,
                        "speed": speed,
                        "occupancy": occupancy,
                        "density": density,
                    })

                # Calculate edge averages
                if interval_speeds:
                    edge_data["avg_speed"] = sum(interval_speeds) / len(
                        interval_speeds
                    )
                    speeds.append(edge_data["avg_speed"])

                if interval_occupancies:
                    edge_data["avg_occupancy"] = sum(interval_occupancies) / len(
                        interval_occupancies
                    )
                    occupancies.append(edge_data["avg_occupancy"])

                if interval_densities:
                    edge_data["avg_density"] = sum(interval_densities) / len(
                        interval_densities
                    )
                    densities.append(edge_data["avg_density"])

                result["edges"][edge_id] = edge_data

            # Calculate network-level averages
            result["total_edges"] = edge_count

            if speeds:
                result["avg_speed"] = sum(speeds) / len(speeds)

            if occupancies:
                result["avg_occupancy"] = sum(occupancies) / len(occupancies)

            if densities:
                result["avg_density"] = sum(densities) / len(densities)

            logger.debug(
                f"Parsed edgedata: {edge_count} edges, "
                f"avg_speed={result['avg_speed']:.2f}m/s, "
                f"avg_occupancy={result['avg_occupancy']:.2f}"
            )

        except Exception as e:
            logger.error(f"Error parsing edgedata.xml {edgedata_path}: {e}")
            result["error"] = str(e)

        return result

    def _compare_edge_segments(
        self,
        baseline_edgedata: Dict[str, Any],
        plan_edgedata: Dict[str, Any]
    ) -> tuple[int, int]:
        """
        Compare edge segments between baseline and plan

        Args:
            baseline_edgedata: Baseline edgedata metrics
            plan_edgedata: Plan edgedata metrics

        Returns:
            Tuple of (improved_count, deteriorated_count)
        """
        baseline_edges = baseline_edgedata.get("edges", {})
        plan_edges = plan_edgedata.get("edges", {})

        improved = 0
        deteriorated = 0

        for edge_id in plan_edges:
            if edge_id not in baseline_edges:
                # New edge in test plan - consider as improved
                improved += 1
                continue

            baseline_speed = baseline_edges[edge_id].get("avg_speed", 0)
            plan_speed = plan_edges[edge_id].get("avg_speed", 0)

            if plan_speed > baseline_speed:
                improved += 1
            elif plan_speed < baseline_speed:
                deteriorated += 1

        return improved, deteriorated

    def _get_metrics_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about edgedata metrics

        Returns:
            Dict mapping metric name to metadata
        """
        return {
            "improved_segments": {
                "direction": "higher",
                "description": "改善的路段数",
                "unit": "条",
                "include_in_scoring": True,
            },
            "deteriorated_segments": {
                "direction": "lower",
                "description": "恶化的路段数",
                "unit": "条",
                "include_in_scoring": False,
            },
            "avg_speed": {
                "direction": "higher",
                "description": "平均速度",
                "unit": "m/s",
                "include_in_scoring": True,
            },
            "avg_occupancy": {
                "direction": "lower",
                "description": "平均占有率",
                "unit": "无",
                "include_in_scoring": False,
            },
            "total_edges": {
                "direction": "higher",
                "description": "分析的路段总数",
                "unit": "条",
                "include_in_scoring": False,
            },
        }

    def get_baseline_edgedata(self) -> Dict[str, Any]:
        """Get baseline edgedata metrics"""
        return self.baseline_edgedata.copy()

    def get_plan_edgedata(self, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Get edgedata for specific plan or all plans"""
        if plan_id:
            return self.plan_edgedata.get(plan_id, {})
        return self.plan_edgedata.copy()


# Convenience function
def analyze_edgedata(
    batch_dir: str,
    plan_ids: List[str],
    baseline_plan_id: str
) -> Dict[str, Any]:
    """
    Analyze edgedata.xml for all plans

    Args:
        batch_dir: Batch directory path
        plan_ids: List of plan IDs
        baseline_plan_id: Baseline plan ID

    Returns:
        Dict with analysis results
    """
    analyzer = EdgeDataAnalyzer()
    return analyzer.analyze(Path(batch_dir), plan_ids, baseline_plan_id)
