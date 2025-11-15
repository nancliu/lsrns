# Enhanced EdgeData Generation with Event & Control Impact Integration

**Change ID**: `edgedata-enhancement` (Sub-proposal of `event-based-case-architecture`)
**Status**: Proposal
**Created**: 2025-11-15
**Type**: Feature Enhancement
**Priority**: P1
**Scope**: edgeData generation, Shared configuration, Multi-scenario analysis

---

## Overview

### Problem Statement

Currently, `edgeData.add.xml` is generated simplistically:

1. **Smart Mode** (Event-based): Monitor only the primary event edge + reverse direction
   - Example: Event on edge `3026` → Monitor `[3026, -3026]` (2 edges)
   - **Limitation**: Ignores surrounding affected edges

2. **Fallback Mode** (Non-event): Monitor all edges in network
   - **Limitation**: Excessive data, poor performance, high database load
   - Example: Network with 5,000 edges → 5,000 edges monitored

### Ideal Behavior

**Should aggregate edge/lane lists from**:
1. **Event impact zone**: All edges affected by the event
   - Directly impacted: Event location edge + adjacent edges
   - Spillback effects: Upstream congestion propagation

2. **Control strategy impact zones**: All edges controlled by each strategy
   - VSS (Variable Speed Sign): Affected segments
   - TEC (Toll Entry Control): Entrance/exit edges
   - DHS (Dynamic Hard Shoulder): Hard shoulder segment edges

3. **Generate ONCE per event**: Create unified `edgeData.add.xml` shared across ALL scenarios
   - Saves processing time
   - Ensures consistent monitoring across strategies
   - Enables direct strategy comparison (same edges monitored)

### Proposed Solution

Implement **event-level edgeData aggregation** where:

- **1 Event → 1 Unified edgeData List → Multiple Simulations**
- **Aggregation**: Event edges + Control strategy edges → Single edge list
- **Storage**: `case/config/edgeData.add.xml` (per event, not per simulation)
- **Reuse**: All scenario simulations in same event case share the same edgeData configuration
- **Monitoring**: Smart selection (controlled set) instead of all edges

---

## Goals

### Primary Goals

1. **Accurate Monitoring**: Monitor all edges impacted by event + each control strategy
2. **Configuration Reuse**: Generate edgeData list once per event, shared across all scenarios
3. **Consistent Analysis**: All scenarios from same event monitor identical edge sets
4. **Improved Performance**: Monitor only relevant edges (not entire network)

### Secondary Goals

5. **Strategy Isolation**: Optional: Generate strategy-specific edgeData variants if needed
6. **Flexibility**: Support multiple impact zone definitions (radius, explicit list, etc.)
7. **Extensibility**: Allow custom edge lists per event

---

## Benefits

### Analysis Quality
- **Holistic View**: Monitor direct impacts + spillback + control effects
- **Fair Comparison**: All strategies monitored on same edge sets
- **Better Insights**: Identify secondary impacts beyond primary event location

### Resource Efficiency
- **Processing**: No duplicate edge aggregation for each scenario
- **Disk Space**: Single edgeData configuration per event
- **Performance**: Smaller datasets = faster SUMO simulation

### Operational Benefits
- **Clarity**: Clear relationship between event/strategy and monitored edges
- **Maintainability**: Single point of configuration per event
- **Scalability**: Works with any number of strategies per event

---

## Detailed Design

### Data Model

#### Event Edge Impact Definition

```json
{
  "event_id": "7180720",
  "event_type": "交通事故",
  "event_location": {
    "edge_id": "3026",
    "lane_id": "3026_1",
    "coordinates": {"x": 1000, "y": 2000}
  },
  "impact_zone": {
    "primary_edges": ["3026", "-3026"],
    "adjacent_edges": ["3025", "-3025", "3027", "-3027"],
    "spillback_edges": ["3024", "-3024", "3023", "-3023"],
    "all_impacted_edges": ["3023", "-3023", "3024", "-3024", "3025", "-3025", "3026", "-3026", "3027", "-3027"],
    "generation_method": "radius_2_hops"
  }
}
```

