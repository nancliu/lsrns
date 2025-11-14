# Event Scenario Case Status Identification Timeline

**Date**: 2025-11-13
**Question**: When is simulation_metadata.json created? How to identify event scenario case creation status before it's created?
**Status**: ✅ ANSWERED

---

## Timeline: Case Creation to Simulation Metadata

### Phase 1: Case Creation (Immediate)
**When**: User clicks "创建" in scenario_browser.html
**What Gets Created**:
- ✅ `cases/{case_id}/metadata.json` - **CREATED IMMEDIATELY**
- ✅ `cases/{case_id}/config/od_file_info.json` - **CREATED IMMEDIATELY**
- ✅ `scenario_index.json` updated with `created_cases` - **CREATED IMMEDIATELY** (via ScenarioCaseMapper)

**Status at This Point**: `status: "created"` or `"od_generating"`

```json
{
  "case_id": "case_20251113_120000",
  "status": "created",  // or "od_generating" if OD is pending
  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故"
  }
}
```

**Frontend Can Display**:
- ✅ Case created status (from scenario_index.json created_cases)
- ✅ OD generation status (from case metadata status field)

---

### Phase 2: Simulation Preparation (User Clicks "仿真" Button)
**When**: User clicks [开始批量仿真] or [仿真] to prepare simulations
**What Gets Created**:
- ✅ `cases/{case_id}/simulations/{sim_id}/simulation_metadata.json` - **CREATED DURING PREPARE**
- ✅ `cases/{case_id}/simulations/{sim_id}/simulation.sumocfg` - **CREATED DURING PREPARE**

**What's In simulation_metadata.json**:
```json
{
  "metadata_version": "2.0",
  "simulation_id": "sim_20251113_120530",
  "case_id": "case_20251113_120000",
  "status": "pending",
  "created_at": "2025-11-13T12:05:30",
  "source_scenario": {
    "scenario_id": "scenario_10754_no_control",
    "event_id": "10754",
    "event_type": "交通事故"
  }
}
```

**Code Location**: `api/services/simulation_service.py:54-56` (prepare_simulation)
```python
# 创建并保存仿真元数据（pending）
sim_metadata = self._create_simulation_metadata(request, simulation_id, simulation_folder, cfg_file)
sim_metadata["status"] = "pending"
MetadataManager.save_simulation_metadata(simulation_folder, sim_metadata)
```

---

### Phase 3: Simulation Execution (User Clicks "启动仿真")
**When**: User clicks [启动仿真] or system auto-starts batch
**What Gets Updated**:
- ✅ `cases/{case_id}/simulations/{sim_id}/simulation_metadata.json` - **STATUS UPDATED TO "running"**
- ✅ `cases/{case_id}/metadata.json` - **STATUS UPDATED TO "simulating"**

**Status at This Point**:
```json
{
  "status": "running",
  "started_at": "2025-11-13T12:07:00"
}
```

---

## Complete Case Status Identification Timeline

```
T0: User creates case from scenario_browser.html
    │
    ├─ ✅ cases/{case_id}/metadata.json created
    │  ├─ source_scenario: {scenario_id, event_id, event_type}
    │  └─ status: "created" or "od_generating"
    │
    ├─ ✅ scenario_index.json updated
    │  └─ created_cases array: [case_id, status, created_at]
    │
    └─ Frontend can display: "✓ 已创建" or "⏳ 生成中"

T1: User clicks [仿真] to prepare simulations
    │
    ├─ ✅ cases/{case_id}/simulations/{sim_id}/simulation_metadata.json created
    │  ├─ source_scenario copied from case metadata
    │  └─ status: "pending"
    │
    └─ Frontend can display: "⏳ 等待启动"

T2: System starts simulation (click "启动" or auto-start)
    │
    ├─ ✅ simulation_metadata.json status updated to "running"
    ├─ ✅ case metadata status updated to "simulating"
    │
    └─ Frontend can display: "▶️ 仿真中"

T3: Simulation completes
    │
    ├─ ✅ simulation_metadata.json status updated to "completed"
    ├─ ✅ case metadata status updated to "completed"
    │
    └─ Frontend can display: "✅ 已完成"
```

