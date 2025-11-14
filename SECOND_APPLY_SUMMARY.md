# Second OpenSpec Apply: Case+Simulation Creation Redesign

**Date**: 2025-11-13
**Status**: ✅ DESIGN COMPLETE, READY FOR IMPLEMENTATION
**Issue**: simulation_metadata.json created too late → case-scenario relationship invisible
**Solution**: Modal-based unified case+simulation creation in one step

---

## Problem Analysis

### Current Issue
```
User clicks "创建"
  → Case created (metadata.json only)
  → simulation_metadata.json NOT created yet ❌
  → User navigates away
  → Case appears "orphaned" (no simulation relationship)

Later (if user remembers):
  → User clicks "仿真"
  → prepare_simulation() called
  → simulation_metadata.json FINALLY created ✅
  → Now case-scenario relationship visible
```

**Root Cause**: Two-step workflow, metadata created incrementally

**User Impact**: Case-scenario relationship invisible until simulation preparation

---

## Solution Proposed by User

> 创建案例按钮加载模式框，并完成模式框的默认填写，用户修改仿真方面的参数后，点击启动仿真案例创建，这时触发od数据的处理、taz文件的复制，sumocfg文件的生成等，并建立场景和场景案例的元数据，为仿真的启动做好准备

**Meaning**:
1. Show modal when user clicks "Create"
2. Pre-fill with default simulation parameters
3. User customizes if needed
4. Click "Start Simulation Case Creation"
5. Backend creates: case + case metadata + OD data + TAZ files + sumocfg + simulation_metadata.json ← ALL IN ONE STEP
6. Establish complete scenario-case metadata linkage
7. Prepare everything for simulation startup

---

## New Unified Workflow

```
BEFORE (Two-Step, Broken):
  [创建] → Case created (incomplete)
           → No simulation metadata
           → Relationship invisible

AFTER (One-Step, Complete):
  [创建] → Modal opens (pre-filled)
        → User customizes (optional)
        → [启动仿真案例创建]
        → Backend atomically:
           1. Creates case + metadata
           2. Processes OD data
           3. Copies TAZ files
           4. Generates sumocfg
           5. Creates simulation_metadata.json ✅ (KEY!)
           6. Registers in scenario_index.json
        → Case-scenario-simulation relationship IMMEDIATELY visible!
```

---

## Modal Dialog Design

**Trigger**: User clicks "创建" in scenario row

**Content**:
```
┌───────────────────────────────────┐
│ 📋 创建仿真案例               × │
├───────────────────────────────────┤
│                                 │
│ 场景信息 (只读)                  │
│ • 场景ID: scenario_10754_...    │
│ • 事件类型: 交通事故             │
│ • 管控策略: NO_CONTROL          │
│ • 事件时间: 2025-06-10 10:43 ~  │
│                                 │
│ ─────────────────────────────── │
│                                 │
│ 仿真配置 (可编辑)                │
│ • 仿真时长: [2.5] 小时          │
│ • 随机种子: [auto]              │
│ • 仿真模式: ◉ 微观 ○ 中观       │
│                                 │
│ 输出配置:                        │
│ ☑ EdgeData  ☑ Summary           │
│ ☑ TripInfo  ☐ VehRoute          │
│                                 │
│ ───────────────────────────────  │
│                                 │
│ [取消]  [启动仿真案例创建] →     │
│                                 │
└───────────────────────────────────┘
```

**Pre-filled Defaults**:
- simulation_duration_hours: 2.5 (editable, 1-24)
- random_seed: null (backend auto-generates)
- simulation_type: "microscopic"
- output_config: EdgeData + Summary + TripInfo checked

---

## Backend Implementation

### New Endpoint
`POST /api/v1/case/create-case-with-simulation`

