"""
Scenario Library Initialization Script (Phase 5)

Initializes a scenario library case for batch scenario management.

Purpose:
- Creates a unified case structure for event scenarios
- Copies scenario files (.add.xml, metadata) to case directory
- Sets up scenario index for case management
- Enables case-based scenario workflow

Usage:
    python scripts/initialize_scenario_library.py [--output-dir cases]

Architecture:
- Creates: cases/case_event_scenarios_library/
- Organizes scenarios by event type and strategy
- Maintains scenario_index.json for browser/API access
- Links to SUMO configs in output/scenarios/

Author: AI Assistant
Created: 2025-11-11
Version: 1.0.0
"""

import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import argparse

logger = logging.getLogger(__name__)


class ScenarioLibraryInitializer:
    """Initializes event scenario library case structure."""

    def __init__(self, project_root: Optional[Path] = None, case_dir: Optional[Path] = None):
        """
        Initialize library initializer.

        Args:
            project_root: Project root directory path
            case_dir: Parent directory for cases (defaults to project_root/cases)
        """
        if project_root is None:
            project_root = Path.cwd()

        self.project_root = project_root
        self.case_dir = case_dir or (self.project_root / "cases")
        self.scenarios_root = self.project_root / "output" / "scenarios"
        self.library_case_name = "case_event_scenarios_library"
        self.library_case_path = self.case_dir / self.library_case_name

    def validate_scenarios(self) -> bool:
        """Validate that scenarios have been generated."""
        if not self.scenarios_root.exists():
            logger.error(f"Scenarios root directory not found: {self.scenarios_root}")
            return False

        scenario_dirs = list(self.scenarios_root.glob("*/*/scenario_*"))
        if not scenario_dirs:
            logger.error("No generated scenarios found in output/scenarios/")
            return False

        logger.info(f"Found {len(scenario_dirs)} scenario directories")
        return True

    def create_case_structure(self) -> bool:
        """Create case directory structure."""
        try:
            # Create main case directory
            self.library_case_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (self.library_case_path / "config").mkdir(exist_ok=True)
            (self.library_case_path / "scenarios").mkdir(exist_ok=True)
            (self.library_case_path / "simulations").mkdir(exist_ok=True)
            (self.library_case_path / "analysis").mkdir(exist_ok=True)

            logger.info(f"Created case structure at: {self.library_case_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating case structure: {e}")
            return False

    def copy_scenarios_to_case(self) -> Dict[str, int]:
        """
        Copy scenario files from output/scenarios to case directory.

        Returns:
            Dictionary with copy statistics
        """
        stats = {
            'scenarios_copied': 0,
            'add_xml_copied': 0,
            'metadata_copied': 0,
            'sumocfg_copied': 0,
            'errors': 0
        }

        try:
            # Iterate through event types
            for event_dir in self.scenarios_root.iterdir():
                if not event_dir.is_dir() or event_dir.name.startswith('_'):
                    continue

                event_type = event_dir.name

                # Create event type subdirectory in case
                event_case_dir = self.library_case_path / "scenarios" / event_type
                event_case_dir.mkdir(parents=True, exist_ok=True)

                # Iterate through strategies
                for strategy_dir in event_dir.iterdir():
                    if not strategy_dir.is_dir():
                        continue

                    strategy = strategy_dir.name

                    # Create strategy subdirectory
                    strategy_case_dir = event_case_dir / strategy
                    strategy_case_dir.mkdir(parents=True, exist_ok=True)

                    # Copy scenario directories
                    for scenario_dir in strategy_dir.iterdir():
                        if not scenario_dir.is_dir() or not scenario_dir.name.startswith('scenario_'):
                            continue

                        try:
                            target_scenario_dir = strategy_case_dir / scenario_dir.name
                            if target_scenario_dir.exists():
                                shutil.rmtree(target_scenario_dir)

                            # Copy entire scenario directory
                            shutil.copytree(scenario_dir, target_scenario_dir)
                            stats['scenarios_copied'] += 1

                            # Count files
                            add_xml_files = list(target_scenario_dir.glob("*.add.xml"))
                            stats['add_xml_copied'] += len(add_xml_files)

                            json_files = list(target_scenario_dir.glob("*.json"))
                            stats['metadata_copied'] += len(json_files)

                            sumocfg_files = list(target_scenario_dir.glob("*.sumocfg"))
                            stats['sumocfg_copied'] += len(sumocfg_files)

                        except Exception as e:
                            logger.warning(f"Error copying scenario {scenario_dir.name}: {e}")
                            stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error copying scenarios to case: {e}")
            stats['errors'] += 1

        return stats

    def create_case_metadata(self) -> bool:
        """Create case metadata.json file."""
        try:
            metadata = {
                "case_id": self.library_case_name,
                "case_name": "Event Scenarios Library",
                "description": "Unified case for event scenario management and batch simulation",
                "created_at": datetime.now().isoformat(),
                "case_type": "event_scenarios_library",
                "version": "1.0.0",
                "files": {
                    "network_file": "templates/network_files/sichuan202508v7.net.xml",
                    "routes_file": None,
                    "taz_file": None,
                    "od_file": None
                },
                "time_range": {
                    "start": None,
                    "end": None,
                    "note": "Individual scenarios define their own time ranges"
                },
                "templates": {
                    "vehicle_types": "templates/config_templates/vehicle_templates/vehicle_types.json",
                    "emission_model": "HBEFA3/PC_G_EU4",
                    "rou_template": None
                },
                "config": {
                    "output_config": {
                        "tripinfo": True,
                        "vehroute": True,
                        "summary": True,
                        "netstate": False,
                        "edgedata": False,
                        "emission": False,
                        "fcd": False
                    },
                    "simulation_options": {
                        "max_depart_delay": 1,
                        "ignore_route_errors": True,
                        "collision_action": "warn"
                    }
                },
                "status": "active",
                "statistics": {
                    "total_scenarios": 0,
                    "note": "Updated after scenarios are copied"
                }
            }

            # Count scenarios
            scenario_count = len(list(
                self.library_case_path.glob("scenarios/**/scenario_*")
            ))
            metadata["statistics"]["total_scenarios"] = scenario_count

            metadata_path = self.library_case_path / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Created case metadata: {metadata_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating case metadata: {e}")
            return False

    def create_scenario_index(self) -> bool:
        """Create scenario index for case."""
        try:
            # Load scenario index from output/scenarios
            main_index_path = self.scenarios_root / "scenario_index.json"
            if not main_index_path.exists():
                logger.warning(f"Main scenario index not found: {main_index_path}")
                return True  # Not critical

            with open(main_index_path, 'r', encoding='utf-8') as f:
                main_index = json.load(f)

            # Create case-specific index with relative paths
            case_index = {
                "timestamp": datetime.now().isoformat(),
                "case_id": self.library_case_name,
                "total_scenarios": main_index["metadata"]["total_scenarios"],
                "scenarios": [],
                "by_event_type": {},
                "by_strategy": {}
            }

            # Adjust paths to be relative to case directory
            for scenario in main_index.get("scenarios", []):
                case_scenario = scenario.copy()

                # Adjust file paths to relative (inside case/scenarios)
                if "scenario_directory" in scenario:
                    scenario_dir = Path(scenario["scenario_directory"])
                    relative_path = scenario_dir.relative_to(self.scenarios_root)
                    case_scenario["scenario_directory"] = f"scenarios/{relative_path}".replace("\\", "/")

                # Add SUMO config path if it exists
                full_scenario_path = self.library_case_path / case_scenario["scenario_directory"]
                sumocfg_path = full_scenario_path / "simulation.sumocfg"
                if sumocfg_path.exists():
                    case_scenario["sumocfg_path"] = f"{case_scenario['scenario_directory']}/simulation.sumocfg"

                case_index["scenarios"].append(case_scenario)

                # Update by_event_type
                event_type = case_scenario.get("event_type", "unknown")
                if event_type not in case_index["by_event_type"]:
                    case_index["by_event_type"][event_type] = 0
                case_index["by_event_type"][event_type] += 1

                # Update by_strategy
                strategy = case_scenario.get("strategy", "unknown")
                if strategy not in case_index["by_strategy"]:
                    case_index["by_strategy"][strategy] = 0
                case_index["by_strategy"][strategy] += 1

            # Save case-specific index
            index_path = self.library_case_path / "scenario_index.json"
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(case_index, f, indent=2, ensure_ascii=False)

            logger.info(f"Created case scenario index: {index_path}")
            logger.info(f"  Scenarios indexed: {len(case_index['scenarios'])}")
            logger.info(f"  By event type: {case_index['by_event_type']}")
            logger.info(f"  By strategy: {case_index['by_strategy']}")

            return True

        except Exception as e:
            logger.error(f"Error creating scenario index: {e}")
            return False

    def initialize_library(self) -> Dict[str, Any]:
        """
        Initialize scenario library case.

        Returns:
            Initialization result summary
        """
        result = {
            'success': False,
            'library_case_path': str(self.library_case_path),
            'steps': {
                'validate_scenarios': False,
                'create_case_structure': False,
                'copy_scenarios': False,
                'create_metadata': False,
                'create_index': False
            },
            'statistics': {},
            'error': None
        }

        try:
            # Step 1: Validate scenarios exist
            if not self.validate_scenarios():
                result['error'] = "Scenario validation failed"
                return result
            result['steps']['validate_scenarios'] = True

            # Step 2: Create case structure
            if not self.create_case_structure():
                result['error'] = "Case structure creation failed"
                return result
            result['steps']['create_case_structure'] = True

            # Step 3: Copy scenarios
            copy_stats = self.copy_scenarios_to_case()
            result['statistics']['copy_stats'] = copy_stats
            if copy_stats['errors'] == 0:
                result['steps']['copy_scenarios'] = True
            else:
                logger.warning(f"Copy completed with {copy_stats['errors']} errors")

            # Step 4: Create metadata
            if self.create_case_metadata():
                result['steps']['create_metadata'] = True

            # Step 5: Create index
            if self.create_scenario_index():
                result['steps']['create_index'] = True

            result['success'] = all(result['steps'].values())
            return result

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error during initialization: {e}", exc_info=True)
            return result


def initialize_library(
    project_root: Optional[Path] = None,
    case_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Initialize scenario library.

    Args:
        project_root: Project root directory
        case_dir: Cases directory (defaults to project_root/cases)

    Returns:
        Initialization result
    """
    initializer = ScenarioLibraryInitializer(project_root, case_dir)
    return initializer.initialize_library()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize event scenarios library case"
    )
    parser.add_argument(
        '--output-dir',
        default='cases',
        help='Directory for cases (default: cases)'
    )
    parser.add_argument(
        '--project-root',
        help='Project root directory (auto-detected if not specified)'
    )

    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else None
    case_dir = Path(args.output_dir)

    logger.info("=" * 60)
    logger.info("Scenario Library Initialization")
    logger.info("=" * 60)

    result = initialize_library(project_root, case_dir)

    logger.info("\n" + "=" * 60)
    logger.info("Initialization Summary")
    logger.info("=" * 60)

    if result['success']:
        logger.info(f"✓ Library case created: {result['library_case_path']}")
        logger.info(f"  Scenarios copied: {result['statistics'].get('copy_stats', {}).get('scenarios_copied', 0)}")
        logger.info(f"  .add.xml files: {result['statistics'].get('copy_stats', {}).get('add_xml_copied', 0)}")
        logger.info(f"  Metadata files: {result['statistics'].get('copy_stats', {}).get('metadata_copied', 0)}")
        logger.info(f"  SUMO configs: {result['statistics'].get('copy_stats', {}).get('sumocfg_copied', 0)}")
        sys.exit(0)
    else:
        logger.error(f"✗ Initialization failed: {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
