# EdgeData Incremental Update Design

**Issue Identified**: Sequential scenario creation causes inconsistent edge monitoring
**Date**: 2025-11-15
**Status**: Critical Design Amendment

---

## Problem Statement

### User Creation Pattern (Sequential)

Users don't create all scenarios at once. Typical workflow:

```
Day 1: Create scenario_7180720_no_control (baseline)
  └─ Run simulation, analyze results

Day 2: Create scenario_7180720_vss (test VSS strategy)
  └─ Compare with baseline

Day 3: Create scenario_7180720_dhs (test DHS strategy)
  └─ Compare all three

Day 4: Create scenario_7180720_tec (test TEC strategy)
  └─ Final comparison of all strategies
```

### Original Design Flaw

**Original approach** (one-time generation):

```
Day 1: scenario_no_control created
  ├─ Generate edgeData.add.xml
  │  └─ Includes: Event edges only [3023...3027] (10 edges)
  └─ All future scenarios use THIS edgeData

Day 2: scenario_vss created
  ├─ VSS edges [3000...3050] NOT included in edgeData!
  └─ Monitoring INCOMPLETE for VSS strategy

Day 3: scenario_dhs created
  ├─ DHS edges [4000, shoulder] NOT included in edgeData!
  └─ Monitoring INCOMPLETE for DHS strategy

Day 4: scenario_tec created
  ├─ TEC edges [5000...5002] NOT included in edgeData!
  └─ Monitoring INCOMPLETE for TEC strategy
```

**Result**: ❌ Inconsistent monitoring, unfair comparison, missing data

---

## Solution: Incremental Update Approach

### Core Principle

**Every time a new scenario is added to an event case**:
1. Extract edges from the NEW scenario's strategy
2. Merge with existing edge list
3. Regenerate edgeData.add.xml
4. Optionally: Flag existing simulations for re-run (or log warning)

### Data Flow

```
Day 1: Create scenario_no_control
  ├─ Event case created: case_event_7180720
  ├─ Extract edges:
  │  └─ Event impact: [3023...3027] (10 edges)
  │  └─ No control strategy: none
  ├─ Generate edgeData.add.xml v1:
  │  └─ edges="3023 -3023 3024 -3024 3025 -3025 3026 -3026 3027 -3027"
  │  └─ Total: 10 edges
  └─ Create simulation: event_simulation_scenario_7180720_no_control/

Day 2: Create scenario_vss
  ├─ Event case exists: case_event_7180720
  ├─ Load existing edgeData metadata
  ├─ Extract NEW strategy edges:
  │  └─ VSS control: [3000...3050] (102 edges)
  ├─ Merge with existing:
  │  └─ Old: [3023...3027] (10 edges)
  │  └─ New: [3000...3050] (102 edges)
  │  └─ Merged: [3000...3050, 3023...3027] (112 edges, deduplicated)
  ├─ UPDATE edgeData.add.xml v2:
  │  └─ edges="3000 -3000 3001 -3001 ... 3050 -3050 3023 -3023 ..."
  │  └─ Total: 112 edges
  ├─ Update case metadata:
  │  └─ edgedata_config.version = 2
  │  └─ edgedata_config.last_updated = "2025-11-15T10:30:00Z"
  │  └─ source_breakdown.vss_strategy = 102
  ├─ Create simulation: event_simulation_scenario_7180720_vss/
  └─ ⚠️ Flag previous simulation for re-run (optional)

Day 3: Create scenario_dhs
  ├─ Event case exists: case_event_7180720
  ├─ Load existing edgeData metadata (v2)
  ├─ Extract NEW strategy edges:
  │  └─ DHS control: [4000, 4000_shoulder, 3999] (4 edges)
  ├─ Merge with existing:
  │  └─ Old: [3000...3050, 3023...3027] (112 edges)
  │  └─ New: [3999, 4000, 4000_shoulder] (4 edges)
  │  └─ Merged: [3000...3050, 3023...3027, 3999, 4000, 4000_shoulder] (116 edges)
  ├─ UPDATE edgeData.add.xml v3:
  │  └─ Total: 116 edges
  ├─ Update case metadata:
  │  └─ edgedata_config.version = 3
  │  └─ source_breakdown.dhs_strategy = 4
  ├─ Create simulation: event_simulation_scenario_7180720_dhs/
  └─ ⚠️ Flag previous simulations for re-run (optional)

Day 4: Create scenario_tec
  ├─ Similar process...
  └─ Final edgeData.add.xml v4: 122 edges total
```

