"""
Event Scenario Library API Support (Phase 5)

Provides utilities for quick case creation from event scenarios.

Purpose (Option A Architecture):
- Backend support for quick case creation from event scenarios
- Validates input files (network, OD data, TAZ)
- Creates case metadata with event scenario linkage
- Prepares case structure for simulation

Usage:
    # As API support (from backend)
    from scripts.initialize_scenario_library import QuickCaseCreator
    creator = QuickCaseCreator()
    result = creator.create_case_from_event(...)

    # Or as standalone script (for testing)
    python scripts/initialize_scenario_library.py --event-id 12547 --network network.xml ...

Architecture (Option A):
- Event scenarios: output/scenarios/ (read-only library)
- Cases: cases/ (independent, with full input data)
- Quick create: Frontend → API → This module → Create case
- Event application: Simulation with event scenario injection

Author: AI Assistant
Created: 2025-11-11
Version: 2.0.0 (Redesigned for Option A)
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


class QuickCaseCreator:
    """Creates cases quickly from event scenarios (Option A Architecture)."""

    def __init__(self, project_root: Optional[Path] = None, case_dir: Optional[Path] = None):
        """
        Initialize quick case creator.

        Args:
            project_root: Project root directory path
            case_dir: Parent directory for cases (defaults to project_root/cases)
        """
        if project_root is None:
            project_root = Path.cwd()

        self.project_root = project_root
        self.case_dir = case_dir or (self.project_root / "cases")
        self.scenarios_root = self.project_root / "output" / "scenarios"

    def validate_event_scenario(self, event_type: str, strategy: str, scenario_id: str) -> bool:
        """
        Validate that event scenario exists and is complete.

        Args:
            event_type: Event type (e.g., '01_交通事故')
            strategy: Strategy type (vss, dhs, tec)
            scenario_id: Scenario ID (e.g., 'scenario_12547_vss')

        Returns:
            True if scenario is valid and complete
        """
        scenario_dir = self.scenarios_root / event_type / strategy / scenario_id

        if not scenario_dir.exists():
            logger.error(f"Scenario directory not found: {scenario_dir}")
            return False

        # Check required files
        required_files = [
            "event_description.json",
            "traffic_input_config.json",
            "control_strategy_config.json",
            "simulation.sumocfg"
        ]

        for required_file in required_files:
            if not (scenario_dir / required_file).exists():
                logger.error(f"Missing required file in scenario: {required_file}")
                return False

        logger.info(f"Event scenario validated: {scenario_dir.name}")
        return True

    def validate_case_inputs(self, network_file: str, od_file: str, taz_file: Optional[str] = None) -> bool:
        """
        Validate case input files.

        Args:
            network_file: Path to network XML file
            od_file: Path to OD/routes file
            taz_file: Optional path to TAZ file

        Returns:
            True if all inputs are accessible
        """
        # Check network file
        net_path = Path(network_file)
        if not net_path.exists():
            # Try relative to project root
            net_path = self.project_root / network_file
            if not net_path.exists():
                logger.error(f"Network file not found: {network_file}")
                return False

        # Check OD file
        od_path = Path(od_file)
        if not od_path.exists():
            od_path = self.project_root / od_file
            if not od_path.exists():
                logger.error(f"OD file not found: {od_file}")
                return False

        # Check TAZ file if provided
        if taz_file:
            taz_path = Path(taz_file)
            if not taz_path.exists():
                taz_path = self.project_root / taz_file
                if not taz_path.exists():
                    logger.warning(f"TAZ file not found: {taz_file}")
                    # Don't fail, TAZ is optional

        logger.info("Case input files validated")
        return True

    def create_case_from_event(
        self,
        case_name: str,
        case_id: str,
        event_type: str,
        strategy: str,
        scenario_id: str,
        network_file: str,
        od_file: str,
        taz_file: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a case from an event scenario (Quick Create).

        Args:
            case_name: Display name for case
            case_id: Unique case identifier (e.g., 'case_交通事故_vss_20251111')
            event_type: Event type (e.g., '01_交通事故')
            strategy: Strategy (vss, dhs, tec)
            scenario_id: Scenario ID (e.g., 'scenario_12547_vss')
            network_file: Path to network XML
            od_file: Path to OD/routes file
            taz_file: Optional path to TAZ file
            description: Case description

        Returns:
            Result dictionary:
            {
                'success': bool,
                'case_path': str,
                'case_id': str,
                'event_scenario': {event info},
                'error': Optional[str]
            }
        """
        result = {
            'success': False,
            'case_path': None,
            'case_id': case_id,
            'event_scenario': None,
            'error': None
        }

        try:
            # Step 1: Validate event scenario
            if not self.validate_event_scenario(event_type, strategy, scenario_id):
                result['error'] = f"Event scenario validation failed: {scenario_id}"
                return result

            # Step 2: Validate case inputs
            if not self.validate_case_inputs(network_file, od_file, taz_file):
                result['error'] = "Case input files validation failed"
                return result

            # Step 3: Create case directory
            case_path = self.case_dir / case_id
            if case_path.exists():
                logger.warning(f"Case already exists, will override: {case_path}")
                shutil.rmtree(case_path)

            case_path.mkdir(parents=True, exist_ok=True)
            (case_path / "config").mkdir(exist_ok=True)
            (case_path / "simulations").mkdir(exist_ok=True)
            (case_path / "analysis").mkdir(exist_ok=True)

            # Step 4: Copy input files to case config
            self._copy_case_inputs(case_path, network_file, od_file, taz_file)

            # Step 5: Create case metadata with event scenario linkage
            scenario_path = self.scenarios_root / event_type / strategy / scenario_id
            self._create_case_metadata(
                case_path, case_name, case_id, description,
                network_file, od_file, taz_file,
                event_type, strategy, scenario_id, scenario_path
            )

            result['success'] = True
            result['case_path'] = str(case_path)

            # Load event scenario metadata
            result['event_scenario'] = self._load_event_scenario_info(scenario_path)

            logger.info(f"✓ Created case from event: {case_id}")

        except Exception as e:
            result['error'] = f"Error creating case: {str(e)}"
            logger.error(result['error'], exc_info=True)

        return result

    def _copy_case_inputs(
        self,
        case_path: Path,
        network_file: str,
        od_file: str,
        taz_file: Optional[str] = None
    ) -> None:
        """Copy case input files to case config directory."""
        config_dir = case_path / "config"

        # Copy network file
        net_src = Path(network_file)
        if not net_src.exists():
            net_src = self.project_root / network_file
        if net_src.exists():
            shutil.copy2(net_src, config_dir / net_src.name)
            logger.info(f"Copied network file: {net_src.name}")

        # Copy OD file
        od_src = Path(od_file)
        if not od_src.exists():
            od_src = self.project_root / od_file
        if od_src.exists():
            shutil.copy2(od_src, config_dir / od_src.name)
            logger.info(f"Copied OD file: {od_src.name}")

        # Copy TAZ file if provided
        if taz_file:
            taz_src = Path(taz_file)
            if not taz_src.exists():
                taz_src = self.project_root / taz_file
            if taz_src.exists():
                shutil.copy2(taz_src, config_dir / taz_src.name)
                logger.info(f"Copied TAZ file: {taz_src.name}")

    def _create_case_metadata(
        self,
        case_path: Path,
        case_name: str,
        case_id: str,
        description: str,
        network_file: str,
        od_file: str,
        taz_file: Optional[str],
        event_type: str,
        strategy: str,
        scenario_id: str,
        scenario_path: Path
    ) -> None:
        """Create case metadata.json with event scenario linkage."""
        # Get file names
        network_fname = Path(network_file).name
        od_fname = Path(od_file).name
        taz_fname = Path(taz_file).name if taz_file else None

        # Load event scenario info
        event_desc_path = scenario_path / "event_description.json"
        event_desc = {}
        if event_desc_path.exists():
            with open(event_desc_path, 'r', encoding='utf-8') as f:
                event_desc = json.load(f)

        metadata = {
            "case_id": case_id,
            "case_name": case_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "case_type": "event_scenario_case",
            "version": "1.0.0",
            "files": {
                "network_file": f"config/{network_fname}",
                "routes_file": f"config/{od_fname}",
                "taz_file": f"config/{taz_fname}" if taz_fname else None,
                "od_file": None
            },
            "time_range": {
                "start": event_desc.get("time", {}).get("start_time"),
                "end": event_desc.get("time", {}).get("end_time"),
                "note": "From linked event scenario"
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
            "event_scenario": {
                "event_type": event_type,
                "strategy": strategy,
                "scenario_id": scenario_id,
                "scenario_path": str(scenario_path),
                "event_id": event_desc.get("event_id"),
                "event_location": event_desc.get("location", {}).get("edge_id")
            },
            "status": "active"
        }

        metadata_path = case_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Created case metadata: {metadata_path}")

    def _load_event_scenario_info(self, scenario_path: Path) -> Dict[str, Any]:
        """Load event scenario information."""
        try:
            event_desc_path = scenario_path / "event_description.json"
            control_config_path = scenario_path / "control_strategy_config.json"

            event_desc = {}
            control_config = {}

            if event_desc_path.exists():
                with open(event_desc_path, 'r', encoding='utf-8') as f:
                    event_desc = json.load(f)

            if control_config_path.exists():
                with open(control_config_path, 'r', encoding='utf-8') as f:
                    control_config = json.load(f)

            return {
                'event_type': event_desc.get("event_type"),
                'event_id': event_desc.get("event_id"),
                'location': event_desc.get("location"),
                'time': event_desc.get("time"),
                'strategy': control_config.get("strategy_type")
            }

        except Exception as e:
            logger.warning(f"Error loading event scenario info: {e}")
            return {}

    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """
        Get list of all available event scenarios.

        Returns:
            List of scenario dicts with event type, strategy, scenario_id
        """
        scenarios = []

        try:
            if not self.scenarios_root.exists():
                return scenarios

            # Load scenario index
            index_path = self.scenarios_root / "scenario_index.json"
            if index_path.exists():
                with open(index_path, 'r', encoding='utf-8') as f:
                    index = json.load(f)

                for scenario in index.get("scenarios", []):
                    scenarios.append({
                        'event_type': scenario.get('event_type'),
                        'strategy': scenario.get('strategy'),
                        'event_id': scenario.get('event_id'),
                        'scenario_id': scenario.get('scenario_id')
                    })

        except Exception as e:
            logger.warning(f"Error loading scenario index: {e}")

        return scenarios


def quick_create_case_from_event(
    case_name: str,
    case_id: str,
    event_type: str,
    strategy: str,
    scenario_id: str,
    network_file: str,
    od_file: str,
    taz_file: Optional[str] = None,
    description: str = "",
    project_root: Optional[Path] = None,
    case_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Utility function: Create case from event scenario.

    Args:
        case_name: Display name for case
        case_id: Unique case identifier
        event_type: Event type
        strategy: Control strategy
        scenario_id: Scenario ID
        network_file: Network file path
        od_file: OD/routes file path
        taz_file: Optional TAZ file path
        description: Case description
        project_root: Project root directory
        case_dir: Cases directory

    Returns:
        Result dictionary
    """
    creator = QuickCaseCreator(project_root, case_dir)
    return creator.create_case_from_event(
        case_name=case_name,
        case_id=case_id,
        event_type=event_type,
        strategy=strategy,
        scenario_id=scenario_id,
        network_file=network_file,
        od_file=od_file,
        taz_file=taz_file,
        description=description
    )


# Old methods below are deprecated, kept for reference only
# =========================================================

class _DeprecatedScenarioLibraryInitializer:
    """Deprecated: Use QuickCaseCreator instead."""

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




def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Event Scenario Library Support - Quick Case Creation"
    )
    parser.add_argument(
        '--mode',
        choices=['create-case', 'list-scenarios'],
        default='list-scenarios',
        help='Operation mode'
    )
    parser.add_argument(
        '--case-id',
        help='Case ID for creation (required for create-case mode)'
    )
    parser.add_argument(
        '--case-name',
        help='Display name for case (required for create-case mode)'
    )
    parser.add_argument(
        '--event-type',
        help='Event type (required for create-case mode)'
    )
    parser.add_argument(
        '--strategy',
        help='Control strategy (required for create-case mode)'
    )
    parser.add_argument(
        '--scenario-id',
        help='Scenario ID (required for create-case mode)'
    )
    parser.add_argument(
        '--network-file',
        help='Network file path (required for create-case mode)'
    )
    parser.add_argument(
        '--od-file',
        help='OD/Routes file path (required for create-case mode)'
    )
    parser.add_argument(
        '--taz-file',
        help='TAZ file path (optional)'
    )
    parser.add_argument(
        '--description',
        default='',
        help='Case description (optional)'
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
    logger.info("Event Scenario Library Support (Option A Architecture)")
    logger.info("=" * 60)

    if args.mode == 'list-scenarios':
        # List available scenarios
        creator = QuickCaseCreator(project_root, case_dir)
        scenarios = creator.get_available_scenarios()

        logger.info(f"Available event scenarios: {len(scenarios)}")
        for scenario in scenarios:
            logger.info(f"  - {scenario['event_type']} / {scenario['strategy']} "
                       f"(Event ID: {scenario['event_id']}, Scenario: {scenario['scenario_id']})")
        sys.exit(0)

    elif args.mode == 'create-case':
        # Create case from event
        required_args = [
            'case_id', 'case_name', 'event_type', 'strategy',
            'scenario_id', 'network_file', 'od_file'
        ]
        missing = [arg for arg in required_args if not getattr(args, arg)]

        if missing:
            logger.error(f"Missing required arguments: {', '.join(missing)}")
            sys.exit(1)

        logger.info(f"Creating case from event scenario...")
        logger.info(f"  Case ID: {args.case_id}")
        logger.info(f"  Case Name: {args.case_name}")
        logger.info(f"  Event: {args.event_type} / {args.strategy}")

        result = quick_create_case_from_event(
            case_name=args.case_name,
            case_id=args.case_id,
            event_type=args.event_type,
            strategy=args.strategy,
            scenario_id=args.scenario_id,
            network_file=args.network_file,
            od_file=args.od_file,
            taz_file=args.taz_file,
            description=args.description,
            project_root=project_root,
            case_dir=case_dir
        )

        logger.info("\n" + "=" * 60)
        logger.info("Case Creation Summary")
        logger.info("=" * 60)

        if result['success']:
            logger.info(f"✓ Case created successfully")
            logger.info(f"  Case Path: {result['case_path']}")
            logger.info(f"  Case ID: {result['case_id']}")
            logger.info(f"  Event Scenario: {result['event_scenario'].get('event_type')} / "
                       f"{result['event_scenario'].get('strategy')}")
            sys.exit(0)
        else:
            logger.error(f"✗ Case creation failed: {result['error']}")
            sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
