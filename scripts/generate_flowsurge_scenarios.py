"""
Flow Surge Scenario Generation Script

Generates flow surge workload scenarios from flow_high_events.csv.
Flow surge events represent high traffic volume periods (not disruption events).

Key Features:
- Filters events with duration >= 30 minutes
- Adds DHS control strategy for morning peak (7:30-9:30)
- No baseline comparison (only control strategy comparison)
- Event type: "流量激增工况" (Flow Surge Workload)
- Uses CongestionInjector (no XML injection)
- Affects entire edge (no lane-level precision)

Usage:
    python scripts/generate_flowsurge_scenarios.py

Output:
    - output/scenarios/07_flowsurge/{strategy}/scenario_*.add.xml
    - Enhanced CSV with control strategy information

Author: AI Assistant
Created: 2025-11-14
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.control_tools.scenario_generator import ScenarioGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# G4202南段DHS路段定义 (K20-K40)
G4202_SOUTH_DHS_EDGES = [
    "-12680", "-10376.203", "-10376", "-6906",
    "-1438", "-3324", "-4360", "-10188"
]

# DHS管控时间段定义
DHS_MORNING_CONTROL_START = "07:30:00"
DHS_MORNING_CONTROL_END = "09:30:00"


def load_and_filter_flowsurge_events(csv_path: str, min_duration_minutes: int = 30) -> pd.DataFrame:
    """
    Load and filter flow surge events.

    Args:
        csv_path: Path to flow_high_events.csv
        min_duration_minutes: Minimum event duration in minutes (default: 30)

    Returns:
        Filtered DataFrame with events >= min_duration_minutes
    """
    logger.info(f"Loading flow surge events from: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8')
    logger.info(f"Loaded {len(df)} raw flow surge events")

    # Calculate duration in minutes
    df['开始时间_dt'] = pd.to_datetime(df['开始时间'])
    df['结束时间_dt'] = pd.to_datetime(df['结束时间'])
    df['duration_minutes'] = (df['结束时间_dt'] - df['开始时间_dt']).dt.total_seconds() / 60

    # Filter by duration
    df_filtered = df[df['duration_minutes'] >= min_duration_minutes].copy()
    logger.info(f"Filtered to {len(df_filtered)} events with duration >= {min_duration_minutes} minutes")

    if len(df_filtered) == 0:
        logger.warning(f"No events found with duration >= {min_duration_minutes} minutes")

    return df_filtered


def enhance_with_control_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enhance events with control strategy information.

    For events overlapping with morning peak DHS control period (7:30-9:30),
    add DHS control strategy info.

    Args:
        df: DataFrame with flow surge events

    Returns:
        Enhanced DataFrame with control strategy columns
    """
    df_enhanced = df.copy()

    # Check if event time range overlaps with morning peak DHS control period
    # Morning peak DHS: 7:30-9:30 daily
    def check_morning_peak_overlap(row):
        """
        Check if event overlaps with morning peak DHS control period.

        Logic: Event overlaps if:
        - Event start time <= DHS end time (9:30) AND
        - Event end time >= DHS start time (7:30)
        """
        event_start_time = row['开始时间_dt'].time()
        event_end_time = row['结束时间_dt'].time()

        dhs_start = pd.to_datetime(DHS_MORNING_CONTROL_START).time()
        dhs_end = pd.to_datetime(DHS_MORNING_CONTROL_END).time()

        # Check time overlap (assuming same day)
        return (event_start_time <= dhs_end) and (event_end_time >= dhs_start)

    df_enhanced['is_morning_peak'] = df_enhanced.apply(check_morning_peak_overlap, axis=1)

    # Add control strategy columns
    df_enhanced['管控措施'] = df_enhanced.apply(
        lambda row: 'DHS（动态硬路肩开放）' if row['is_morning_peak'] else '',
        axis=1
    )

    # Add control time range for morning peak events
    df_enhanced['管控开始时间'] = df_enhanced.apply(
        lambda row: row['开始时间_dt'].replace(
            hour=7, minute=30, second=0
        ).strftime('%Y-%m-%d %H:%M:%S') if row['is_morning_peak'] else '',
        axis=1
    )

    df_enhanced['管控结束时间'] = df_enhanced.apply(
        lambda row: row['开始时间_dt'].replace(
            hour=9, minute=30, second=0
        ).strftime('%Y-%m-%d %H:%M:%S') if row['is_morning_peak'] else '',
        axis=1
    )

    # Add control scope (G4202南段 for morning peak)
    df_enhanced['管控范围'] = df_enhanced.apply(
        lambda row: 'G4202南段K20-K40（硬路肩开放）' if row['is_morning_peak'] else '',
        axis=1
    )

    logger.info(f"Enhanced {df_enhanced['is_morning_peak'].sum()} events with DHS control strategy")

    return df_enhanced