#### Control Strategy Impact Definition

```json
{
  "strategy_id": "vss_incident_response",
  "strategy_type": "VSS",
  "control_location": {
    "start_edge": "3000",
    "end_edge": "3050",
    "affected_edges": ["3000", "-3000", "3001", "-3001", ..., "3050", "-3050"]
  }
}
```

```json
{
  "strategy_id": "tec_entrance_control",
  "strategy_type": "TEC",
  "control_location": {
    "toll_entrance": "entrance_edge_5000",
    "affected_edges": ["5000", "-5000", "5001", "-5001", "5002", "-5002"]
  }
}
```

```json
{
  "strategy_id": "dhs_utilization",
  "strategy_type": "DHS",
  "control_location": {
    "dhs_segment": "dhs_segment_1",
    "main_edges": ["4000", "-4000"],
    "shoulder_edges": ["4000_shoulder", "-4000_shoulder"],
    "affected_edges": ["4000", "-4000", "4000_shoulder", "-4000_shoulder", "3999", "-3999"]
  }
}
```

#### Unified edgeData Configuration

```json
{
  "case_id": "case_event_7180720",
  "event_id": "7180720",
  "edgedata_config": {
    "version": "1.0",
    "generation_method": "event_control_aggregation",
    "generated_at": "2025-11-15T10:30:00Z",
    "edge_aggregation": {
      "from_event_impact": ["3023", "-3023", "3024", "-3024", "3025", "-3025", "3026", "-3026", "3027", "-3027"],
      "from_control_strategies": {
        "vss_incident_response": ["3000", "-3000", "3001", "-3001", ..., "3050", "-3050"],
        "tec_entrance_control": ["5000", "-5000", "5001", "-5001", "5002", "-5002"],
        "dhs_utilization": ["4000", "-4000", "4000_shoulder", "-4000_shoulder", "3999", "-3999"]
      },
      "unified_edge_list": [
        "3000", "-3000", "3001", "-3001", ..., "3050", "-3050",
        "3023", "-3023", "3024", "-3024", "3025", "-3025", "3026", "-3026", "3027", "-3027",
        "3999", "-3999", "4000", "-4000", "4000_shoulder", "-4000_shoulder",
        "5000", "-5000", "5001", "-5001", "5002", "-5002"
      ]
    },
    "monitoring_config": {
      "frequency": 300,
      "exclude_empty": true,
      "with_internal": false
    },
    "statistics": {
      "total_edges": 74,
      "event_edges": 10,
      "strategy_specific": {
        "vss_incident_response": 51,
        "tec_entrance_control": 6,
        "dhs_utilization": 5
      }
    }
  }
}
```

### Component Architecture

#### 1. Edge Impact Aggregator (NEW)

**Location**: `shared/utilities/edge_aggregator.py`

```python
class EdgeImpactAggregator:
    """Aggregate edge impacts from event and control strategies."""

    def aggregate_event_impact_edges(
        self,
        event_id: str,
        event_edge_id: str,
        method: str = "radius_2_hops"
    ) -> List[str]:
        """
        Get all edges affected by event.

        Methods:
        - "immediate": primary_edge + reverse
        - "radius_1_hop": primary + adjacent (±1 edge)
        - "radius_2_hops": primary + adjacent + spillback (±2 edges)
        - "explicit": load from event metadata

        Args:
            event_id: Event identifier
            event_edge_id: Primary event edge
            method: Impact calculation method

        Returns:
            List of affected edge IDs
        """
        pass

    def aggregate_strategy_impact_edges(
        self,
        scenario_id: str,
        strategy_type: str
    ) -> Dict[str, List[str]]:
        """
        Get all edges affected by control strategies in scenario.

        Args:
            scenario_id: Scenario identifier
            strategy_type: Strategy type (VSS, TEC, DHS, etc.)

        Returns:
            Dict mapping strategy_id → affected_edges
        """
        pass

    def aggregate_all_impacts(
        self,
        event_id: str,
        scenario_edges: Dict[str, List[str]]
    ) -> List[str]:
        """
        Merge event impacts + all strategy impacts into unified list.

        Handles:
        - Deduplication
        - Bidirectional edge handling
        - Sorting for consistency

        Args:
            event_id: Event identifier
            scenario_edges: Dict of strategy → edge lists

        Returns:
            Unified, deduplicated edge list
        """
        pass
```

