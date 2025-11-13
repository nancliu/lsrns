# enhance-morning-peak-control-plans Design Document

## Design Overview

This document outlines the architectural approach for generating 12-20 additional morning peak control plans for the G4202 and G5 highway network.

## Key Design Decisions

### DD-1: Systematic Plan Generation Approach

**Decision**: Use a parameterized generator pattern rather than manual plan creation

**Rationale**:
- Ensures systematic coverage of spatial-temporal parameter space
- Maintains consistency in plan structure and naming
- Enables reproducible plan generation
- Facilitates future plan extensions

**Implementation**:
```python
PlanGenerator(
    highway_segments=[...],
    time_intervals=[...],
    strategy_combinations=[...],
    severity_levels=[...]
) -> List[ControlPlan]
```

### DD-2: Unified Naming Convention for Plan Collection

**Decision**: Use consistent prefix `plan_morning_peak_g4202_` for all plans in the collection

**Naming Pattern**:
- ID Format: `plan_morning_peak_g4202_{strategy}_{location}_{severity}_v{n}`
- Chinese Name: `G4202早高峰{策略类型}{区段}{严重程度}综合管控方案V{n}`

**Examples**:
- `plan_morning_peak_g4202_vss_k0k20_moderate_v1` → "G4202早高峰VSS东段中度综合管控方案V1"
- `plan_morning_peak_g4202_vss_tec_k40k60_severe_v2` → "G4202早高峰VSS+TEC西段严重综合管控方案V2"
- `plan_morning_peak_g4202_full_composite_severe_v3` → "G4202早高峰全策略严重综合管控方案V3"

**Benefits**:
- Enables multi-selection through common prefix
- Supports regex pattern matching: `plan_morning_peak_g4202_*`
- Facilitates UI grouping and filtering
- Clear collection membership identification
- Version control support with `v{n}` suffix

### DD-3: Strategy Parameter Variation

**Decision**: Create three severity levels for each strategy type

**Severity Levels**:
1. **Mild**: Conservative parameters (minimal intervention)
   - VSS: Speed reduction 10-20%
   - TEC: Flow control 10-20%
   - DHS: Limited lane opening

2. **Moderate**: Balanced parameters (typical response)
   - VSS: Speed reduction 20-30%
   - TEC: Flow control 20-40%
   - DHS: Standard lane opening

3. **Severe**: Aggressive parameters (maximum intervention)
   - VSS: Speed reduction 30-50%
   - TEC: Flow control 40-60%
   - DHS: Full lane opening

**Rationale**:
- Covers full range of control intensities
- Enables optimization to find appropriate response level
- Matches real-world escalation protocols

### DD-4: Spatial Coverage Strategy

**Decision**: Divide highways into logical segments based on traffic patterns

**G4202 Segments**:
- K0-K20: Eastern section (high commuter traffic)
- K20-K40: Southern section (mixed traffic)
- K40-K60: Western section (industrial traffic)
- K60-K85: Northern section (interchange heavy)

**G5 Coverage**:
- Focus on interchange areas with G4202
- Include 2km upstream/downstream of interchanges
- Cover major on/off ramps

**Rationale**:
- Reflects actual traffic flow patterns
- Enables targeted control strategies
- Aligns with existing traffic monitoring infrastructure

### DD-5: Temporal Interval Design

**Decision**: Create overlapping time windows within morning peak

**Time Intervals**:
1. **Pre-peak ramp-up**: 6:30-7:30 (preparation phase)
2. **Early morning peak**: 7:00-8:00 (first wave)
3. **Core morning peak**: 7:30-9:00 (maximum load)
4. **Late morning peak**: 8:30-10:00 (second wave)
5. **Post-peak transition**: 9:30-10:30 (wind-down)

**Rationale**:
- Captures different traffic build-up patterns
- Enables proactive vs reactive strategy testing
- Provides smooth transitions between control periods

### DD-6: Strategy Combination Rules

**Decision**: Define valid strategy combinations and conflict resolution

