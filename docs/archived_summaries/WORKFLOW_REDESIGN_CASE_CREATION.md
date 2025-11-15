# Workflow Redesign: Case Creation with Simulation Parameters

**Date**: 2025-11-13
**Status**: 📋 DESIGN & IMPLEMENTATION PLAN
**Priority**: P0 (Blocking case-scenario relationship display)
**Author**: User Requirement Analysis + Claude Code

---

## Problem Identification

### Current Workflow ❌
```
User Action                  Backend                      Result
────────────────────────────────────────────────────────────
1. Click "创建"
   (in scenario row)
   │
   ├─→ Case created
   │   ├─ metadata.json created
   │   ├─ od_file_info.json created
   │   ├─ scenario_index.json updated
   │   └─ NO simulation_metadata.json yet ❌
   │
   └─→ Frontend shows "✓ 已创建"

2. User navigates away, then comes back
   │
   └─→ Cannot see case-scenario relationship
       (because simulation_metadata.json not created yet)

3. User clicks "仿真" button in case page
   │
   ├─→ prepare_simulation() called
   │   ├─ simulation_metadata.json FINALLY created ✅
   │   └─ sumocfg generated
   │
   └─→ Now can see simulation-case relationship

ISSUE: Case-scenario relationship invisible until simulation prepared!
```

### Why This Is a Problem
- ❌ User creates case but doesn't see it in relationship view
- ❌ Case "orphaned" until simulation preparation
- ❌ Two-step process confuses users
- ❌ Metadata not created until much later

---

## Proposed Solution ✅

### New Workflow: "Create Case" + "Configure Simulation" in One Flow

```
User Action                  Backend                      Result
────────────────────────────────────────────────────────────
1. Click "创建"
   (in scenario row)
   │
   ├─→ Modal dialog opens
   │   ├─ Pre-fill scenario info (read-only)
   │   ├─ Pre-fill simulation defaults:
   │   │  ├─ simulation_duration_hours: 2.5h
   │   │  ├─ random_seed: auto-generate
   │   │  ├─ output_config: EdgeData+Summary+TripInfo
   │   │  └─ simulation_type: microscopic
   │   │
   │   └─ Show [启动仿真案例创建] button
   │
   └─→ User can modify parameters if needed

2. User clicks [启动仿真案例创建]
   │
   ├─→ Backend: CREATE_CASE_WITH_SIMULATION
   │   ├─ Step 1: Create case
   │   │  ├─ Generate case_id
   │   │  ├─ Create case structure
   │   │  ├─ Create metadata.json (with source_scenario)
   │   │  └─ Register in scenario_index.json created_cases
   │   │
   │   ├─ Step 2: Process OD data (background)
   │   │  ├─ Fetch from database (if needed)
   │   │  ├─ Generate od.xml and routes.xml
   │   │  └─ Update case metadata: status = "od_ready"
   │   │
   │   ├─ Step 3: Copy TAZ files
   │   │  ├─ Copy from templates/taz_files/
   │   │  └─ Store in cases/{case_id}/config/
   │   │
   │   ├─ Step 4: Prepare simulation
   │   │  ├─ Generate simulation_id
   │   │  ├─ Create simulation directory
   │   │  ├─ Generate sumocfg file ✅
   │   │  ├─ Create simulation_metadata.json ✅ (with source_scenario)
   │   │  └─ Update case metadata: status = "ready_to_simulate"
   │   │
   │   └─ Step 5: Register simulation in scenario_index.json
   │      └─ Add sim_id to case's simulations array
   │
   └─→ Return case_id and simulation_id to frontend

3. Frontend receives result
   │
   ├─→ Update scenario_index.json view
   │   └─ Show "✓ 已创建" + "✓ 已准备仿真"
   │
   └─→ Auto-navigate to case-simulation-center.html
       (Case-simulation relationship IMMEDIATELY VISIBLE!)

4. User clicks [启动仿真] in case page
   │
   ├─→ Backend: START_SIMULATION
   │   ├─ Load simulation_metadata.json (already exists!)
   │   ├─ Execute SUMO simulation
   │   └─ Stream progress
   │
   └─→ Done! Full simulation metadata chain visible

BENEFIT: Case-scenario relationship visible immediately!
```