#### 2. Enhanced SUMO Utils

**Location**: `shared/utilities/sumo_utils.py`

**Modified Function**: `generate_edgedata_for_case()`

```python
def generate_edgedata_for_case(
    case_root: Path,
    case_metadata: Dict[str, Any],
    edge_list: Optional[List[str]] = None,
    method: str = "event_control_aggregation"
) -> Path:
    """
    Generate edgeData.add.xml for a case.

    Args:
        case_root: Case directory path
        case_metadata: Case metadata (includes event_scenario info)
        edge_list: Optional pre-computed edge list
        method: Generation method:
          - "intelligent": event + strategy impact aggregation
          - "event_only": event edges only
          - "explicit": use provided edge_list
          - "full_network": all network edges (backward compat)

    Returns:
        Path to generated edgeData.add.xml
    """
    pass
```

#### 3. Case Service Enhancement

**Location**: `api/services/case_service.py`

**New Method**: `_generate_event_edgedata()`

```python
async def _generate_event_edgedata(
    self,
    case_path: Path,
    case_metadata: Dict[str, Any],
    scenarios: List[str]
) -> None:
    """
    Generate unified edgeData.add.xml for event.

    1. Extract event_id from first scenario
    2. Load event edge impact information
    3. Load all strategy impacts for scenarios
    4. Aggregate edges
    5. Generate edgeData.add.xml

    Args:
        case_path: Case directory
        case_metadata: Case metadata
        scenarios: List of scenario_ids in case
    """
    pass
```

### Data Flow

#### Scenario: Creating 4 Scenarios from Same Event

```
Event 7180720 (Traffic Accident on edge 3026)
├─ Impact zone: [3023, 3024, 3025, 3026, 3027] + reverses
│
├─ Scenario 1: scenario_7180720_vss
│  ├─ VSS Strategy: Affects edges [3000-3050]
│  └─ Control edges: [3000-3050] + reverses
│
├─ Scenario 2: scenario_7180720_tec
│  ├─ TEC Strategy: Affects toll entrance
│  └─ Control edges: [5000-5002] + reverses
│
├─ Scenario 3: scenario_7180720_dhs
│  ├─ DHS Strategy: Affects main + shoulder lanes
│  └─ Control edges: [4000, 4000_shoulder] + reverses
│
└─ Scenario 4: scenario_7180720_no_control
   └─ No strategy (baseline)

AGGREGATION:
Event edges: [3023, 3024, 3025, 3026, 3027] + reverses (10 edges)
VSS edges: [3000-3050] + reverses (102 edges)
TEC edges: [5000-5002] + reverses (6 edges)
DHS edges: [4000, 4000_shoulder] + reverses (4 edges)

UNIFIED LIST:
├─ Deduplicate: Remove overlaps
├─ Sort: For consistency
└─ Result: ~120 unique edges

STORAGE:
cases/case_event_7180720/config/edgeData.add.xml
  <edgeData edges="3000 -3000 3001 -3001 ... 5002 -5002" />

USAGE:
All 4 scenarios reference same edgeData.add.xml
├─ event_simulation_scenario_7180720_vss: SUMO uses unified list
├─ event_simulation_scenario_7180720_tec: SUMO uses unified list
├─ event_simulation_scenario_7180720_dhs: SUMO uses unified list
└─ event_simulation_scenario_7180720_no_control: SUMO uses unified list
```

