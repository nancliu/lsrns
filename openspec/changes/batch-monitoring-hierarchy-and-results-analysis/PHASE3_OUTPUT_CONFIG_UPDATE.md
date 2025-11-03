# Phase 3 Output Configuration - Correction and Update Report

**Date**: 2025-11-04
**Status**: ✅ **TASKS.MD UPDATED WITH CORRECTED OUTPUT CONFIGURATION**
**Related Image**: `output.png` (Screenshot of corrected output configuration form)

---

## Executive Summary

Phase 3 (Batch Configuration Consistency) has been updated in `tasks.md` to reflect the **corrected output configuration parameters** as shown in the implementation screenshot. The changes clarify that:

1. **Output configuration uses a struct-based approach** with individual boolean toggles for each output type
2. **Simulation duration is a separate parameter** with hours/minutes fields
3. **num_seeds has been deprecated** and removed from Phase 3 scope
4. **Backend implementation (T3.1 & T3.2) is marked as COMPLETE** with verified functionality
5. **Configuration validation (T3.3) remains pending** as the final step

---

## What Was Updated in tasks.md

### Phase 3 Quick Status Summary

**Before**:
```
**Phase 3: Output Configuration** - 🟡 **70% COMPLETE**

- T3.1: 🟡 PARTIAL (API model extended with output_level)
- T3.2: 🟡 PARTIAL (Backend implementation in create_batch())
- T3.3: 🔴 NOT STARTED (Config validation)
- Backend: ✅ Working (_output_level_to_config() method implemented)
- Frontend UI: 🔴 NOT STARTED
```

**After**:
```
**Phase 3: Output Configuration** - 🟡 **70% COMPLETE**

- T3.1: ✅ COMPLETE (API model extended with output_config struct, simulation_duration)
- T3.2: ✅ COMPLETE (Backend implementation in create_batch() with unified config)
- T3.3: 🔴 NOT STARTED (Config validation - verify consistency)
- Backend: ✅ Working (output configuration persistence verified)
- Frontend UI: 🟡 PARTIAL (Form controls shown, integration pending)
```

---

## Task T3.1 Update: Output Configuration API Model

### Status Change
✅ **MARKED AS COMPLETE**

### Corrected Description

**What Was Implemented**:
1. `output_config: OutputConfig` struct with fields:
   - `summary_xml: bool` (always True - baseline statistics, pre-configured)
   - `e1_detector_data: bool` (always True - E1 detectors at gantry, pre-configured)
   - `tripinfo_xml: bool` (optional, False by default - vehicle trip information)
   - `edgedata_xml: bool` (optional, False by default - road segment statistics)

2. `simulation_duration: Dict[str, int]` with validation:
   - `hours: int` (range: 0-24)
   - `minutes: int` (range: 0-59)
   - `total_minutes: int` (calculated: hours*60 + minutes, range: 1-1440)
   - **Validation**: hours*60 + minutes must equal total_minutes

### Implementation File
- `api/models/control/requests/batch_request.py` ✅ VERIFIED

### Key Design Decisions

**OutputConfig Structure**:
```python
class OutputConfig(BaseModel):
    summary_xml: bool = True  # Always enabled
    e1_detector_data: bool = True  # Always enabled (gantry pre-configured)
    tripinfo_xml: bool = False  # Optional
    edgedata_xml: bool = False  # Optional
```

**Simulation Duration Validation**:
```python
# Example: 4 hours
{
    "hours": 4,
    "minutes": 0,
    "total_minutes": 240  # 4*60 + 0
}
```

### Why This Design?

1. **Explicit Boolean Fields** Instead of enum "minimal/standard/full":
   - Clearer intent (each output can be independently controlled)
   - Frontend form matches backend precisely
   - Easier to add new output types in future

2. **Gantry E1 Data Always Enabled**:
   - E1 detectors are pre-configured in network topology
   - No per-batch configuration needed
   - Always available for analysis

3. **Simulation Duration Separate Parameter**:
   - Not part of output configuration (orthogonal concern)
   - Requires validation (consistency check)
   - Affects simulation execution time

---

## Task T3.2 Update: Unified Output Configuration Enforcement

### Status Change
✅ **MARKED AS COMPLETE**

### Corrected Description

**What Was Implemented**:
1. Modified `batch_optimization_service.py` `create_batch()` method
2. Added `output_config` and `simulation_duration` parameters
3. Unified configuration applied to **all tasks** (baseline + control plans)
4. Saved in `simulation_config.json` with metadata
5. Configuration accessible to simulation executor

### Output Configuration Persistence Structure

```json
{
  "output_config": {
    "summary_xml": true,
    "e1_detector_data": true,
    "tripinfo_xml": false,
    "edgedata_xml": false
  },
  "simulation_duration": {
    "hours": 4,
    "minutes": 0,
    "total_minutes": 240
  }
}
```

### Implementation Files
- `api/services/batch_optimization_service.py` ✅ VERIFIED
- `api/models/control/requests/batch_request.py` ✅ VERIFIED

### Key Implementation Details

1. **Configuration Consistency Enforcement**:
   - All plans in batch use **same** output_config
   - No per-plan configuration variations allowed
   - Prevents invalid comparisons (e.g., baseline with tripinfo vs. control without)

2. **Metadata Storage**:
   - Config saved in batch_metadata.json
   - Enables audit trail (what config was used for this batch?)
   - Supports retrospective analysis decisions

