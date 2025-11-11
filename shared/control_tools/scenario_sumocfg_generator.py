"""
Event Scenario SUMO Configuration Generator (Phase 5)

⚠️ DEPRECATED FOR SCENARIO LIBRARY: This module should NOT be used to generate
   .sumocfg files in the scenario library (output/scenarios/). According to
   ARCHITECTURE_CHANGES.md, scenario library is read-only and contains only
   scenario definitions.

CORRECT USAGE (Cases Workflow):
   This module should be refactored to generate .sumocfg files when creating
   case simulations in the cases branch:

   Location: cases/{case_id}/simulations/scenario_{event_id}_{variant}/simulation.sumocfg

   Naming Convention (Flat Structure):
   - scenario_{id}_baseline/     - No event, no control (baseline)
   - scenario_{id}_with_event/   - Event only, no control
   - scenario_{id}_vss/          - Event + VSS control
   - scenario_{id}_dhs/          - Event + DHS control
   - scenario_{id}_tec/          - Event + TEC control

   Requirements:
   - Use relative paths only (no absolute paths)
   - Copy .add.xml files to simulation directory
   - Follow existing cases structure (no results/ subdirectory)
   - E1 detector outputs in e1/ subdirectory
   - Add scenario_group field to simulation_metadata.json

Purpose:
- Creates SUMO configuration files for simulation execution
- Integrates scenario definitions with case-specific inputs
- Configures output files (summary, tripinfo, vehroute, e1)

Design Principles (CORRECTED):
1. Scenario library (output/scenarios/) is read-only (NO .sumocfg)
2. SUMO configs generated in cases/{case_id}/simulations/scenario_{id}_{variant}/
3. Flat structure maintains compatibility with existing simulation listing
4. Relative paths for network, routes, and additional files
5. Files directly in scenario_{id}_{variant}/ (no results/ subdirectory)
6. E1 detector outputs in scenario_{id}_{variant}/e1/ subdirectory
7. simulation_metadata.json includes scenario_group field for grouping

TODO: Refactor this module for cases workflow

Author: AI Assistant
Created: 2025-11-11 (Updated: 2025-11-11)
Version: 1.0.0 (DEPRECATED for scenario library)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ScenarioSUMOConfigGenerator:
    """Generates SUMO configuration files for event scenarios."""

    # Standard network file location
    NETWORK_FILE = "templates/network_files/sichuan202508v7.net.xml"

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize SUMO config generator for scenarios.

        Args:
            project_root: Project root directory path
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root
        self.network_file = self.project_root / self.NETWORK_FILE
        self.scenarios_root = self.project_root / "output" / "scenarios"

    def generate_sumocfg_content(
        self,
        scenario_dir: Path,
        additional_file: Path,
        duration_seconds: int,
        output_dir: Path
    ) -> str:
        """
        Generate SUMO configuration XML content.

        Args:
            scenario_dir: Path to scenario directory
            additional_file: Path to .add.xml file (scenario definition)
            duration_seconds: Simulation duration in seconds
            output_dir: Output directory for simulation results

        Returns:
            SUMO configuration XML as string
        """
        # Use absolute paths for network file and additional file
        # SUMO requires forward slashes on Windows
        net_file_abs = str(self.network_file).replace("\\", "/")
        add_file_abs = str(additional_file).replace("\\", "/")
        output_dir_rel = "results"  # Subdirectory for results (relative to sumocfg)

        sumocfg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="{net_file_abs}"/>
        <additional-files value="{add_file_abs}"/>
    </input>

    <time>
        <begin value="0"/>
        <end value="{duration_seconds}"/>
        <step-length value="1.0"/>
    </time>

    <output>
        <summary-file value="{output_dir_rel}/summary.xml"/>
        <tripinfo-output value="{output_dir_rel}/tripinfo.xml"/>
        <vehroute-output value="{output_dir_rel}/vehroute.xml"/>
    </output>

    <processing>
        <ignore-route-errors value="true"/>
        <collision.action value="warn"/>
        <max-depart-delay value="1"/>
    </processing>

    <report>
        <verbose value="false"/>
        <no-step-log value="true"/>
    </report>
</configuration>"""
        return sumocfg_content

    def process_scenario(
        self,
        scenario_dir: Path
    ) -> Dict[str, Any]:
        """
        Generate SUMO config for a single scenario.

        Args:
            scenario_dir: Path to scenario directory containing metadata JSON files

        Returns:
            Dictionary with processing results:
            {
                'success': bool,
                'scenario_dir': str,
                'sumocfg_path': str,
                'add_xml_path': str,
                'results_dir': str,
                'error': Optional[str]
            }
        """
        result = {
            'success': False,
            'scenario_dir': str(scenario_dir),
            'sumocfg_path': None,
            'add_xml_path': None,
            'results_dir': None,
            'error': None
        }

        try:
            # Validate scenario directory exists
            if not scenario_dir.exists():
                result['error'] = f"Scenario directory not found: {scenario_dir}"
                logger.error(result['error'])
                return result

            # Load traffic input config to get duration
            traffic_config_path = scenario_dir / "traffic_input_config.json"
            if not traffic_config_path.exists():
                result['error'] = f"Missing traffic_input_config.json in {scenario_dir}"
                logger.error(result['error'])
                return result

            with open(traffic_config_path, 'r', encoding='utf-8') as f:
                traffic_config = json.load(f)

            duration_hours = traffic_config.get('simulation_duration_hours', 2.0)
            duration_seconds = int(duration_hours * 3600)

            # Find .add.xml file
            add_xml_files = list(scenario_dir.glob("scenario_*.add.xml"))
            if not add_xml_files:
                result['error'] = f"No scenario .add.xml files found in {scenario_dir}"
                logger.error(result['error'])
                return result

            add_xml_path = add_xml_files[0]

            # Create results directory
            results_dir = scenario_dir / "results"
            results_dir.mkdir(parents=True, exist_ok=True)

            # Generate SUMO config
            sumocfg_content = self.generate_sumocfg_content(
                scenario_dir=scenario_dir,
                additional_file=add_xml_path,
                duration_seconds=duration_seconds,
                output_dir=results_dir
            )

            # Save sumocfg file
            sumocfg_path = scenario_dir / "simulation.sumocfg"
            with open(sumocfg_path, 'w', encoding='utf-8') as f:
                f.write(sumocfg_content)

            result['success'] = True
            result['sumocfg_path'] = str(sumocfg_path)
            result['add_xml_path'] = str(add_xml_path)
            result['results_dir'] = str(results_dir)

            logger.info(
                f"Generated SUMO config for scenario: {scenario_dir.name}"
            )

        except Exception as e:
            result['error'] = f"Error processing scenario: {str(e)}"
            logger.error(result['error'], exc_info=True)

        return result

    def batch_generate(self, event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate SUMO configs for all scenarios or specific event type.

        Directory structure: output/scenarios/{event_type_dir}/scenario_{id}_{strategy}/

        Args:
            event_type: Optional event type filter (e.g., '01_交通事故')
                       If None, processes all event types

        Returns:
            Summary dictionary:
            {
                'total_processed': int,
                'successful': int,
                'failed': int,
                'results': [
                    {scenario results...}
                ]
            }
        """
        summary = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'results': [],
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Determine directories to process
            if event_type:
                event_dirs = [self.scenarios_root / event_type]
            else:
                event_dirs = [d for d in self.scenarios_root.iterdir()
                             if d.is_dir() and not d.name.startswith('_') and d.name != 'scenario_index.json']

            for event_dir in event_dirs:
                if not event_dir.exists():
                    logger.warning(f"Event directory not found: {event_dir}")
                    continue

                # Process scenario subdirectories directly (scenario_{id}_{strategy}/)
                # Structure: output/scenarios/{event_type}/scenario_{id}_{strategy}/
                scenario_dirs = [d for d in event_dir.iterdir()
                               if d.is_dir() and d.name.startswith('scenario_')]

                for scenario_dir in scenario_dirs:
                    result = self.process_scenario(scenario_dir)
                    summary['results'].append(result)
                    summary['total_processed'] += 1

                    if result['success']:
                        summary['successful'] += 1
                    else:
                        summary['failed'] += 1

        except Exception as e:
            logger.error(f"Error during batch generation: {str(e)}", exc_info=True)

        logger.info(
            f"Batch generation complete: "
            f"{summary['successful']}/{summary['total_processed']} successful"
        )

        return summary

    def create_scenario_library_index(self) -> Dict[str, Any]:
        """
        Create/update index of all scenarios with SUMO configs.

        Returns:
            Index dictionary with scenario metadata
        """
        index = {
            'timestamp': datetime.now().isoformat(),
            'scenarios_with_sumo': [],
            'by_event_type': {},
            'by_strategy': {},
            'statistics': {
                'total_with_sumo': 0,
                'by_event_type': {},
                'by_strategy': {}
            }
        }

        try:
            # Walk through scenarios directory
            for event_dir in self.scenarios_root.iterdir():
                if not event_dir.is_dir() or event_dir.name.startswith('_'):
                    continue

                event_type = event_dir.name
                index['by_event_type'][event_type] = []
                index['statistics']['by_event_type'][event_type] = 0

                for strategy_dir in event_dir.iterdir():
                    if not strategy_dir.is_dir():
                        continue

                    strategy = strategy_dir.name
                    if strategy not in index['by_strategy']:
                        index['by_strategy'][strategy] = []
                        index['statistics']['by_strategy'][strategy] = 0

                    # Find scenario directories with sumocfg
                    for scenario_dir in strategy_dir.iterdir():
                        if not scenario_dir.is_dir():
                            continue

                        sumocfg_path = scenario_dir / "simulation.sumocfg"
                        if sumocfg_path.exists():
                            # Load scenario metadata
                            metadata = self._load_scenario_metadata(scenario_dir)
                            if metadata:
                                metadata['sumocfg_path'] = str(sumocfg_path)
                                metadata['results_dir'] = str(scenario_dir / "results")

                                index['scenarios_with_sumo'].append(metadata)
                                index['by_event_type'][event_type].append(metadata)
                                index['by_strategy'][strategy].append(metadata)

                                index['statistics']['total_with_sumo'] += 1
                                index['statistics']['by_event_type'][event_type] += 1
                                index['statistics']['by_strategy'][strategy] += 1

        except Exception as e:
            logger.error(f"Error creating index: {str(e)}", exc_info=True)

        return index

    def _load_scenario_metadata(self, scenario_dir: Path) -> Optional[Dict[str, Any]]:
        """Load scenario metadata from JSON files."""
        try:
            event_desc_path = scenario_dir / "event_description.json"
            control_config_path = scenario_dir / "control_strategy_config.json"

            if not event_desc_path.exists() or not control_config_path.exists():
                return None

            with open(event_desc_path, 'r', encoding='utf-8') as f:
                event_desc = json.load(f)

            with open(control_config_path, 'r', encoding='utf-8') as f:
                control_config = json.load(f)

            return {
                'scenario_id': scenario_dir.name,
                'event_id': event_desc.get('event_id'),
                'event_type': event_desc.get('event_type'),
                'strategy': control_config.get('strategy_type'),
                'event_location': event_desc.get('location', {}).get('edge_id'),
                'event_start_time': event_desc.get('time', {}).get('start_time'),
                'event_end_time': event_desc.get('time', {}).get('end_time'),
                'scenario_directory': str(scenario_dir)
            }

        except Exception as e:
            logger.error(f"Error loading metadata from {scenario_dir}: {str(e)}")
            return None


def generate_all_scenario_configs(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate SUMO configs for all event scenarios.

    Args:
        project_root: Project root directory (auto-detected if None)

    Returns:
        Summary of generation results
    """
    generator = ScenarioSUMOConfigGenerator(project_root)

    # Batch generate configs
    logger.info("Starting batch SUMO config generation for all scenarios...")
    summary = generator.batch_generate()

    # Create/update index
    logger.info("Creating scenario library index...")
    index = generator.create_scenario_library_index()

    # Save index
    index_path = generator.scenarios_root / "scenarios_with_sumo_index.json"
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved index to: {index_path}")
    except Exception as e:
        logger.error(f"Error saving index: {str(e)}")

    return {
        'generation_summary': summary,
        'library_index': index
    }


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    result = generate_all_scenario_configs()
    print(f"\nGeneration Complete:")
    print(f"  Total processed: {result['generation_summary']['total_processed']}")
    print(f"  Successful: {result['generation_summary']['successful']}")
    print(f"  Failed: {result['generation_summary']['failed']}")