### Atomic Operation Sequence
```python
async def create_case_with_simulation(request):
    # Step 1: Create case directory and metadata
    case_id = generate_id()
    create_case_metadata(case_id, source_scenario)

    # Step 2: Process OD data (async, background)
    await process_od_data(case_id, od_file)

    # Step 3: Copy TAZ files
    copy_taz_files(case_id)

    # Step 4-5: Prepare simulation + create simulation_metadata.json
    sim_id = generate_id()
    create_simulation_metadata(sim_id, case_id, source_scenario)
    generate_sumocfg(sim_id)

    # Step 6: Register in scenario_index.json
    scenario_mapper.register_case_creation(scenario_id, case_id)

    # Step 7: Update case status
    update_case_status(case_id, "ready_to_simulate")

    return {
        "case_id": case_id,
        "simulation_id": sim_id,
        "status": "ready_to_simulate"
    }
```

### Metadata Created Immediately
```json
// cases/{case_id}/metadata.json
{
  "metadata_version": "2.0",
  "case_id": "case_20251113_120000",
  "status": "ready_to_simulate",
  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故",
    "control_strategy_type": "NO_CONTROL"
  }
}

// cases/{case_id}/simulations/{sim_id}/simulation_metadata.json
{
  "metadata_version": "2.0",
  "simulation_id": "sim_20251113_120530",
  "case_id": "case_20251113_120000",
  "status": "pending",
  "source_scenario": { ... },  // ← KEY!
  "simulation_params": { ... }
}
```

---

## Files to Create/Modify

### Frontend
1. **scenario_browser.html** - Add `<div id="caseCreationModal" class="modal"></div>`
2. **scenario_browser.js** - Add modal functions:
   - `openCreateCaseModal(scenarioId, ...)`
   - `submitCreateCaseWithSimulation(...)`
   - Update "创建" button handler
3. **scenario_browser.css** - Modal styling

### Backend
1. **api/routes/case_routes.py** - Add endpoint:
   ```python
   @router.post("/create-case-with-simulation")
   async def create_case_with_simulation(request):
   ```

2. **api/services/case_service.py** - Add method:
   ```python
   async def create_case_with_simulation(self, request):
   ```

3. **api/models/requests/case_requests.py** - Add request model:
   ```python
   class CreateCaseWithSimulationRequest(BaseModel):
   ```

---

## Improvements Over Current

| Aspect | Before | After |
|--------|--------|-------|
| **Steps** | 2 | 1 |
| **simulation_metadata.json** | Created later | Created immediately |
| **User Interface** | Direct button | Modal with options |
| **Parameter Control** | No | Yes |
| **Relationship Visibility** | Hidden | Visible immediately |
| **Atomic** | No | Yes |
| **Metadata Completeness** | Incomplete | Complete |

---

## Documentation Delivered

1. **WORKFLOW_REDESIGN_CASE_CREATION.md** (500+ lines)
   - Complete problem analysis
   - Full solution design with code
   - Modal specifications
   - Workflow diagrams
   - Acceptance criteria

2. **CASE_SIMULATION_CREATION_REDESIGN.md** (400+ lines)
   - Summary of issue and solution
   - Technical design
   - Timeline and status

---

## Implementation Status

**Design Phase**: ✅ COMPLETE
- ✅ Problem analysis
- ✅ Solution design
- ✅ Modal dialog design
- ✅ Backend endpoint design
- ✅ Documentation

**Ready for Implementation Phase**:
- 📋 Frontend modal component
- 📋 Backend endpoint
- 📋 Service method
- 📋 Request model
- 📋 Integration testing

**Estimated Timeline**: 2-3 days for full implementation

---

## Key Benefits

✅ **Solves root problem**: simulation_metadata.json created immediately
✅ **Better UX**: One-step vs two-step workflow
✅ **Parameter preview**: Customize before committing
✅ **Complete metadata**: Full chain established atomically
✅ **Immediate visibility**: Case-scenario relationship visible right away
✅ **Clear workflow**: Modal dialog is intuitive
✅ **Auto-navigation**: Takes user to correct page

---

## Next Action

**Ready to**: Begin implementation phase
- Create modal dialog
- Implement backend endpoint
- Integrate and test
- Deploy

**Design documents** ready for reference and implementation guidance.

---

**Status**: 🎯 Design Complete | Ready for Implementation Phase
