# Phase 1 Cleanup Implementation Plan

**Date**: 2025-11-15
**Status**: In Progress
**Base Document**: CASE_AND_ANALYSIS_CLEANUP_GUIDE.md
**Goal**: Consolidate duplicate API endpoints and implement unified case creation workflow

---

## Summary

Phase 1 cleanup consolidates 4 case creation endpoints into 2 clear workflows:
1. **OD Workflow**: `POST /api/v1/case/` (基础创建)
2. **Event Workflow**: `POST /api/v1/case/from-event-scenario` (事件场景创建，自动创建仿真)

## Current State (Duplicates)

### Duplicate Case Creation Endpoints (4 → 2)

| Current Endpoint | Service Method | Purpose | Status |
|------------------|----------------|---------|--------|
| `POST /api/v1/case/create_case/` | `create_case()` | OD extraction | ✅ Keep (rename) |
| `POST /api/v1/case/create-from-scenario` | `quick_create_case_from_event()` | Event scenario | ❌ Duplicate |
| `POST /api/v1/case/quick-create-from-event` | `quick_create_case_from_event()` | Event scenario (duplicate) | ❌ DELETE |
| `POST /api/v1/case/create-case-with-simulation` | `create_case_with_simulation()` | Unified (redundant) | ❌ DELETE |

### Duplicate Service Methods (5 → 2)

**CaseService methods to consolidate:**
```python
❌ _get_or_create_event_case()
❌ _get_or_create_event_case_with_lock()
❌ create_case_from_scenario()
❌ quick_create_case_from_event()

✅ create_case() - Keep as is
✅ create_case_from_event_scenario() - NEW unified method (replaces 4 above)
```

### Duplicate Simulation Endpoints (4 → 0)

**These endpoints should be deleted** (simulation creation now automatic via case creation):
```
❌ POST /api/v1/simulation/          # Create simulation
❌ GET  /api/v1/simulation/          # List simulations
❌ GET  /api/v1/simulation/{sim_id}  # Get simulation details
❌ POST /api/v1/simulation/{sim_id}/start  # Start simulation
```

---

## Implementation Steps

### Step 1: Update Case Routes (api/routes/case_routes.py)

**Changes:**
1. Rename endpoint: `/create_case/` → `/` (make it `POST /api/v1/case`)
2. Consolidate: `/create-from-scenario` and `/quick-create-from-event` → `/from-event-scenario`
3. Delete: `/create-case-with-simulation` endpoint

**Before:**
```python
@router.post("/create_case/")
async def create_case(request: CaseCreationRequest):
    ...

@router.post("/create-from-scenario")
async def create_case_from_scenario(request: EventScenarioQuickCreateRequest):
    ...

@router.post("/quick-create-from-event")
async def quick_create_case_from_event(request: EventScenarioQuickCreateRequest):
    ...

@router.post("/create-case-with-simulation")
async def create_case_with_simulation(request: CreateCaseWithSimulationRequest):
    ...
```

**After:**
```python
@router.post("/", response_model=BaseResponse)
async def create_case(request: CaseCreationRequest):
    # OD Workflow: Basic case creation

@router.post("/from-event-scenario", response_model=BaseResponse)
async def create_case_from_event_scenario(request: CreateFromEventScenarioRequest):
    # Event Workflow: Create case + auto-create simulation
    # Returns: { case_id, simulation_id, case_type: "event_based", status }
```

### Step 2: Update Case Service (api/services/case_service.py)

**Changes:**
1. Keep `create_case()` unchanged (OD workflow)
2. Create new `create_case_from_event_scenario()` (unified event workflow)
3. Delete 4 old methods: `_get_or_create_event_case()`, `_get_or_create_event_case_with_lock()`, `create_case_from_scenario()`, `quick_create_case_from_event()`
4. Move critical logic into the new unified method with clear locking

**Method signature:**
```python
async def create_case_from_event_scenario(
    self,
    request: CreateFromEventScenarioRequest
) -> CaseCreationResponse:
    """
    从事件场景创建案例并自动创建仿真。

    这是 Phase 2 事件场景工作流的主要入口。
    替代：create_case_from_scenario() + quick_create_case_from_event()

    Returns:
        case_id: "case_event_{event_id}"
        simulation_id: "event_simulation_scenario_{scenario_id}"
        case_type: "event_based"
        status: "case_created_with_scenario"
    """
```

