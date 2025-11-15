"""
Fix VSS and TEC timing parameters in existing flow surge scenarios.

This script corrects the begin/end seconds in speed_steps/flow_intervals
and the activation_time/deactivation_time in the timing section of
control_strategy_config.json files.

Usage:
    python scripts/fix_flowsurge_timing.py

Author: AI Assistant
Created: 2025-11-14
Version: 1.0.0
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_flowsurge_scenarios(base_dir: Path) -> List[Path]:
    """
    Find all flow surge scenario directories.

    Args:
        base_dir: Base scenarios directory

    Returns:
        List of scenario directory paths
    """
    flowsurge_dir = base_dir / '07_flowsurge'
    if not flowsurge_dir.exists():
        logger.warning(f"Flow surge directory not found: {flowsurge_dir}")
        return []

    # Find all scenario directories (exclude index files)
    scenarios = [
        d for d in flowsurge_dir.iterdir()
        if d.is_dir() and d.name.startswith('scenario_')
    ]

    logger.info(f"Found {len(scenarios)} flow surge scenarios")
    return scenarios


def read_json_file(file_path: Path) -> Dict[str, Any]:
    """Read and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return {}


def write_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Write data to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to write {file_path}: {e}")
        return False


def calculate_vss_tec_timing(event_data: Dict, traffic_config: Dict) -> Dict[str, Any]:
    """
    Calculate correct VSS/TEC timing parameters.

    Args:
        event_data: Event description data
        traffic_config: Traffic input config data

    Returns:
        Dictionary with timing parameters
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

    # Response delay and recovery period
    response_delay = timedelta(seconds=300)  # 5 min
    recovery_period = timedelta(seconds=600)  # 10 min

    # Calculate control activation and deactivation times
    control_start_time = event_start + response_delay
    control_end_time = event_end + recovery_period

    # Convert to simulation seconds (relative to sim_start)
    begin_seconds = max(0, int((control_start_time - sim_start).total_seconds()))
    end_seconds_raw = int((control_end_time - sim_start).total_seconds())

    # Ensure not exceeding simulation duration
    end_seconds = min(end_seconds_raw, sim_duration_seconds)

    return {
        'begin': begin_seconds,
        'end': end_seconds,
        'activation_time': control_start_time.strftime("%Y-%m-%d %H:%M:%S"),
        'deactivation_time': control_end_time.strftime("%Y-%m-%d %H:%M:%S")
    }


def fix_vss_scenario(scenario_dir: Path) -> bool:
    """
    Fix VSS scenario timing parameters.

    Args:
        scenario_dir: Scenario directory path

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Fixing VSS scenario: {scenario_dir.name}")

    # Read required files
    event_desc_path = scenario_dir / 'event_description.json'
    traffic_config_path = scenario_dir / 'traffic_input_config.json'
    control_config_path = scenario_dir / 'control_strategy_config.json'

    if not all([event_desc_path.exists(), traffic_config_path.exists(), control_config_path.exists()]):
        logger.warning(f"Missing required files in {scenario_dir.name}")
        return False

    event_data = read_json_file(event_desc_path)
    traffic_config = read_json_file(traffic_config_path)
    control_config = read_json_file(control_config_path)

    if not all([event_data, traffic_config, control_config]):
        return False

    # Calculate correct timing
    timing_params = calculate_vss_tec_timing(event_data, traffic_config)

    # Update speed_steps begin/end
    if 'parameters' in control_config and 'speed_steps' in control_config['parameters']:
        for step in control_config['parameters']['speed_steps']:
            old_begin = step.get('begin', 'N/A')
            old_end = step.get('end', 'N/A')
            step['begin'] = timing_params['begin']
            step['end'] = timing_params['end']
            logger.info(f"  Updated speed_steps: begin {old_begin} → {timing_params['begin']}, "
                       f"end {old_end} → {timing_params['end']}")

    # Update timing section
    if 'timing' in control_config:
        old_activation = control_config['timing'].get('activation_time', 'N/A')
        old_deactivation = control_config['timing'].get('deactivation_time', 'N/A')
        control_config['timing']['activation_time'] = timing_params['activation_time']
        control_config['timing']['deactivation_time'] = timing_params['deactivation_time']
        logger.info(f"  Updated timing: activation {old_activation} → {timing_params['activation_time']}, "
                   f"deactivation {old_deactivation} → {timing_params['deactivation_time']}")

    # Write updated config
    success = write_json_file(control_config_path, control_config)
    if success:
        logger.info(f"  ✓ Successfully fixed {scenario_dir.name}")
    return success