### Implementation Steps

#### Phase 1: Infrastructure (2 days)

1. **Task 1**: Create `EdgeImpactAggregator` class
   - Methods for event impact extraction
   - Methods for strategy impact extraction
   - Merge/deduplicate logic

2. **Task 2**: Enhance `sumo_utils.generate_edgedata_for_case()`
   - Support multiple generation methods
   - Call aggregator to build edge lists
   - Generate XML with unified edge list

3. **Task 3**: Add metadata support
   - Store edge aggregation info in case metadata
   - Track generation method used
   - Record edge list statistics

#### Phase 2: Integration (2 days)

4. **Task 4**: Enhance Case Service
   - New method: `_generate_event_edgedata()`
   - Called during case creation for new event cases
   - Stores metadata about edge aggregation

5. **Task 5**: Update workflow
   - Modified `_get_or_create_event_case()` to generate edgeData
   - First scenario triggers full aggregation
   - Subsequent scenarios reuse aggregated config

6. **Task 6**: Frontend integration
   - Display edge aggregation info in scenario browser
   - Show monitoring zones for visualization
   - Warn if aggregation incomplete

#### Phase 3: Testing & Documentation (1.5 days)

7. **Task 7**: Comprehensive tests
   - Unit tests for aggregation logic
   - Integration tests for case creation
   - Performance benchmarks

8. **Task 8**: Documentation
   - Update API docs with edge aggregation details
   - Architecture diagrams showing edge flows
   - User guide for understanding edge monitoring

---

## Data Extraction Sources

### Event Edge Impact

**Source 1**: Event scenario metadata
- Location: `output/scenarios/{event_type}/scenario_{event_id}_*/event_description.json`
- Fields: `event_location.edge_id`, `event_location.impact_zone`

**Source 2**: Network file analysis
- Location: `templates/network_files/{network_name}.net.xml`
- Method: Parse XML to find adjacent edges
- Implementation: `shared/utilities/network_analyzer.py` (may exist or create)

### Control Strategy Edge Impact

**Source 1**: Strategy configuration files
- Location: `control_data/strategies/{strategy_type}/{strategy_id}.json`
- Fields: Define affected edge ranges for each strategy type

**Source 2**: Strategy XML files
- Location: Various control .add.xml files
- Method: Parse XML to extract controlled edges

**Source 3**: Case metadata during simulation creation
- Track which strategies are used
- Extract their control zones

---

## Configuration & Customization

### Edge Aggregation Methods

```python
EDGE_AGGREGATION_METHODS = {
    "immediate": {
        "description": "Only primary event edge + reverse",
        "edges": ["event_edge_id", "-event_edge_id"],
        "use_case": "Minimal monitoring, fastest"
    },
    "radius_1_hop": {
        "description": "Primary + adjacent edges (±1)",
        "edges": ["event_edge_id", "-event_edge_id", "adjacent_edges..."],
        "use_case": "Quick analysis"
    },
    "radius_2_hops": {
        "description": "Primary + adjacent + spillback (±2)",
        "edges": ["event_edge_id", "-event_edge_id", "adjacent...", "spillback..."],
        "use_case": "Standard incident analysis"
    },
    "explicit": {
        "description": "Use edges from event metadata",
        "edges": "from event_scenario.impact_zone.edge_list",
        "use_case": "Pre-defined impact zones"
    },
    "event_control_aggregation": {
        "description": "Event impact + all strategy controls",
        "edges": "merge(event_edges, strategy1_edges, strategy2_edges, ...)",
        "use_case": "Comprehensive multi-strategy comparison (RECOMMENDED)"
    }
}
```

### Case Metadata Extension