---

## Detailed Design

### 1. Modal Dialog Component (Frontend)

**Trigger**: When user clicks "创建" button in scenario row

**Modal Content**:
```
┌─────────────────────────────────────────────────────┐
│  📋 创建仿真案例                              ×    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  场景信息 (只读)                                    │
│  ├─ 场景ID: scenario_10754_no_control              │
│  ├─ 事件类型: 交通事故                             │
│  ├─ 管控策略: NO_CONTROL                           │
│  └─ 事件时间: 2025-06-10 10:43:48 ~ 11:14:50       │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  仿真配置 (可编辑)                                  │
│  ├─ 仿真时长: [2.5] 小时 (1-24h)                   │
│  ├─ 随机种子: [auto] (或输入整数)                  │
│  ├─ 仿真模式: ◉ 微观仿真 ○ 中观仿真               │
│  │                                                 │
│  └─ 输出配置:                                      │
│     ☑ EdgeData (路段数据)                          │
│     ☑ Summary (汇总统计)                           │
│     ☑ TripInfo (出行数据)                          │
│     ☐ VehRoute (车辆路线)                          │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  说明:                                              │
│  • 点击下方按钮后，系统会自动:                      │
│    - 处理OD数据 (如需从数据库生成)                 │
│    - 复制TAZ文件到案例目录                         │
│    - 生成仿真配置文件                              │
│    - 建立完整的元数据关系                          │
│                                                     │
│  [取消]  [启动仿真案例创建] →                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Default Values** (Pre-filled):
```javascript
{
  case_name: `case_${scenario_id}_${timestamp}`,
  scenario_id: "scenario_10754_no_control",
  event_id: "10754",
  event_type: "交通事故",
  strategy: "NO_CONTROL",

  // 仿真参数默认值
  simulation_duration_hours: 2.5,
  random_seed: null,  // Backend will auto-generate
  simulation_type: "microscopic",

  // 输出配置
  output_config: {
    generate_edgedata: true,
    generate_summary: true,
    generate_tripinfo: true,
    generate_vehroute: false
  }
}
```

### 2. Backend API: New Endpoint

**Endpoint**: `POST /api/v1/case/create-case-with-simulation`

**Request**:
```json
{
  "scenario_id": "scenario_10754_no_control",
  "event_id": "10754",
  "event_type": "交通事故",
  "strategy": "NO_CONTROL",
  "case_name": "case_20251113_...",

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

  "message": "案例创建成功，仿真已准备就绪",

  "files_created": {
    "case_metadata": "cases/case_20251113_120000/metadata.json",
    "simulation_metadata": "cases/case_20251113_120000/simulations/sim_20251113_120530/simulation_metadata.json",
    "sumocfg": "cases/case_20251113_120000/simulations/sim_20251113_120530/simulation.sumocfg",
    "od_file": "cases/case_20251113_120000/config/od_20251113_120000.xml"
  }
}
```

### 3. Backend Implementation: CaseService Enhancement

**New Method**: `create_case_with_simulation()`

```python
async def create_case_with_simulation(self, request: CreateCaseWithSimulationRequest) -> Dict[str, Any]:
    """
    创建案例并立即准备仿真 (New Workflow - Phase 2.5)

    工作流:
    1. 创建案例 + 基础元数据
    2. 处理OD数据 (async, background)
    3. 复制TAZ文件
    4. 生成sumocfg
    5. 创建simulation_metadata.json (NEW!)
    6. 更新场景索引

    Returns:
        包含case_id, simulation_id, 以及文件列表
    """
    try:
        # Step 1: Create case
        case_id = self.generate_unique_id("case_event")
        case_dir = DirectoryManager.create_case_structure(case_id)

        # Create case metadata (v2.0)
        case_metadata = {
            "metadata_version": "2.0",
            "case_id": case_id,
            "source_scenario": {
                "scenario_id": request.scenario_id,
                "event_id": request.event_id,
                "event_type": request.event_type,
                "control_strategy_type": request.strategy
            },
            "status": "creating",
            "created_at": datetime.now().isoformat()
        }
        MetadataManager.save_case_metadata(case_dir, case_metadata)

        # Step 2: Process OD data (async, non-blocking)
        od_file_info = await self._process_od_data_async(
            case_id, case_dir, request.od_file
        )

        # Step 3: Copy TAZ files
        taz_file_path = await self._copy_taz_files(case_dir)

        # Step 4: Generate sumocfg
        sim_metadata = await self._generate_simulation_config(
            case_id, case_dir, request
        )

        # Step 5: Create simulation_metadata.json (KEY CHANGE!)
        simulation_id = self.generate_unique_id("sim")
        sim_dir = case_dir / "simulations" / simulation_id
        sim_dir.mkdir(parents=True, exist_ok=True)

        simulation_metadata = {
            "metadata_version": "2.0",
            "simulation_id": simulation_id,
            "case_id": case_id,
            "source_scenario": case_metadata["source_scenario"],  # ← Copy from case
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "simulation_params": {
                "duration_hours": request.simulation_duration_hours,
                "random_seed": request.random_seed or self._generate_random_seed(),
                "simulation_type": request.simulation_type
            },
            "output_config": request.output_config
        }
        MetadataManager.save_simulation_metadata(sim_dir, simulation_metadata)

        # Step 6: Register in scenario index
        mapper = ScenarioCaseMapper()
        mapper.register_case_creation(
            scenario_id=request.scenario_id,
            case_id=case_id,
            case_name=request.case_name,
            case_status="ready_to_simulate"
        )

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
                "sumocfg": str(sim_dir / "simulation.sumocfg"),
                "od_file": str(case_dir / "config" / f"od_{case_id}.xml")
            }
        }

    except Exception as e:
        logger.error(f"Failed to create case with simulation: {e}")
        raise