---

## Implementation Design

### Modified Component: EdgeImpactAggregator

**New Method**: `update_edgedata_for_new_scenario()`

```python
def update_edgedata_for_new_scenario(
    self,
    case_path: Path,
    case_metadata: Dict[str, Any],
    new_scenario_id: str,
    new_strategy_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update existing edgeData.add.xml with edges from new scenario.

    Args:
        case_path: Path to case directory
        case_metadata: Current case metadata
        new_scenario_id: ID of new scenario being added
        new_strategy_config: Strategy configuration for new scenario

    Returns:
        Updated edge aggregation info

    Workflow:
    1. Load existing edgeData.add.xml and parse current edge list
    2. Extract edges from new scenario's strategy
    3. Merge new edges with existing edges (deduplicate)
    4. Regenerate edgeData.add.xml with updated edge list
    5. Update case metadata with new version info
    6. Return updated aggregation info
    """
    # Load existing edgeData
    edgedata_file = case_path / "config" / "edgeData.add.xml"
    existing_edges = self._parse_existing_edgedata(edgedata_file)

    # Extract new strategy edges
    new_edges = self.aggregate_strategy_impact_edges(
        {new_scenario_id: new_strategy_config}
    )

    # Merge
    merged = self.merge_edge_impacts(
        event_edges=[],  # Already in existing_edges
        strategy_edges=new_edges
    )

    # Combine with existing
    all_edges = list(set(existing_edges + merged['unified_edge_list']))
    all_edges.sort()

    # Regenerate edgeData.add.xml
    from shared.utilities.sumo_utils import generate_edgedata_xml_for_case
    generate_edgedata_xml_for_case(
        edge_list=all_edges,
        output_file=edgedata_file,
        frequency=300,
        exclude_empty=True,
        with_internal=False
    )

    # Update metadata
    version = case_metadata.get('edgedata_config', {}).get('version', 0) + 1
    updated_info = {
        'version': version,
        'last_updated': datetime.now().isoformat(),
        'total_unique_edges': len(all_edges),
        'scenarios_included': list(case_metadata.get('scenarios', [])) + [new_scenario_id],
        'update_reason': f'Added scenario {new_scenario_id}'
    }

    return updated_info


def _parse_existing_edgedata(self, edgedata_file: Path) -> List[str]:
    """Parse existing edgeData.add.xml to extract edge list."""
    import xml.etree.ElementTree as ET

    if not edgedata_file.exists():
        return []

    tree = ET.parse(edgedata_file)
    root = tree.getroot()

    edgedata_elem = root.find('.//edgeData')
    if edgedata_elem is None:
        return []

    edges_attr = edgedata_elem.get('edges', '')
    if not edges_attr:
        return []  # All edges monitored

    return edges_attr.split()
```

### Modified Method: Case Service `_create_scenario_simulation()`

**Enhancement**: Check if edgeData needs updating

```python
async def _create_scenario_simulation(
    self,
    case_path: Path,
    case_metadata: Dict[str, Any],
    request: CreateCaseWithSimulationRequest
) -> Tuple[str, Path]:
    """
    Create simulation directory for a specific scenario.

    ENHANCEMENT: Update edgeData if new scenario adds strategy edges.
    """
    # ... existing code to create simulation directory ...

    # NEW: Update edgeData for new scenario
    if not is_new_case:  # Case already exists
        # Load strategy config for this scenario
        strategy_config = self._load_scenario_strategy_config(
            request.scenario_id,
            request.strategy
        )

        # Update edgeData with new strategy edges
        if strategy_config:
            from shared.utilities.edge_aggregator import EdgeImpactAggregator
            aggregator = EdgeImpactAggregator()

            updated_info = aggregator.update_edgedata_for_new_scenario(
                case_path=case_path,
                case_metadata=case_metadata,
                new_scenario_id=request.scenario_id,
                new_strategy_config=strategy_config
            )

            # Update case metadata
            case_metadata.setdefault('edgedata_config', {}).update(updated_info)
            self._save_case_metadata(case_path, case_metadata)

            logger.info(
                f"Updated edgeData.add.xml to v{updated_info['version']} "
                f"with {updated_info['total_unique_edges']} total edges"
            )

            # Optional: Flag previous simulations for re-run
            self._flag_simulations_for_rerun(case_path, case_metadata)

    # ... rest of existing simulation creation code ...
```

### New Method: Flag Simulations for Re-run (Optional)