---

## How to Identify Event Scenario Case Status **BEFORE** simulation_metadata.json Created

### At T0-T1 (Case Created, Before Simulation Prepared)

**Method 1: Read scenario_index.json** (Recommended)
```javascript
// In scenario_browser.js (ALREADY IMPLEMENTED)
const response = await fetch('/output/scenarios/scenario_index.json');
for (const scenario of data.scenarios) {
    const created_cases = scenario.created_cases || [];  // Array of case records
    // Each case has: case_id, status, created_at, source_scenario
}
```

**Method 2: Read case metadata.json**
```python
# In backend
from pathlib import Path
import json

case_path = Path("cases") / case_id
metadata_file = case_path / "metadata.json"
with open(metadata_file) as f:
    case_metadata = json.load(f)

status = case_metadata.get("status")  # "created", "od_generating", etc.
source_scenario = case_metadata.get("source_scenario")  # Confirms it's v2.0
```

**What You Can Tell**:
- ✅ Case exists
- ✅ Case status (created, od_generating, processing)
- ✅ Source scenario ID
- ✅ OD file status (from od_file_info.json)
- ❌ Simulation status (simulation_metadata.json doesn't exist yet)

---

## Key Insight: Three-Level Status Identification

### Level 1: Case Level (Immediate, No Simulation Yet)
**Files Available**:
- `cases/{case_id}/metadata.json`
- `scenario_index.json` (created_cases)
- `cases/{case_id}/config/od_file_info.json`

**Status Fields**:
```json
{
  "status": "created",           // Case creation status
  "source_scenario": {...},      // Links to scenario
  "od_file_status": "exists",    // OD file readiness
  "od_generation_started": true  // OD generation tracking
}
```

**What frontend Can Display**:
```
scenario_browser.html:
  • "✓ 已创建" (case exists)
  • "⏳ 生成中" (OD generation in progress)
  • "✗ 失败" (OD generation failed)
```

### Level 2: Simulation Level (After Prepare, Before Start)
**Files Available**:
- `cases/{case_id}/simulations/{sim_id}/simulation_metadata.json`
- `cases/{case_id}/simulations/{sim_id}/simulation.sumocfg`

**Additional Status Fields**:
```json
{
  "status": "pending",                    // Simulation preparation status
  "simulation_id": "sim_20251113_120530",
  "source_scenario": {...},               // Copied from case
  "created_at": "2025-11-13T12:05:30"
}
```

**What frontend Can Display**:
```
case-simulation-center.html:
  • "⏳ 等待启动" (prepared, pending execution)
  • "▶️ 仿真中" (running)
  • "✅ 已完成" (completed)
```

### Level 3: Analysis Level (After Simulation Completes)
**Files Available**:
- `cases/{case_id}/analysis/batch_id/analysis_metadata.json`

**Status Fields**:
```json
{
  "status": "running",
  "source_scenario": {...},  // Backtracked from simulation
  "tasks_completed": 50,
  "total_tasks": 100
}
```

---

## Practical: How scenario_browser.js Identifies Status

**Current Implementation** (Lines 23-111 in scenario_browser.js):

```javascript
// Strategy 1: Primary - Read scenario_index.json directly
try {
    const response = await fetch('/output/scenarios/scenario_index.json');
    for (const scenario of data.scenarios) {
        const scenario_id = scenario.files.scenario_dir;
        const created_cases = scenario.created_cases || [];  // THIS is the key

        scenarioCaseMap[scenario_id] = created_cases.map(c => ({
            case_id: c.case_id,
            status: c.status,           // ← Status from scenario metadata!
            created_at: c.created_at
        }));
    }
}

// Usage in renderScenarios():
function getScenarioStatusDisplay(scenario_id) {
    const cases = scenarioCaseMap[scenario_id] || [];
    if (cases.length === 0) {
        return '<span class="status-badge status-none">— 未创建</span>';
    }

    const caseItem = cases[0];
    const status = caseItem.status;  // Read from created_cases[0].status

    switch(status) {
        case 'created':
            return '<span class="status-badge status-success">✓ 已创建</span>';
        case 'od_generating':
            return '<span class="status-badge status-progress">⏳ 生成中</span>';
        case 'completed':
            return '<span class="status-badge status-completed">✅ 已完成</span>';
    }
}
```

---

## Design Decision: Why Not Wait for simulation_metadata.json?

**Answer**: Because we shouldn't!

✅ **For Case Creation Status** (Before Simulation):
- Case metadata and scenario_index.json available immediately
- No need to wait for simulation preparation
- Users need immediate feedback that case was created

❌ **If We Waited for simulation_metadata.json**:
- Delay between case creation and status display
- User doesn't know if case creation succeeded
- Worse UX

---

## Implementation Timeline Summary

| Event | Files Created | Status Available | Frontend Display |
|-------|---------------|-----------------|-----------------|
| Case created | metadata.json, scenario_index.json | ✅ Immediate | "✓ 已创建" |
| OD generating | (updated status) | ✅ Immediate | "⏳ 生成中" |
| OD complete | (updated status) | ✅ Immediate | "✓ 已创建" |
| Simulation prep | simulation_metadata.json | ✅ After prep | "⏳ 等待启动" |
| Simulation start | (updated status) | ✅ After start | "▶️ 仿真中" |
| Simulation done | (updated status) | ✅ After done | "✅ 已完成" |

---

## Answer to "When simulation_metadata.json Created?"

**Short Answer**:
- **Created**: During `prepare_simulation()` phase (when user clicks [仿真])
- **Before This**: Only case metadata exists

**Timeline**:
```
T0: Case creation
   └─ metadata.json created ✅
   └─ scenario_index.json updated ✅
   └─ simulation_metadata.json NOT YET ❌

T1: Simulation preparation (user clicks [仿真])
   └─ metadata.json exists ✅
   └─ scenario_index.json exists ✅
   └─ simulation_metadata.json created ✅
   └─ simulation.sumocfg created ✅

T2: Simulation execution (user clicks [启动])
   └─ simulation_metadata.json status updated to "running"
```

---

## Answer to "How to Identify Case Status BEFORE simulation_metadata.json?"

**Primary Method** (Implemented ✅):
```
Read scenario_index.json → created_cases array → case status
↓
Instant, No simulation needed
```

**Alternative Methods**:
1. **Read case metadata.json** - Direct status check
2. **Check od_file_info.json** - OD generation status
3. **API call** - Fallback, more comprehensive

**Example**:
```javascript
// scenario_browser.js already does this correctly!
const response = await fetch('/output/scenarios/scenario_index.json');
const scenarios = response.data.scenarios;
const targetScenario = scenarios.find(s => s.files.scenario_dir === "scenario_10754_no_control");
const cases = targetScenario.created_cases;  // Already have status!
const status = cases[0].status;  // "created", "od_generating", etc.
```

---

## Summary

**When is simulation_metadata.json created?**
- During `prepare_simulation()` when user clicks [仿真] button
- Not at case creation time

**How to identify case status BEFORE simulation_metadata.json?**
- ✅ **Implemented**: Read `scenario_index.json` → `created_cases` array
- Alternative: Read `cases/{case_id}/metadata.json` directly
- Fallback: API call to `/api/v1/case/list_cases`

**Current Implementation Status**:
- ✅ scenario_browser.js correctly uses scenario_index.json
- ✅ Case status displays immediately after creation
- ✅ No waiting for simulation_metadata.json
- ✅ Backward compatible with cases without created_cases

---

**Conclusion**: The implementation correctly handles case status identification before simulation_metadata.json is created! ✅
