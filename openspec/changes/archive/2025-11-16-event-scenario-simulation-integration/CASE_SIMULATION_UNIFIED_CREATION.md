# Unified Case + Simulation Creation Workflow

**Date**: 2025-11-13
**Status**: 📋 DESIGN READY FOR IMPLEMENTATION
**Priority**: P0 (Blocking case-scenario relationship display)
**Related Tasks**: Task 2.8-2.10 (Workflow Integration)
**Type**: Backend + Frontend Enhancement

---

## Problem Statement

### Current Issue (Task 2.8-2.10 Implementation Gap)
When creating a case from scenario_browser.html:
- `simulation_metadata.json` is **not** created at case creation time
- It's only created later during `prepare_simulation()` phase
- This breaks the case-scenario relationship visibility requirement
- Users cannot see case-scenario linkage until simulation preparation
- Two-step workflow is confusing and error-prone

### Root Cause
```
Current Workflow (Broken):
  Step 1: Create Case
    └─ metadata.json created
    └─ scenario_index.json updated
    └─ simulation_metadata.json NOT created ❌

  Step 2: (Later) Prepare Simulation
    └─ simulation_metadata.json FINALLY created ✅
    └─ Only then is relationship complete
```

### User Experience Problem
- Case appears "orphaned" after creation
- No way to view case-scenario relationship immediately
- Users must remember to click "仿真" button later
- Metadata is incomplete at case creation time

---

## Solution Design

### New Unified Workflow (One-Step)

```
User clicks "创建" in scenario_browser.html
    ↓
Modal dialog opens with:
  • Scenario info (read-only from scenario_index.json)
  • Simulation defaults (pre-filled)
    ↓
User customizes parameters (optional)
    ↓
User clicks [启动仿真案例创建]
    ↓
Backend executes ATOMIC operation:
  1. Generate case_id
  2. Create case directory structure
  3. Create case metadata.json (with source_scenario)
  4. Process OD data (async, non-blocking)
  5. Copy TAZ files to case config/
  6. Generate simulation.sumocfg
  7. Create simulation_metadata.json (with source_scenario) ← KEY!
  8. Register in scenario_index.json
  9. Update case status to "ready_to_simulate"
    ↓
Frontend receives response:
  • case_id + simulation_id
  • Complete metadata chain established
    ↓
Auto-navigate to case-simulation-center.html
    ↓
User immediately sees case-scenario-simulation relationship! ✅
```

---

## Implementation Requirements

### Frontend: Modal Dialog Component

**Trigger**: User clicks "创建" button in scenario row

**Modal HTML Structure**:
```html
<div class="modal" id="caseCreationModal">
  <div class="modal-content" style="max-width: 500px;">
    <div class="modal-header">
      <h2>📋 创建仿真案例</h2>
      <button class="modal-close" onclick="closeModal('caseCreationModal')">×</button>
    </div>
    <div class="modal-body">
      <!-- Scenario info (read-only) -->
      <h3>场景信息 (只读)</h3>
      <div class="form-group">
        <label>场景ID</label>
        <input type="text" id="modalScenarioId" readonly>
      </div>
      <div class="form-group">
        <label>事件类型</label>
        <input type="text" id="modalEventType" readonly>
      </div>
      <div class="form-group">
        <label>管控策略</label>
        <input type="text" id="modalStrategy" readonly>
      </div>

      <hr>

      <!-- Simulation config (editable) -->
      <h3>仿真配置 (可编辑)</h3>
      <div class="form-group">
        <label>仿真时长 (小时)</label>
        <input type="number" id="simDuration" value="2.5" min="1" max="24">
      </div>
      <div class="form-group">
        <label>随机种子</label>
        <input type="text" id="randomSeed" placeholder="auto-generate">
      </div>
      <div class="form-group">
        <label>仿真模式</label>
        <div>
          <label><input type="radio" name="simType" value="microscopic" checked> 微观仿真</label>
          <label><input type="radio" name="simType" value="mesoscopic"> 中观仿真</label>
        </div>
      </div>

      <!-- Output config -->
      <div class="form-group">
        <label>输出配置</label>
        <div class="checkbox-group">
          <label><input type="checkbox" id="outputEdgedata" checked> EdgeData</label>
          <label><input type="checkbox" id="outputSummary" checked> Summary</label>
          <label><input type="checkbox" id="outputTripinfo" checked> TripInfo</label>
          <label><input type="checkbox" id="outputVehroute"> VehRoute</label>
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal('caseCreationModal')">取消</button>
      <button class="btn btn-primary" id="submitCreateBtn" onclick="submitCreateCaseWithSimulation()">
        🚀 启动仿真案例创建
      </button>
    </div>
  </div>
</div>
```

