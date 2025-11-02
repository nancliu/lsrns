# Phase 2 Preparation: Cascade Regeneration Implementation Plan

**Date Created**: 2025-11-02
**Status**: Preparation (Pre-Implementation)
**Target Timeline**: 1-2 weeks after Phase 1 completion
**Phase 1 Status**: ✅ COMPLETE (63/63 tests passing, >95% coverage, deployment-ready)

---

## Executive Summary

Phase 2 introduces **cascade regeneration** - the ability to automatically regenerate all plans' control.add.xml files when a strategy they reference is updated. This ensures data consistency across the system and prevents orphaned XML configurations.

**Key Objectives**:
- Track which plans reference which strategies
- Implement cascade regeneration logic (async)
- Add manual regeneration endpoint
- Maintain audit trail of cascade events
- Achieve zero data loss during updates

**Scope**: Strategy update workflow only (not creation or deletion at this phase)

---

## Current State Analysis (Pre-Phase 2)

### Existing Infrastructure

1. **Strategy Instance Storage** (`control_data/strategies/`)
   - Individual strategy JSON files (14 existing strategies)
   - Each strategy has `referenced_by` field (array of plan_ids)
   - Example: `strategy_real_vss_g4202_001.json` contains `"referenced_by": ["plan_20251102_130055_62386"]`

2. **Plan Metadata** (`control_data/plans/{plan_id}/plan_metadata.json`)
   - Contains `strategy_ids` array listing all strategies used
   - Example: `"strategy_ids": ["strategy_real_vss_g4202_001", "strategy_real_vss_g4202_002"]`
   - Already has `updated_at` timestamp

3. **Plan Index** (`control_data/plans/plans_index.json`)
   - Lists all plans with basic metadata
   - Can be used to enumerate plans for validation

4. **XML Generation** (`shared/control_tools/additional_generator.py`)
   - Phase 1 implementation: `generate_plan_additional()`
   - Produces control.add.xml for a given plan
   - Includes validation assertions
   - Handles all three strategy types (VSS, DHS, TEC)

### Missing Infrastructure

1. **Reverse Reference Index**
   - No centralized "strategy → plans that use it" mapping
   - Currently need to scan all plan metadata.json files to find dependents
   - **Solution needed**: Create `strategy_refs.json` or enhance existing `referenced_by` field

2. **Cascade Regeneration Logic**
   - No method to regenerate all dependent plans
   - No async/background task support for bulk operations
   - No progress tracking for multi-plan regeneration

3. **Manual Regeneration Endpoint**
   - No API endpoint to force XML regeneration
   - Useful for troubleshooting and manual fixes

4. **Audit Logging**
   - Minimal tracking of cascade events
   - No clear audit trail for debugging failed cascades

---

## Architecture Overview

### Three-Layer Cascade System

```
Layer 1: Strategy Update
    ↓
    Strategy update completes successfully
    ↓
Layer 2: Reference Discovery
    ↓
    Query: "Which plans use this strategy?"
    Result: [plan_id_1, plan_id_2, ...]
    ↓
Layer 3: Async Cascade Regeneration
    ↓
    For each referencing plan (parallel):
    - Load plan metadata
    - Load all strategies in plan
    - Generate new control.add.xml
    - Validate XML
    - Write to file
    - Log result
    ↓
Return to caller immediately (don't wait)
```

### Data Flow

```
User: PUT /api/v1/control/strategies/{strategy_id}
    ↓
StrategyInstanceService.update_strategy()
    ↓
    Validation: Parameter bounds, types ✓ (Phase 1)
    File update: Save strategy JSON ✓
    Index update: Update strategies_index.json ✓
    ↓
    NEW: Trigger cascade regeneration
    ├─ asyncio.create_task(self._cascade_regenerate_plans(strategy_id))
    └─ Return 200 with status: "update_complete, cascade_in_progress"
    ↓
Background: Cascade Regeneration Task
    ├─ Get all plans referencing this strategy
    ├─ For each plan: regenerate_plan_xml(plan_id)
    │  ├─ Load plan metadata
    │  ├─ Load all strategy instances
    │  ├─ Generate new control.add.xml
    │  ├─ Validate against SUMO schema
    │  ├─ Write to disk
    │  └─ Log result (success/failure)
    └─ Complete (failures don't block strategy update)
```