**Combination Rules**:
1. **VSS + TEC**: Complementary (speed + flow control)
2. **VSS + DHS**: Complementary (speed + capacity)
3. **TEC + DHS**: Careful coordination (avoid bottlenecks)
4. **VSS + TEC + DHS**: Maximum intervention scenarios

**Conflict Resolution**:
- No overlapping VSS zones within 1km
- TEC points minimum 2km apart
- DHS segments must have continuous coverage
- Strategy priority: Safety > Flow > Efficiency

**Rationale**:
- Prevents conflicting control actions
- Ensures traffic flow coherence
- Maintains safety standards

## UI Integration Design

### Plan Collection Display
The comprehensive control plan collection will be displayed in the UI with:

1. **Collection Header**: "G4202早高峰综合管控方案集"
2. **Multi-Selection Support**:
   - Checkbox for each plan
   - "Select All Morning Peak" button
   - "Select by Strategy Type" filters (VSS/TEC/DHS)
   - "Select by Severity" filters (Mild/Moderate/Severe)

3. **Visual Organization**:
   - Group plans by strategy combination
   - Color-code by severity level
   - Show plan count badge: "20 plans available"
   - Preview tooltip on hover

4. **Batch Operations**:
   - "Run Selected Plans" for parallel simulation
   - "Compare Selected Plans" for ranking analysis
   - "Export Selected Plans" for documentation

## Data Model

### Control Plan Structure
```json
{
  "plan_id": "plan_morning_peak_g4202_vss_tec_k40k60_severe_v1",
  "plan_name": "G4202早高峰VSS+TEC西段严重综合管控方案V1",
  "collection": "morning_peak_g4202",
  "collection_name": "G4202早高峰综合管控方案集",
  "description": "针对G4202早高峰严重拥堵的复合管控方案",
  "metadata": {
    "highway": ["G4202", "G5"],
    "segments": ["K0-K20", "interchange_A"],
    "time_range": "07:00-09:00",
    "severity": "severe",
    "strategies": ["VSS", "TEC"],
    "expected_volume": "high",
    "optimization_goal": "minimize_delay"
  },
  "strategies": [
    {
      "strategy_id": "strat_xxx",
      "type": "VSS",
      "location": "G4202_K10",
      "parameters": {...}
    },
    {
      "strategy_id": "strat_yyy",
      "type": "TEC",
      "location": "G4202_K5",
      "parameters": {...}
    }
  ],
  "validation": {
    "network_validated": true,
    "xml_generated": true,
    "conflict_check": "passed"
  }
}
```

## Integration Points

### With Batch Optimization System
- Plans must be registered in `plans_index.json`
- Each plan requires `control.add.xml` generation
- Plan metadata must include batch-compatible fields
- Support for parallel execution with different random seeds

### With Control Strategy Ranking
- Plans must provide comparable metrics
- Strategy effectiveness tracking per plan
- Support for multi-criteria evaluation
- Results aggregation across plan variations

### With Event Scenario System
- Plans can be triggered by event scenarios
- Support for dynamic plan selection based on conditions
- Integration with scenario library for testing

## Performance Considerations

### Simulation Resource Management
- Each plan simulation requires ~500MB RAM
- 60 parallel simulations need ~30GB RAM
- CPU allocation: 75% of available threads
- I/O optimization for result file writing

### Plan Generation Performance
- Target: Generate all 20 plans in < 5 minutes
- XML validation: < 1 second per plan
- Metadata indexing: < 100ms per plan
- Batch preparation: < 30 seconds for 60 tasks

## Validation Strategy

### Plan Validation Levels
1. **Syntax Validation**: XML structure, JSON format
2. **Network Validation**: Edge/junction existence
3. **Strategy Validation**: Parameter ranges, conflicts
4. **Simulation Validation**: Test run with baseline case
5. **Performance Validation**: Metrics collection and comparison

### Validation Checkpoints
- Pre-generation: Template and network data validation
- During generation: Real-time constraint checking
- Post-generation: Complete plan validation
- Pre-simulation: Final compatibility check
- Post-simulation: Results verification