**JavaScript Functions** (in scenario_browser.js):
```javascript
/**
 * Open case creation modal with defaults
 */
function openCreateCaseModal(scenarioId, eventType, strategy) {
    // Pre-fill scenario info (read-only)
    document.getElementById('modalScenarioId').value = scenarioId;
    document.getElementById('modalEventType').value = getEventTypeDisplay(eventType);
    document.getElementById('modalStrategy').value = getStrategyDisplay(strategy);

    // Pre-fill simulation defaults
    document.getElementById('simDuration').value = 2.5;
    document.getElementById('randomSeed').value = '';
    document.querySelector('input[name="simType"][value="microscopic"]').checked = true;
    document.getElementById('outputEdgedata').checked = true;
    document.getElementById('outputSummary').checked = true;
    document.getElementById('outputTripinfo').checked = true;
    document.getElementById('outputVehroute').checked = false;

    showModal('caseCreationModal');
}

/**
 * Submit case + simulation creation to backend
 */
async function submitCreateCaseWithSimulation() {
    // Find current scenario from allScenarios
    const scenarioId = document.getElementById('modalScenarioId').value;
    const scenario = allScenarios.find(s => s.scenario_id === scenarioId);

    if (!scenario) {
        alert('❌ 场景信息不完整');
        return;
    }

    // Collect form data
    const request = {
        scenario_id: scenarioId,
        event_id: scenario.event_id,
        event_type: scenario.event_type,
        strategy: scenario.strategy,
        case_name: `case_${scenarioId}_${Date.now()}`,

        // Simulation parameters
        simulation_duration_hours: parseFloat(document.getElementById('simDuration').value),
        random_seed: document.getElementById('randomSeed').value || null,
        simulation_type: document.querySelector('input[name="simType"]:checked').value,

        // Output config
        output_config: {
            generate_edgedata: document.getElementById('outputEdgedata').checked,
            generate_summary: document.getElementById('outputSummary').checked,
            generate_tripinfo: document.getElementById('outputTripinfo').checked,
            generate_vehroute: document.getElementById('outputVehroute').checked
        },

        // File references
        network_file: 'templates/network_files/sichuan202508v7.net.xml',
        od_file: 'dwd.dwd_od_weekly',
        taz_file: null
    };

    try {
        const btn = document.getElementById('submitCreateBtn');
        btn.disabled = true;
        btn.textContent = '⏳ 创建中...';

        const response = await fetch('/api/v1/case/create-case-with-simulation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });

        const result = await response.json();

        if (result.success || result.data) {
            const caseId = result.case_id || result.data.case_id;
            const simulationId = result.simulation_id || result.data.simulation_id;

            // Close modal and refresh
            closeModal('caseCreationModal');

            // Update scenario browser view
            await loadCreatedCases();
            renderScenarios();

            // Auto-navigate to case-simulation-center
            window.location.href = `case-simulation-center.html?case_id=${caseId}&simulation_id=${simulationId}`;

        } else {
            alert(`❌ 创建失败: ${result.message || result.error || 'Unknown error'}`);
            btn.disabled = false;
            btn.textContent = '🚀 启动仿真案例创建';
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`❌ 创建失败: ${error.message}`);
        const btn = document.getElementById('submitCreateBtn');
        btn.disabled = false;
        btn.textContent = '🚀 启动仿真案例创建';
    }
}

// Update "创建" button handler
// OLD: onclick="directCreateCase(scenarioId, eventType, strategy)"
// NEW: onclick="openCreateCaseModal(scenarioId, eventType, strategy)"
```

### Backend: New API Endpoint

**Endpoint**: `POST /api/v1/case/create-case-with-simulation`

**Route** (in `api/routes/case_routes.py`):
```python
@router.post("/create-case-with-simulation", response_model=BaseResponse)
@handle_service_errors
async def create_case_with_simulation(request: CreateCaseWithSimulationRequest):
    """
    Unified case + simulation creation (Task 2.8 Enhancement)

    Creates case metadata, processes OD data, copies TAZ files,
    generates sumocfg, and creates simulation_metadata.json in ONE atomic operation.

    This ensures complete metadata linkage and immediate case-scenario relationship visibility.
    """
    case_service = CaseService()
    result = await case_service.create_case_with_simulation(request)
    return create_success_response("案例创建成功，仿真已准备就绪", result)
```

### Backend: Service Implementation

