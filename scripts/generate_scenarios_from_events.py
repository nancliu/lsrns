"""
Event Scenario Batch Generation Script

Generates 18+ event scenario configuration bundles from event CSV data.
Filters representative events and maps them to control strategies (VSS, DHS, TEC).

Usage:
    python scripts/generate_scenarios_from_events.py

Output:
    - output/scenarios/{event_type}/{strategy}/scenario_*.add.xml
    - output/scenarios/{event_type}/{strategy}/event_description.json
    - output/scenarios/{event_type}/{strategy}/traffic_input_config.json
    - output/scenarios/{event_type}/{strategy}/control_strategy_config.json
    - output/scenarios/scenario_index.json

Author: AI Assistant
Created: 2025-01-10
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import json
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.control_tools.scenario_generator import ScenarioGenerator
# Note: scenario_sumocfg_generator is not used here - sumocfg files are generated
# when scenarios are applied to cases, not during scenario library generation
from shared.utilities.toll_mapping_utils import resolve_toll_edges

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 事件类型映射表 (normalize CSV event types to standard types)
# 应用于CSV中非标准的事件类型描述
EVENT_TYPE_MAPPING = {
    # 标准类型 (直接映射)
    '交通事故': '交通事故',
    '交通阻塞': '交通阻塞',
    '交通管制': '交通管制',
    '地质灾害': '地质灾害',
    '车辆故障': '车辆故障',
    '恶劣天气': '恶劣天气',

    # 非标准类型映射规则 (2025-11-11修复)
    '暴雨橙色预警': '恶劣天气',        # 暴雨预警属于恶劣天气
    '暴雨黄色预警': '恶劣天气',        # 黄色预警也属于恶劣天气
    '暴雨红色预警': '恶劣天气',        # 红色预警也属于恶劣天气
    '突发事件': '车辆故障',             # 突发事件(如车辆自燃)属于车辆故障
}


def load_events_csv(csv_path: str) -> pd.DataFrame:
    """
    Load events from CSV file.

    Args:
        csv_path: Path to events CSV file

    Returns:
        DataFrame with event data
    """
    logger.info(f"Loading events from: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8')
    logger.info(f"Loaded {len(df)} events")
    return df


def calculate_duration_hours(row: pd.Series) -> float:
    """
    Calculate event duration in hours.

    Args:
        row: Event data row with 开始时间 and 结束时间

    Returns:
        Duration in hours, or -1 if calculation fails
    """
    try:
        start = pd.to_datetime(row['开始时间'])
        end = pd.to_datetime(row['结束时间'])
        duration = (end - start).total_seconds() / 3600
        return duration
    except Exception:
        return -1


def score_event_quality(row: pd.Series) -> float:
    """
    Score event quality for scenario generation.

    Scoring criteria:
    - Duration: 1-2 hours optimal (score 1.0), decreases outside range
    - Data completeness: All required fields present (score 0-1)
    - Spatial matching: Has edge_id and junction_id (score 0.5 each)

    Args:
        row: Event data row

    Returns:
        Quality score (0-3.0, higher is better)
    """
    score = 0.0

    # Duration score (0-1.0)
    duration = calculate_duration_hours(row)
    if 1.0 <= duration <= 2.0:
        score += 1.0  # Optimal duration
    elif 0.5 <= duration <= 3.0:
        # Acceptable duration, slightly lower score
        score += 0.7
    elif duration > 0:
        # Too short or too long
        score += 0.3

    # Data completeness score (0-1.0)
    required_fields = ['report_id', '类型', '开始时间', '结束时间', 'edge_id', '占用车道情况']
    complete_count = sum(1 for field in required_fields if pd.notna(row.get(field)))
    score += complete_count / len(required_fields)

    # Spatial matching score (0-1.0)
    if pd.notna(row.get('edge_id')):
        score += 0.5
    if pd.notna(row.get('junction_id')):
        score += 0.5

    return score


def filter_representative_events(events_df: pd.DataFrame, target_count: int = 18,
                                 specific_event_ids: List[int] = None) -> pd.DataFrame:
    """
    Filter representative events for scenario generation.

    Filtering criteria:
    - Duration: 0.5-3 hours
    - Spatial matching: Has edge_id and junction_id
    - Data completeness: All required fields present
    - Distribution: Balanced across event types and locations

    Args:
        events_df: DataFrame with all events
        target_count: Target number of events to select
        specific_event_ids: If provided, filter for only these event IDs (skips other filtering)

    Returns:
        DataFrame with filtered events
    """
    logger.info(f"Filtering events (target: {target_count} events)")
    logger.info(f"Total events in CSV: {len(events_df)}")

    # If specific event IDs provided, filter for those only
    if specific_event_ids:
        logger.info(f"Filtering for specific event IDs: {specific_event_ids}")
        result = events_df[events_df['report_id'].isin(specific_event_ids)].copy()
        logger.info(f"Found {len(result)} events matching specific IDs")
        return result

    # Step 1: Calculate duration for all events
    events_df['duration_hours'] = events_df.apply(calculate_duration_hours, axis=1)

    # Step 2: Filter by duration (0.5-3 hours)
    filtered = events_df[
        (events_df['duration_hours'] >= 0.5) &
        (events_df['duration_hours'] <= 3.0)
    ].copy()
    logger.info(f"After duration filter (0.5-3 hours): {len(filtered)} events")

    # Step 3: Filter by data completeness with relaxed requirements for certain event types
    # Phase 3.5: Relaxed data requirements for 交通管制 and 交通阻塞
    completeness_mask = (
        filtered['edge_id'].notna() &
        filtered['report_id'].notna() &
        filtered['类型'].notna()
    )

    # For 交通事故, 地质灾害, 车辆故障, 恶劣天气: Require lane occupation data
    accident_types = ['交通事故', '地质灾害', '车辆故障', '恶劣天气']
    accident_mask = filtered['类型'].isin(accident_types)
    completeness_mask = completeness_mask & (
        ~accident_mask | filtered['占用车道情况'].notna()
    )

    # For 交通管制 (Road Control): Require control data but NOT lane occupation
    road_control_mask = filtered['类型'] == '交通管制'
    completeness_mask = completeness_mask & (
        ~road_control_mask | filtered['管控收费站'].notna()
    )

    # For 交通阻塞 (Congestion): No required lane data, prefer but don't require control data
    # (congestion can use event-activated control)

    filtered = filtered[completeness_mask]
    logger.info(f"After completeness filter (relaxed for 交通管制/阻塞): {len(filtered)} events")

    # Step 4: Score event quality
    filtered['quality_score'] = filtered.apply(score_event_quality, axis=1)

    # Step 5: Stratify by event type (aim for 3 events per type)
    event_types = filtered['类型'].unique()
    logger.info(f"Event types available: {list(event_types)}")

    selected_events = []
    events_per_type = max(3, target_count // len(event_types))

    for event_type in event_types:
        type_events = filtered[filtered['类型'] == event_type].copy()
        type_events = type_events.sort_values('quality_score', ascending=False)

        # Select top N events of this type
        selected = type_events.head(events_per_type)
        selected_events.append(selected)
        logger.info(f"  {event_type}: Selected {len(selected)} events (from {len(type_events)} available)")

    result = pd.concat(selected_events, ignore_index=True)

    # If we haven't met target_count, add more high-quality events
    if len(result) < target_count:
        remaining_events = filtered[~filtered['report_id'].isin(result['report_id'])]
        remaining_events = remaining_events.sort_values('quality_score', ascending=False)
        additional = remaining_events.head(target_count - len(result))
        result = pd.concat([result, additional], ignore_index=True)

    logger.info(f"Final selection: {len(result)} events")
    return result


def parse_csv_control_data(event_row: pd.Series) -> Dict[str, Any]:
    """
    Parse CSV control data fields for real operational control strategies.

    Extracts control data from CSV fields:
    - 管控开始时间: Control start time
    - 管控结束时间: Control end time (optional)
    - 管控收费站: Comma-separated toll station IDs
    - 管控范围: Human-readable control range description
    - 管控措施: Control measure description

    Args:
        event_row: Event data row from CSV

    Returns:
        Dict with parsed control data, or empty dict if no control data available
    """
    control_data = {}

    # Check if control data fields exist and are not NaN
    if pd.notna(event_row.get("管控开始时间")) and pd.notna(event_row.get("管控收费站")):
        control_data["has_csv_control"] = True
        control_data["activation_time"] = str(event_row.get("管控开始时间", ""))
        control_data["deactivation_time"] = (
            str(event_row.get("管控结束时间", ""))
            if pd.notna(event_row.get("管控结束时间"))
            else None
        )

        # Parse toll station IDs
        toll_stations_str = str(event_row.get("管控收费站", ""))
        toll_station_ids = [sid.strip() for sid in toll_stations_str.split(",") if sid.strip()]
        control_data["toll_station_ids"] = toll_station_ids

        # Resolve toll stations to edge IDs using toll_mapping_utils
        try:
            entrance_edges = resolve_toll_edges(toll_station_ids)
            control_data["entrance_edges"] = entrance_edges
            if len(entrance_edges) < len(toll_station_ids):
                logger.warning(f"Only resolved {len(entrance_edges)}/{len(toll_station_ids)} toll stations to edges")
        except Exception as e:
            logger.warning(f"Error resolving toll stations: {e}")
            control_data["entrance_edges"] = []

        # Store additional fields
        control_data["control_range"] = str(event_row.get("管控范围", ""))
        control_data["control_measure"] = str(event_row.get("管控措施", ""))

        logger.debug(f"Parsed CSV control data: {len(toll_station_ids)} stations, "
                    f"{len(entrance_edges)} resolved edges")
    else:
        control_data["has_csv_control"] = False
        logger.debug("No CSV control data available for this event")

    return control_data


def is_dhs_eligible_location(event_row: pd.Series) -> bool:
    """
    Check if the event location is eligible for DHS (Dynamic Hard Shoulder) control.

    DHS requires physical emergency lane (hard shoulder) availability.
    Only specific highway segments have emergency lanes suitable for DHS.

    Eligibility criteria:
    - G4202 South segment K30-K55 (成都绕城高速南段): Has emergency lanes
    - Other segments: No DHS infrastructure

    Args:
        event_row: Event data row

    Returns:
        bool: True if location supports DHS, False otherwise
    """
    road = event_row.get('所在高速公路', '')
    mileage_str = event_row.get('发生地点', '')  # e.g., "51.17", "30.5"

    # G4202 South segment check (成都绕城高速南段 K30-K55)
    if 'G4202' in str(road):
        try:
            # Extract mileage number from string
            # Handle formats like "51.17", "K51.17", "51+170"
            mileage_cleaned = str(mileage_str).replace('K', '').replace('+', '.').strip()
            if '|' in mileage_cleaned:  # Handle multiple mileages
                mileage_cleaned = mileage_cleaned.split('|')[0]

            mileage = float(mileage_cleaned)

            # Check if within K30-K55 range
            if 30.0 <= mileage <= 55.0:
                logger.info(f"Event at G4202 K{mileage:.1f} - DHS eligible (K30-K55 range)")
                return True
            else:
                logger.debug(f"Event at G4202 K{mileage:.1f} - outside DHS range (K30-K55)")
                return False
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Could not parse mileage '{mileage_str}' for DHS eligibility check: {e}")
            return False

    # For other highways, default to False
    logger.debug(f"Event on {road} - DHS not eligible (not G4202 South K30-K55)")
    return False


def map_event_to_strategies(event_row: pd.Series) -> List[Dict[str, Any]]:
    """
    Map event to control strategies with parameters.

    Two-mode control strategy selection:
    - MODE 1 (CSV Priority): Use real operational control data from CSV when available
    - MODE 2 (Event-Activated): Fall back to event-based control timing

    Strategy mapping:
    - VSS (Variable Speed Sign): Speed limit reduction based on event severity
    - DHS (Dynamic Hard Shoulder): Opens shoulder lane to maintain capacity (location-restricted)
    - TEC (Toll Entrance Control): Flow rate control at toll entrances

    Args:
        event_row: Event data row

    Returns:
        List of strategy configurations with calculated parameters
    """
    event_type = event_row.get('类型', '交通事故')
    affected_lanes = event_row.get('占用车道情况', '')
    edge_id = event_row.get('edge_id', '')

    # Parse CSV control data (Phase 3.5)
    csv_control = parse_csv_control_data(event_row)

    # Calculate parameters based on event characteristics
    strategies = []

    # Always add a no-control baseline scenario for every event
    # This allows comparing event-only impact vs. event+control impact
    strategies.append({
        "strategy_type": "NO_CONTROL",
        "params": {
            "description": "Event-only baseline (no control strategy applied)",
            "event_only": True,
        }
    })

    # Phase 3.5: Event type-specific control logic
    # ============================================

    # 3.5.4.1: 交通管制 (Road Control) - MUST use CSV control data
    if event_type == '交通管制':
        if not csv_control.get("has_csv_control"):
            logger.warning(f"交通管制 event {event_row.get('report_id')} missing CSV control data - skipping")
            return []  # Return empty strategies for road control without data
        # Road control must use TEC with CSV toll stations
        logger.info(f"Generating 交通管制 scenario with CSV control data")
        # Continue with TEC strategy generation below (will use CSV data)

    # 3.5.4.2: 交通阻塞 (Congestion) - Prefer CSV, no lane closure
    # Note: CongestionInjector already handles no event injection
    if event_type == '交通阻塞':
        if csv_control.get("has_csv_control"):
            logger.info(f"Generating 交通阻塞 scenario with CSV control data")
        else:
            logger.info(f"Generating 交通阻塞 scenario with event-activated control (no lane closure)")
        # For congestion, we'll only generate TEC or VSS, not DHS
        # DHS not applicable for congestion (no lane closure)

    # VSS Strategy: Variable speed limit
    # Skip for 交通管制 (uses TEC only) - already filtered above
    # For 交通阻塞 (congestion): Only VSS, no lane closure
    # For accidents/disasters: VSS with severity-based speed
    if event_type != '交通管制' and edge_id:  # Road control uses TEC only, require edge_id
        if '应急车道' in str(affected_lanes) or '紧急停车带' in str(affected_lanes):
            speed_limit_kmh = 70  # Emergency lane only, less severe
        elif '第一车道' in str(affected_lanes) or '行车道' in str(affected_lanes):
            speed_limit_kmh = 50  # Main lane blocked, more severe
        else:
            speed_limit_kmh = 60  # Default (congestion or no lane info)

        strategies.append({
            "strategy_type": "VSS",
            "params": {
                "speed_limit_kmh": speed_limit_kmh,
                "affected_edges": [edge_id],
                "response_delay_seconds": 300,  # 5 min detection + activation
                "recovery_period_seconds": 600,  # 10 min after event clears
            }
        })
    elif event_type != '交通管制':
        logger.warning(f"Event {event_row.get('report_id')} missing edge_id, skipping VSS strategy")

    # DHS Strategy: Dynamic Hard Shoulder
    # Skip for 交通管制 (road control uses TEC only)
    # Skip for 交通阻塞 (congestion - no physical lane closure)
    # For accidents/disasters: Only if emergency lane NOT already occupied, edge_id available, AND location eligible
    if event_type not in ['交通管制', '交通阻塞'] and edge_id:
        if '应急车道' not in str(affected_lanes) and '紧急停车带' not in str(affected_lanes):
            # Check if location is DHS-eligible (has emergency lane infrastructure)
            if is_dhs_eligible_location(event_row):
                strategies.append({
                    "strategy_type": "DHS",
                    "params": {
                        "open_shoulder": True,
                        "affected_edges": [edge_id],
                        "response_delay_seconds": 300,
                        "recovery_period_seconds": 600,
                    }
                })
                logger.debug(f"DHS strategy added for event {event_row.get('report_id')} at eligible location")
            else:
                logger.debug(f"DHS strategy skipped for event {event_row.get('report_id')} - location not eligible (no emergency lane)")

    # TEC Strategy: Toll Entrance Control
    # MODE 1: Use CSV control data if available (real toll station closures)
    # MODE 2: Fall back to event-based control (simulated response)
    if csv_control.get("has_csv_control") and csv_control.get("entrance_edges"):
        # Use real operational control data from CSV
        strategies.append({
            "strategy_type": "TEC",
            "params": {
                "entrance_edges": csv_control["entrance_edges"],
                "flow_reduction": 0.8,  # Toll station closure = 80% flow reduction
                "csv_control": True,
                "activation_time": csv_control["activation_time"],
                "deactivation_time": csv_control.get("deactivation_time"),
                "toll_station_ids": csv_control["toll_station_ids"],
                "control_range": csv_control.get("control_range", ""),
                "control_measure": csv_control.get("control_measure", ""),
            }
        })
        logger.debug(f"TEC strategy using CSV control data: {len(csv_control['entrance_edges'])} toll stations")
    elif edge_id:
        # Fall back to event-activated control (simulated response)
        if '第一车道' in str(affected_lanes) or '第二车道' in str(affected_lanes):
            flow_reduction = 0.4  # Severe blockage, reduce flow more
        else:
            flow_reduction = 0.2  # Minor blockage, slight reduction

        strategies.append({
            "strategy_type": "TEC",
            "params": {
                "flow_reduction": flow_reduction,
                "entrance_edges": [edge_id],  # Required by TEC
                "response_delay_seconds": 300,
                "recovery_period_seconds": 600,
                "csv_control": False,
            }
        })
        logger.debug(f"TEC strategy using event-activated control (no CSV data)")
    else:
        logger.warning(f"Event {event_row.get('report_id')} missing edge_id, skipping TEC strategy (no CSV control)")

    return strategies


def prepare_event_data(event_row: pd.Series) -> Dict[str, Any]:
    """
    Convert CSV row to event data dictionary with standardized field names.

    Maps CSV column names to ScenarioGenerator expected field names.
    Normalizes event types using EVENT_TYPE_MAPPING.

    Args:
        event_row: Event row from CSV

    Returns:
        Event data dictionary
    """
    # Normalize event type using mapping table
    raw_type = event_row.get("类型", "交通事故")
    normalized_type = EVENT_TYPE_MAPPING.get(raw_type, raw_type)

    return {
        "report_id": str(event_row.get("report_id", "")),
        "event_type": normalized_type,
        "event_description": event_row.get("详细信息", "")[:100] if pd.notna(event_row.get("详细信息")) else "",
        "road": event_row.get("所在高速公路", ""),
        "direction": event_row.get("上下行", ""),
        "mileage": f"K{event_row.get('发生地点', '')}+000" if pd.notna(event_row.get("发生地点")) else "",
        "junction_id": str(event_row.get("junction_id", "")),
        "edge_id": str(event_row.get("edge_id", "")),
        # Parse affected lanes - handle both comma and 、 separators
        "affected_lanes": (
            [lane.strip() for lane in str(event_row.get("占用车道情况", "应急车道"))
             .replace("、", ",").split(",") if lane.strip()]
            if pd.notna(event_row.get("占用车道情况"))
            else ["应急车道"]
        ),
        "start_time": event_row.get("开始时间", ""),
        "end_time": event_row.get("结束时间", ""),
    }


def generate_scenario_library(events_csv: str, network_file: str,
                              output_dir: str = "output/scenarios",
                              target_count: int = 18,
                              specific_event_ids: List[int] = None) -> Dict[str, Any]:
    """
    Generate scenario library from events CSV.

    Args:
        events_csv: Path to events CSV file
        network_file: Path to SUMO network file
        output_dir: Output directory for scenarios
        target_count: Number of events to select for scenario generation (default: 18)
        specific_event_ids: If provided, regenerate only these event IDs

    Returns:
        Dictionary with generation results
    """
    logger.info("=" * 60)
    logger.info("Event Scenario Library Generation")
    logger.info("=" * 60)
    if specific_event_ids:
        logger.info(f"Regenerating specific event IDs: {specific_event_ids}")
    else:
        logger.info(f"Target event count: {target_count}")

    # Load events
    events_df = load_events_csv(events_csv)

    # Filter representative events
    selected_events = filter_representative_events(events_df, target_count=target_count,
                                                   specific_event_ids=specific_event_ids)

    # Initialize scenario generator
    generator = ScenarioGenerator(network_file=network_file, output_base_dir=output_dir)

    results = {
        "total_events": len(selected_events),
        "total_scenarios": 0,
        "success": [],
        "failed": [],
    }

    # Generate scenarios for each event
    for idx, event_row in selected_events.iterrows():
        # Prepare event data with standardized field names
        event_data = prepare_event_data(event_row)

        # Map event to strategies
        strategies = map_event_to_strategies(event_row)

        # Generate scenario for each strategy
        for strategy_config in strategies:
            try:
                # Validate required parameters before generation
                strategy_type = strategy_config["strategy_type"]
                params = strategy_config["params"]

                # Skip VSS if affected_edges is empty
                if strategy_type == "VSS" and not params.get("affected_edges"):
                    logger.warning(f"⊘ Skipping VSS for event {event_data.get('report_id')}: "
                                 f"No affected_edges (missing edge_id)")
                    results["failed"].append({
                        "event_id": event_data.get("report_id"),
                        "strategy": strategy_type,
                        "error": "Missing edge_id for VSS strategy"
                    })
                    continue

                # Skip TEC if entrance_edges is empty
                if strategy_type == "TEC" and not params.get("entrance_edges"):
                    logger.warning(f"⊘ Skipping TEC for event {event_data.get('report_id')}: "
                                 f"No entrance_edges (missing edge_id)")
                    results["failed"].append({
                        "event_id": event_data.get("report_id"),
                        "strategy": strategy_type,
                        "error": "Missing edge_id for TEC strategy"
                    })
                    continue

                # Skip DHS if affected_edges is empty
                if strategy_type == "DHS" and not params.get("affected_edges"):
                    logger.warning(f"⊘ Skipping DHS for event {event_data.get('report_id')}: "
                                 f"No affected_edges (missing edge_id)")
                    results["failed"].append({
                        "event_id": event_data.get("report_id"),
                        "strategy": strategy_type,
                        "error": "Missing edge_id for DHS strategy"
                    })
                    continue

                # Generate scenario
                scenario_files = generator.generate_scenario(
                    event_data=event_data,
                    strategy_type=strategy_type,
                    control_params=params
                )

                results["success"].append({
                    "event_id": event_data.get("report_id"),
                    "strategy": strategy_type,
                    "files": {k: str(v) for k, v in scenario_files.items()}
                })
                results["total_scenarios"] += 1

                logger.info(f"✓ Generated scenario: Event {event_data.get('report_id')} + "
                          f"{strategy_type}")

            except Exception as e:
                logger.error(f"✗ Failed to generate scenario: Event {event_data.get('report_id')} + "
                           f"{strategy_config['strategy_type']}: {e}")
                results["failed"].append({
                    "event_id": event_data.get("report_id"),
                    "strategy": strategy_config["strategy_type"],
                    "error": str(e)
                })

    # Generate scenario index
    create_scenario_index(results, output_dir)

    # Print summary
    logger.info("=" * 60)
    logger.info("Generation Summary")
    logger.info("=" * 60)
    logger.info(f"Total events processed: {results['total_events']}")
    logger.info(f"Scenarios generated: {results['total_scenarios']}")
    logger.info(f"Successful: {len(results['success'])}")
    logger.info(f"Failed: {len(results['failed'])}")

    return results


def create_scenario_index(results: Dict[str, Any], output_dir: str):
    """
    Update unified scenario_index.json with new scenario metadata (APPEND MODE).

    IMPORTANT: This function APPENDS to existing index, not overwrites it.
    This prevents data loss when regenerating specific scenarios.

    Args:
        results: Generation results dictionary
        output_dir: Output directory
    """
    index_path = Path(output_dir) / "scenario_index.json"

    # Build new scenarios list with metadata
    new_scenarios = []
    for scenario_info in results["success"]:
        # Read event description JSON to get metadata
        event_desc_path = scenario_info["files"].get("event_description")
        if event_desc_path and Path(event_desc_path).exists():
            with open(event_desc_path, 'r', encoding='utf-8') as f:
                event_desc = json.load(f)

            # Extract scenario_dir from file paths
            add_xml_path = Path(scenario_info["files"]["add_xml"])
            scenario_dir = add_xml_path.parent.name

            new_scenarios.append({
                "event_id": scenario_info["event_id"],
                "event_type": event_desc.get("event_type", "未知"),
                "strategy": scenario_info["strategy"],
                "location": event_desc.get("location", {}),
                "time": event_desc.get("time", {}),
                "files": {
                    "scenario_dir": scenario_dir,
                    "add_xml": add_xml_path.name,
                    "event_description": "event_description.json",
                    "traffic_config": "traffic_input_config.json",
                    "control_config": "control_strategy_config.json"
                },
                "created_cases": []
            })

    # Load existing unified index if it exists
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            unified_index = json.load(f)
        logger.info(f"Loaded existing unified index with {len(unified_index.get('scenarios', []))} scenarios")
        before_count = len(unified_index.get('scenarios', []))
    else:
        unified_index = {
            'generated_at': pd.Timestamp.now().isoformat(),
            'total_scenarios': 0,
            'scenarios': []
        }
        before_count = 0
        logger.info("Creating new unified index")

    # Append new scenarios to unified index
    unified_index['scenarios'].extend(new_scenarios)

    # Update metadata
    unified_index['generated_at'] = pd.Timestamp.now().isoformat()
    unified_index['total_scenarios'] = len(unified_index['scenarios'])

    # Save unified index
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(unified_index, f, indent=2, ensure_ascii=False)

    logger.info(f"Updated unified scenario index: {index_path}")
    logger.info(f"  Scenarios: {before_count} -> {len(unified_index['scenarios'])} (+{len(new_scenarios)} new)")

    # Calculate statistics for the newly added scenarios only
    stats_by_type = {}
    stats_by_strategy = {}
    for scenario in new_scenarios:
        event_type = scenario["event_type"]
        strategy = scenario["strategy"]
        stats_by_type[event_type] = stats_by_type.get(event_type, 0) + 1
        stats_by_strategy[strategy] = stats_by_strategy.get(strategy, 0) + 1

    logger.info(f"  New scenarios by event type: {stats_by_type}")
    logger.info(f"  New scenarios by strategy: {stats_by_strategy}")


def validate_input_data(events_csv: str, network_file: str, output_dir: str) -> bool:
    """
    Validate input data and environment before generation.

    Args:
        events_csv: Path to events CSV file
        network_file: Path to SUMO network file
        output_dir: Output directory path

    Returns:
        True if all validations pass, False otherwise
    """
    logger.info("Validating input data...")

    # Check events CSV exists and is readable
    if not Path(events_csv).exists():
        logger.error(f"Events CSV not found: {events_csv}")
        return False

    try:
        df = pd.read_csv(events_csv, nrows=1)
        required_columns = ['report_id', '类型', '开始时间', '结束时间', 'edge_id', '占用车道情况']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns in CSV: {missing_columns}")
            return False
    except Exception as e:
        logger.error(f"Failed to read events CSV: {e}")
        return False

    # Check network file exists
    if not Path(network_file).exists():
        logger.error(f"Network file not found: {network_file}")
        return False

    # Check output directory is writable
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        test_file = output_path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        logger.error(f"Output directory is not writable: {e}")
        return False

    logger.info("✓ All input validations passed")
    return True


def main():
    """Main entry point"""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate traffic event scenarios with control strategies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate 18 representative scenarios (default)
  python scripts/generate_scenarios_from_events.py

  # Generate 50 scenarios
  python scripts/generate_scenarios_from_events.py --target-count 50

  # Generate 100 scenarios
  python scripts/generate_scenarios_from_events.py --target-count 100

  # Generate all valid scenarios (329 events)
  python scripts/generate_scenarios_from_events.py --target-count 329
        '''
    )
    parser.add_argument(
        '--target-count',
        type=int,
        default=18,
        help='Number of events to generate scenarios for (default: 18)'
    )
    parser.add_argument(
        '--events-csv',
        default="events/all_extracted_events.csv",
        help='Path to events CSV file (default: events/all_extracted_events.csv)'
    )
    parser.add_argument(
        '--network-file',
        default="templates/network_files/sichuan202508v7.net.xml",
        help='Path to SUMO network file (default: templates/network_files/sichuan202508v7.net.xml)'
    )
    parser.add_argument(
        '--output-dir',
        default="output/scenarios",
        help='Output directory for scenarios (default: output/scenarios)'
    )
    parser.add_argument(
        '--specific-event-ids',
        type=int,
        nargs='+',
        help='Regenerate specific event IDs (e.g., --specific-event-ids 11554 12522)'
    )

    args = parser.parse_args()

    # Configuration from arguments
    EVENTS_CSV = args.events_csv
    NETWORK_FILE = args.network_file
    OUTPUT_DIR = args.output_dir
    TARGET_COUNT = args.target_count
    SPECIFIC_EVENT_IDS = args.specific_event_ids

    if SPECIFIC_EVENT_IDS:
        logger.info(f"🎯 Regenerating specific events: {SPECIFIC_EVENT_IDS}")
    else:
        logger.info(f"🎯 Target event count: {TARGET_COUNT}")

    # Validate inputs
    if not validate_input_data(EVENTS_CSV, NETWORK_FILE, OUTPUT_DIR):
        logger.error("Input validation failed. Exiting.")
        sys.exit(1)

    # Generate scenario library
    try:
        results = generate_scenario_library(
            events_csv=EVENTS_CSV,
            network_file=NETWORK_FILE,
            output_dir=OUTPUT_DIR,
            target_count=TARGET_COUNT,
            specific_event_ids=SPECIFIC_EVENT_IDS
        )

        # Note: SUMO configuration files (simulation.sumocfg) are NOT generated
        # during scenario library generation. They will be created when scenarios
        # are applied to cases (cases branch workflow).
        # Scenario library is read-only and contains only scenario definition files.

        # Exit with appropriate code
        if results["failed"]:
            logger.warning(f"Generation completed with {len(results['failed'])} failures")
            sys.exit(1)
        else:
            logger.info("All scenarios generated successfully!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error during scenario generation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
