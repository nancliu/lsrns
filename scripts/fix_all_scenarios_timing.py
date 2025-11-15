"""
Fix VSS and TEC timing parameters in all existing scenarios (all event types).

This script corrects the begin/end seconds in speed_steps/flow_intervals
and the activation_time/deactivation_time in the timing section of
control_strategy_config.json files for all event types.

Usage:
    python scripts/fix_all_scenarios_timing.py

Author: AI Assistant
Created: 2025-11-14
Version: 1.0.0
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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


def calculate_vss_tec_timing(event_data: Dict, traffic_config: Dict,
                             response_delay_seconds: int = 300,
                             recovery_period_seconds: int = 600) -> Dict[str, Any]:
    """
    Calculate correct VSS/TEC timing parameters.

    时间计算逻辑（响应式控制）：
    1. 仿真范围 = 事件时间 ± buffer
    2. 管控激活 = 事件开始 + response_delay
    3. 管控撤销 = 事件结束 + recovery_period
    4. begin/end = 相对于仿真开始的秒数
    5. 截断：不超过仿真总时长

    Args:
        event_data: Event description data
        traffic_config: Traffic input config data
        response_delay_seconds: Response delay in seconds (default: 300 = 5min)
        recovery_period_seconds: Recovery period in seconds (default: 600 = 10min)

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
    response_delay = timedelta(seconds=response_delay_seconds)
    recovery_period = timedelta(seconds=recovery_period_seconds)

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


def get_strategy_type_from_path(scenario_dir: Path) -> str:
    """
    Determine strategy type from scenario directory name.

    Args:
        scenario_dir: Scenario directory path

    Returns:
        Strategy type string (VSS, TEC, DHS, NO_CONTROL, or empty string)
    """
    dir_name = scenario_dir.name.lower()

    if '_vss' in dir_name:
        return 'VSS'
    elif '_tec' in dir_name:
        return 'TEC'
    elif '_dhs' in dir_name:
        return 'DHS'
    elif '_no_control' in dir_name:
        return 'NO_CONTROL'
    else:
        return ''


def fix_vss_scenario(scenario_dir: Path) -> Tuple[bool, str]:
    """
    Fix VSS scenario timing parameters.

    Args:
        scenario_dir: Scenario directory path

    Returns:
        Tuple of (success, message)
    """
    logger.info(f"Fixing VSS scenario: {scenario_dir}")

    # Read required files
    event_desc_path = scenario_dir / 'event_description.json'
    traffic_config_path = scenario_dir / 'traffic_input_config.json'
    control_config_path = scenario_dir / 'control_strategy_config.json'

    if not all([event_desc_path.exists(), traffic_config_path.exists(), control_config_path.exists()]):
        return False, f"Missing required files"

    event_data = read_json_file(event_desc_path)
    traffic_config = read_json_file(traffic_config_path)
    control_config = read_json_file(control_config_path)

    if not all([event_data, traffic_config, control_config]):
        return False, "Failed to read required files"

    # Get response_delay and recovery_period from config
    response_delay_seconds = control_config.get('parameters', {}).get('response_delay_seconds', 300)
    recovery_period_seconds = control_config.get('parameters', {}).get('recovery_period_seconds', 600)

    # Calculate correct timing
    timing_params = calculate_vss_tec_timing(
        event_data, traffic_config,
        response_delay_seconds, recovery_period_seconds
    )

    # Track changes
    changes = []

    # Update speed_steps begin/end
    if 'parameters' in control_config and 'speed_steps' in control_config['parameters']:
        for step in control_config['parameters']['speed_steps']:
            old_begin = step.get('begin', 'N/A')
            old_end = step.get('end', 'N/A')
            step['begin'] = timing_params['begin']
            step['end'] = timing_params['end']
            if old_begin != timing_params['begin'] or old_end != timing_params['end']:
                changes.append(f"speed_steps: {old_begin}→{timing_params['begin']}, {old_end}→{timing_params['end']}")

    # Update timing section
    if 'timing' in control_config:
        old_activation = control_config['timing'].get('activation_time', 'N/A')
        old_deactivation = control_config['timing'].get('deactivation_time', 'N/A')
        control_config['timing']['activation_time'] = timing_params['activation_time']
        control_config['timing']['deactivation_time'] = timing_params['deactivation_time']
        if old_activation != timing_params['activation_time'] or old_deactivation != timing_params['deactivation_time']:
            changes.append(f"timing: {old_activation}→{timing_params['activation_time']}, {old_deactivation}→{timing_params['deactivation_time']}")

    # Write updated config
    if write_json_file(control_config_path, control_config):
        if changes:
            return True, f"Updated: {'; '.join(changes)}"
        else:
            return True, "Already correct"
    else:
        return False, "Failed to write config"