### Step 3: Update Request/Response Models

**New Request Model:**
```python
class CreateFromEventScenarioRequest(BaseModel):
    scenario_id: str  # 场景ID
    simulation_duration_hours: float  # 仿真时长
    output_config: Optional[Dict] = None  # 输出配置
```

**Response Model:**
```python
class CaseCreationResponse(BaseModel):
    case_id: str
    case_type: str  # "event_based" | "od_extraction"
    simulation_id: Optional[str]  # Only for event_based
    metadata: Dict
    status: str  # "case_created" | "case_created_with_scenario"
```

### Step 4: Update Simulation Routes (api/routes/simulation_routes.py)

**Delete 4 endpoints:**
```python
❌ @router.post("/") - Create simulation
❌ @router.get("/") - List simulations
❌ @router.get("/{sim_id}") - Get details
❌ @router.post("/{sim_id}/start") - Start simulation
```

**Note:** Simulation creation now happens automatically in case creation (Phase 1.5)

### Step 5: Update Documentation Files

Files to update in the change directory:
- [ ] `proposal.md` - Update Phase 1 scope
- [ ] `design.md` - Update architecture diagram
- [ ] `tasks.md` - Mark Phase 1 tasks as complete
- [ ] `CASE_AND_ANALYSIS_CLEANUP_GUIDE.md` - Update implementation status

---

## Acceptance Criteria

### Endpoint Consolidation
- [ ] `POST /api/v1/case/` works for OD workflow (basic case creation)
- [ ] `POST /api/v1/case/from-event-scenario` works for event workflow (case + auto-simulation)
- [ ] Old endpoints return 404 (properly deleted)

### Service Consolidation
- [ ] `CaseService.create_case()` unchanged, still works for OD workflow
- [ ] `CaseService.create_case_from_event_scenario()` works, handles all event scenarios
- [ ] Old methods (`quick_create_case_from_event`, etc.) are deleted
- [ ] No service errors when loading old cases

### API Consistency
- [ ] Endpoint naming follows RESTful style (no trailing slashes)
- [ ] Request/Response models are clearly named
- [ ] Response includes all required fields (case_id, simulation_id if applicable, status)

### Backward Compatibility
- [ ] Existing OD workflow cases still load and work
- [ ] No changes to OD case creation behavior
- [ ] No changes to control plan or batch optimization workflows

---

## Testing Checklist

Before marking Phase 1 as complete:

### Unit Tests
- [ ] Test: Create OD case via `POST /api/v1/case/`
- [ ] Test: Create event case via `POST /api/v1/case/from-event-scenario`
- [ ] Test: Event case automatically gets simulation_id
- [ ] Test: Event case metadata includes scenario lineage

### Integration Tests
- [ ] Test: List cases shows both OD and event cases
- [ ] Test: Get event case includes simulation info
- [ ] Test: Clone event case works correctly

### Manual Tests
- [ ] Old OD case loading still works
- [ ] New event case creation through both endpoints returns identical results
- [ ] API documentation reflects new endpoints

---

## Rollback Plan (if needed)

If issues arise:
1. Revert commits to case_routes.py and case_service.py
2. Restore deleted methods from git history
3. Re-add old endpoints with deprecation warnings

---

## Status

**Phase 1 Cleanup Status**: 🔄 IN_PROGRESS

- [ ] Routes updated
- [ ] Service consolidated
- [ ] Models updated
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Ready for Phase 1.5 (Batch Simulation Management)

---

## Next Phases (after Phase 1)

- **Phase 1.5**: Implement batch simulation startup and monitoring (`EventSimulationService`)
- **Phase 2**: Implement comparative analysis (`EventSimulationAnalysisService`)
- **Phase 3**: API naming normalization

**Estimated Timeline**: Phase 1 (2 hours) → Phase 1.5 (1 day) → Phase 2 (2-3 days)