def fix_tec_scenario(scenario_dir: Path) -> bool:
    """
    Fix TEC scenario timing parameters.

    Args:
        scenario_dir: Scenario directory path

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Fixing TEC scenario: {scenario_dir.name}")

    # Read required files
    event_desc_path = scenario_dir / 'event_description.json'
    traffic_config_path = scenario_dir / 'traffic_input_config.json'
    control_config_path = scenario_dir / 'control_strategy_config.json'

    if not all([event_desc_path.exists(), traffic_config_path.exists(), control_config_path.exists()]):
        logger.warning(f"Missing required files in {scenario_dir.name}")
        return False

    event_data = read_json_file(event_desc_path)
    traffic_config = read_json_file(traffic_config_path)
    control_config = read_json_file(control_config_path)

    if not all([event_data, traffic_config, control_config]):
        return False

    # Calculate correct timing
    timing_params = calculate_vss_tec_timing(event_data, traffic_config)

    # Update flow_intervals begin/end
    if 'parameters' in control_config and 'flow_intervals' in control_config['parameters']:
        for interval in control_config['parameters']['flow_intervals']:
            old_begin = interval.get('begin', 'N/A')
            old_end = interval.get('end', 'N/A')
            interval['begin'] = timing_params['begin']
            interval['end'] = timing_params['end']
            logger.info(f"  Updated flow_intervals: begin {old_begin} → {timing_params['begin']}, "
                       f"end {old_end} → {timing_params['end']}")

    # Update timing section
    if 'timing' in control_config:
        old_activation = control_config['timing'].get('activation_time', 'N/A')
        old_deactivation = control_config['timing'].get('deactivation_time', 'N/A')
        control_config['timing']['activation_time'] = timing_params['activation_time']
        control_config['timing']['deactivation_time'] = timing_params['deactivation_time']
        logger.info(f"  Updated timing: activation {old_activation} → {timing_params['activation_time']}, "
                   f"deactivation {old_deactivation} → {timing_params['deactivation_time']}")

    # Write updated config
    success = write_json_file(control_config_path, control_config)
    if success:
        logger.info(f"  ✓ Successfully fixed {scenario_dir.name}")
    return success


def fix_all_scenarios(scenarios_base_dir: Path) -> Dict[str, int]:
    """
    Fix all flow surge VSS and TEC scenarios.

    Args:
        scenarios_base_dir: Base scenarios directory

    Returns:
        Dictionary with fix statistics
    """
    logger.info("=" * 80)
    logger.info("FLOW SURGE SCENARIO TIMING FIX")
    logger.info("=" * 80)

    # Find all scenarios
    scenarios = find_flowsurge_scenarios(scenarios_base_dir)

    if not scenarios:
        logger.error("No flow surge scenarios found")
        return {'total': 0, 'vss_fixed': 0, 'tec_fixed': 0, 'vss_failed': 0, 'tec_failed': 0}

    stats = {
        'total': len(scenarios),
        'vss_fixed': 0,
        'tec_fixed': 0,
        'vss_failed': 0,
        'tec_failed': 0,
        'skipped': 0
    }

    # Process each scenario
    for scenario_dir in scenarios:
        # Determine strategy type from directory name
        if '_vss' in scenario_dir.name:
            success = fix_vss_scenario(scenario_dir)
            if success:
                stats['vss_fixed'] += 1
            else:
                stats['vss_failed'] += 1

        elif '_tec' in scenario_dir.name:
            success = fix_tec_scenario(scenario_dir)
            if success:
                stats['tec_fixed'] += 1
            else:
                stats['tec_failed'] += 1

        else:
            # Skip NO_CONTROL and DHS scenarios
            logger.debug(f"Skipping {scenario_dir.name} (not VSS/TEC)")
            stats['skipped'] += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("FIX SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total scenarios found: {stats['total']}")
    logger.info(f"VSS scenarios fixed: {stats['vss_fixed']}")
    logger.info(f"TEC scenarios fixed: {stats['tec_fixed']}")
    logger.info(f"VSS scenarios failed: {stats['vss_failed']}")
    logger.info(f"TEC scenarios failed: {stats['tec_failed']}")
    logger.info(f"Scenarios skipped: {stats['skipped']}")
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
        if stats['vss_failed'] > 0 or stats['tec_failed'] > 0:
            logger.warning("Some scenarios failed to fix. Check logs above.")
            return 1

        logger.info("\n✓ All VSS and TEC scenarios fixed successfully")
        return 0

    except Exception as e:
        logger.error(f"Fix process failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