def convert_event_to_dict(row: pd.Series) -> Dict[str, Any]:
    """
    Convert DataFrame row to event data dictionary.

    Args:
        row: DataFrame row with event data

    Returns:
        Event data dictionary for scenario generation
    """
    event_data = {
        'report_id': str(row['report_id']),
        'event_type': '流量激增工况',  # Flow Surge Workload
        'event_description': f"流量激增事件，发生于{row['发生地点']}，持续{row['duration_minutes']:.0f}分钟",
        'road': row['所在高速公路'],
        'direction': row['上下行'],
        'mileage': '',  # Flow surge doesn't have specific mileage
        'junction_id': str(row['junction_id']) if pd.notna(row['junction_id']) else '',
        'edge_id': str(row['edge_id']),
        'start_time': row['开始时间'],
        'end_time': row['结束时间'],
        'affected_lanes': [],  # Flow surge affects entire edge, not specific lanes
    }

    return event_data


def determine_control_strategies(row: pd.Series) -> List[str]:
    """
    Determine applicable control strategies for a flow surge event.

    Flow surge events support:
    - VSS: Speed control to smooth traffic flow
    - DHS: Open hard shoulder (if during morning peak and on suitable segment)
    - TEC: Toll station flow control

    Args:
        row: Event data row

    Returns:
        List of control strategy types (e.g., ['VSS', 'DHS', 'TEC'])
    """
    strategies = ['VSS', 'TEC']  # Always applicable

    # Add DHS if event is during morning peak
    if row['is_morning_peak']:
        strategies.append('DHS')
        logger.debug(f"Event {row['report_id']} eligible for DHS (morning peak)")

    return strategies


# VSS and TEC parameter generation removed - time calculation now handled by scenario_generator
# See CRITICAL_ISSUES_AND_REFACTORING_PLAN.md Phase 2 for details


def generate_control_params_dhs(event_row: pd.Series) -> Dict[str, Any]:
    """
    Generate DHS control parameters for flow surge event.

    Strategy: Open hard shoulder during morning peak to increase capacity.

    DHS固定管控时段：每日7:30-9:30

    时间计算逻辑：
    1. 仿真开始时间 = 事件开始 - 30分钟buffer
    2. 仿真结束时间 = 事件结束 + 30分钟buffer
    3. DHS管控开始 = 7:30（固定）
    4. DHS管控结束 = 9:30（固定）
    5. 转换为仿真秒数：相对于仿真开始时间
    6. 截断：不超过仿真总时长

    示例（事件6120705）：
    - 事件时间: 07:05-07:35
    - 仿真时间: 06:35-08:05（90分钟=5400秒）
    - DHS管控: 07:30-09:30
    - begin: (07:30-06:35) = 55分钟 = 3300秒
    - end: min((09:30-06:35), 仿真时长) = min(175分钟, 90分钟) = 5400秒

    Args:
        event_row: Event data row

    Returns:
        DHS control parameters with correct begin/end times and affected_lanes
    """
    from datetime import datetime, timedelta

    # Use G4202 south segment edges for morning peak DHS
    affected_edges = G4202_SOUTH_DHS_EDGES
    lane_index = 0  # Emergency lane (_0)

    # Generate affected_lanes list: edge_id + "_" + lane_index
    affected_lanes = [f"{edge}_{lane_index}" for edge in affected_edges]

    # Calculate simulation time range (event time + 30min buffer)
    event_start = pd.to_datetime(event_row['开始时间'])
    event_end = pd.to_datetime(event_row['结束时间'])
    buffer = timedelta(minutes=30)

    sim_start = event_start - buffer
    sim_end = event_end + buffer
    sim_duration_seconds = int((sim_end - sim_start).total_seconds())

    # DHS固定管控时段：7:30-9:30
    dhs_start_time = event_start.replace(hour=7, minute=30, second=0, microsecond=0)
    dhs_end_time = event_start.replace(hour=9, minute=30, second=0, microsecond=0)

    # 转换为仿真时间（相对于sim_start的秒数）
    dhs_begin_seconds = max(0, int((dhs_start_time - sim_start).total_seconds()))
    dhs_end_seconds_raw = int((dhs_end_time - sim_start).total_seconds())

    # 确保不超过仿真总时长
    dhs_end_seconds = min(dhs_end_seconds_raw, sim_duration_seconds)

    # 计算实际管控时间（仿真时间内的重叠部分）
    actual_control_start = sim_start + timedelta(seconds=dhs_begin_seconds)
    actual_control_end = sim_start + timedelta(seconds=dhs_end_seconds)

    return {
        'shoulder_segments': affected_edges,  # Fixed: use correct field name for validation
        'affected_lanes': affected_lanes,
        'hard_shoulder_lane_index': lane_index,  # Emergency lane (rightmost, _0)
        'activation_schedule': [  # Fixed: use correct field name for validation
            {
                'begin': dhs_begin_seconds,  # 相对于仿真开始的秒数
                'end': dhs_end_seconds,      # 相对于仿真开始的秒数，不超过仿真时长
                'status': 'OPEN',  # DHS opens the hard shoulder
                'allowed_vehicle_types': ['passenger']  # Only passenger cars
            }
        ],
        'response_delay_seconds': 0,  # Pre-scheduled, no delay
        'recovery_period_seconds': 0,  # Pre-scheduled end time
        # 添加timing信息（用于control_strategy_config.json生成）
        '_actual_control_start': actual_control_start.strftime('%Y-%m-%d %H:%M:%S'),
        '_actual_control_end': actual_control_end.strftime('%Y-%m-%d %H:%M:%S'),
        '_sim_start': sim_start.strftime('%Y-%m-%d %H:%M:%S'),
        '_sim_duration_seconds': sim_duration_seconds
    }


