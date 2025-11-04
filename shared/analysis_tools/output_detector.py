"""
Output Configuration Detector for Control Strategy Ranking

Responsibilities:
- Read batch simulation_config.json to determine available outputs
- Detect which analysis outputs (summary.xml, tripinfo.xml, edgedata.xml) are available
- Return output combination information for adaptive scoring
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OutputDetector:
    """Detects available outputs based on batch configuration and file existence"""

    def __init__(self):
        """Initialize output detector"""
        self.available_outputs = {}
        self.output_paths = {}
        self.output_combination = ""

    def detect_outputs(
        self,
        batch_dir: Path,
        baseline_plan_id: str
    ) -> Dict[str, Any]:
        """
        Detect available outputs for ranking analysis

        Args:
            batch_dir: Batch directory path (e.g., cases/{case_id}/simulations/batch_001)
            baseline_plan_id: Baseline plan ID to check for output files

        Returns:
            Dict with keys:
                - available_outputs: {"summary": bool, "tripinfo": bool, "edgedata": bool}
                - output_combination: "summary" | "summary+tripinfo" | "summary+edgedata" | "summary+tripinfo+edgedata"
                - output_paths: {output_type: file_path_or_none}
                - output_config: parsed output_config from simulation_config.json
        """
        self.available_outputs = {}
        self.output_paths = {}

        batch_dir = Path(batch_dir)

        # Step 1: Read simulation_config.json to get output configuration
        output_config = self._read_output_config(batch_dir)
        self.available_outputs["summary"] = True  # Always available (mandatory)

        # Step 2: Check for tripinfo.xml
        tripinfo_enabled = output_config.get("output_tripinfo", False)
        tripinfo_path = batch_dir / baseline_plan_id / "tripinfo.xml"
        self.available_outputs["tripinfo"] = (
            tripinfo_enabled and tripinfo_path.exists()
        )
        self.output_paths["tripinfo"] = (
            tripinfo_path if self.available_outputs["tripinfo"] else None
        )

        # Step 3: Check for edgedata.xml
        edgedata_enabled = output_config.get("output_edgedata", False)
        edgedata_path = batch_dir / baseline_plan_id / "edgedata" / "edgedata.xml"
        self.available_outputs["edgedata"] = (
            edgedata_enabled and edgedata_path.exists()
        )
        self.output_paths["edgedata"] = (
            edgedata_path if self.available_outputs["edgedata"] else None
        )

        # Step 4: Determine output combination
        self.output_combination = self._determine_combination()

        logger.info(
            f"Output detection complete: {self.output_combination} "
            f"({self.available_outputs})"
        )

        return {
            "available_outputs": self.available_outputs.copy(),
            "output_combination": self.output_combination,
            "output_paths": self.output_paths.copy(),
            "output_config": output_config,
        }

    def _read_output_config(self, batch_dir: Path) -> Dict[str, Any]:
        """
        Read simulation_config.json to get output configuration

        Args:
            batch_dir: Batch directory path

        Returns:
            Dict with output_* keys (output_tripinfo, output_edgedata, etc.)
        """
        config_path = batch_dir / "simulation_config.json"

        if not config_path.exists():
            logger.warning(f"simulation_config.json not found: {config_path}")
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Extract output configuration
            output_config = {}
            for key in [
                "output_tripinfo",
                "output_vehroute",
                "output_netstate",
                "output_fcd",
                "output_emission",
                "output_edgedata",
            ]:
                output_config[key] = config.get(key, False)

            logger.debug(f"Output config from simulation_config.json: {output_config}")
            return output_config

        except Exception as e:
            logger.error(f"Error reading output config: {e}")
            return {}

    def _determine_combination(self) -> str:
        """
        Determine output combination string

        Returns:
            One of: "summary", "summary+tripinfo", "summary+edgedata", "summary+tripinfo+edgedata"
        """
        parts = ["summary"]

        if self.available_outputs.get("tripinfo"):
            parts.append("tripinfo")

        if self.available_outputs.get("edgedata"):
            parts.append("edgedata")

        return "+".join(parts)

    def get_available_outputs(self) -> Dict[str, bool]:
        """Get available outputs dictionary"""
        return self.available_outputs.copy()

    def get_output_combination(self) -> str:
        """Get output combination string"""
        return self.output_combination

    def get_output_paths(self) -> Dict[str, Path]:
        """Get output file paths"""
        return self.output_paths.copy()


# Convenience function
def detect_outputs(batch_dir: str, baseline_plan_id: str) -> Dict[str, Any]:
    """
    Detect available outputs for a batch

    Args:
        batch_dir: Batch directory path
        baseline_plan_id: Baseline plan ID

    Returns:
        Dict with output detection results
    """
    detector = OutputDetector()
    return detector.detect_outputs(Path(batch_dir), baseline_plan_id)