```python
def _flag_simulations_for_rerun(
    self,
    case_path: Path,
    case_metadata: Dict[str, Any]
) -> None:
    """
    Mark existing simulations as needing re-run after edgeData update.

    This is OPTIONAL - depends on whether we want strict consistency.

    Options:
    1. AUTO RE-RUN: Delete old simulation outputs, force re-run
    2. FLAG ONLY: Mark simulation metadata with 'outdated_edgedata' flag
    3. LOG WARNING: Just log that edgeData was updated
    """
    simulations = case_metadata.get('simulations', {})
    edgedata_version = case_metadata.get('edgedata_config', {}).get('version', 1)

    for sim_id, sim_info in simulations.items():
        sim_dir = case_path / "simulations" / sim_id
        sim_metadata_file = sim_dir / "simulation_metadata.json"

        if sim_metadata_file.exists():
            with open(sim_metadata_file, 'r', encoding='utf-8') as f:
                sim_metadata = json.load(f)

            # Check if simulation was run with older edgeData version
            sim_edgedata_version = sim_metadata.get('edgedata_version', 0)

            if sim_edgedata_version < edgedata_version:
                # Mark as outdated
                sim_metadata['edgedata_outdated'] = True
                sim_metadata['edgedata_version_used'] = sim_edgedata_version
                sim_metadata['current_edgedata_version'] = edgedata_version
                sim_metadata['rerun_recommended'] = True

                with open(sim_metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(sim_metadata, f, ensure_ascii=False, indent=2)

                logger.warning(
                    f"Simulation {sim_id} used edgeData v{sim_edgedata_version}, "
                    f"current is v{edgedata_version}. Re-run recommended."
                )
```

---

## Case Metadata Structure

### Enhanced edgedata_config

```json
{
  "case_id": "case_event_7180720",
  "edgedata_config": {
    "version": 4,
    "generation_method": "incremental_update",
    "created_at": "2025-11-15T09:00:00Z",
    "last_updated": "2025-11-15T15:30:00Z",
    "update_history": [
      {
        "version": 1,
        "timestamp": "2025-11-15T09:00:00Z",
        "scenario_added": "scenario_7180720_no_control",
        "edges_added": 10,
        "total_edges": 10
      },
      {
        "version": 2,
        "timestamp": "2025-11-15T10:30:00Z",
        "scenario_added": "scenario_7180720_vss",
        "edges_added": 102,
        "total_edges": 112
      },
      {
        "version": 3,
        "timestamp": "2025-11-15T12:15:00Z",
        "scenario_added": "scenario_7180720_dhs",
        "edges_added": 4,
        "total_edges": 116
      },
      {
        "version": 4,
        "timestamp": "2025-11-15T15:30:00Z",
        "scenario_added": "scenario_7180720_tec",
        "edges_added": 6,
        "total_edges": 122
      }
    ],
    "source_breakdown": {
      "event_impact": 10,
      "vss_strategy": 102,
      "dhs_strategy": 4,
      "tec_strategy": 6
    },
    "current_edges": 122,
    "scenarios_included": [
      "scenario_7180720_no_control",
      "scenario_7180720_vss",
      "scenario_7180720_dhs",
      "scenario_7180720_tec"
    ]
  }
}
```

---

## Handling Re-runs

### Option 1: Strict Consistency (Recommended for Analysis)

**Policy**: When edgeData is updated, previous simulations MUST be re-run

```python
# In _flag_simulations_for_rerun()
if sim_edgedata_version < edgedata_version:
    # Delete old output
    output_dirs = ['edgedata', 'e1', 'tripinfo', 'vehroute']
    for output_dir in output_dirs:
        output_path = sim_dir / output_dir
        if output_path.exists():
            shutil.rmtree(output_path)
            logger.info(f"Deleted outdated output: {output_path}")

    # Mark simulation as pending re-run
    sim_metadata['status'] = 'pending_rerun'
    sim_metadata['rerun_reason'] = 'edgedata_updated'
```

**Frontend behavior**:
- Show warning: "EdgeData updated, simulation results outdated"
- Button: "Re-run Simulation"
- Disable analysis until re-run complete

### Option 2: Soft Warning (Less Strict)

**Policy**: Log warning but allow using old results

```python
# Just flag, don't delete
sim_metadata['edgedata_outdated'] = True
sim_metadata['rerun_recommended'] = True
```

**Frontend behavior**:
- Show warning icon
- Tooltip: "Simulated with older edge list (v2), current is v4"
- Allow analysis but show disclaimer

### Option 3: Automatic Re-run (Most Aggressive)

