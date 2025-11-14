# Case+Simulation Creation Redesign Summary

**Date**: 2025-11-13
**Status**: ✅ DESIGN COMPLETE, READY FOR IMPLEMENTATION
**Issue**: simulation_metadata.json created too late, case-scenario relationship invisible
**Solution**: Modal-based unified case+simulation creation in one step

---

## The Problem

### Current Issue
```
User clicks "创建" → Case created, NO simulation_metadata.json
                   ↓
                   Case appears "orphaned"
                   ↓
User must click "仿真" later → simulation_metadata.json FINALLY created
                              ↓
                              Only then can see case-scenario relationship
```

**User Pain Points**:
- ❌ Two-step process is confusing
- ❌ Case-scenario relationship invisible initially
- ❌ Must navigate between pages
- ❌ simulation_metadata.json created too late
- ❌ No way to preview simulation parameters before committing

---

## The Solution

### New Unified Workflow
```
User clicks "创建" in scenario row
    ↓
Modal dialog opens with:
  • Scenario info (read-only): event_type, strategy, time range
  • Simulation defaults (editable): duration, random_seed, mode, outputs
    ↓
User customizes simulation parameters (or uses defaults)
    ↓
User clicks [启动仿真案例创建]
    ↓
Backend creates EVERYTHING in one atomic operation:
  1. Generate case_id
  2. Create case metadata (with source_scenario)
  3. Process OD data (async, background)
  4. Copy TAZ files
  5. Generate sumocfg
  6. Create simulation_metadata.json (with source_scenario) ← KEY!
  7. Register in scenario_index.json
    ↓
Frontend immediately shows:
  "✓ 已创建" + "✓ 已准备仿真"
    ↓
Auto-navigate to case-simulation-center.html
    ↓
User can immediately see case-scenario-simulation relationship!
```

---

## Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Step Count** | 2 steps (create + prepare) | 1 step (create+prepare unified) |
| **simulation_metadata.json** | Created later in prepare phase | Created immediately in case creation |
| **User Experience** | Confusing workflow | Clear modal-based workflow |
| **Relationship Visibility** | Hidden until second step | Visible immediately |
| **Parameter Preview** | Must commit to defaults | Can customize before committing |
| **Navigation** | Must go to case page | Auto-navigate to proper page |

---

## Technical Design

### 1. Frontend Modal Dialog

**Trigger**: User clicks "创建" button in scenario row

**Modal Contents**:
```
┌─ Scenario Info (Read-Only) ─────┐
│ • scenario_id                   │
│ • event_type                    │
│ • control_strategy              │
│ • time_range                    │
├─ Simulation Config (Editable) ──┤
│ • simulation_duration: 2.5h     │
│ • random_seed: auto             │
│ • simulation_type: microscopic  │
│ • output_config: checklist      │
├─ Action Buttons ────────────────┤
│ [取消] [启动仿真案例创建]         │
└─────────────────────────────────┘
```

**Default Values**:
```javascript
{
  simulation_duration_hours: 2.5,    // 1-24 hours
  random_seed: null,                 // Backend auto-generates
  simulation_type: "microscopic",    // or "mesoscopic"
  output_config: {
    generate_edgedata: true,
    generate_summary: true,
    generate_tripinfo: true,
    generate_vehroute: false
  }
}
```

### 2. Backend Endpoint

**New Endpoint**: `POST /api/v1/case/create-case-with-simulation`

**Request**:
```json
{
  "scenario_id": "scenario_10754_no_control",
  "event_id": "10754",
  "event_type": "交通事故",
  "strategy": "NO_CONTROL",

  "simulation_duration_hours": 2.5,
  "random_seed": null,
  "simulation_type": "microscopic",

  "output_config": {
    "generate_edgedata": true,
    "generate_summary": true,
    "generate_tripinfo": true,
    "generate_vehroute": false
  },

  "network_file": "templates/network_files/sichuan202508v7.net.xml",
  "od_file": "dwd.dwd_od_weekly",
  "taz_file": null
}
```

