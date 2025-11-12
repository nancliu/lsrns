# Architecture Correction: Flat Structure for Event Scenario Simulations

**Date**: 2025-11-11
**Issue**: Original ARCHITECTURE_CHANGES.md proposed nested structure that would break existing simulation listing functionality
**Solution**: Use flat structure with naming convention

---

## Problem

### Original Proposal (INCORRECT)
```
cases/{case_id}/simulations/
└── scenario_sim_12547/         ← Scenario group (not a simulation)
    ├── sim_baseline/            ← Actual simulations
    ├── sim_with_event/
    └── sim_with_control_vss/
```

**Issues**:
- ❌ Existing API lists `simulations/*` as direct children
- ❌ Each directory in `simulations/` is expected to be a runnable simulation
- ❌ `scenario_sim_12547/` would be listed but cannot be executed
- ❌ Would require major refactoring of existing code

### Existing System (Must Maintain)
```
cases/{case_id}/simulations/
├── sim_1028_093903_micro/      ← Regular simulation
├── sim_1028_095159_micro/
└── simulations_index.json
```

**Current Behavior**:
- ✅ API iterates over `simulations/*` subdirectories
- ✅ Each subdirectory = one runnable simulation
- ✅ UI displays simulation list directly

---

## Solution: Flat Structure with Naming Convention

### Corrected Structure
```
cases/{case_id}/simulations/
├── sim_1028_093903_micro/           ← Existing regular simulations
├── scenario_12547_baseline/         ← Event scenario: baseline
├── scenario_12547_with_event/       ← Event scenario: event only
├── scenario_12547_vss/              ← Event scenario: event + VSS
├── scenario_12547_dhs/              ← Event scenario: event + DHS
└── simulations_index.json
```

### Naming Convention

**Regular Simulations** (existing):
- Pattern: `sim_{timestamp}_{type}/`
- Example: `sim_1028_093903_micro/`

**Event Scenario Simulations** (new):
- Pattern: `scenario_{event_id}_{variant}/`
- Variants:
  - `scenario_{id}_baseline` - No event, no control (baseline comparison)
  - `scenario_{id}_with_event` - Event only, no control
  - `scenario_{id}_{strategy}` - Event + control (vss/dhs/tec)

### Benefits

1. **✅ Zero Breaking Changes**
   - Existing API continues to work without modification
   - Each directory is still a runnable simulation
   - UI displays both regular and scenario simulations

2. **✅ Clear Identification**
   - Naming convention clearly distinguishes scenario simulations
   - Easy to filter: `scenario_*` vs `sim_*`

3. **✅ Logical Grouping**
   - Same event ID appears in related simulation names
   - Can query by `scenario_group` field in metadata

4. **✅ Metadata-Based Association**
   ```json
   // simulation_metadata.json
   {
     "simulation_id": "scenario_12547_vss",
     "scenario_group": "12547",  ← Links related simulations
     "scenario_variant": "vss",
     "scenario_event_type": "accident"
   }
   ```

---

## Implementation Guide

### When Creating Event Scenario Simulations

1. **Directory Naming**:
   ```python
   simulation_id = f"scenario_{event_id}_{variant}"
   simulation_folder = case_path / "simulations" / simulation_id
   ```

2. **Metadata Fields** (add to `simulation_metadata.json`):
   ```python
   metadata.update({
       "scenario_group": event_id,
       "scenario_variant": variant,  # baseline, with_event, vss, dhs, tec
       "scenario_event_type": event_type,  # accident, congestion, etc.
       "scenario_event_id": event_id,
       "scenario_control_strategy": strategy if variant not in ["baseline", "with_event"] else None
   })
   ```

3. **Filtering and Grouping**:
   ```python
   # Get all simulations for an event
   event_simulations = [s for s in simulations if s.get("scenario_group") == event_id]

   # Group by scenario
   from collections import defaultdict
   by_scenario = defaultdict(list)
   for sim in simulations:
       if "scenario_group" in sim:
           by_scenario[sim["scenario_group"]].append(sim)
   ```

---

## Comparison

| Aspect | Nested Structure | Flat Structure (CHOSEN) |
|--------|-----------------|-------------------------|
| **Compatibility** | ❌ Breaks existing API | ✅ Zero breaking changes |
| **Implementation** | ❌ Requires refactoring | ✅ Works immediately |
| **Listing** | ❌ Two-level iteration | ✅ Single-level iteration |
| **Identification** | ⚠️ Requires special handling | ✅ Clear naming convention |
| **Grouping** | ✅ Directory structure | ✅ Metadata field |
| **UI Changes** | ❌ Must update UI code | ✅ No UI changes needed |

---

## Updated Files

- ✅ `openspec/changes/add-event-scenario-sumo-configuration/ARCHITECTURE_CHANGES.md` - Corrected structure
- ✅ `shared/control_tools/scenario_sumocfg_generator.py` - Updated documentation
- ✅ `openspec/changes/add-event-scenario-sumo-configuration/ARCHITECTURE_CORRECTION.md` - This file

---

## Migration Notes

**No migration needed** - This correction was made before implementation, so no existing event scenario simulations exist to migrate.

**For future implementation**:
- Use flat structure with `scenario_{id}_{variant}/` naming
- Add `scenario_group` field to metadata
- Existing code requires no changes

---

**Status**: ✅ Architecture corrected and documented
**Date**: 2025-11-11
**Approved**: Ready for implementation