---

## Implementation Components

### Component 1: Strategy Reference Tracking

**File**: `control_data/strategies/strategy_refs.json` (NEW)

**Purpose**: Reverse index for quick lookup of plans using a strategy

**Format**:
```json
{
  "strategy_real_vss_g4202_001": {
    "referenced_by": ["plan_20251102_130055_62386", "plan_vss_morning_peak_severe"],
    "last_updated": "2025-11-02T13:00:55Z",
    "reference_count": 2
  },
  "strategy_real_vss_g4202_002": {
    "referenced_by": ["plan_20251102_130055_62386"],
    "last_updated": "2025-11-02T13:00:55Z",
    "reference_count": 1
  }
}
```

**Why separate file?**
- Fast lookup O(1) for "which plans use this strategy?"
- Efficient caching (entire file loaded once, reused for multiple operations)
- Distributed update management (single file, atomic writes)

**Initialization Task** (Phase 2.1):
- Scan all plan_metadata.json files
- For each plan, extract strategy_ids array
- Build reverse index
- Save to strategy_refs.json

**Maintenance**:
- Update when: Strategy assigned to plan, Strategy removed from plan, Plan created/deleted
- Keep both `strategy.referenced_by` and `strategy_refs.json` in sync

### Component 2: Cascade Regeneration Service

**File**: `api/services/control/cascade_regeneration_service.py` (NEW)

**Key Methods**:

```python
class CascadeRegenerationService:

    async def trigger_cascade_for_strategy(
        self,
        strategy_id: str,
        reason: str = "strategy_update"  # For audit trail
    ) -> CascadeRegenerationResult:
        """
        Trigger cascade regeneration for all plans using this strategy.

        Returns immediately - regeneration happens in background.

        Returns:
            CascadeRegenerationResult with status and plan list
        """

    async def _regenerate_plan_xml(
        self,
        plan_id: str,
        strategy_ids: List[str]
    ) -> PlanRegenerationResult:
        """
        Regenerate control.add.xml for a single plan.

        Includes:
        - Load all strategies
        - Call additional_generator.generate_plan_additional()
        - Validate XML
        - Write to disk
        - Log result
        """

    def _find_referencing_plans(
        self,
        strategy_id: str
    ) -> List[str]:
        """
        Find all plans that reference a given strategy.

        Queries strategy_refs.json for O(1) lookup.
        """

    async def _log_cascade_event(
        self,
        event_type: str,  # "cascade_start", "plan_regenerated", "cascade_complete"
        strategy_id: str,
        plan_id: Optional[str],
        result: Dict[str, Any]
    ) -> None:
        """
        Log cascade event for audit trail.

        Writes to: logs/cascade_audit.log
        """
```

**Implementation Details**:

1. **Async Processing**:
   - Use `asyncio.create_task()` from strategy update handler
   - Don't wait for completion
   - Return immediately to caller

2. **Parallel Execution**:
   - Use `asyncio.gather()` to regenerate multiple plans in parallel
   - Limit concurrency with `asyncio.Semaphore(max_parallel=3)`
   - Balance: speed vs. resource usage

3. **Error Handling**:
   - Cascade failures don't block strategy update
   - Each plan regeneration failure logged separately
   - Collect all failures, report summary
   - Retry logic: optional (deferred to Phase 3)

4. **Atomicity**:
   - Each plan XML written atomically (write to temp, move to final)
   - If validation fails: don't write file, log error
   - Prevent partial/corrupt XML on disk

### Component 3: Manual Regeneration Endpoint

**File**: `api/routes/control_plan_routes.py` (MODIFICATION)

**New Endpoint**:
```
POST /api/v1/control/plans/{plan_id}/regenerate-xml
```

**Purpose**: Force manual XML regeneration for a single plan

**Request**:
```json
{}
```

**Response** (200 OK):
```json
{
  "plan_id": "plan_20251102_130055_62386",
  "status": "regenerated",
  "generated_at": "2025-11-02T14:30:00Z",
  "strategies_count": 2,
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  }
}
```

