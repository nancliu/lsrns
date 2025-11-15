# Decision Q16: Where to Store Simulation Scenario Metadata

**Decision Date**: 2025-11-13
**Priority**: P0 (Completes AD-12 Three-Level Tracking)
**Status**: ✅ DECIDED (Recommendation: Extend simulation_metadata.json)

---

## Problem Statement

When a simulation is created from an event scenario case, we need to track the scenario lineage so that:
- Users can trace analysis results back to original scenario
- System can show "from scenario X with strategy Y" in simulation UI
- Complete metadata chain: Analysis → Simulation → Case → Scenario

**Question**: Where should we store `source_scenario` information in the simulation?

**Options**:
1. **Option A**: Add `source_scenario` field to existing `simulation_metadata.json`
2. **Option B**: Create new `simulation_scenario_metadata.json` file
3. **Option C**: Extend `od_file_info.json` with scenario fields

---

## Option Comparison

### Option A: Extend simulation_metadata.json ✅ RECOMMENDED

**Pros**:
- ✅ Single file = single source of truth for simulation metadata
- ✅ Follows v2.0 metadata pattern (consistent with case metadata)
- ✅ No new files = simpler file structure
- ✅ Tools can read one file for complete simulation context
- ✅ Backward compatible: optional field, v1.0 simulations unaffected
- ✅ Aligns with AD-12 (all metadata in one place per level)

**Cons**:
- Slightly larger file (adds ~5-10 lines for scenario info)

**Implementation**:
```json
{
  "metadata_version": "2.0",
  "simulation_id": "sim_20251113_120530",
  "case_id": "case_20251113_120000",
  "created_at": "2025-11-13T12:05:30",

  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故",
    "control_strategy_type": "NO_CONTROL"
  },

  ... (rest of simulation metadata)
}
```

**Current Status**: `simulation_metadata.json` already has optional fields; v2.0 can extend this

---

### Option B: Create od_scenario_metadata.json

**Pros**:
- Separation of concerns: scenario info separate from simulation config

**Cons**:
- ❌ Creates additional file to manage
- ❌ Harder to maintain consistency (scenario info in two places?)
- ❌ Tools need to read two files for complete context
- ❌ Unclear file naming: "od_scenario" suggests OD-specific, but applies to all simulations
- ❌ Increases file complexity without clear benefit
- ❌ Violates "single source of truth" principle

**File Structure** (Not Recommended):
```
cases/case_id/simulations/sim_id/
├── simulation_metadata.json
├── simulation.sumocfg
├── od_scenario_metadata.json (NEW - extra file)
└── outputs/
```

---

### Option C: Extend od_file_info.json

**Pros**:
- Can use existing file update patterns