**Method** (in `api/services/case_service.py`):
```python
async def create_case_with_simulation(
    self,
    request: CreateCaseWithSimulationRequest
) -> Dict[str, Any]:
    """
    Create case with complete simulation preparation (Unified Workflow)

    Steps:
    1. Create case + metadata (with source_scenario)
    2. Process OD data (async, background)
    3. Copy TAZ files
    4. Generate sumocfg
    5. Create simulation_metadata.json (with source_scenario) ← KEY!
    6. Register in scenario_index.json
    7. Update case status

    Returns:
        Dict with case_id, simulation_id, status, and files created
    """
    try:
        # Step 1: Create case directory and metadata
        case_id = self.generate_unique_id("case_event")
        case_dir = DirectoryManager.create_case_structure(case_id)

        # Create v2.0 case metadata with source_scenario
        case_metadata = {
            "metadata_version": "2.0",
            "case_id": case_id,
            "case_name": request.case_name,
            "status": "creating",
            "created_at": datetime.now().isoformat(),

            # Source scenario linkage
            "source_scenario": {
                "scenario_id": request.scenario_id,
                "event_id": request.event_id,
                "event_type": request.event_type,
                "control_strategy_type": request.strategy
            }
        }
        MetadataManager.save_case_metadata(case_dir, case_metadata)
        logger.info(f"Created case metadata: {case_id}")

        # Step 2: Process OD data (async, non-blocking)
        od_file_info = await self._process_od_data_async(
            case_id, case_dir, request.od_file
        )
        logger.info(f"OD data processing started for case: {case_id}")

        # Step 3: Copy TAZ files
        taz_file_path = None
        if request.taz_file:
            taz_file_path = await self._copy_taz_files(case_dir, request.taz_file)
            logger.info(f"TAZ files copied for case: {case_id}")

        # Step 4-5: Create simulation + simulation_metadata.json
        simulation_id = self.generate_unique_id("sim")
        sim_dir = case_dir / "simulations" / simulation_id
        sim_dir.mkdir(parents=True, exist_ok=True)

        # Generate sumocfg
        sumocfg_file = await self._generate_sumocfg(
            case_dir, sim_dir, request
        )
        logger.info(f"Generated sumocfg for simulation: {simulation_id}")

        # Create simulation_metadata.json (CRITICAL: include source_scenario!)
        simulation_metadata = {
            "metadata_version": "2.0",
            "simulation_id": simulation_id,
            "case_id": case_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),

            # Copy source_scenario from case (AD-12: Three-Level Tracking)
            "source_scenario": case_metadata["source_scenario"],

            "simulation_params": {
                "duration_hours": request.simulation_duration_hours,
                "random_seed": request.random_seed or self._generate_random_seed(),
                "simulation_type": request.simulation_type
            },

            "output_config": request.output_config,
            "config_file": str(sumocfg_file)
        }
        MetadataManager.save_simulation_metadata(sim_dir, simulation_metadata)
        logger.info(f"Created simulation_metadata.json: {simulation_id}")

        # Step 6: Register in scenario_index.json
        mapper = ScenarioCaseMapper()
        mapper.register_case_creation(
            scenario_id=request.scenario_id,
            case_id=case_id,
            case_name=request.case_name,
            case_status="ready_to_simulate"
        )
        logger.info(f"Registered case in scenario index: {case_id}")

        # Step 7: Update case status to ready
        case_metadata["status"] = "ready_to_simulate"
        MetadataManager.save_case_metadata(case_dir, case_metadata)

        return {
            "success": True,
            "case_id": case_id,
            "simulation_id": simulation_id,
            "case_status": "ready_to_simulate",
            "simulation_status": "pending",
            "message": "案例创建成功，仿真已准备就绪",

            "files_created": {
                "case_metadata": str(case_dir / "metadata.json"),
                "simulation_metadata": str(sim_dir / "simulation_metadata.json"),
                "sumocfg": str(sumocfg_file),
                "od_file": od_file_info.get("od_file_path") if od_file_info else None
            }
        }

    except Exception as e:
        logger.error(f"Failed to create case with simulation: {e}")
        raise
```

### Data Model

**Request Model** (in `api/models/requests/case_requests.py`):
```python
class CreateCaseWithSimulationRequest(BaseModel):
    """Unified case + simulation creation request"""

    # Scenario information
    scenario_id: str
    event_id: str
    event_type: str
    strategy: str
    case_name: str

    # Simulation parameters
    simulation_duration_hours: float = Field(..., ge=1, le=24)
    random_seed: Optional[int] = None
    simulation_type: str = Field(default="microscopic")

    # Output configuration
    output_config: Dict[str, bool] = Field(default={
        "generate_edgedata": True,
        "generate_summary": True,
        "generate_tripinfo": True,
        "generate_vehroute": False
    })

    # File references
    network_file: str
    od_file: str
    taz_file: Optional[str] = None
```

---

## Metadata Structure (After Creation)

### Case Metadata
```json
{
  "metadata_version": "2.0",
  "case_id": "case_20251113_120000",
  "case_name": "case_scenario_10754_no_control_1731401400000",
  "status": "ready_to_simulate",
  "created_at": "2025-11-13T12:00:00.000000",

  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故",
    "control_strategy_type": "NO_CONTROL"
  }
}
```

