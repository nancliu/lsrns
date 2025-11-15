# Phase 1 Implementation Analysis & Detailed Change Plan

**Date**: 2025-11-15
**Status**: Analysis Phase
**Objective**: Provide detailed, line-by-line implementation guidance for Phase 1 cleanup

---

## Current State Analysis

### Case Service Method Locations

Based on grep analysis of case_service.py (2160 lines):

**Methods to DELETE:**
1. `_get_or_create_event_case()` - Line 213
2. `_get_or_create_event_case_with_lock()` - Line 319
3. `create_case_from_scenario()` - Line 951
4. `quick_create_case_from_event()` - Line 1068
5. `create_case_with_simulation()` - Line 1521

**Methods to KEEP:**
1. `create_case()` - Line 33 (OD Workflow - UNCHANGED)
2. `list_cases()` - Unchanged
3. `get_case()` - Unchanged
4. `delete_case()` - Unchanged
5. `clone_case()` - Unchanged

**Helper Methods to Preserve:**
- `_create_standard_directories()` - Used in case creation
- `_create_v2_metadata_from_scenario()` - Used in v2.0 case creation
- `_create_od_table()` - Used in OD generation
- Other helper methods referenced by consolidation logic

### Case Routes Endpoint Locations

Based on case_routes.py:

**Endpoints to DELETE:**
1. `@router.post("/create-from-scenario")` - Line 81
2. `@router.post("/quick-create-from-event")` - Line 100
3. `@router.post("/create-case-with-simulation")` - Line 119

**Endpoints to RENAME:**
1. `@router.post("/create_case/")` - Line 23 → Should become `@router.post("/")`

**Endpoints to KEEP:**
- `/list_cases/`
- `/case/{case_id}`
- `DELETE /case/{case_id}`
- `/case/{case_id}/clone`

---

## Key Technical Decisions

### 1. Which Method Becomes the Unified Event Method?

The `create_case_with_simulation()` method (line 1521) is the **most complete** implementation:
- ✅ Handles event-based architecture
- ✅ Implements locking for thread safety
- ✅ Manages case reuse across scenarios
- ✅ Returns complete response with simulation_id
- ✅ Handles OD generation async
- ✅ Updates scenario index

**Decision**: Rename `create_case_with_simulation()` → `create_case_from_event_scenario()`

### 2. Request Model Consolidation

**Current Models:**
- `EventScenarioQuickCreateRequest` - Used by two old endpoints
- `CreateCaseWithSimulationRequest` - Used by create_case_with_simulation

**New Unified Request Model:**
```python
class CreateFromEventScenarioRequest(BaseModel):
    # Combines fields from both old request types
    # Fields from EventScenarioQuickCreateRequest
    scenario_id: str
    case_name: str
    network_file: str
    od_file: str  # Can be file path or database table ref
    taz_file: str
    event_type: str
    strategy: str
    description: Optional[str] = None

    # Fields from CreateCaseWithSimulationRequest
    simulation_duration_hours: Optional[float] = None
    output_config: Optional[Dict] = None
    case_id: Optional[str] = None
```

### 3. Response Model Consolidation

**New Unified Response:**
```python
class CaseCreationResponse(BaseModel):
    case_id: str
    case_type: str  # "event_based" | "od_extraction"
    simulation_id: Optional[str]  # Required for event cases
    case_dir: Optional[str]
    metadata: Dict
    status: str  # "case_created" | "case_created_with_scenario"
    is_new_case: Optional[bool]  # For event cases (case reuse)
```

---

## Implementation Strategy

### Phase 1A: Prepare (No Code Changes Yet)

1. ✅ Analyze current code structure
2. ✅ Identify dependencies between methods
3. ✅ Create unified request/response models
4. ✅ Document backward compatibility concerns

### Phase 1B: Model Changes (Safe, Non-Breaking)

**Step 1**: Create new unified request model
- Add `CreateFromEventScenarioRequest` to `api/models/requests/case_requests.py`
- Keep old models for now (backward compat)

**Step 2**: Create new unified response model
- Add `CaseCreationResponse` to `api/models/responses/`
- Keep old response models (backward compat)

### Phase 1C: Routes Changes (Safe)

**Step 1**: Add new unified endpoints (non-breaking addition)
```python
@router.post("/", response_model=BaseResponse)
async def create_case_od(request: CaseCreationRequest):
    # OD Workflow - RENAMED endpoint

@router.post("/from-event-scenario", response_model=BaseResponse)
async def create_case_from_event_scenario(request: CreateFromEventScenarioRequest):
    # Event Workflow - NEW unified endpoint
```

**Step 2**: Update old endpoints to deprecation warnings
```python
# Mark old endpoints as deprecated but keep them working
# They'll route to new endpoints internally
```

**Step 3**: Once tested, remove old endpoints

### Phase 1D: Service Changes (Main Work)

**Step 1**: Rename method
- `create_case_with_simulation()` → `create_case_from_event_scenario()`
- Update method signature to accept new `CreateFromEventScenarioRequest`
- Update internal request handling

**Step 2**: Delete unused methods
- `_get_or_create_event_case()` - Logic now in renamed method
- `_get_or_create_event_case_with_lock()` - Locking still in renamed method
- `create_case_from_scenario()` - Functionality merged into renamed method
- `quick_create_case_from_event()` - Functionality merged into renamed method
- ~~`create_case_with_simulation()`~~ - Renamed, not deleted