**Cons**:
- ❌ Mixes concerns: OD file info + scenario lineage (doesn't belong together)
- ❌ od_file_info.json is for data source references, not scenario metadata
- ❌ Not all simulations have od_file_info.json (only OD extraction cases)
- ❌ Event scenario simulations should have scenario metadata regardless of OD source
- ❌ Conceptually wrong: scenario linkage ≠ OD file information
- ❌ Harder to discover (users looking at simulation_metadata.json won't find it)

**File Structure** (Not Recommended):
```json
{
  "od_file": "dwd.dwd_od_weekly",
  "time_range": {...},
  "scenario": {  // ❌ Scenario info in OD file config?
    "scenario_id": "scenario_10754_no_control"
  }
}
```

---

## Decision: Option A ✅

**Rationale**:

1. **Consistency**: Matches pattern in case metadata (v2.0 includes source_scenario)

2. **Simplicity**: One file per metadata level
   - Case Level: metadata.json (case + source_scenario)
   - Simulation Level: simulation_metadata.json (simulation + source_scenario)
   - Analysis Level: analysis_metadata.json (analysis + source_scenario)

3. **Backward Compatibility**: Optional field
   - Old simulations without source_scenario still work
   - v2.0 simulations add optional field

4. **Architecture Alignment**: AD-12 Three-Level Tracking
   ```
   Level 1: Case metadata.json
   ├─ source_scenario: {...}

   Level 2: Simulation simulation_metadata.json
   ├─ source_scenario: {...}

   Level 3: Analysis analysis_metadata.json
   ├─ source_scenario: {...}
   ```

5. **Tool Usability**: Single file read gets complete context

---

## Implementation Plan

### When: During Simulation Creation

**File**: `shared/data_processors/simulation_processor.py`

**Code** (Example):
```python
def create_simulation_metadata(case_id, case_metadata, sim_id, config):
    """
    Create v2.0 simulation metadata with scenario lineage

    Args:
        case_metadata: Case metadata (includes source_scenario if v2.0)
        sim_id: Simulation ID
        config: Simulation configuration

    Returns:
        Simulation metadata with optional source_scenario field
    """

    metadata = {
        "metadata_version": "2.0",
        "simulation_id": sim_id,
        "case_id": case_id,
        "created_at": datetime.now().isoformat(),

        # NEW: Copy scenario lineage from case if available
        "source_scenario": case_metadata.get("source_scenario"),

        # Existing fields
        "simulation_params": config,
        "status": "pending",
        "input_files": {...},
        ...
    }

    return metadata
```

### Detection of v2.0 Cases

During simulation creation, check if case is v2.0:

```python
def is_v2_case(case_metadata):
    """Check if case has v2.0 metadata with source_scenario"""
    return (
        case_metadata.get("metadata_version") == "2.0" and
        case_metadata.get("source_scenario") is not None
    )

# In create_simulation_metadata:
if is_v2_case(case_metadata):
    simulation_metadata["source_scenario"] = case_metadata["source_scenario"]
    simulation_metadata["metadata_version"] = "2.0"
else:
    # v1.0 case: no source_scenario, simulation is v1.0 compatible
    simulation_metadata["metadata_version"] = "1.0"
```

---

## Three-Level Metadata Chain (Complete)

### Level 1: Case Metadata
```json
{
  "metadata_version": "2.0",
  "case_id": "case_20251113_120000",
  "case_name": "Morning Peak Accident Control",

  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故",
    "control_strategy_type": "NO_CONTROL"
  },
  ...
}
```

### Level 2: Simulation Metadata
```json
{
  "metadata_version": "2.0",
  "simulation_id": "sim_20251113_120530",
  "case_id": "case_20251113_120000",

  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故",
    "control_strategy_type": "NO_CONTROL"
  },

  "scenario_config": {
    "event_description": {...},
    "control_strategy_config": {...}
  },

  ...
}
```

### Level 3: Analysis Metadata
```json
{
  "metadata_version": "2.0",
  "analysis_batch_id": "analysis_batch_20251113_130000",
  "case_id": "case_20251113_120000",
  "simulation_id": "sim_20251113_120530",

  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故"
  },

  ...
}
```

**Traceability**: Analysis → Simulation → Case → Scenario ✅

---

## Backward Compatibility

| Case Type | Case Metadata | Simulation Metadata | Result |
|-----------|---------------|-------------------|--------|
| v2.0 Event Scenario | Has source_scenario | Inherits source_scenario | ✅ Full lineage |
| v1.0 OD Extraction | No source_scenario | No source_scenario | ✅ Unchanged behavior |

---

## File Structure (Final)

```
cases/case_id/
├── metadata.json                          ← source_scenario (if v2.0)
├── simulations/
│   └── sim_id/
│       ├── simulation_metadata.json        ← source_scenario (NEW, if v2.0)
│       ├── simulation.sumocfg
│       └── outputs/
│           └── summary.xml
└── analysis/
    └── batch_id/
        ├── analysis_metadata.json         ← source_scenario (if v2.0)
        ├── edgedata/
        └── tripinfo/

// NO new files created ✅
// Only one new optional field in simulation_metadata.json ✅
```

---

## Questions Addressed

### Q: What if case is v1.0 (no source_scenario)?
**A**: Simulation will also be v1.0 (no source_scenario field). Backward compatible.

### Q: What if simulation created from UI, not API?
**A**: SimulationService checks case metadata. If case is v2.0, simulation gets v2.0.

### Q: Can users update source_scenario in simulation?
**A**: Should be read-only (immutable after creation). Analysis services never modify.

### Q: How do analysis results link back to scenario?
**A**: Analysis metadata copies source_scenario from simulation. Full chain preserved.

---

## Decision Summary

| Aspect | Decision |
|--------|----------|
| **Storage Location** | `simulation_metadata.json` |
| **Field Name** | `source_scenario` |
| **Version** | v2.0 metadata (optional, backward compatible) |
| **Copy Strategy** | Copy from case_metadata during simulation creation |
| **File Structure** | One file per metadata level (case, simulation, analysis) |
| **Implementation** | Extend SimulationService during simulation creation |

---

## Next Steps

1. ✅ **Implement** in SimulationService when creating v2.0 simulations
2. ✅ **Test** that v2.0 cases → v2.0 simulations with source_scenario
3. ✅ **Verify** that v1.0 cases → v1.0 simulations (backward compat)
4. ✅ **Update** analysis services to preserve source_scenario lineage
5. ✅ **Document** in CLAUDE.md under AD-12

---

## References

- **AD-12**: Three-Level Metadata Tracking (this decision completes it)
- **AD-7**: 1:1 Case-Scenario Binding
- **AD-8**: Configuration Override Policy
- **v2.0 Metadata**: Defined in design.md (proposal.md section 1)

---

**Decision**: ✅ Extend `simulation_metadata.json` with `source_scenario` field
**Rationale**: Consistency, simplicity, backward compatibility
**Status**: Ready for implementation
**Owner**: SimulationService enhancement during Phase 2
