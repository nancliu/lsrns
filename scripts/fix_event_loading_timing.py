"""
Fix event loading timing in all existing scenarios.

This script corrects the begin/end seconds in closedLane elements
of .add.xml files across all scenarios (NO_CONTROL, VSS, TEC, DHS).

CRITICAL ISSUE (2025-11-14):
- Event loading times were incorrectly calculated
- Events loaded at t=0 instead of actual event time relative to simulation start
- Affected ALL 477 scenarios across all event types

Usage:
    python scripts/fix_event_loading_timing.py

Author: AI Assistant
Created: 2025-11-14
Version: 1.0.0
"""

import sys
import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_all_scenarios(base_dir: Path) -> List[Path]:
    """
    Find all scenario directories across all event types.

    Args:
        base_dir: Base scenarios directory

    Returns:
        List of scenario directory paths
    """
    scenarios = []

    # Find all event type directories (numeric prefixed)
    event_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name[:2].isdigit()]

    logger.info(f"Found {len(event_dirs)} event type directories")

    for event_dir in event_dirs:
        # Find scenario directories within each event type
        scenario_dirs = [
            d for d in event_dir.iterdir()
            if d.is_dir() and d.name.startswith('scenario_')
        ]
        scenarios.extend(scenario_dirs)

    logger.info(f"Found {len(scenarios)} total scenarios across all event types")
    return scenarios


def read_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Read and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return None


def calculate_event_timing(event_data: Dict, traffic_config: Dict) -> Dict[str, int]:
    """
    Calculate correct event loading timing parameters.

    Time calculation logic:
    1. Simulation range = event time ± buffer (30 min)
    2. Event loading start = event start time (relative to sim start)
    3. Event loading end = event end time (relative to sim start)
    4. begin/end = seconds relative to simulation start

    Args:
        event_data: Event description data
        traffic_config: Traffic input config data

    Returns:
        Dictionary with timing parameters: {'begin': int, 'end': int}
    """
    # Extract event times
    event_start_str = event_data['time']['start_time']
    event_end_str = event_data['time']['end_time']

    # Extract simulation times
    sim_start_str = traffic_config['od_time_range']['start']
    sim_end_str = traffic_config['od_time_range']['end']

    # Parse times
    event_start = datetime.strptime(event_start_str, "%Y-%m-%d %H:%M:%S")
    event_end = datetime.strptime(event_end_str, "%Y-%m-%d %H:%M:%S")
    sim_start = datetime.strptime(sim_start_str, "%Y-%m-%d %H:%M:%S")
    sim_end = datetime.strptime(sim_end_str, "%Y-%m-%d %H:%M:%S")

    # Calculate simulation duration
    sim_duration_seconds = int((sim_end - sim_start).total_seconds())

    # Convert event times to simulation seconds (relative to sim_start)
    begin_seconds = max(0, int((event_start - sim_start).total_seconds()))
    end_seconds_raw = int((event_end - sim_start).total_seconds())

    # Ensure not exceeding simulation duration
    end_seconds = min(end_seconds_raw, sim_duration_seconds)

    return {
        'begin': begin_seconds,
        'end': end_seconds
    }


def update_add_xml_timing(xml_path: Path, begin: int, end: int) -> Tuple[bool, str]:
    """
    Update closedLane timing in .add.xml file.

    Args:
        xml_path: Path to .add.xml file
        begin: Correct begin time in seconds
        end: Correct end time in seconds

    Returns:
        Tuple of (success, message)
    """
    try:
        # Parse XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find all closedLane elements
        closed_lanes = root.findall('.//closedLane')

        if not closed_lanes:
            return True, "No closedLane elements (congestion/flow surge event)"

        changes = []
        for lane in closed_lanes:
            old_begin = lane.get('begin')
            old_end = lane.get('end')

            # Update attributes
            lane.set('begin', str(begin))
            lane.set('end', str(end))

            if old_begin != str(begin) or old_end != str(end):
                changes.append(f"closedLane: begin {old_begin}→{begin}, end {old_end}→{end}")

        if changes:
            # Write updated XML with proper formatting
            # Preserve XML declaration and formatting
            tree.write(xml_path, encoding='UTF-8', xml_declaration=True)

            # Fix formatting (ElementTree doesn't preserve pretty print well)
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ensure proper XML formatting
            if not content.startswith('<?xml version="1.0" encoding="UTF-8"?>'):
                content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content

            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True, f"Updated: {'; '.join(changes)}"
        else:
            return True, "Already correct"

    except ET.ParseError as e:
        return False, f"XML parse error: {e}"
    except Exception as e:
        return False, f"Update failed: {e}"