**Response**:
```json
{
  "success": true,
  "case_id": "case_20251113_120000",
  "simulation_id": "sim_20251113_120530",
  "case_status": "ready_to_simulate",
  "simulation_status": "pending",

  "files_created": {
    "case_metadata": "cases/case_20251113_120000/metadata.json",
    "simulation_metadata": "cases/.../simulations/sim_.../simulation_metadata.json",
    "sumocfg": "cases/.../simulations/sim_.../simulation.sumocfg",
    "od_file": "cases/case_20251113_120000/config/od_*.xml"
  }
}
```

### 3. Backend Implementation Steps

New method: `CaseService.create_case_with_simulation()`

```python
async def create_case_with_simulation(request):
    # Step 1: Create case + metadata (with source_scenario)
    case_id = generate_id()
    create_case_metadata(case_id, request.source_scenario)

    # Step 2: Process OD data (async, non-blocking)
    await process_od_data_async(case_id, request.od_file)

    # Step 3: Copy TAZ files
    copy_taz_files(case_id)

    # Step 4-5: Prepare simulation + create simulation_metadata.json
    sim_id = generate_id()
    create_simulation_metadata(sim_id, case_id, request)
    generate_sumocfg(sim_id)

    # Step 6: Register in scenario_index.json
    mapper.register_case_creation(scenario_id, case_id)

    # Step 7: Update case status
    update_case_status(case_id, "ready_to_simulate")

    return {
        "case_id": case_id,
        "simulation_id": sim_id,
        "message": "案例创建成功，仿真已准备就绪"
    }
```

---

## Files to Create/Modify

### Frontend Changes

**1. scenario_browser.html**
```html
<!-- Add modal div -->
<div class="modal" id="caseCreationModal"></div>
```

**2. scenario_browser.js**
```javascript
// Change "创建" button click handler
button onclick="openCreateCaseModal(scenarioId, eventType, strategy)"

// Add new functions:
// - openCreateCaseModal(scenarioId, eventType, strategy)
// - submitCreateCaseWithSimulation(scenarioId, eventType, strategy)
```

**3. scenario_browser.css**
```css
/* Add modal styling if not already present */
```

### Backend Changes

**1. api/routes/case_routes.py**
```python
@router.post("/create-case-with-simulation")
async def create_case_with_simulation(request: CreateCaseWithSimulationRequest):
    """创建案例并立即准备仿真 (Unified workflow)"""
    case_service = CaseService()
    result = await case_service.create_case_with_simulation(request)
    return create_success_response("案例创建成功", result)
```

**2. api/services/case_service.py**
```python
async def create_case_with_simulation(self, request):
    """创建案例并立即准备仿真"""
    # Implementation as shown above
```

**3. api/models/requests/case_requests.py**
```python
class CreateCaseWithSimulationRequest(BaseModel):
    """案例+仿真统一创建请求"""
    scenario_id: str
    event_id: str
    event_type: str
    strategy: str
    case_name: str

    # Simulation parameters
    simulation_duration_hours: float
    random_seed: Optional[int] = None
    simulation_type: str

    # Output configuration
    output_config: Dict[str, bool]

    # File references
    network_file: str
    od_file: str
    taz_file: Optional[str] = None
```

---

## Workflow Execution Flow

### Frontend Flow
```
User Action                         Frontend Function
───────────────────────────────────────────────────────
Click "创建" button      →  openCreateCaseModal(scenario_id, ...)
                            └─ Display modal with defaults

Modify parameters        →  User edits form fields
                            (all changes in modal)

Click [启动仿真案例创建]  →  submitCreateCaseWithSimulation(...)
                            └─ Collect form data
                            └─ POST to /api/v1/case/create-case-with-simulation
                            └─ Wait for response

Response received        →  Close modal
                            └─ Update scenario browser view
                            └─ Auto-navigate to case-simulation-center.html
```

### Backend Flow
```
Request Received                    Backend Service
───────────────────────────────────────────────────────
Parse request        →  CaseService.create_case_with_simulation()

Create case          →  DirectoryManager.create_case_structure()
                        └─ Create metadata.json (with source_scenario)

Process OD data      →  (async, background)
                        └─ Fetch from DB if needed
                        └─ Generate od.xml, routes.xml

Copy TAZ files       →  Copy from templates to case config/

Generate sumocfg     →  SimulationService.generate_sumocfg()

Create sim metadata  →  Create simulation_metadata.json
                        └─ Include source_scenario (KEY!)
                        └─ Set status to "pending"

Register in index    →  ScenarioCaseMapper.register_case_creation()
                        └─ Add to created_cases array

Update case status   →  MetadataManager.update_case_metadata()
                        └─ Set status to "ready_to_simulate"

Return response      →  Return case_id, simulation_id, status
```