**Response** (400 Bad Request):
```json
{
  "error": "XML validation failed",
  "validation_errors": [
    {
      "element": "variableSpeedSign",
      "type": "bounds_error",
      "message": "Speed 160 m/s exceeds maximum 50 m/s"
    }
  ]
}
```

**Use Cases**:
- Troubleshooting: Manually re-validate a plan's XML
- Recovery: Fix a plan after manual file edits
- Testing: Validate XML generation without changing strategies

### Component 4: Audit Logging System

**File**: `logs/cascade_audit.log` (NEW, git-ignored)

**Format**: Structured JSON lines
```json
{"timestamp": "2025-11-02T14:30:00Z", "event_type": "cascade_start", "strategy_id": "strategy_real_vss_g4202_001", "referencing_plans": 2}
{"timestamp": "2025-11-02T14:30:01Z", "event_type": "plan_regenerated", "plan_id": "plan_20251102_130055_62386", "strategy_id": "strategy_real_vss_g4202_001", "result": "success"}
{"timestamp": "2025-11-02T14:30:02Z", "event_type": "plan_regenerated", "plan_id": "plan_vss_morning_peak_severe", "strategy_id": "strategy_real_vss_g4202_001", "result": "success"}
{"timestamp": "2025-11-02T14:30:02Z", "event_type": "cascade_complete", "strategy_id": "strategy_real_vss_g4202_001", "successful": 2, "failed": 0}
```

**Purpose**: Debugging and compliance
- Track who triggered what cascade
- Identify failed regenerations
- Audit trail for data integrity

**Logging Locations**:
- Strategy update: Log that cascade was triggered
- Cascade start: Log plan list and strategy ID
- Each plan regeneration: Log success/failure + errors
- Cascade complete: Summary of results

---

## Pre-Implementation Checklist

### Phase 1 Verification ✅
- [x] All 63 tests passing
- [x] Code coverage >95%
- [x] All 14 strategies validated
- [x] XML validator implemented and tested
- [x] Parameter transformation validated

### Phase 2 Readiness ✅
- [x] Phase 1 Complete and Approved
- [x] Architecture documented
- [x] Data structures identified
- [x] Current state analyzed
- [x] Implementation plan prepared

### Ready to Implement: YES ✅

**Blockers**: None
**Dependencies**: Phase 1 (COMPLETE ✅)
**Estimated Effort**: 1-2 weeks

---

## Success Criteria for Phase 2

### Functional
- Strategy update triggers cascade regeneration
- All referencing plans' XML regenerated successfully
- Manual regeneration endpoint works
- Cascade failures logged, don't block strategy update
- Zero data loss during cascade

### Quality
- All existing tests continue to pass
- New integration tests for cascade (2-5 test cases)
- >95% code coverage on new cascade code
- All Phase 1 functionality unaffected

### Performance
- Strategy update response: <500ms (includes async trigger)
- Cascade regeneration: <5s per plan (for typical 3-strategy plan)
- Parallel regeneration: 3 plans simultaneously

### Documentation
- Cascade regeneration documented in CLAUDE.md
- API endpoint documented
- Troubleshooting guide created
- Audit log format documented

---

## Risk Assessment

### Low Risk
- Phase 1 provides solid foundation (xml_validator, parameter transformation)
- Strategy structure well-defined
- Plan metadata structure clear
- Async framework already in place (FastAPI)