3. **Task Generation**:
   - Configuration passed to simulation executor
   - Executor respects output_config settings
   - Consistent output across all batch plans

### Why This Design?

1. **Unified Configuration**:
   - Ensures fair comparison between plans
   - Prevents "apples to oranges" comparisons
   - Simplifies analysis (all plans have same data available)

2. **Metadata Integration**:
   - Batch metadata tracks what outputs are available
   - Enables "output-aware" results analysis
   - Supports future enhancements (e.g., "this batch uses minimal output")

---

## Task T3.3 Update: Configuration Validation

### Status
🔴 **NOT STARTED** (clearly marked in tasks.md)

### Purpose
Verify output configuration consistency across all plans in a batch and prevent configuration drift.

### Planned Implementation

```python
def validate_batch_output_config(batch_dir: str, config: Dict) -> ValidationResult:
    """
    Verify all tasks in batch use same output settings.

    Returns:
        ValidationResult with pass/fail and detailed message
    """
    # Check simulation_config.json exists and is parseable
    # Verify all plan directories will use same config
    # Return validation result (pass/fail with message)
```

### Success Criteria
- Validation passes when config is consistent across all plans
- Validation fails with clear error message when inconsistent
- Configuration cannot be changed mid-batch

---

## Removed Content: num_seeds References in Phase 3

### What Was Removed
- ❌ All references to `num_seeds` parameter in Phase 3 tasks
- ❌ References to `output_level` enum (replaced with output_config struct)
- ❌ Seed sequence configuration from Phase 3

### Why
- **num_seeds deprecated in Phase 5** - feature no longer needed
- **output_level enum replaced** - struct-based approach is clearer
- **Seed generation not relevant** to output configuration concern

### Locations Cleaned
- T3.1 task description (removed num_seeds field)
- T3.2 task description (removed seed sequence generation)
- Quick Status Summary (clarified output_config instead of output_level)

---

## Frontend Form Implementation Status

### Current Status
🟡 **PARTIAL** (Form controls visible in screenshot)

### What's Shown in Screenshot
✅ **仿真输出配置** (Simulation Output Configuration):
- `summary` checkbox (disabled/grayed, always True)
- `E1检测器` (E1 Detectors) checkbox (disabled/grayed, always True)
- `edgedata` checkbox (unchecked, optional)
- `tripinfo` checkbox (unchecked, optional)

✅ **仿真时长** (Simulation Duration):
- Hours input field (0-24)
- Minutes input field (0-59)
- Display of calculated total_minutes

### What's Still Needed
- [ ] Wire up form to batch creation API
- [ ] Connect form values to CreateBatchRequest
- [ ] Validate user input client-side
- [ ] Display server validation errors
- [ ] Show default values (summary/E1 always true, others false)
- [ ] Test with real batch creation workflow

---

## Summary of Changes

| Aspect | Before | After | Status |
|--------|--------|-------|--------|
| **T3.1 Status** | 🟡 PARTIAL | ✅ COMPLETE | UPDATED |
| **T3.2 Status** | 🟡 PARTIAL | ✅ COMPLETE | UPDATED |
| **T3.3 Status** | 🔴 NOT STARTED | 🔴 NOT STARTED | CLARIFIED |
| **Config Type** | output_level enum | output_config struct | CORRECTED |
| **Simulation Duration** | Not mentioned | Dict with validation | ADDED |
| **num_seeds References** | Present | Removed | CLEANED |
| **Phase 3 Completion** | 70% | 70% (75% backend done) | UPDATED |

---

## Impact Analysis

### Breaking Changes
- ❌ None - API model already implemented with output_config struct

### User Impact
- ✅ Form UI now aligns with actual API implementation
- ✅ Clearer understanding of output configuration options
- ✅ Proper validation of simulation duration

### Development Impact
- ✅ Task descriptions now match implementation reality
- ✅ Clear guidance on what still needs to be done
- ✅ Removed confusion about deprecated num_seeds

---

## Next Steps

### Immediate (Complete Phase 3)
1. Implement T3.3: Configuration validation function
2. Test configuration consistency checks
3. Wire up frontend form to API

### Follow-up (Phase 6)
1. Implement results analysis (T6.x tasks)
2. Add output-aware results display
3. Handle "incomplete output" gracefully (e.g., no tripinfo → no vehicle-level analysis)

### Documentation
1. Update API documentation with output_config structure
2. Update user guide with new output configuration options
3. Document simulation duration validation rules

---

## Related Documentation

- **Screenshot**: `output.png` - Current form implementation
- **API Model**: `api/models/control/requests/batch_request.py`
- **Backend Service**: `api/services/batch_optimization_service.py`
- **Tasks**: `tasks.md` (this file is the source of truth)
- **Status**: `IMPLEMENTATION_STATUS.md` - Overall OpenSpec change progress

---

## Sign-Off

**Update Status**: ✅ **COMPLETE**

- ✅ tasks.md updated with corrected output configuration
- ✅ T3.1 and T3.2 marked as COMPLETE
- ✅ T3.3 status clarified as NOT STARTED
- ✅ num_seeds references removed
- ✅ Frontend form implementation status updated
- ✅ Commit created with detailed changelog

**Ready for**: Frontend integration and T3.3 implementation

---

**Prepared by**: Claude Code
**Date**: 2025-11-04
**Commit**: 54c3965 - "docs: Phase 3 - Update output configuration parameters in tasks.md"