---

## Metadata State at Each Phase

### After Step 1 (Case Creation)
```json
// cases/{case_id}/metadata.json
{
  "metadata_version": "2.0",
  "case_id": "case_20251113_120000",
  "status": "creating",
  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故",
    "control_strategy_type": "NO_CONTROL"
  }
}
```

### After Step 5 (Simulation Metadata Created)
```json
// cases/{case_id}/simulations/{sim_id}/simulation_metadata.json
{
  "metadata_version": "2.0",
  "simulation_id": "sim_20251113_120530",
  "case_id": "case_20251113_120000",
  "status": "pending",
  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故",
    "control_strategy_type": "NO_CONTROL"
  },
  "simulation_params": {
    "duration_hours": 2.5,
    "random_seed": 12345,
    "simulation_type": "microscopic"
  }
}
```

### After Step 6 (Scenario Index Updated)
```json
// /output/scenarios/scenario_index.json
{
  "scenarios": [{
    "scenario_dir": "scenario_10754_no_control",
    "created_cases": [{
      "case_id": "case_20251113_120000",
      "status": "ready_to_simulate",
      "source_scenario": "scenario_10754_no_control",
      "created_at": "2025-11-13T12:00:00"
    }]
  }]
}
```

**Result**: Complete metadata chain visible immediately! ✅

---

## User Experience

### Before (Current)
```
1. User sees scenario in list
2. Clicks "创建" → Case created, but no feedback about simulation
3. User must navigate to case page
4. Clicks "仿真" → Now simulation is prepared
5. Finally can see complete relationship

ISSUE: Confusing, multi-step, unclear workflow
```

### After (New)
```
1. User sees scenario in list
2. Clicks "创建" → Modal opens with defaults pre-filled
3. User optionally customizes simulation parameters
4. Clicks [启动仿真案例创建]
5. Backend creates case + simulation metadata
6. Auto-navigate to case-simulation-center.html
7. User immediately sees complete case-scenario-simulation relationship

BENEFIT: Clear, one-step, obvious workflow
```

---

## Implementation Timeline

### Phase 1: Frontend Implementation (1-2 days)
1. Create modal component in scenario_browser.html
2. Implement modal form with defaults
3. Add submission handler
4. Update button click handler

### Phase 2: Backend Implementation (1-2 days)
1. Create new request model
2. Implement `create_case_with_simulation()` method
3. Create new API endpoint
4. Update scenario_index.json registration

### Phase 3: Testing & Integration (1 day)
1. Test modal display and parameter collection
2. Test backend creation workflow
3. Verify metadata creation
4. Test complete user flow

### Phase 4: Documentation (0.5 days)
1. Update API documentation
2. Add workflow diagrams to CLAUDE.md
3. Create user guide

---

## Acceptance Criteria

✅ Modal opens with scenario info (read-only)
✅ Simulation parameters pre-filled with sensible defaults
✅ User can modify parameters before submitting
✅ One click creates case + prepares simulation
✅ simulation_metadata.json created immediately (not later)
✅ case-scenario relationship visible without refresh
✅ Auto-navigate to case-simulation-center.html
✅ All metadata (case, simulation, scenario index) properly linked
✅ OD processing happens asynchronously (non-blocking)
✅ Clear user feedback at each step

---

## Status

**Design**: ✅ COMPLETE
**Documentation**: ✅ COMPLETE
**Ready for Implementation**: ✅ YES

**Next**: Proceed to implementation phase (frontend modal + backend endpoint)

---

## Reference Documents

- **Detailed Design**: `WORKFLOW_REDESIGN_CASE_CREATION.md`
- **Related**: Phase 2 Tasks from `openspec/changes/event-scenario-simulation-integration/tasks.md`
- **Architecture**: `CLAUDE.md` (AD-12, AD-13, principles)