**Policy**: Automatically trigger re-run when edgeData updates

```python
# In _flag_simulations_for_rerun()
if sim_edgedata_version < edgedata_version:
    # Trigger async re-run
    self._trigger_async_rerun(sim_id, case_path)
```

---

## Recommended Implementation Strategy

### Phase 1: Basic Incremental Update (MUST HAVE)

✅ Implement `update_edgedata_for_new_scenario()`
✅ Update edgeData.add.xml when new scenario added
✅ Track version in case metadata
✅ Log update history

### Phase 2: Consistency Tracking (SHOULD HAVE)

✅ Mark simulations with edgeData version used
✅ Flag outdated simulations
✅ Warn users in frontend

### Phase 3: Auto Re-run (NICE TO HAVE)

⏳ Implement automatic re-run trigger
⏳ Queue management for re-runs
⏳ Progress tracking

---

## API Response Changes

### When Adding New Scenario to Existing Case

```json
{
  "case_id": "case_event_7180720",
  "simulation_id": "event_simulation_scenario_7180720_vss",
  "is_new_case": false,
  "edgedata_config": {
    "updated": true,
    "version": 2,
    "previous_version": 1,
    "edges_added": 102,
    "total_edges": 112,
    "update_timestamp": "2025-11-15T10:30:00Z",
    "scenarios_now_included": [
      "scenario_7180720_no_control",
      "scenario_7180720_vss"
    ]
  },
  "previous_simulations_status": {
    "affected_count": 1,
    "action": "flagged_for_rerun",
    "outdated_simulations": [
      "event_simulation_scenario_7180720_no_control"
    ]
  },
  "message": "Scenario added successfully. EdgeData updated to v2. Previous simulations should be re-run for consistency."
}
```

---

## User Workflow Example

### Scenario: User Creates Scenarios Over Multiple Days

**Day 1**: Create baseline
```
POST /api/v1/scenario/create_case_with_simulation
{
  "scenario_id": "scenario_7180720_no_control",
  "strategy": "no_control"
}

Response:
{
  "case_id": "case_event_7180720",
  "is_new_case": true,
  "edgedata_config": {
    "version": 1,
    "total_edges": 10,
    "source": ["event_impact"]
  }
}
```

**Day 2**: Add VSS strategy
```
POST /api/v1/scenario/create_case_with_simulation
{
  "scenario_id": "scenario_7180720_vss",
  "strategy": "vss"
}

Response:
{
  "case_id": "case_event_7180720",
  "is_new_case": false,
  "edgedata_config": {
    "updated": true,
    "version": 2,
    "total_edges": 112,
    "edges_added": 102
  },
  "previous_simulations_status": {
    "outdated": ["event_simulation_scenario_7180720_no_control"],
    "recommendation": "Re-run previous simulations for fair comparison"
  }
}
```

**Day 3**: User re-runs baseline
```
POST /api/v1/simulation/rerun/{simulation_id}

Result: Baseline simulation now uses updated edgeData (v2)
```

---

## Benefits of Incremental Update Approach

✅ **Flexibility**: Users can add scenarios over time
✅ **Consistency**: All scenarios eventually use same edge list
✅ **Transparency**: Version tracking shows when/why updates happened
✅ **Fair Comparison**: Final analysis uses consistent monitoring
✅ **User Control**: Users decide when to re-run simulations

---

## Trade-offs

### Incremental Update
**Pros**:
- Flexible (add scenarios anytime)
- Consistent final state
- Transparent version tracking

**Cons**:
- Requires re-running old simulations
- More complex implementation
- Version management overhead

### One-Time Creation
**Pros**:
- Simple implementation
- No re-runs needed
- No version tracking

**Cons**:
- ❌ Requires knowing all scenarios upfront
- ❌ Inconsistent monitoring if scenarios added later
- ❌ Unfair comparison across strategies

---

## Decision

✅ **RECOMMENDATION**: Implement Incremental Update with Soft Warning (Option 2)

**Rationale**:
1. Matches real user workflow (sequential scenario creation)
2. Maintains consistency across all scenarios
3. Provides transparency through version tracking
4. Allows users to decide when to re-run
5. Balances flexibility with data quality

**Implementation Priority**:
- Phase 1 (Basic Update): P0 (must have)
- Phase 2 (Tracking): P0 (must have)
- Phase 3 (Auto Re-run): P2 (nice to have)

---

**Status**: Design Amendment Complete
**Date**: 2025-11-15
**Impact**: Modifies Task 6.1, 6.3, 6.4 to include incremental update logic