### Simulation Metadata
```json
{
  "metadata_version": "2.0",
  "simulation_id": "sim_20251113_120530",
  "case_id": "case_20251113_120000",
  "status": "pending",
  "created_at": "2025-11-13T12:05:30.000000",

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
  },

  "output_config": {
    "generate_edgedata": true,
    "generate_summary": true,
    "generate_tripinfo": true,
    "generate_vehroute": false
  },

  "config_file": "cases/case_20251113_120000/simulations/sim_20251113_120530/simulation.sumocfg"
}
```

### Scenario Index Update
```json
{
  "created_cases": [
    {
      "case_id": "case_20251113_120000",
      "case_name": "case_scenario_10754_no_control_1731401400000",
      "status": "ready_to_simulate",
      "source_scenario": "scenario_10754_no_control",
      "created_at": "2025-11-13T12:00:00.000000"
    }
  ]
}
```

---

## Implementation Checklist

### Frontend Changes
- [ ] Add modal HTML div to scenario_browser.html
- [ ] Implement `openCreateCaseModal()` function
- [ ] Implement `submitCreateCaseWithSimulation()` function
- [ ] Update "创建" button onclick handler to call `openCreateCaseModal()`
- [ ] Test modal display and parameter collection
- [ ] Test form validation (duration 1-24h)
- [ ] Test auto-navigation after successful creation

### Backend Changes
- [ ] Create `CreateCaseWithSimulationRequest` model
- [ ] Implement `create_case_with_simulation()` endpoint route
- [ ] Implement service method with atomic operation
- [ ] Helper methods:
  - [ ] `_process_od_data_async()` - Non-blocking OD processing
  - [ ] `_copy_taz_files()` - Copy TAZ files
  - [ ] `_generate_sumocfg()` - Generate simulation config
- [ ] Error handling for each step
- [ ] Logging for debugging
- [ ] Unit tests for endpoint

### Integration & Testing
- [ ] Test complete workflow (modal → API → metadata creation)
- [ ] Verify simulation_metadata.json created immediately
- [ ] Verify case-scenario-simulation relationship in metadata
- [ ] Verify auto-navigation to case-simulation-center.html
- [ ] Verify scenario_index.json updated correctly
- [ ] Test with different simulation parameter values
- [ ] Test OD data processing (async)
- [ ] Test error scenarios (invalid duration, network failure, etc.)

---

## Impact on Related Tasks

### Task 2.8: Scenario Browser - Create Case Integration
**Status**: Enhanced → Now includes modal + unified creation
**Change**: Instead of direct case creation, opens modal for simulation parameter configuration

### Task 2.9: Case Management - Case List & Filtering
**Status**: No change required
**Note**: Cases now appear immediately with "ready_to_simulate" status

### Task 2.10: Case Management - Simulation Monitoring
**Status**: Enhanced → Simulations already prepared at case creation time
**Note**: Simulations start from "pending" status, not from uninitialized state

---

## Acceptance Criteria

✅ Modal opens when "创建" button clicked with:
  - Scenario info (read-only)
  - Simulation defaults (editable)

✅ User can customize simulation parameters:
  - Duration (1-24 hours)
  - Random seed
  - Simulation mode
  - Output config

✅ One-step atomic creation:
  - Case directory created
  - Case metadata created (with source_scenario)
  - OD data processing triggered
  - TAZ files copied
  - simulation_metadata.json created (with source_scenario) ← KEY!
  - scenario_index.json updated
  - Returns case_id + simulation_id

✅ Complete metadata chain established:
  - case metadata → source_scenario
  - simulation_metadata → source_scenario
  - scenario_index → created_cases

✅ Immediate relationship visibility:
  - Frontend shows "✓ 已创建" + "✓ 已准备仿真"
  - Auto-navigate to case-simulation-center.html
  - User sees complete case-scenario-simulation relationship

✅ No breaking changes:
  - Old case creation endpoint still works
  - v1.0 cases still supported
  - Backward compatible

---

## Related Documentation

- **Design**: `WORKFLOW_REDESIGN_CASE_CREATION.md` (in project root)
- **Summary**: `CASE_SIMULATION_CREATION_REDESIGN.md` (in project root)
- **Related Tasks**: Task 2.8, 2.9, 2.10
- **Architecture**: AD-12 (Three-Level Metadata Tracking)

---

## Status

**Design**: ✅ COMPLETE
**Ready for Implementation**: ✅ YES
**Estimated Effort**: 2-3 days (frontend + backend + testing)

---

**This document guides the implementation of the unified case+simulation creation workflow to solve the case-scenario relationship visibility issue.**
