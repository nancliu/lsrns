"""
Scenario Index Updater - Update scenario_index.json when new scenarios are created
"""
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ScenarioIndexUpdater:
    """Update and maintain scenario_index.json"""

    def __init__(self, scenarios_dir: Path = None):
        """
        Initialize updater.

        Args:
            scenarios_dir: Path to scenarios directory (default: output/scenarios)
        """
        self.scenarios_dir = scenarios_dir or Path("output/scenarios")
        self.index_file = self.scenarios_dir / "scenario_index.json"

    def add_scenario(self, scenario_dir_name: str) -> bool:
        """
        Add a single scenario to the index.

        Args:
            scenario_dir_name: Scenario directory name (e.g., scenario_12345_tec)

        Returns:
            True if successfully added, False otherwise
        """
        # Find the scenario directory
        scenario_path = None
        for event_type_dir in self.scenarios_dir.iterdir():
            if not event_type_dir.is_dir():
                continue
            potential_path = event_type_dir / scenario_dir_name
            if potential_path.exists():
                scenario_path = potential_path
                break

        if not scenario_path:
            logger.error(f"Scenario directory not found: {scenario_dir_name}")
            return False

        # Read event_description.json
        event_desc_file = scenario_path / "event_description.json"
        if not event_desc_file.exists():
            logger.error(f"event_description.json not found in {scenario_dir_name}")
            return False

        try:
            with open(event_desc_file, 'r', encoding='utf-8') as f:
                event_desc = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read event_description.json: {e}")
            return False

        # Build scenario metadata
        scenario_metadata = self._build_scenario_metadata(scenario_dir_name, event_desc)

        # Load existing index
        index_data = self._load_index()

        # Check if scenario already exists
        existing_dirs = {s["files"]["scenario_dir"] for s in index_data["scenarios"]}
        if scenario_dir_name in existing_dirs:
            logger.info(f"Scenario {scenario_dir_name} already in index, skipping")
            return True

        # Add to index
        index_data["scenarios"].append(scenario_metadata)

        # Save index
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Added scenario to index: {scenario_dir_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False

    def add_scenarios_batch(self, scenario_dir_names: List[str]) -> Dict[str, int]:
        """
        Add multiple scenarios to the index in batch.

        Args:
            scenario_dir_names: List of scenario directory names

        Returns:
            {"added": count, "skipped": count, "failed": count}
        """
        added = 0
        skipped = 0
        failed = 0

        # Load existing index once
        index_data = self._load_index()
        existing_dirs = {s["files"]["scenario_dir"] for s in index_data["scenarios"]}

        new_scenarios = []

        for scenario_dir_name in scenario_dir_names:
            if scenario_dir_name in existing_dirs:
                skipped += 1
                continue

            # Find scenario directory
            scenario_path = None
            for event_type_dir in self.scenarios_dir.iterdir():
                if not event_type_dir.is_dir():
                    continue
                potential_path = event_type_dir / scenario_dir_name
                if potential_path.exists():
                    scenario_path = potential_path
                    break

            if not scenario_path:
                logger.warning(f"Scenario directory not found: {scenario_dir_name}")
                failed += 1
                continue

            # Read event_description.json
            event_desc_file = scenario_path / "event_description.json"
            if not event_desc_file.exists():
                logger.warning(f"event_description.json not found in {scenario_dir_name}")
                failed += 1
                continue

            try:
                with open(event_desc_file, 'r', encoding='utf-8') as f:
                    event_desc = json.load(f)

                scenario_metadata = self._build_scenario_metadata(scenario_dir_name, event_desc)
                new_scenarios.append(scenario_metadata)
                added += 1

            except Exception as e:
                logger.error(f"Failed to process {scenario_dir_name}: {e}")
                failed += 1

        # Add new scenarios to index
        if new_scenarios:
            index_data["scenarios"].extend(new_scenarios)
            try:
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, ensure_ascii=False, indent=2)
                logger.info(f"✅ Added {added} scenarios to index")
            except Exception as e:
                logger.error(f"Failed to save index: {e}")
                return {"added": 0, "skipped": skipped, "failed": failed + added}

        return {"added": added, "skipped": skipped, "failed": failed}

    def _load_index(self) -> Dict[str, Any]:
        """Load scenario index from file."""
        if not self.index_file.exists():
            return {"scenarios": []}

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return {"scenarios": []}

    def _build_scenario_metadata(self, scenario_dir_name: str, event_desc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build scenario metadata entry for index.

        Args:
            scenario_dir_name: Scenario directory name
            event_desc: Event description data from JSON

        Returns:
            Scenario metadata dictionary
        """
        # Extract event_id and strategy from directory name
        parts = scenario_dir_name.split('_')
        event_id = parts[1] if len(parts) > 1 else ""
        strategy = parts[2].upper() if len(parts) > 2 else "NO_CONTROL"

        # Determine add.xml filename based on event type and strategy
        event_type = event_desc.get("event_type", "")
        event_type_en = {
            "交通事故": "accident",
            "交通拥堵": "congestion",
            "交通管制": "road_control",
            "车辆故障": "breakdown",
            "恶劣天气": "weather",
            "交通阻塞": "congestion"  # Alternative name
        }.get(event_type, "event")

        if strategy == "NO_CONTROL":
            add_xml_name = f"scenario_{event_type_en}_event_{event_id}.add.xml"
        else:
            add_xml_name = f"scenario_{event_type_en}_{strategy.lower()}_{event_id}.add.xml"

        # Calculate duration
        duration_hours = 0
        if event_desc.get("event_time") and event_desc.get("clearance_time"):
            try:
                start = datetime.fromisoformat(event_desc["event_time"])
                end = datetime.fromisoformat(event_desc["clearance_time"])
                duration_hours = round((end - start).total_seconds() / 3600, 2)
            except Exception:
                pass

        # Build metadata
        return {
            "event_id": event_id,
            "event_type": event_type,
            "strategy": strategy,
            "location": {
                "road": event_desc.get("location", {}).get("road", ""),
                "direction": event_desc.get("location", {}).get("direction", ""),
                "mileage": event_desc.get("location", {}).get("mileage", ""),
                "junction_id": event_desc.get("location", {}).get("junction_id", ""),
                "edge_id": event_desc.get("location", {}).get("edge_id", "")
            },
            "time": {
                "start_time": event_desc.get("event_time", ""),
                "end_time": event_desc.get("clearance_time", ""),
                "duration_hours": duration_hours
            },
            "files": {
                "scenario_dir": scenario_dir_name,
                "add_xml": add_xml_name,
                "event_description": "event_description.json",
                "traffic_config": "traffic_input_config.json",
                "control_config": "control_strategy_config.json"
            },
            "created_cases": []
        }