def fix_scenario_event_timing(scenario_dir: Path) -> Tuple[bool, str]:
    """
    Fix event loading timing for a single scenario.

    Args:
        scenario_dir: Scenario directory path

    Returns:
        Tuple of (success, message)
    """
    logger.debug(f"Fixing scenario: {scenario_dir.name}")

    # Read required files
    event_desc_path = scenario_dir / 'event_description.json'
    traffic_config_path = scenario_dir / 'traffic_input_config.json'

    if not event_desc_path.exists():
        return False, "Missing event_description.json"

    if not traffic_config_path.exists():
        return False, "Missing traffic_input_config.json"

    event_data = read_json_file(event_desc_path)
    traffic_config = read_json_file(traffic_config_path)

    if not event_data or not traffic_config:
        return False, "Failed to read required files"

    # Calculate correct timing
    timing_params = calculate_event_timing(event_data, traffic_config)

    # Find .add.xml file
    add_xml_files = list(scenario_dir.glob("*.add.xml"))

    if not add_xml_files:
        return False, "No .add.xml file found"

    if len(add_xml_files) > 1:
        logger.warning(f"Multiple .add.xml files found in {scenario_dir.name}, using first")

    add_xml_path = add_xml_files[0]

    # Update .add.xml
    success, message = update_add_xml_timing(
        add_xml_path,
        timing_params['begin'],
        timing_params['end']
    )

    return success, message


def fix_all_scenarios(scenarios_base_dir: Path) -> Dict[str, int]:
    """
    Fix all scenarios' event loading timing.

    Args:
        scenarios_base_dir: Base scenarios directory

    Returns:
        Dictionary with fix statistics
    """
    logger.info("=" * 80)
    logger.info("EVENT LOADING TIMING FIX (ALL SCENARIOS)")
    logger.info("=" * 80)

    # Find all scenarios
    scenarios = find_all_scenarios(scenarios_base_dir)

    if not scenarios:
        logger.error("No scenarios found")
        return {'total': 0, 'fixed': 0, 'already_correct': 0, 'failed': 0, 'skipped': 0}

    stats = {
        'total': len(scenarios),
        'fixed': 0,
        'already_correct': 0,
        'failed': 0,
        'skipped': 0
    }

    # Process each scenario
    for scenario_dir in scenarios:
        try:
            success, message = fix_scenario_event_timing(scenario_dir)

            if success:
                if "Already correct" in message:
                    stats['already_correct'] += 1
                    logger.info(f"  ✓ {scenario_dir.name}: {message}")
                elif "No closedLane" in message:
                    stats['skipped'] += 1
                    logger.debug(f"  ⊘ {scenario_dir.name}: {message}")
                else:
                    stats['fixed'] += 1
                    logger.info(f"  ✓ {scenario_dir.name}: {message}")
            else:
                stats['failed'] += 1
                logger.error(f"  ✗ {scenario_dir.name}: {message}")

        except Exception as e:
            stats['failed'] += 1
            logger.error(f"  ✗ {scenario_dir.name}: Unexpected error: {e}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("FIX SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total scenarios found: {stats['total']}")
    logger.info(f"Scenarios updated: {stats['fixed']}")
    logger.info(f"Scenarios already correct: {stats['already_correct']}")
    logger.info(f"Scenarios skipped (no event injection): {stats['skipped']}")
    logger.info(f"Scenarios failed: {stats['failed']}")
    logger.info("=" * 80)

    return stats


def main():
    """Main entry point."""
    scenarios_base_dir = project_root / 'output' / 'scenarios'

    if not scenarios_base_dir.exists():
        logger.error(f"Scenarios directory not found: {scenarios_base_dir}")
        return 1

    try:
        stats = fix_all_scenarios(scenarios_base_dir)

        # Check if any fixes failed
        if stats['failed'] > 0:
            logger.warning("Some scenarios failed to fix. Check logs above.")
            return 1

        logger.info("\n✓ All scenarios processed successfully")
        return 0

    except Exception as e:
        logger.error(f"Fix process failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
