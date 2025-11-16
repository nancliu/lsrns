# Phase 1 Implementation Status - Case Consolidation

**Date**: 2025-11-15
**Status**: Preparation Complete - Ready for Code Changes
**Scope**: Consolidate 4 case creation endpoints → 2 clear workflows

---

## Change Summary

### Objective
Implement the cleanup plan from `CASE_AND_ANALYSIS_CLEANUP_GUIDE.md` Phase 1 to remove duplicate endpoints and consolidate into a clean 2-endpoint architecture.

### What's Being Changed

#### 1. API Routes (case_routes.py)

**Delete/Rename:**
```
OLD                              NEW                              REASON
================================================================
POST /api/v1/case/create_case/  POST /api/v1/case/               Rename for cleaner RESTful style
POST /api/v1/case/create-from-scenario     →  Consolidate into /from-event-scenario
POST /api/v1/case/quick-create-from-event →  DELETE (duplicate of above)
POST /api/v1/case/create-case-with-simulation  →  DELETE (auto-simulation is now standard)
```

**Final Endpoints:**
```
✅ POST   /api/v1/case                              # OD Workflow: Basic case creation
✅ POST   /api/v1/case/from-event-scenario        # Event Workflow: Case + auto-simulation
✅ GET    /api/v1/case                             # List cases
✅ GET    /api/v1/case/{case_id}                  # Get case details
✅ DELETE /api/v1/case/{case_id}                  # Delete case
✅ POST   /api/v1/case/{case_id}/clone            # Clone case
```

#### 2. Case Service (case_service.py)

**Consolidate Methods:**

| Old Methods | New Method | Purpose |
|-------------|-----------|---------|
| `create_case_from_scenario()` | `create_case_from_event_scenario()` | Create case from event scenario with auto-simulation |
| `quick_create_case_from_event()` | (merged into above) | - |
| `_get_or_create_event_case()` | (logic moved to unified method) | Internal logic consolidation |
| `_get_or_create_event_case_with_lock()` | (logic moved to unified method) | Locking handled in unified method |
| `create_case_with_simulation()` | (merged into above) | Auto-simulation now standard in event workflow |

**Keep Unchanged:**
```python
✅ create_case()  # OD workflow unchanged
✅ list_cases()
✅ get_case()
✅ delete_case()
✅ clone_case()
```

#### 3. Request/Response Models

**New Models Needed:**
```python
class CreateFromEventScenarioRequest(BaseModel):
    scenario_id: str
    simulation_duration_hours: float
    output_config: Optional[Dict] = None

class CaseCreationResponse(BaseModel):
    case_id: str
    case_type: str  # "event_based" | "od_extraction"
    simulation_id: Optional[str]
    metadata: Dict
    status: str  # "case_created" | "case_created_with_scenario"
```

#### 4. Simulation Routes (simulation_routes.py)

**Delete 4 Single-Simulation Endpoints:**
```
❌ POST /api/v1/simulation/
❌ GET  /api/v1/simulation/
❌ GET  /api/v1/simulation/{sim_id}
❌ POST /api/v1/simulation/{sim_id}/start
```

**Rationale**: Simulations are now created automatically when creating an event case. Batch simulation management will be handled by `EventSimulationService` (Phase 1.5).

---

## Implementation Order

### Stage 1: Service Layer (case_service.py)
1. Create new `create_case_from_event_scenario()` method
   - Extract common logic from 4 old methods
   - Add locking mechanism
   - Return proper response with simulation_id
2. Delete 4 old methods
3. Validate OD workflow (`create_case()`) still works

### Stage 2: Routes Layer (case_routes.py)
1. Consolidate case creation endpoints
   - Rename `POST /case/create_case/` → `POST /case/`
   - Merge scenario creation endpoints
2. Update request/response models
3. Delete old endpoints

### Stage 3: Clean Up (simulation_routes.py)
1. Delete 4 obsolete simulation endpoints
2. Add deprecation notes to any related documentation

### Stage 4: Documentation (change files)
1. Update `proposal.md` - Phase 1 completion
2. Update `design.md` - Remove deprecated methods
3. Update `tasks.md` - Mark Phase 1 complete
4. Update `CASE_AND_ANALYSIS_CLEANUP_GUIDE.md` - Implementation status

---

## Backward Compatibility

### What Stays the Same
✅ OD extraction workflow (`POST /api/v1/case/` with OD data)
✅ Case listing, deletion, cloning
✅ Existing cases continue to load
✅ Control plan optimization workflow