### Medium Risk
- Race conditions: Multiple concurrent updates to same strategy
  - **Mitigation**: File locking (Python's fcntl on Linux, msvcrt on Windows)

- Cascade cascades: If plan XML regeneration triggers another update
  - **Mitigation**: Prevent re-entrancy with flag or audit check

### Low Impact Risks
- Audit log file grows large over time
  - **Mitigation**: Rotate logs (e.g., daily rotation)

- Parallel regeneration resource exhaustion
  - **Mitigation**: Semaphore limits concurrency

---

## Detailed Implementation Tasks (Phase 2)

### 2.1: Initialize Strategy Reference Index
- [ ] Create `control_data/strategies/strategy_refs.json` template
- [ ] Write initialization script: scan all plans, build reverse index
- [ ] Run initialization script
- [ ] Verify strategy_refs.json contains all current references

### 2.2: Implement Cascade Regeneration Service
- [ ] Create `api/services/control/cascade_regeneration_service.py`
- [ ] Implement `trigger_cascade_for_strategy()` - async entry point
- [ ] Implement `_regenerate_plan_xml()` - single plan regeneration
- [ ] Implement `_find_referencing_plans()` - reference lookup
- [ ] Implement `_log_cascade_event()` - audit logging
- [ ] Add error handling and retry logic
- [ ] Add unit tests (5-8 test cases)

### 2.3: Integrate Cascade into Strategy Update
- [ ] Modify `strategy_instance_service.update_strategy()`
- [ ] After successful strategy save: trigger cascade via asyncio.create_task()
- [ ] Return immediately with cascade status
- [ ] Maintain backward compatibility with one-step updates

### 2.4: Add Manual Regeneration Endpoint
- [ ] Create response model: `PlanRegenerationResponse`
- [ ] Add route: `POST /api/v1/control/plans/{plan_id}/regenerate-xml`
- [ ] Implement: Load plan, regenerate XML, validate, write
- [ ] Add error handling (404 if plan not found, 400 if validation fails)
- [ ] Document in code comments

### 2.5: Implement Audit Logging
- [ ] Create `logs/` directory (git-ignored)
- [ ] Implement cascade audit logging
- [ ] Log to both file and logger
- [ ] Include: timestamp, event_type, strategy_id, plan_id, result, errors

### 2.6: Create Tests for Phase 2
- [ ] Test: Strategy update triggers cascade
- [ ] Test: All referencing plans regenerated successfully
- [ ] Test: Cascade failure doesn't block strategy update
- [ ] Test: Manual regeneration endpoint
- [ ] Test: Audit logging records all events
- [ ] Test: Reference index stays in sync

### 2.7: Documentation
- [ ] Update CLAUDE.md with cascade regeneration section
- [ ] Document manual regeneration endpoint
- [ ] Create troubleshooting guide for failed cascades
- [ ] Document audit log format

---

## Timeline Estimate

| Task | Duration | Dependencies |
|------|----------|--------------|
| 2.1 - Reference Index | 1-2 hours | Phase 1 complete |
| 2.2 - Cascade Service | 3-4 hours | Reference index ready |
| 2.3 - Integration | 1-2 hours | Cascade service ready |
| 2.4 - Manual Endpoint | 1-2 hours | Cascade service ready |
| 2.5 - Audit Logging | 1 hour | Services ready |
| 2.6 - Testing | 2-3 hours | All services ready |
| 2.7 - Documentation | 1-2 hours | Implementation complete |
| **TOTAL** | **10-16 hours** | ~1.5-2 weeks (including review, fixes) |

---

## Notes for Implementation

### Synchronization Strategy
- Both `strategy.referenced_by` (in strategy JSON) and `strategy_refs.json` must stay in sync
- When adding/removing plan: update both places
- Consider using helper function: `_sync_strategy_references(strategy_id, plan_ids)`

### Atomicity Guarantees
- Strategy update: Atomic file write (save strategy, update index)
- Plan XML regeneration: Write to temp file, then atomic rename
- Audit logging: Append-only (least likely to corrupt)

### Performance Optimization
- Cache strategy_refs.json in memory (reload on strategy updates)
- Use `asyncio.gather()` with semaphore for parallel regeneration
- Batch operations (e.g., load multiple plans in one directory scan)

### Future Phases (Post Phase 2)
- **Phase 3**: Documentation & migration guide
- **Phase 4**: Network topology validation (optional)
- **Phase 5**: Retry logic and recovery mechanisms
- **Phase 6**: Cascade cascade prevention (complex cascades)

---

## Approval Status

**Phase 2 Preparation**: ✅ COMPLETE
**Status**: Ready for implementation upon user approval
**Blockers**: None
**Next Step**: User confirmation to proceed with Phase 2 implementation

---

**Created**: 2025-11-02
**Prepared by**: OpenSpec validation framework
**For**: validate-strategy-xml-generation OpenSpec change