def fix_tec_scenario(scenario_dir: Path) -> Tuple[bool, str]:
    """
    Fix TEC scenario timing parameters.

    Args:
        scenario_dir: Scenario directory path

    Returns:
        Tuple of (success, message)
    """
    logger.info(f"Fixing TEC scenario: {scenario_dir}")

    # Read required files
    event_desc_path = scenario_dir / 'event_description.json'
    traffic_config_path = scenario_dir / 'traffic_input_config.json'
    control_config_path = scenario_dir / 'control_strategy_config.json'

    if not all([event_desc_path.exists(), traffic_config_path.exists(), control_config_path.exists()]):
        return False, "Missing required files"

    event_data = read_json_file(event_desc_path)
    traffic_config = read_json_file(traffic_config_path)
    control_config = read_json_file(control_config_path)

    if not all([event_data, traffic_config, control_config]):
        return False, "Failed to read required files"

    # Get response_delay and recovery_period from config
    response_delay_seconds = control_config.get('parameters', {}).get('response_delay_seconds', 300)
    recovery_period_seconds = control_config.get('parameters', {}).get('recovery_period_seconds', 600)

    # Calculate correct timing
    timing_params = calculate_vss_tec_timing(
        event_data, traffic_config,
        response_delay_seconds, recovery_period_seconds
    )

    # Track changes
    changes = []

    # Update flow_intervals begin/end
    if 'parameters' in control_config and 'flow_intervals' in control_config['parameters']:
        for interval in control_config['parameters']['flow_intervals']:
            old_begin = interval.get('begin', 'N/A')
            old_end = interval.get('end', 'N/A')
            interval['begin'] = timing_params['begin']
            interval['end'] = timing_params['end']
            if old_begin != timing_params['begin'] or old_end != timing_params['end']:
                changes.append(f"flow_intervals: {old_begin}→{timing_params['begin']}, {old_end}→{timing_params['end']}")

    # Update timing section
    if 'timing' in control_config:
        old_activation = control_config['timing'].get('activation_time', 'N/A')
        old_deactivation = control_config['timing'].get('deactivation_time', 'N/A')
        control_config['timing']['activation_time'] = timing_params['activation_time']
        control_config['timing']['deactivation_time'] = timing_params['deactivation_time']
        if old_activation != timing_params['activation_time'] or old_deactivation != timing_params['deactivation_time']:
            changes.append(f"timing: {old_activation}→{timing_params['activation_time']}, {old_deactivation}→{timing_params['deactivation_time']}")

    # Write updated config
    if write_json_file(control_config_path, control_config):
        if changes:
            return True, f"Updated: {'; '.join(changes)}"
        else:
            return True, "Already correct"
    else:
        return False, "Failed to write config"


def fix_all_scenarios(scenarios_base_dir: Path) -> Dict[str, int]:
    """
    Fix all VSS and TEC scenarios across all event types.

    Args:
        scenarios_base_dir: Base scenarios directory

    Returns:
        Dictionary with fix statistics
    """
    logger.info("=" * 80)
    logger.info("ALL SCENARIOS TIMING FIX (VSS & TEC)")
    logger.info("=" * 80)

    # Find all scenarios
    scenarios = find_all_scenarios(scenarios_base_dir)

    if not scenarios:
        logger.error("No scenarios found")
        return {'total': 0, 'vss_fixed': 0, 'tec_fixed': 0, 'vss_failed': 0, 'tec_failed': 0}

    stats = {
        'total': len(scenarios),
        'vss_fixed': 0,
        'vss_already_correct': 0,
        'vss_failed': 0,
        'tec_fixed': 0,
        'tec_already_correct': 0,
        'tec_failed': 0,
        'skipped': 0
    }

    # Process each scenario
    for scenario_dir in scenarios:
        strategy_type = get_strategy_type_from_path(scenario_dir)

        if strategy_type == 'VSS':
            success, message = fix_vss_scenario(scenario_dir)
            if success:
                if "Already correct" in message:
                    stats['vss_already_correct'] += 1
                    logger.info(f"  ✓ {scenario_dir.name}: {message}")
                else:
                    stats['vss_fixed'] += 1
                    logger.info(f"  ✓ {scenario_dir.name}: {message}")
            else:
                stats['vss_failed'] += 1
                logger.error(f"  ✗ {scenario_dir.name}: {message}")

        elif strategy_type == 'TEC':
            success, message = fix_tec_scenario(scenario_dir)
            if success:
                if "Already correct" in message:
                    stats['tec_already_correct'] += 1
                    logger.info(f"  ✓ {scenario_dir.name}: {message}")
                else:
                    stats['tec_fixed'] += 1
                    logger.info(f"  ✓ {scenario_dir.name}: {message}")
            else:
                stats['tec_failed'] += 1
                logger.error(f"  ✗ {scenario_dir.name}: {message}")

        else:
            # Skip NO_CONTROL, DHS, and unknown scenarios
            stats['skipped'] += 1
            logger.debug(f"Skipping {scenario_dir.name} (type: {strategy_type or 'unknown'})")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("FIX SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total scenarios found: {stats['total']}")
    logger.info(f"VSS scenarios updated: {stats['vss_fixed']}")
    logger.info(f"VSS scenarios already correct: {stats['vss_already_correct']}")
    logger.info(f"VSS scenarios failed: {stats['vss_failed']}")
    logger.info(f"TEC scenarios updated: {stats['tec_fixed']}")
    logger.info(f"TEC scenarios already correct: {stats['tec_already_correct']}")
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

        logger.info("\n✓ All VSS and TEC scenarios processed successfully")
        return 0

    except Exception as e:
        logger.error(f"Fix process failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
