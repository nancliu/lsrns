# Enhanced EdgeData Generation - Detailed Design

**Change ID**: `edgedata-enhancement`
**Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Design Ready for Implementation

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [Integration Points](#integration-points)
5. [API Changes](#api-changes)
6. [Implementation Guide](#implementation-guide)
7. [Error Handling](#error-handling)
8. [Testing Strategy](#testing-strategy)

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                 Case Creation Workflow                       │
│                                                              │
│  1. Extract event_id from scenario_id                       │
│  2. Check if case_event_{event_id} exists                   │
│  3. If NEW:                                                  │
│     a. Create case directory                                │
│     b. Generate edgeData:                                   │
│        ├─ Extract event impact edges                        │
│        ├─ Load all scenarios' strategies                    │
│        ├─ Get strategy impact edges                         │
│        ├─ Aggregate & deduplicate                           │
│        └─ Generate unified edgeData.add.xml                 │
│     c. Save to case/config/edgeData.add.xml                 │
│  4. If REUSE: Use existing edgeData.add.xml                 │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|-----------|
| **Aggregate at case creation** | Single generation per event, reuse across scenarios | Requires strategy data upfront |
| **Store in case/config/** | Shared across all simulations | All scenarios share identical edge list |
| **Include all strategy impacts** | Comprehensive monitoring | Larger edge list (but still <1% of network) |
| **Deduplicate in aggregator** | Clean edge list | Small performance overhead |
| **Store metadata** | Track aggregation details for debugging | Additional metadata fields |

---

## Component Design

### 1. Edge Impact Aggregator

**Location**: `shared/utilities/edge_aggregator.py` (NEW)

#### Class: EdgeImpactAggregator

```python
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class EdgeImpactSource:
    """Represents a source of edge impacts."""
    source_type: str  # "event", "vss", "tec", "dhs"
    source_id: str    # event_id or strategy_id
    edge_ids: List[str]
    description: str


class EdgeImpactAggregator:
    """
    Aggregates edge impacts from event and control strategies.

    Purpose:
    - Extract edges affected by event location
    - Extract edges controlled by each strategy
    - Merge into unified, deduplicated list
    - Generate edgeData.add.xml configuration
    """

    def __init__(self):
        """Initialize aggregator."""
        self.logger = logger

    def aggregate_event_impact_edges(
        self,
        case_metadata: Dict[str, any],
        method: str = "radius_2_hops"
    ) -> List[str]:
        """
        Extract all edges affected by event.

        Args:
            case_metadata: Case metadata with event_scenario info
            method: Impact calculation method:
              - "immediate": primary_edge + reverse only
              - "radius_1_hop": ±1 adjacent edges
              - "radius_2_hops": ±2 edges (default)
              - "explicit": from event_scenario.impact_zone

        Returns:
            List of edge IDs affected by event

        Raises:
            ValueError: If event_scenario data invalid
        """
        if 'event_scenario' not in case_metadata:
            self.logger.warning("No event_scenario in metadata, returning empty")
            return []

        event_scenario = case_metadata['event_scenario']
        if 'event_location' not in event_scenario:
            self.logger.warning("No event_location in event_scenario")
            return []

        event_location = event_scenario['event_location']
        primary_edge = event_location.get('edge_id')

        if not primary_edge:
            self.logger.warning("No edge_id in event_location")
            return []

        # Build edge list based on method
        if method == "immediate":
            edges = self._build_immediate_edges(primary_edge)

        elif method == "radius_1_hop":
            edges = self._build_radius_1_hop_edges(primary_edge)

        elif method == "radius_2_hops":
            edges = self._build_radius_2_hop_edges(primary_edge)

        elif method == "explicit":
            edges = self._extract_explicit_edges(event_scenario)

        else:
            raise ValueError(f"Unknown method: {method}")

        self.logger.info(f"Event impact edges ({method}): {len(edges)} edges")
        return edges

    def _build_immediate_edges(self, primary_edge: str) -> List[str]:
        """Build edge list for immediate method."""
        edges = [primary_edge]

        # Add reverse edge
        if primary_edge.startswith('-'):
            reverse = primary_edge[1:]
        else:
            reverse = f"-{primary_edge}"

        edges.append(reverse)

        # Remove duplicates (in case primary is both + -)
        edges = list(set(edges))

        return sorted(edges)

    def _build_radius_1_hop_edges(self, primary_edge: str) -> List[str]:
        """
        Build edge list for radius_1_hop method.

        Includes:
        - Primary edge + reverse
        - Adjacent edges (±1)
        """
        edges = self._build_immediate_edges(primary_edge)

        # Extract edge number
        edge_num = self._extract_edge_number(primary_edge)

        # Add adjacent edges (±1)
        for offset in [-1, 1]:
            adj_edge_num = edge_num + offset
            edges.append(str(adj_edge_num))
            edges.append(f"-{adj_edge_num}")

        # Remove duplicates and sort
        edges = list(set(edges))
        return sorted(edges)

    def _build_radius_2_hop_edges(self, primary_edge: str) -> List[str]:
        """
        Build edge list for radius_2_hop method.

        Includes:
        - Primary edge + reverse
        - Adjacent edges (±1)
        - Spillback edges (±2)
        """
        edges = self._build_radius_1_hop_edges(primary_edge)

        # Extract edge number
        edge_num = self._extract_edge_number(primary_edge)

        # Add spillback edges (±2)
        for offset in [-2, 2]:
            spillback_edge_num = edge_num + offset
            edges.append(str(spillback_edge_num))
            edges.append(f"-{spillback_edge_num}")

        # Remove duplicates and sort
        edges = list(set(edges))
        return sorted(edges)

    def _extract_edge_number(self, edge_id: str) -> int:
        """Extract numeric part from edge ID."""
        # Handle negative edges
        if edge_id.startswith('-'):
            edge_id = edge_id[1:]

        # Extract numeric part (may have suffixes like _1)
        numeric_part = ''.join(c for c in edge_id if c.isdigit())

        try:
            return int(numeric_part)
        except ValueError:
            self.logger.warning(f"Could not extract edge number from {edge_id}")
            return 0

    def _extract_explicit_edges(self, event_scenario: Dict) -> List[str]:
        """Extract edge list from explicit definition in metadata."""
        if 'impact_zone' in event_scenario:
            impact_zone = event_scenario['impact_zone']

            # Try different field names
            for field_name in ['edge_list', 'edges', 'edge_ids', 'all_impacted_edges']:
                if field_name in impact_zone:
                    edges = impact_zone[field_name]
                    if isinstance(edges, list):
                        return edges

        self.logger.warning("No explicit edge list found in impact_zone")
        return []

    def aggregate_strategy_impact_edges(
        self,
        strategies_config: Dict[str, Dict]
    ) -> Dict[str, List[str]]:
        """
        Extract edges affected by control strategies.

        Args:
            strategies_config: Dict mapping strategy_id → strategy definition
              Example:
              {
                "vss_incident": {
                  "type": "VSS",
                  "start_edge": "3000",
                  "end_edge": "3050"
                },
                "tec_toll": {
                  "type": "TEC",
                  "affected_edges": ["5000", "-5000", ...]
                }
              }

        Returns:
            Dict mapping strategy_id → edge_ids list
            Example:
            {
              "vss_incident": ["3000", "-3000", "3001", "-3001", ...],
              "tec_toll": ["5000", "-5000", ...]
            }
        """
        strategy_edges = {}

        for strategy_id, strategy_def in strategies_config.items():
            try:
                strategy_type = strategy_def.get('type', 'unknown')

                if strategy_type == 'VSS':
                    edges = self._extract_vss_edges(strategy_def)

                elif strategy_type == 'TEC':
                    edges = self._extract_tec_edges(strategy_def)

                elif strategy_type == 'DHS':
                    edges = self._extract_dhs_edges(strategy_def)

                else:
                    self.logger.warning(f"Unknown strategy type: {strategy_type}")
                    edges = []

                strategy_edges[strategy_id] = edges
                self.logger.info(f"Strategy {strategy_id} ({strategy_type}): {len(edges)} edges")

            except Exception as e:
                self.logger.error(f"Error extracting edges for {strategy_id}: {e}")
                strategy_edges[strategy_id] = []

        return strategy_edges

    def _extract_vss_edges(self, strategy_def: Dict) -> List[str]:
        """
        Extract edges for VSS (Variable Speed Sign) strategy.

        VSS typically affects a range of edges.
        """
        edges = []

        # Method 1: Explicit edge list
        if 'affected_edges' in strategy_def:
            edges = strategy_def['affected_edges']
            return edges

        # Method 2: Edge range (start to end)
        if 'start_edge' in strategy_def and 'end_edge' in strategy_def:
            start_num = self._extract_edge_number(strategy_def['start_edge'])
            end_num = self._extract_edge_number(strategy_def['end_edge'])

            for edge_num in range(start_num, end_num + 1):
                edges.append(str(edge_num))
                edges.append(f"-{edge_num}")

            return sorted(list(set(edges)))

        self.logger.warning("VSS strategy missing edge definition")
        return []

    def _extract_tec_edges(self, strategy_def: Dict) -> List[str]:
        """
        Extract edges for TEC (Toll Entry Control) strategy.

        TEC typically affects toll entrance and nearby edges.
        """
        edges = []

        # Method 1: Explicit edge list
        if 'affected_edges' in strategy_def:
            edges = strategy_def['affected_edges']
            return edges

        # Method 2: Toll entrance + nearby
        if 'toll_entrance' in strategy_def:
            entrance_edge = strategy_def['toll_entrance']
            edges.append(entrance_edge)

            # Add reverse
            if entrance_edge.startswith('-'):
                edges.append(entrance_edge[1:])
            else:
                edges.append(f"-{entrance_edge}")

            # Add nearby edges
            entrance_num = self._extract_edge_number(entrance_edge)
            for offset in [-1, 1]:
                nearby_num = entrance_num + offset
                edges.append(str(nearby_num))
                edges.append(f"-{nearby_num}")

            return sorted(list(set(edges)))

        self.logger.warning("TEC strategy missing toll entrance definition")
        return []

    def _extract_dhs_edges(self, strategy_def: Dict) -> List[str]:
        """
        Extract edges for DHS (Dynamic Hard Shoulder) strategy.

        DHS affects main line edges + shoulder lane edges.
        """
        edges = []

        # Method 1: Explicit edge list
        if 'affected_edges' in strategy_def:
            edges = strategy_def['affected_edges']
            return edges

        # Method 2: Main edges + shoulder edges
        if 'main_edges' in strategy_def:
            edges.extend(strategy_def['main_edges'])

        if 'shoulder_edges' in strategy_def:
            edges.extend(strategy_def['shoulder_edges'])

        # Add reverses
        reverses = []
        for edge in edges:
            if edge.startswith('-'):
                reverses.append(edge[1:])
            else:
                reverses.append(f"-{edge}")

        edges.extend(reverses)

        return sorted(list(set(edges)))

    def merge_edge_impacts(
        self,
        event_edges: List[str],
        strategy_edges: Dict[str, List[str]]
    ) -> Dict[str, any]:
        """
        Merge event edges with all strategy edges.

        Handles:
        - Deduplication
        - Sorting
        - Tracking of source origins

        Args:
            event_edges: List of event-impacted edges
            strategy_edges: Dict of strategy_id → edges

        Returns:
            Dict with merged info:
            {
              "unified_edge_list": [...],
              "source_breakdown": {
                "event": [...],
                "vss_incident": [...],
                ...
              },
              "statistics": {
                "total_unique": 125,
                "from_event": 10,
                "from_strategies": 115
              }
            }
        """
        # Create set for deduplication
        all_edges: Set[str] = set()

        # Track sources
        source_breakdown = {}
        source_breakdown['event'] = list(set(event_edges))

        # Add event edges
        all_edges.update(event_edges)

        # Add strategy edges
        for strategy_id, edges in strategy_edges.items():
            unique_edges = list(set(edges))
            source_breakdown[strategy_id] = unique_edges
            all_edges.update(edges)

        # Create unified list (sorted for consistency)
        unified_list = sorted(list(all_edges))

        # Calculate statistics
        total_from_strategies = sum(
            len(source_breakdown[s]) for s in source_breakdown if s != 'event'
        )

        stats = {
            "total_unique_edges": len(unified_list),
            "from_event": len(event_edges),
            "from_strategies": total_from_strategies,
            "by_strategy": {
                strategy_id: len(edges)
                for strategy_id, edges in source_breakdown.items()
                if strategy_id != 'event'
            }
        }

        return {
            "unified_edge_list": unified_list,
            "source_breakdown": source_breakdown,
            "statistics": stats
        }

    def validate_edges(
        self,
        edge_ids: List[str],
        network_file: Path
    ) -> Dict[str, any]:
        """
        Validate that edges exist in network file.

        Args:
            edge_ids: Edge IDs to validate
            network_file: Path to network .net.xml file

        Returns:
            Validation result:
            {
              "valid_edges": [...],
              "invalid_edges": [...],
              "success_rate": 0.95
            }
        """
        import xml.etree.ElementTree as ET

        valid = []
        invalid = []

        try:
            tree = ET.parse(network_file)
            root = tree.getroot()

            # Get all edge IDs from network
            network_edge_ids = set()
            for edge_elem in root.findall('.//edge'):
                edge_id = edge_elem.get('id')
                if edge_id:
                    network_edge_ids.add(edge_id)

            # Validate provided edges
            for edge_id in edge_ids:
                # Handle negative edges (usually not in network)
                check_id = edge_id[1:] if edge_id.startswith('-') else edge_id

                if check_id in network_edge_ids:
                    valid.append(edge_id)
                else:
                    invalid.append(edge_id)

            success_rate = len(valid) / len(edge_ids) if edge_ids else 0

            return {
                "valid_edges": valid,
                "invalid_edges": invalid,
                "success_rate": success_rate,
                "total_edges": len(edge_ids),
                "valid_count": len(valid),
                "invalid_count": len(invalid)
            }

        except Exception as e:
            self.logger.error(f"Error validating edges: {e}")
            return {
                "valid_edges": edge_ids,
                "invalid_edges": [],
                "success_rate": 1.0,
                "error": str(e)
            }
```

### 2. Enhanced SUMO Utils

**Location**: `shared/utilities/sumo_utils.py`

**New Function**: `generate_edgedata_xml_for_case()`

```python
def generate_edgedata_xml_for_case(
    edge_list: List[str],
    output_file: Path,
    frequency: int = 300,
    exclude_empty: bool = True,
    with_internal: bool = False
) -> str:
    """
    Generate edgeData.add.xml content with given edge list.

    Args:
        edge_list: List of edge IDs to monitor
        output_file: Path where XML will be saved
        frequency: Sampling frequency (seconds)
        exclude_empty: Exclude empty edges from output
        with_internal: Include internal edges

    Returns:
        XML content as string
    """
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<additional>
  <edgeData id="ed1"
    freq="{frequency}"
    file="edgedata/edgedata.xml"
    edges="{' '.join(edge_list)}"
    excludeEmpty="{'true' if exclude_empty else 'false'}"
    withInternal="{'true' if with_internal else 'false'}"/>
</additional>'''

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    return xml_content
```

**Modified Function**: `generate_sumocfg_for_simulation()`

```python
def generate_sumocfg_for_simulation(
    case_metadata: Dict[str, Any],
    simulation_type: str,
    simulation_folder: Path,
    case_root: Path,
    simulation_params: Dict[str, Any],
    use_shared_edgedata: bool = True  # NEW PARAMETER
) -> str:
    """
    Generate SUMO configuration.

    Args:
        use_shared_edgedata: If True, reference case/config/edgeData.add.xml
                           If False, use legacy per-simulation edgeData
    """
    # ... existing code ...

    # NEW: Handle edgeData configuration
    additional_files = []

    if simulation_params.get('output_edgedata', False):
        if use_shared_edgedata:
            # Reference shared edgeData from case config
            edgedata_path = rel_to_config / "edgeData.add.xml"
            additional_files.append(str(edgedata_path).replace('\\', '/'))
        else:
            # Legacy per-simulation edgeData (backward compat)
            # Generate edgeData in simulation folder
            edgedata_path = simulation_folder / "edgeData.add.xml"
            if edgedata_path.exists():
                additional_files.append("edgeData.add.xml")

    # ... rest of function ...
```

### 3. Case Service Enhancement

**Location**: `api/services/case_service.py`

**New Method**: `_generate_event_edgedata()`

```python
async def _generate_event_edgedata(
    self,
    case_path: Path,
    case_metadata: Dict[str, Any],
    scenarios: Optional[List[str]] = None
) -> None:
    """
    Generate unified edgeData.add.xml for event.

    Aggregates edges from:
    1. Event impact zone
    2. All control strategies in scenarios

    Args:
        case_path: Case directory path
        case_metadata: Case metadata with event info
        scenarios: List of scenario_ids (optional, can extract from request)

    Raises:
        Exception: If edge aggregation fails
    """
    from shared.utilities.edge_aggregator import EdgeImpactAggregator
    from shared.utilities.sumo_utils import generate_edgedata_xml_for_case

    try:
        event_id = case_metadata.get('event_id')
        logger.info(f"Generating unified edgeData for event {event_id}")

        # Initialize aggregator
        aggregator = EdgeImpactAggregator()

        # Step 1: Extract event impact edges
        event_edges = aggregator.aggregate_event_impact_edges(
            case_metadata,
            method="radius_2_hops"  # Configurable
        )

        logger.info(f"Event edges: {len(event_edges)} edges")

        # Step 2: Extract strategy impact edges
        # This requires loading strategy data for all scenarios
        strategy_edges = {}

        if scenarios:
            for scenario_id in scenarios:
                try:
                    scenario_strategies = self._load_scenario_strategies(
                        scenario_id,
                        case_metadata
                    )

                    for strategy_id, strategy_def in scenario_strategies.items():
                        strategy_edges_list = aggregator.aggregate_strategy_impact_edges(
                            {strategy_id: strategy_def}
                        )
                        strategy_edges.update(strategy_edges_list)

                except Exception as e:
                    logger.warning(f"Could not load strategies for {scenario_id}: {e}")

        logger.info(f"Strategy edges: {len(strategy_edges)} strategies")

        # Step 3: Merge all impacts
        merged = aggregator.merge_edge_impacts(event_edges, strategy_edges)
        unified_edge_list = merged['unified_edge_list']

        logger.info(f"Unified edge list: {len(unified_edge_list)} unique edges")

        # Step 4: Validate edges (optional but recommended)
        network_file = Path(case_metadata['files']['network_file'])
        validation = aggregator.validate_edges(unified_edge_list, network_file)

        if validation['success_rate'] < 0.8:
            logger.warning(f"Low validation rate: {validation['success_rate']}")

        # Step 5: Generate edgeData.add.xml
        edgedata_path = case_path / "config" / "edgeData.add.xml"
        generate_edgedata_xml_for_case(
            edge_list=unified_edge_list,
            output_file=edgedata_path,
            frequency=300,
            exclude_empty=True,
            with_internal=False
        )

        logger.info(f"EdgeData saved: {edgedata_path}")

        # Step 6: Update case metadata with aggregation info
        case_metadata['edgedata_config'] = {
            'generation_method': 'event_control_aggregation',
            'generated_at': datetime.now().isoformat(),
            'edge_aggregation': {
                'event_impact_method': 'radius_2_hops',
                'total_unique_edges': len(unified_edge_list),
                'from_event': len(event_edges),
                'from_strategies': sum(len(e) for e in strategy_edges.values()),
                'source_breakdown': merged['source_breakdown'],
                'validation': validation
            },
            'shared_config': True
        }

        self._save_case_metadata(case_path, case_metadata)

        logger.info(f"EdgeData configuration completed: {len(unified_edge_list)} edges")

    except Exception as e:
        logger.error(f"Error generating event edgeData: {e}", exc_info=True)
        raise

def _load_scenario_strategies(
    self,
    scenario_id: str,
    case_metadata: Dict[str, Any]
) -> Dict[str, Dict]:
    """
    Load strategy definitions for a scenario.

    Args:
        scenario_id: Scenario identifier
        case_metadata: Case metadata

    Returns:
        Dict mapping strategy_id → strategy_definition
    """
    from pathlib import Path
    import json

    strategies = {}

    # Try to load from scenario metadata
    event_type = case_metadata.get('event_type', '01_accident')
    scenario_dir = Path('output/scenarios') / event_type / scenario_id

    # Look for strategy configuration files
    # This depends on how strategies are stored in your project
    # Example: control_data/strategies/{strategy_type}/{strategy_name}.json

    # For now, return empty (can be enhanced based on actual structure)
    return strategies
```

**Modified Method**: `_get_or_create_event_case()`

```python
async def _get_or_create_event_case(
    self,
    event_id: str,
    event_type: str,
    network_file: str,
    od_file: str,
    taz_file: Optional[str],
    time_range: Dict[str, str],
    description: Optional[str] = None,
    scenarios: Optional[List[str]] = None  # NEW
) -> Tuple[Path, bool, Dict[str, Any]]:
    """
    Get existing event case or create new one.

    NEW: Generates unified edgeData if new case created

    Args:
        scenarios: List of scenario_ids for edge aggregation
    """
    case_id = f"case_event_{event_id}"
    case_path = Path("cases") / case_id
    metadata_file = case_path / "metadata.json"

    if case_path.exists() and (case_path / "config").exists():
        # ... reuse existing case ...
        with open(metadata_file, 'r', encoding='utf-8') as f:
            case_metadata = json.load(f)

        return case_path, False, case_metadata

    else:
        # ... create new case ...
        # ... create metadata ...

        # NEW: Generate unified edgeData for event
        if scenarios:
            await self._generate_event_edgedata(
                case_path=case_path,
                case_metadata=case_metadata,
                scenarios=scenarios
            )

        return case_path, True, case_metadata
```

---

## Data Flow

### Flow 1: Creating First Scenario (New Event Case)

```
User clicks "创建" for scenario_7180720_vss
  ↓
Frontend → Backend (POST /api/v1/scenario/create_case_with_simulation)
  ├─ scenario_id: "scenario_7180720_vss"
  ├─ event_id: "7180720"
  └─ strategy: "vss"
  ↓
Backend: create_case_with_simulation()
  ├─ Extract event_id: "7180720"
  ├─ Call _get_or_create_event_case("7180720")
  │  ├─ Check if case_event_7180720 exists → NO
  │  ├─ Create case directories
  │  ├─ Call _generate_event_edgedata()
  │  │  ├─ EdgeImpactAggregator.aggregate_event_impact_edges()
  │  │  │  └─ Extract edges: [3023, -3023, 3024, -3024, 3025, -3025, 3026, -3026, 3027, -3027]
  │  │  ├─ EdgeImpactAggregator.aggregate_strategy_impact_edges()
  │  │  │  └─ Extract VSS edges: [3000, -3000, 3001, -3001, ..., 3050, -3050]
  │  │  ├─ merge_edge_impacts()
  │  │  │  └─ Deduplicate: [3000, -3000, ..., 3050, -3050, 3023, -3023, ..., 3027, -3027]
  │  │  ├─ validate_edges() → Check against network file
  │  │  ├─ generate_edgedata_xml_for_case()
  │  │  │  └─ Create case/config/edgeData.add.xml with unified edge list
  │  │  └─ Update case metadata with aggregation info
  │  └─ Return (case_path, True, case_metadata)
  ├─ Call _create_scenario_simulation()
  │  ├─ Create simulation directory
  │  ├─ Copy scenario .add.xml
  │  ├─ Generate simulation.sumocfg
  │  │  └─ References: config/edgeData.add.xml (SHARED!)
  │  └─ Create output directories (edgedata/, e1/)
  └─ Return response
  ↓
Frontend receives:
{
  "case_id": "case_event_7180720",
  "simulation_id": "event_simulation_scenario_7180720_vss",
  "is_new_case": true,
  "edgedata_method": "event_control_aggregation",
  "total_edges_monitored": 124
}
```

### Flow 2: Creating Second Scenario (Same Event)

```
User clicks "创建" for scenario_7180720_tec
  ↓
Frontend → Backend
  ├─ scenario_id: "scenario_7180720_tec"
  └─ strategy: "tec"
  ↓
Backend: create_case_with_simulation()
  ├─ Extract event_id: "7180720"
  ├─ Call _get_or_create_event_case("7180720")
  │  ├─ Check if case_event_7180720 exists → YES
  │  ├─ Load existing metadata
  │  └─ Return (case_path, False, case_metadata)  ✅ edgeData ALREADY GENERATED
  ├─ Call _create_scenario_simulation()
  │  ├─ Create simulation directory
  │  ├─ Copy scenario .add.xml
  │  ├─ Generate simulation.sumocfg
  │  │  └─ References: config/edgeData.add.xml (REUSES SAME UNIFIED LIST!)
  │  └─ Create output directories
  └─ Return response
  ↓
Frontend receives:
{
  "case_id": "case_event_7180720",
  "simulation_id": "event_simulation_scenario_7180720_tec",
  "is_new_case": false,
  "edgedata_method": "event_control_aggregation",
  "total_edges_monitored": 124  ← SAME AS FIRST SCENARIO!
}
```

---

## Integration Points

### 1. Scenario Browser (Frontend)

**Display edge aggregation info**:
```javascript
// After successful case creation
if (response.is_new_case) {
    displayEdgeDataInfo({
        method: response.edgedata_method,
        total_edges: response.total_edges_monitored,
        monitoring_zones: [
            `Event impact: ${response.event_impact_edges} edges`,
            `VSS control: ${response.vss_impact_edges} edges`,
            `TEC control: ${response.tec_impact_edges} edges`,
            `DHS control: ${response.dhs_impact_edges} edges`
        ]
    });
}
```

### 2. Case Service Routes

**Response fields**:
```python
return {
    "case_id": case_id,
    "case_type": "event_based",
    "simulation_id": simulation_id,
    "is_new_case": is_new_case,
    # NEW FIELDS:
    "edgedata_config": {
        "generation_method": "event_control_aggregation",
        "total_unique_edges": 124,
        "source_breakdown": {
            "event_impact": 10,
            "vss_control": 102,
            "tec_control": 6,
            "dhs_control": 4
        }
    },
    "od_generation_status": "in_progress" if is_new_case else "completed",
    "status": "ready"
}
```

### 3. SUMO Configuration

**sumocfg.xml references**:
```xml
<additional-files value="config/dwd_od_weekly.rou.xml,config/edgeData.add.xml,config/TAZ_6.add.xml"/>
```

All simulations from same event reference the SAME `config/edgeData.add.xml`.

---

## API Changes

### Modified Endpoint

**POST `/api/v1/scenario/create_case_with_simulation`**

**Response** (new fields):

```json
{
  "case_id": "case_event_7180720",
  "case_type": "event_based",
  "simulation_id": "event_simulation_scenario_7180720_vss",
  "simulation_path": "cases/case_event_7180720/simulations/event_simulation_scenario_7180720_vss",
  "is_new_case": true,
  "od_generation_status": "in_progress",
  "edgedata_config": {
    "generation_method": "event_control_aggregation",
    "generated_at": "2025-11-15T10:30:00Z",
    "total_unique_edges": 124,
    "from_event_impact": 10,
    "from_strategy_controls": 114,
    "source_breakdown": {
      "event_impact": 10,
      "vss_incident_response": 102,
      "tec_entrance_control": 6,
      "dhs_utilization": 4
    },
    "shared_across_scenarios": true,
    "validation": {
      "valid_edges": 123,
      "invalid_edges": 1,
      "success_rate": 0.992
    }
  },
  "status": "ready",
  "message": "Case created successfully"
}
```

---

## Implementation Guide

### Step 1: Create EdgeImpactAggregator

```python
# shared/utilities/edge_aggregator.py
class EdgeImpactAggregator:
    # Implement all methods (see Component Design section)
```

### Step 2: Enhance sumo_utils.py

```python
# shared/utilities/sumo_utils.py
def generate_edgedata_xml_for_case(...):
    # NEW function

# Modify generate_sumocfg_for_simulation() signature
```

### Step 3: Enhance case_service.py

```python
# api/services/case_service.py
async def _generate_event_edgedata(...):
    # NEW method

# Modify _get_or_create_event_case():
    # Call _generate_event_edgedata() for new cases
```

### Step 4: Update routes (optional)

```python
# api/routes/scenario_routes.py
# Response includes new edgedata_config fields
```

---

## Error Handling

### Scenario 1: Event Data Missing

```python
try:
    event_edges = aggregator.aggregate_event_impact_edges(
        case_metadata,
        method="radius_2_hops"
    )
except KeyError:
    logger.warning("Event location data missing, falling back to fallback method")
    event_edges = []  # Empty list → SUMO monitors all edges
```

### Scenario 2: Strategy Data Unavailable

```python
try:
    strategy_edges = aggregator.aggregate_strategy_impact_edges(
        strategies_config
    )
except Exception as e:
    logger.warning(f"Strategy edge extraction failed: {e}")
    strategy_edges = {}  # Empty dict → only use event edges
```

### Scenario 3: Edge Validation Failures

```python
validation = aggregator.validate_edges(unified_edge_list, network_file)

if validation['success_rate'] < 0.8:
    logger.error(
        f"Low validation rate: {validation['success_rate']}\n"
        f"Invalid edges: {validation['invalid_edges'][:10]}"
    )
    # Decision: Fail or continue with warning?
    # Option A: Raise exception → user must fix metadata
    # Option B: Continue but log warning → graceful degradation
```

### Scenario 4: Concurrent Edge Generation

```python
# Handle case where multiple scenarios try to generate edgeData
# Solution: File locking (already implemented in case service)
```

---

## Testing Strategy

### Unit Tests

**Test File**: `tests/unit/test_edge_aggregator.py`

```python
class TestEdgeImpactAggregator:
    """Test edge aggregation logic."""

    def test_event_edges_immediate(self):
        """Test immediate method: primary + reverse."""
        aggregator = EdgeImpactAggregator()
        edges = aggregator._build_immediate_edges("3026")
        assert set(edges) == {"3026", "-3026"}

    def test_event_edges_radius_2_hops(self):
        """Test radius_2_hops method."""
        aggregator = EdgeImpactAggregator()
        edges = aggregator._build_radius_2_hop_edges("3026")
        assert len(edges) == 10  # ±2 hops × 2 directions + primary

    def test_vss_edge_extraction(self):
        """Test VSS strategy edge extraction."""
        # ...

    def test_merge_without_duplicates(self):
        """Test deduplication in merge."""
        # ...

    def test_validation_against_network(self):
        """Test edge validation."""
        # ...
```

### Integration Tests

**Test File**: `tests/integration/test_edgedata_generation.py`

```python
class TestEdgeDataGeneration:
    """Test edge data generation in case creation."""

    async def test_create_first_scenario_generates_edgedata(self):
        """First scenario triggers edgeData generation."""
        response = await create_case_with_simulation(
            scenario_id="scenario_7180720_vss",
            event_id="7180720",
            ...
        )

        assert response['is_new_case'] == True
        assert 'edgedata_config' in response
        assert response['edgedata_config']['total_unique_edges'] > 10

    async def test_create_second_scenario_reuses_edgedata(self):
        """Second scenario reuses edgeData."""
        # Create first scenario
        response1 = await create_case_with_simulation(...)
        edges1 = response1['edgedata_config']['total_unique_edges']

        # Create second scenario
        response2 = await create_case_with_simulation(
            scenario_id="scenario_7180720_tec",
            ...
        )

        assert response2['is_new_case'] == False
        # CRITICAL: Same edge list
        assert response2['edgedata_config']['total_unique_edges'] == edges1
```

### Performance Tests

**Test File**: `tests/performance/test_edgedata_performance.py`

```python
@pytest.mark.performance
def test_edge_aggregation_speed():
    """Edge aggregation should complete in < 500ms."""
    aggregator = EdgeImpactAggregator()

    start = time.time()
    aggregator.merge_edge_impacts(
        event_edges=[...] * 100,
        strategy_edges={f"s{i}": [...] * 50 for i in range(10)}
    )
    elapsed = time.time() - start

    assert elapsed < 0.5  # < 500ms
```

---

## Backward Compatibility

### For Existing Event-Based Cases

Cases created before edgeData enhancement:
- Still use old edgeData method (immediate or full_network)
- Can be migrated later via migration script
- No breaking changes

### For Time-Based Cases

Time-based cases unaffected:
- Continue using full_network method
- No edgeData aggregation applied
- Behavior identical to before

---

**Document Status**: Design Ready for Implementation
**Review Status**: Pending
**Implementation Status**: Not Started