```

### 4. Frontend: Modal Implementation

**File**: `frontend/scenarios/scenario_browser.js` (new function)

```javascript
async function openCreateCaseModal(scenarioId, eventType, strategy) {
    // Load scenario details
    const scenario = allScenarios.find(s => s.scenario_id === scenarioId);

    // Prepare modal HTML with default values
    const modalHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h2>📋 创建仿真案例</h2>
                <button class="modal-close" onclick="closeModal('caseCreationModal')">×</button>
            </div>
            <div class="modal-body">
                <h3>场景信息 (只读)</h3>
                <div class="form-group">
                    <label>场景ID</label>
                    <input type="text" value="${scenarioId}" readonly>
                </div>
                <div class="form-group">
                    <label>事件类型</label>
                    <input type="text" value="${getEventTypeDisplay(eventType)}" readonly>
                </div>
                <div class="form-group">
                    <label>管控策略</label>
                    <input type="text" value="${getStrategyDisplay(strategy)}" readonly>
                </div>

                <hr>

                <h3>仿真配置 (可编辑)</h3>
                <div class="form-group">
                    <label>仿真时长 (小时)</label>
                    <input type="number" id="simulationDuration" value="2.5" min="1" max="24">
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

                <div class="form-group">
                    <label>输出配置</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="outputEdgedata" checked> EdgeData (路段数据)</label>
                        <label><input type="checkbox" id="outputSummary" checked> Summary (汇总统计)</label>
                        <label><input type="checkbox" id="outputTripinfo" checked> TripInfo (出行数据)</label>
                        <label><input type="checkbox" id="outputVehroute"> VehRoute (车辆路线)</label>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal('caseCreationModal')">取消</button>
                <button class="btn btn-primary" onclick="submitCreateCaseWithSimulation('${scenarioId}', '${eventType}', '${strategy}')">
                    🚀 启动仿真案例创建
                </button>
            </div>
        </div>
    `;

    // Insert modal and show
    document.getElementById('caseCreationModal').innerHTML = modalHTML;
    showModal('caseCreationModal');
}

async function submitCreateCaseWithSimulation(scenarioId, eventType, strategy) {
    // Collect form data
    const request = {
        scenario_id: scenarioId,
        event_id: getEventIdForScenario(scenarioId),
        event_type: eventType,
        strategy: strategy,
        case_name: `case_${scenarioId}_${Date.now()}`,

        // 仿真参数
        simulation_duration_hours: parseFloat(document.getElementById('simulationDuration').value),
        random_seed: document.getElementById('randomSeed').value || null,
        simulation_type: document.querySelector('input[name="simType"]:checked').value,

        // 输出配置
        output_config: {
            generate_edgedata: document.getElementById('outputEdgedata').checked,
            generate_summary: document.getElementById('outputSummary').checked,
            generate_tripinfo: document.getElementById('outputTripinfo').checked,
            generate_vehroute: document.getElementById('outputVehroute').checked
        },

        network_file: 'templates/network_files/sichuan202508v7.net.xml',
        od_file: 'dwd.dwd_od_weekly',
        taz_file: null
    };

    try {
        const response = await fetch('/api/v1/case/create-case-with-simulation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });

        const result = await response.json();

        if (result.success) {
            closeModal('caseCreationModal');

            // Update scenario browser
            await loadCreatedCases();
            renderScenarios();

            // Auto-navigate to case-simulation-center
            window.location.href = `case-simulation-center.html?case_id=${result.case_id}&simulation_id=${result.simulation_id}`;

        } else {
            alert(`❌ 创建失败: ${result.message}`);
        }
    } catch (error) {
        console.error('Failed to create case:', error);
        alert(`❌ 创建失败: ${error.message}`);
    }
}
```

---

## Workflow Comparison

### Before (Current)
```
Step 1: Create Case (minimal)
        └─ metadata.json only
        └─ No simulation info

Step 2: (Later) Prepare Simulation
        └─ simulation_metadata.json created
        └─ Case-simulation link established

ISSUE: Two-step process, metadata incomplete initially
```

### After (New)
```
Step 1: Create Case + Prepare Simulation (unified)
        ├─ metadata.json (with source_scenario)
        ├─ simulation_metadata.json (with source_scenario)
        └─ sumocfg generated
        └─ Case-simulation link IMMEDIATE

BENEFIT: One-step process, complete metadata from start
```

---

## Files to Create/Modify

### New Files
1. **Frontend Modal Component** (New Section in scenario_browser.js)
   - `openCreateCaseModal()` function
   - `submitCreateCaseWithSimulation()` function
   - Modal styling in scenario_browser.css

### Modified Files
1. **api/routes/case_routes.py**
   - Add new endpoint: `POST /api/v1/case/create-case-with-simulation`

2. **api/services/case_service.py**
   - Add new method: `create_case_with_simulation()`
   - Add helper methods for OD processing, TAZ copying, etc.

3. **frontend/scenarios/scenario_browser.html**
   - Add modal div: `<div id="caseCreationModal" class="modal"></div>`

4. **frontend/scenarios/scenario_browser.js**
   - Change "创建" button click handler to open modal
   - Add modal form functions
   - Add submission handler

---

## Key Advantages of New Workflow

| Aspect | Old Workflow | New Workflow |
|--------|------------|------------|
| **Case-Simulation Link** | Created later (two-step) | Created immediately (one-step) |
| **simulation_metadata.json** | Created in prepare phase | Created in case creation |
| **User Experience** | Confusing (two buttons) | Clear (modal dialog) |
| **Metadata Completeness** | Incomplete initially | Complete from start |
| **Scenario Relationship** | Invisible until prepare | Visible immediately |
| **Effort for User** | Two clicks in different pages | One click + modal options |

---

## Implementation Priority

1. **Step 1**: Create modal UI (frontend)
2. **Step 2**: Implement `create_case_with_simulation()` endpoint
3. **Step 3**: Update case creation button to open modal
4. **Step 4**: Update scenario_index.json registration
5. **Step 5**: Test complete workflow
6. **Step 6**: Update documentation

---

## Acceptance Criteria

✅ **Modal Opens When User Clicks "创建"**
- Pre-filled with scenario defaults
- Allows parameter customization
- Shows clear confirmation

✅ **One-Step Case Creation with Simulation Preparation**
- OD data processed
- TAZ files copied
- simulation_metadata.json created
- sumocfg generated
- Returns both case_id and simulation_id

✅ **Complete Metadata From Start**
- case metadata has source_scenario
- simulation metadata has source_scenario
- scenario_index.json tracks case and simulation

✅ **Immediate Case-Scenario Relationship Visible**
- Frontend shows full relationship without refresh
- No orphaned cases
- Clear workflow to user

---

**Ready for Implementation**: ✅
**Status**: 📋 Design Complete, Ready for Coding Phase