```json
{
  "case_id": "case_event_7180720",
  "edgedata_config": {
    "generation_method": "event_control_aggregation",
    "edge_aggregation": {
      "event_impact_method": "radius_2_hops",
      "from_event": 10,
      "from_strategies": 120,
      "total_unique_edges": 125
    }
  }
}
```

---

## Backward Compatibility

### Existing Cases

- Continue using original "immediate" or "full_network" methods
- No changes to existing case metadata
- Optional migration to new aggregation method

### API Compatibility

- New optional parameter: `edge_aggregation_method`
- Default: "event_control_aggregation" for new event-based cases
- Old behavior: "full_network" for legacy time-based cases

### SUMO Compatibility

- edgeData.add.xml format unchanged
- Only content (edge list) differs
- SUMO behavior identical

---

## Performance Impact

### Positive Impacts

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Monitored Edges (per scenario) | 5,000 (all) | ~125 (smart) | 97.5% reduction |
| Data Volume | ~500MB/scenario | ~6MB/scenario | 98.8% reduction |
| Simulation Speed | Baseline | +20-40% faster | Better performance |
| Analysis Time | Slow (large files) | Fast (small files) | 10-100x faster |

### Potential Considerations

- Initial aggregation: ~100ms per event (one-time cost)
- Network file parsing: Optional caching to reduce latency
- Strategy metadata loading: Negligible impact

---

## Risk Assessment

### Risk: Incomplete Edge Detection

**Mitigation**:
- Validate edge IDs against network file
- Warn if edges not found in network
- Provide fallback to larger radius

### Risk: Strategy Impact Data Missing

**Mitigation**:
- Graceful degradation if strategy metadata unavailable
- Fall back to event-only impact
- Log warnings for investigation

### Risk: Excessive Edge List

**Mitigation**:
- Implement limits on edge list size
- Warn if >500 edges included
- Allow manual override

### Risk: Performance Regression

**Mitigation**:
- Cache aggregation results in metadata
- Implement lazy loading of strategy data
- Performance tests required (Phase 3)

---

## Success Criteria

### Functional Requirements
- ✅ Edge aggregation combines event + all strategy impacts
- ✅ Unified edgeData.add.xml generated per event (not per scenario)
- ✅ All scenarios from same event share identical edge list
- ✅ Edge aggregation metadata stored in case metadata
- ✅ Backward compatible with existing cases

### Performance Requirements
- ✅ Edge aggregation completes in < 500ms per event
- ✅ Monitored edges reduced by ≥80% for event-based cases
- ✅ SUMO simulation speed improved by ≥15% due to smaller datasets

### Quality Requirements
- ✅ Unit test coverage >90%
- ✅ Integration tests verify multiple scenarios share edgeData
- ✅ Performance tests validate speed improvements
- ✅ Edge list validation tests ensure all edges exist in network

### Documentation Requirements
- ✅ Design document explaining aggregation logic
- ✅ API documentation updated with new fields
- ✅ Architecture diagrams showing edge flow
- ✅ User guide explaining edge aggregation benefits

---

## Timeline

### Phase 1: Infrastructure (2 days - Week 1)
- Implement EdgeImpactAggregator
- Enhance sumo_utils
- Add metadata support

### Phase 2: Integration (2 days - Week 1)
- Enhance Case Service
- Update workflow
- Frontend integration

### Phase 3: Testing & Docs (1.5 days - Week 2)
- Comprehensive tests
- Documentation
- Code review & refinement

**Total Effort**: 5.5 days
**Estimated Timeline**: 1 week (can overlap with current Phase tasks)

---

## Next Steps

1. **Stakeholder Review**: Confirm approach aligns with requirements
2. **Design Approval**: Review data model and architecture
3. **Task Breakdown**: Create detailed tasks.md entries
4. **Implementation**: Execute Phase 1-3 sequentially
5. **Validation**: Run performance & functionality tests

---

**Document Status**: Proposal - Ready for Review
**Author**: Claude Code
**Date**: 2025-11-15