### What Changes
🔄 Event scenario workflow now uses single endpoint: `POST /api/v1/case/from-event-scenario`
🔄 Case response includes `simulation_id` for event cases
🔄 Simulation creation is now automatic (no separate endpoint)

### Migration Path
- **Old API clients** using old endpoints: Add adapter layer or update clients
- **Existing event cases**: No action needed (created via old endpoints still work)
- **New event cases**: Use `POST /api/v1/case/from-event-scenario`

---

## Data Flow - After Phase 1

```
Event Scenario Workflow:
┌─────────────────────────────────┐
│ POST /api/v1/case/from-event-scenario
├─────────────────────────────────┤
│ Input:
│  - scenario_id
│  - simulation_duration_hours
│  - output_config (optional)
├─────────────────────────────────┤
│ Processing:
│  1. Create case directory
│  2. Set up metadata v2.0 (with source_scenario)
│  3. Verify scenario exists
│  4. Generate rou.xml (MUST FIRST)
│  5. Generate sumocfg.xml (AFTER rou.xml)
│  6. Create simulation automatically
│  7. Store scenario lineage
├─────────────────────────────────┤
│ Output:
│  - case_id: "case_event_xxx"
│  - case_type: "event_based"
│  - simulation_id: "event_simulation_scenario_xxx"
│  - status: "case_created_with_scenario"
└─────────────────────────────────┘

Next Phase (1.5):
POST /api/v1/event-simulation/batch-start
├─ Batch launch created simulations
├─ Monitor progress
└─ Retrieve results
```

---

## Key Technical Notes

### rou.xml → sumocfg.xml Order (Critical!)
```python
# ❌ WRONG ORDER (causes errors):
generate_sumocfg()  # References rou.xml that doesn't exist yet
generate_rou()

# ✅ CORRECT ORDER:
generate_rou()      # Create route file first
generate_sumocfg()  # Then reference it in config
```

### edgedata.xml Smart Generation
When creating case from event scenario:
- Check if event + control strategy involves edge-level analysis
- If yes: Set output_config to generate edgedata.xml
- If no: Skip edgedata generation (save resources, simplify data)
- Document which simulations have edgedata available

---

## Files Affected

| File | Change Type | Details |
|------|-------------|---------|
| `api/routes/case_routes.py` | Modify | Consolidate endpoints |
| `api/services/case_service.py` | Modify | Create unified method, delete 4 old ones |
| `api/models/requests/case_requests.py` | Add | `CreateFromEventScenarioRequest` |
| `api/models/responses/*.py` | Modify | Update response models |
| `api/routes/simulation_routes.py` | Delete | Remove 4 single-sim endpoints |
| `proposal.md` | Update | Phase 1 completion status |
| `design.md` | Update | Architecture after consolidation |
| `tasks.md` | Update | Mark Phase 1 tasks complete |
| `CASE_AND_ANALYSIS_CLEANUP_GUIDE.md` | Update | Implementation status |

---

## Success Criteria

✅ **Endpoints**: 4 case endpoints → 2, 4 sim endpoints → 0
✅ **Code**: Service methods consolidated, duplicates removed
✅ **Tests**: All existing tests pass + new consolidation tests
✅ **Docs**: All change files updated and consistent
✅ **Compat**: Existing workflows unaffected

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Breaking OD workflow | Low | High | Test OD case creation thoroughly |
| Old API clients break | Medium | Medium | Provide migration guide in changelog |
| edgedata config issues | Low | Medium | Test both with/without edgedata |
| rou.xml/sumocfg order | Low | High | Add explicit comments and tests |

---

## Next Steps After Phase 1

Phase 1 completes the **case creation consolidation**. This enables:

✅ **Phase 1.5** (1 day): Implement `EventSimulationService` for batch simulation management
  - `POST /api/v1/event-simulation/batch-start`
  - `GET /api/v1/event-simulation/batch-progress/{batch_id}`
  - `GET /api/v1/event-simulation/batch-results/{batch_id}`

✅ **Phase 2** (2-3 days): Implement `EventSimulationAnalysisService` for comparative analysis
  - `POST /api/v1/event-simulation-analysis/run-comparison`
  - `GET /api/v1/event-simulation-analysis/progress/{batch_id}`
  - `GET /api/v1/event-simulation-analysis/results/{batch_id}`

---

## Sign-Off

Once all changes are complete and tests pass, mark this document as **COMPLETED** and update:
- `CASE_AND_ANALYSIS_CLEANUP_GUIDE.md` → "Phase 1: COMPLETED"
- `tasks.md` → Mark all Phase 1 tasks as complete
- `proposal.md` → Update Phase 1 status to deployed

Target: **2025-11-15 EOD or 2025-11-16 Morning**