# TEC parameter generation also removed - handled by scenario_generator


def generate_flowsurge_scenarios(
    events_csv: str,
    network_file: str,
    output_base_dir: str,
    min_duration_minutes: int = 30,
    max_scenarios: int = None
) -> Dict[str, Any]:
    """
    Generate flow surge scenario configuration bundles.

    Args:
        events_csv: Path to flow_high_events.csv
        network_file: Path to SUMO network file
        output_base_dir: Base directory for scenario output
        min_duration_minutes: Minimum event duration (default: 30)
        max_scenarios: Maximum number of scenarios to generate (None = all)

    Returns:
        Summary statistics dictionary
    """
    logger.info("=" * 80)
    logger.info("FLOW SURGE SCENARIO GENERATION")
    logger.info("=" * 80)

    # Step 1: Load and filter events
    df_events = load_and_filter_flowsurge_events(events_csv, min_duration_minutes)

    if len(df_events) == 0:
        logger.error("No events to process. Exiting.")
        return {'total_events': 0, 'total_scenarios': 0, 'scenarios_by_strategy': {}}

    # Step 2: Enhance with control strategy information
    df_enhanced = enhance_with_control_strategy(df_events)

    # Save enhanced CSV
    enhanced_csv_path = Path(events_csv).parent / 'flow_high_events_enhanced.csv'
    df_enhanced.to_csv(enhanced_csv_path, index=False, encoding='utf-8')
    logger.info(f"Saved enhanced CSV to: {enhanced_csv_path}")

    # Step 3: Limit number of scenarios if specified
    if max_scenarios and len(df_enhanced) > max_scenarios:
        logger.info(f"Limiting to first {max_scenarios} events")
        df_enhanced = df_enhanced.head(max_scenarios)

    # Step 4: Initialize scenario generator
    generator = ScenarioGenerator(
        network_file=network_file,
        output_base_dir=output_base_dir
    )

    # Step 5: Generate scenarios
    scenario_count = 0
    scenarios_by_strategy = {'VSS': 0, 'DHS': 0, 'TEC': 0, 'NO_CONTROL': 0}
    generated_scenarios = []

    for idx, row in df_enhanced.iterrows():
        event_data = convert_event_to_dict(row)
        strategies = determine_control_strategies(row)

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Event {event_data['report_id']} ({idx+1}/{len(df_enhanced)})")
        logger.info(f"Duration: {row['duration_minutes']:.1f} min | Strategies: {strategies}")

        # Generate NO_CONTROL baseline
        try:
            files = generator.generate_scenario(
                event_data=event_data,
                strategy_type='NO_CONTROL',
                control_params={}
            )
            scenario_count += 1
            scenarios_by_strategy['NO_CONTROL'] += 1
            logger.info(f"✓ Generated NO_CONTROL scenario")

            generated_scenarios.append({
                'event_id': event_data['report_id'],
                'event_type': '流量激增工况',
                'strategy': 'NO_CONTROL',
                'scenario_dir': files['add_xml'].parent.name,  # Only scenario directory name, not full path
                'duration_minutes': float(row['duration_minutes'])
            })
        except Exception as e:
            logger.error(f"✗ Failed to generate NO_CONTROL scenario: {e}")

        # Generate control strategy scenarios
        for strategy in strategies:
            try:
                # Generate control parameters
                # Note: Time calculations (begin/end) are now handled automatically by scenario_generator
                if strategy == 'VSS':
                    # Simplified VSS parameters - scenario_generator calculates timing
                    control_params = {
                        'affected_edges': [str(row['edge_id'])],
                        'speed_steps': [
                            {'speed_kmh': 80}  # Mild reduction from normal 100 km/h
                        ],
                        'response_delay_seconds': 300,   # 5 min response
                        'recovery_period_seconds': 600   # 10 min recovery
                    }
                elif strategy == 'DHS':
                    # DHS is flowsurge-specific, keep dedicated function
                    control_params = generate_control_params_dhs(row)
                elif strategy == 'TEC':
                    # Simplified TEC parameters - scenario_generator calculates timing
                    control_params = {
                        'entrance_edges': [str(row['edge_id'])],
                        'flow_intervals': [
                            {'flow_coefficient': 0.9}  # Mild flow control (reduce by 10%)
                        ],
                        'response_delay_seconds': 300,   # 5 min response
                        'recovery_period_seconds': 600   # 10 min recovery
                    }
                else:
                    logger.warning(f"Unknown strategy: {strategy}, skipping")
                    continue

                # Generate scenario
                files = generator.generate_scenario(
                    event_data=event_data,
                    strategy_type=strategy,
                    control_params=control_params
                )

                scenario_count += 1
                scenarios_by_strategy[strategy] += 1
                logger.info(f"✓ Generated {strategy} scenario")

                generated_scenarios.append({
                    'event_id': event_data['report_id'],
                    'event_type': '流量激增工况',
                    'strategy': strategy,
                    'scenario_dir': files['add_xml'].parent.name,  # Only scenario directory name, not full path
                    'duration_minutes': float(row['duration_minutes'])
                })

            except Exception as e:
                logger.error(f"✗ Failed to generate {strategy} scenario: {e}")

    # Step 6: Update unified scenario index (not separate flowsurge index)
    scenario_index_path = Path(output_base_dir) / 'scenario_index.json'

    # Load existing unified index if it exists
    if scenario_index_path.exists():
        with open(scenario_index_path, 'r', encoding='utf-8') as f:
            unified_index = json.load(f)
        logger.info(f"Loaded existing unified index with {len(unified_index.get('scenarios', []))} scenarios")
    else:
        unified_index = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_events': 0,
            'total_scenarios': 0,
            'scenarios_by_strategy': {},
            'scenarios': []
        }

    # Add flow surge scenarios to unified index
    before_count = len(unified_index.get('scenarios', []))
    unified_index['scenarios'].extend(generated_scenarios)

    # Update metadata
    unified_index['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    unified_index['total_scenarios'] = len(unified_index['scenarios'])

    # Save unified index
    with open(scenario_index_path, 'w', encoding='utf-8') as f:
        json.dump(unified_index, f, indent=2, ensure_ascii=False)

    # Also save flowsurge-specific index for reference (but not as primary)
    flowsurge_index_path = Path(output_base_dir) / 'scenario_index_flowsurge.json'
    flowsurge_index = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'event_type': '流量激增工况',
        'total_events': len(df_enhanced),
        'total_scenarios': scenario_count,
        'scenarios_by_strategy': scenarios_by_strategy,
        'scenarios': generated_scenarios,
        'configuration': {
            'min_duration_minutes': min_duration_minutes,
            'dhs_morning_control': f"{DHS_MORNING_CONTROL_START} - {DHS_MORNING_CONTROL_END}",
            'dhs_segments': G4202_SOUTH_DHS_EDGES
        }
    }

    with open(flowsurge_index_path, 'w', encoding='utf-8') as f:
        json.dump(flowsurge_index, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*80}")
    logger.info("GENERATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total events processed: {len(df_enhanced)}")
    logger.info(f"Total scenarios generated: {scenario_count}")
    logger.info(f"Scenarios by strategy: {scenarios_by_strategy}")
    logger.info(f"Unified index updated: {before_count} -> {len(unified_index['scenarios'])} scenarios")
    logger.info(f"Unified index saved to: {scenario_index_path}")

    return unified_index


def main():
    """Main entry point for flow surge scenario generation."""
    # Configuration
    events_csv = project_root / 'events' / 'flow_high_events.csv'
    network_file = project_root / 'templates' / 'network_files' / 'sichuan202508v7.net.xml'
    output_base_dir = project_root / 'output' / 'scenarios'
    min_duration_minutes = 30
    max_scenarios = 5  # Limit to 5 events for testing

    # Validate inputs
    if not events_csv.exists():
        logger.error(f"Events CSV not found: {events_csv}")
        return 1

    if not network_file.exists():
        logger.error(f"Network file not found: {network_file}")
        return 1

    # Generate scenarios
    try:
        summary = generate_flowsurge_scenarios(
            events_csv=str(events_csv),
            network_file=str(network_file),
            output_base_dir=str(output_base_dir),
            min_duration_minutes=min_duration_minutes,
            max_scenarios=max_scenarios
        )

        logger.info("\n✓ Flow surge scenario generation completed successfully")
        return 0

    except Exception as e:
        logger.error(f"\n✗ Flow surge scenario generation failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