**Step 3**: Verify dependencies
- Ensure no other code calls deleted methods
- Update any references to old method names

### Phase 1E: Testing (Comprehensive)

**Unit Tests:**
- Test OD case creation still works (POST /)
- Test event case creation works (POST /from-event-scenario)
- Test event case gets simulation_id
- Test backward compat with old cases

**Integration Tests:**
- Test list_cases shows both types
- Test case cloning for both types
- Test scenario index updates

**Manual Tests:**
- Create OD case via API
- Create event case via API
- Verify responses include all required fields

### Phase 1F: Simulation Routes Changes

Delete 4 obsolete endpoints from `simulation_routes.py`:
- `POST /api/v1/simulation/`
- `GET /api/v1/simulation/`
- `GET /api/v1/simulation/{sim_id}`
- `POST /api/v1/simulation/{sim_id}/start`

**Reason**: Simulation creation is now automatic via case creation

---

## Dependency Analysis

### What Depends on Deleted Methods?

Using grep analysis:

**`_get_or_create_event_case()`**: Called from:
- `create_case_with_simulation()` (will be renamed)
- → Safe to delete after consolidation

**`_get_or_create_event_case_with_lock()`**: Called from:
- `create_case_with_simulation()` (will be renamed)
- → Safe to delete after consolidation

**`create_case_from_scenario()`**: Called from:
- Routes endpoint at line 81
- → Safe to delete after endpoint consolidation

**`quick_create_case_from_event()`**: Called from:
- Routes endpoint at line 100
- Routes endpoint at line 81 (indirect)
- → Safe to delete after endpoint consolidation

**`create_case_with_simulation()`**: Called from:
- Routes endpoint at line 119
- → RENAME to create_case_from_event_scenario

### What Depends on Renamed Method?

`create_case_with_simulation()` → `create_case_from_event_scenario()`:
- Route endpoint at line 119
- → Must update route to call new name

---

## Backward Compatibility Plan

### Preservation Strategy

1. **OD Workflow (create_case)**: Zero changes
   - POST `/api/v1/case/create_case/` → POST `/api/v1/case/`
   - Same method, same behavior, just renamed endpoint
   - Existing cases continue to work

2. **Existing Cases**: All continue to work
   - v1.0 metadata format still supported
   - Case loading unchanged
   - Case cloning unchanged

3. **Event Workflow**: Simplified
   - Two endpoints → one endpoint
   - Three methods → one method
   - Same behavior, cleaner API

### Risks

**Low Risk Items**:
- ✅ Deleting duplicate methods (no external code calls them after route consolidation)
- ✅ Renaming internal helper methods (none called externally)
- ✅ Updating request models (new models, old ones kept for compat)

**Medium Risk Items**:
- ⚠️ Deleting old route endpoints (users must update client code)
  - **Mitigation**: Deprecation warning, migration guide provided

---

## File Modification Order (Recommended)

**Order matters!** Following this sequence ensures we don't break things:

1. **Models** (safe, additive only)
   - Add new request model
   - Add new response model
   - Keep old models

2. **Routes** (add new first, delete old later)
   - Add new unified endpoints
   - Update old endpoints to use new services
   - Test new endpoints work
   - Delete old endpoints

3. **Services** (refactor based on routes)
   - Rename `create_case_with_simulation()` → `create_case_from_event_scenario()`
   - Update method signatures
   - Delete unused methods
   - Test service methods

4. **Tests**
   - Add tests for new endpoints
   - Verify old cases still load
   - Test both OD and event workflows

5. **Simulation Routes** (last, cleanest)
   - Delete 4 obsolete endpoints
   - Verify nothing else calls them

---

## Success Criteria Checklist

### Code Quality
- [ ] 2 case creation endpoints (down from 4)
- [ ] 2 case service methods (down from 5)
- [ ] 0 duplicate logic
- [ ] All tests passing

### Functionality
- [ ] OD workflow works unchanged
- [ ] Event workflow works with single endpoint
- [ ] Backward compatible with existing cases
- [ ] Simulation_id always returned for event cases

### Documentation
- [ ] API docs updated
- [ ] Migration guide followed by users
- [ ] Code comments updated

### Non-Breaking
- [ ] No breaking changes to OD workflow
- [ ] Existing cases load without modification
- [ ] Control plan workflows unaffected
- [ ] Batch optimization workflows unaffected

---

## Timeline Estimate

- **Models**: 30 minutes (straightforward additions)
- **Routes**: 1 hour (add new, test, delete old)
- **Services**: 1.5 hours (refactor and consolidate)
- **Tests**: 1 hour (add and verify)
- **Simulation Routes**: 30 minutes (simple deletion)
- **Buffer/Integration**: 1 hour

**Total**: ~5-6 hours (feasible in one day)

---

## Next Steps

1. Read this document fully
2. Begin with Model changes (Phase 1B)
3. Continue with Routes changes (Phase 1C)
4. Consolidate Services (Phase 1D)
5. Add tests (Phase 1E)
6. Delete simulation endpoints (Phase 1F)
7. Update OpenSpec files
8. Run full test suite
9. Commit and deploy

---

**Document Status**: Ready for Implementation
**Approved**: Yes
**Reviewed**: Self-reviewed for consistency with Phase 1 cleanup goals
