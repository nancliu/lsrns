# Simulation Metadata source_scenario Implementation Guide

**Date**: 2025-11-13
**Status**: 📋 IMPLEMENTATION PLAN (Ready to Code)
**Relates to**: Q16 Decision, Task 1.4 (Three-Level Metadata Tracking)

---

## Why simulation_metadata.json Needs source_scenario

### Current State (After Case Creation)
```
scenario_index.json ✅
├─ created_cases: [case_id, status, source_scenario]
└─ Connects: Scenario → Case

cases/{case_id}/metadata.json ✅
├─ source_scenario: {scenario_id, event_id, event_type}
└─ Connects: Case → Scenario
```

### Gap: Simulation → Scenario Missing ❌
```
simulation_metadata.json (Current, v1.0)
├─ simulation_id, case_id, status
└─ NO source_scenario field
└─ Cannot trace: Simulation → Scenario

Analysis results
├─ No scenario lineage
└─ Cannot show "This analysis is from scenario X"
```

### Solution: Add source_scenario to simulation_metadata.json ✅
```
simulation_metadata.json (v2.0, After Implementation)
├─ simulation_id, case_id, status
├─ source_scenario: {scenario_id, event_id, event_type}  ← NEW
└─ Enables: Simulation → Case → Scenario full chain
```

---

## Implementation: When and How

### Timeline
```
T0: Case created
    └─ case_metadata.json has source_scenario ✅

T1: Simulation prepared (prepare_simulation called)
    ├─ simulation_metadata.json created
    ├─ Should copy source_scenario from case_metadata ← NEED THIS
    └─ Enable: Simulation → Scenario link

T2: Simulation executed
    └─ Analysis results link to simulation
       └─ Which has source_scenario
       └─ Complete lineage possible ✓
```

### Code Location: SimulationService._create_simulation_metadata()

**Current Code** (simulation_service.py:229-299):
```python
def _create_simulation_metadata(self, request: SimulationRequest, simulation_id: str,
                                simulation_folder: Path, cfg_file: str) -> Dict[str, Any]:
    """创建仿真元数据"""

    # Phase 2: 提取 source_scenario 用于三级元数据追踪 (Task 1.4)
    source_scenario = None
    metadata_version = "1.0"  # 默认 v1.0 (向后兼容)

    try:
        case_path = Path("cases") / request.case_id
        case_metadata = MetadataManager.load_case_metadata(case_path)

        # 检测元数据版本 (使用 BaseService 方法)
        metadata_version = self.detect_metadata_version(case_metadata)

        # 如果是 v2.0 事件场景案例,提取 source_scenario
        if metadata_version == "2.0" and "source_scenario_id" in case_metadata:
            source_scenario = {
                "scenario_id": case_metadata.get("source_scenario_id"),
                "event_id": case_metadata.get("source_event_id"),
                "event_type": case_metadata.get("immutable_fields", {}).get("event_type"),
                "control_strategy_type": case_metadata.get("immutable_fields", {}).get("strategy")
            }
    except Exception:
        # 如果无法提取,保持 None (向后兼容)
        pass

    metadata = {
        "simulation_id": simulation_id,
        "case_id": request.case_id,
        "status": "running",
        "created_at": datetime.now().isoformat(),
        # ... other fields
    }

    # Phase 2: 添加 v2.0 字段 (如果适用)
    if metadata_version == "2.0":
        metadata["metadata_version"] = "2.0"
        if source_scenario:
            metadata["source_scenario"] = source_scenario

    return metadata
```

**Issue Found**: Code looks for `source_scenario_id` but case_metadata has `source_scenario` object!

### Correct Fix Needed

**Problem**:
```python
# Line 266 - Wrong field name!
if metadata_version == "2.0" and "source_scenario_id" in case_metadata:
    # ❌ Looking for "source_scenario_id" but it doesn't exist
    # ✅ Should look for "source_scenario"
```

**Correct Implementation** (What needs to be fixed):
```python
def _create_simulation_metadata(self, request: SimulationRequest, simulation_id: str,
                                simulation_folder: Path, cfg_file: str) -> Dict[str, Any]:
    """创建仿真元数据 (v2.0 with full scenario lineage)"""

    # ... existing code ...

    # Phase 2: 提取 source_scenario 用于三级元数据追踪 (Task 1.4)
    source_scenario = None
    metadata_version = "1.0"

    try:
        case_path = Path("cases") / request.case_id
        case_metadata = MetadataManager.load_case_metadata(case_path)

        # 检测元数据版本
        metadata_version = self.detect_metadata_version(case_metadata)

        # 如果是 v2.0 事件场景案例,直接复制 source_scenario
        if metadata_version == "2.0":
            source_scenario = case_metadata.get("source_scenario")
            # source_scenario 结构:
            # {
            #   "scenario_id": "scenario_10754_no_control",
            #   "event_id": "10754",
            #   "event_type": "交通事故",
            #   "control_strategy_type": "NO_CONTROL"
            # }
    except Exception as e:
        logger.warning(f"Failed to extract source_scenario: {e}")
        # 降级:如果无法提取,保持 None (向后兼容)

    metadata = {
        "metadata_version": "2.0" if metadata_version == "2.0" else "1.0",
        "simulation_id": simulation_id,
        "case_id": request.case_id,
        "simulation_name": request.simulation_name,
        "simulation_type": request.simulation_type.value,
        "simulation_params": request.simulation_params or {},
        "status": "pending",  # ← 注意这里是 pending 在 prepare 阶段
        "created_at": datetime.now().isoformat(),
        "started_at": None,  # 启动时才设置
        "description": request.simulation_description,
        "result_folder": str(simulation_folder),
        "config_file": cfg_file,
        "input_files": input_files,
        "gui": request.gui,

        # Phase 2: 添加 source_scenario 以支持完整的三级元数据追踪
        **({"source_scenario": source_scenario} if source_scenario else {})
    }

    return metadata
```

---

## Expected Output After Fix

### Before (v1.0, OD Extraction Case)
```json
{
  "simulation_id": "sim_20251113_120530",
  "case_id": "case_20251016_113040",
  "status": "pending",
  "created_at": "2025-11-13T12:05:30"
}
```

### After (v2.0, Event Scenario Case)
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
    "event_type": "交通事故",
    "control_strategy_type": "NO_CONTROL"
  },

  "simulation_params": {...},
  "input_files": {...}
}
```

---

## How This Enables Full Lineage

### Complete Three-Level Chain

```
1. Scenario Level (scenario_index.json)
   created_cases: [{
     case_id: "case_20251113_120000",
     source_scenario: "scenario_10754_no_control"
   }]

2. Case Level (cases/{case_id}/metadata.json)
   source_scenario: {
     scenario_id: "scenario_10754_no_control",
     event_id: "10754",
     event_type: "交通事故"
   }

3. Simulation Level (simulation_metadata.json) ← AFTER FIX
   source_scenario: {
     scenario_id: "scenario_10754_no_control",
     event_id: "10754",
     event_type: "交通事故"
   }

4. Analysis Level (analysis_metadata.json) ← FUTURE
   source_scenario: {
     scenario_id: "scenario_10754_no_control",
     event_id: "10754",
     event_type: "交通事故"
   }
```

### What This Enables

```javascript
// In analysis_viewer.html
async function showAnalysisLineage(analysisId) {
    const analysis = await fetch(`/analysis/${analysisId}`);
    const simulation = await fetch(`/simulation/${analysis.simulation_id}`);

    // Get scenario info from any level!
    const scenario = analysis.source_scenario ||
                     simulation.source_scenario ||
                     case.source_scenario;

    // Display lineage
    console.log(`Analysis from ${scenario.event_type} event in scenario ${scenario.scenario_id}`);

    // Backtrack to original scenario
    const scenarioData = await fetch(`/scenario/${scenario.scenario_id}`);
}
```

---

## Implementation Checklist

### Step 1: Fix simulation_service.py
- [ ] Line 266: Change `"source_scenario_id" in case_metadata` to `"source_scenario" in case_metadata`
- [ ] Line 268-271: Simplify to `source_scenario = case_metadata.get("source_scenario")`
- [ ] Add logging for source_scenario extraction
- [ ] Test with v2.0 case (should have source_scenario)
- [ ] Test with v1.0 case (should have source_scenario = None, still works)

### Step 2: Verify Metadata Structure
- [ ] Check case metadata uses correct `source_scenario` field name
- [ ] Verify QuickCaseCreator populates `source_scenario` in case metadata
- [ ] Confirm format matches across all three levels

### Step 3: Test Full Chain
- [ ] Create event scenario case
- [ ] Verify case metadata has source_scenario
- [ ] Prepare simulation
- [ ] Verify simulation metadata has source_scenario
- [ ] (Future) Run analysis
- [ ] (Future) Verify analysis metadata has source_scenario

### Step 4: Documentation
- [ ] Update CLAUDE.md with v2.0 metadata structure
- [ ] Document source_scenario propagation pattern
- [ ] Add examples to API documentation

---

## Backward Compatibility Proof

```python
# If case is v1.0 (no source_scenario)
case_metadata = {
    "case_id": "case_20251016_113040",  # Old OD extraction case
    "metadata_version": "1.0",           # Implicit
    # NO source_scenario field
}

# Detection works correctly
metadata_version = detect_metadata_version(case_metadata)  # Returns "1.0"
source_scenario = case_metadata.get("source_scenario")    # Returns None

# Simulation metadata is also v1.0 compatible
simulation_metadata = {
    "simulation_id": "sim_...",
    "case_id": "case_20251016_113040",
    "status": "pending"
    # NO source_scenario, NO metadata_version
}
# ✅ Works fine, no errors, backward compatible
```

---

## Why This Matters

### Use Case 1: Analysis Results UI
```
User views analysis results for a simulation
→ Can show "This simulation was created from scenario X"
→ User can click to see original scenario
→ Complete workflow transparency
```

### Use Case 2: Audit Trail
```
Find which simulations came from which scenarios
SELECT * FROM simulations WHERE source_scenario.event_type = '交通事故'
→ Can report on specific event type impacts
```

### Use Case 3: Comparison Analysis
```
Compare results across all simulations from same event
→ Aggregate metrics for event_id = "10754"
→ Show impact of different control strategies
```

---

## Test Case: Before and After

### Before (Missing source_scenario)
```bash
# Simulate case creation from scenario
POST /api/v1/case/create-from-scenario
  scenario_id: "scenario_10754_no_control"

# Check case metadata ✅
GET cases/case_20251113_120000/metadata.json
  source_scenario: {scenario_id, event_id, event_type} ✅

# Prepare simulation
POST /api/v1/simulation/prepare
  case_id: "case_20251113_120000"

# Check simulation metadata ❌
GET cases/case_20251113_120000/simulations/sim_xxx/simulation_metadata.json
  # NO source_scenario field - BROKEN LINEAGE
```

### After (With source_scenario)
```bash
# Same flow as before

# But now check simulation metadata ✅
GET cases/case_20251113_120000/simulations/sim_xxx/simulation_metadata.json
  source_scenario: {scenario_id, event_id, event_type} ✅
  # Full lineage preserved!
```

---

## Priority and Effort

**Priority**: P0 (Completes AD-12 Three-Level Tracking)
**Effort**: 1 hour (simple fix + testing)
**Benefit**: Complete metadata lineage for analysis results
**Risk**: None (backward compatible, optional field)

---

## Files to Modify

1. **api/services/simulation_service.py**
   - Lines 254-275: Fix source_scenario extraction
   - Lines 293-297: Add source_scenario to metadata dict
   - Effort: ~10 lines changed

2. **Test: test_simulation_metadata_v2.py** (New)
   - Test v2.0 case → v2.0 simulation with source_scenario
   - Test v1.0 case → v1.0 simulation without source_scenario
   - Effort: ~50 lines

---

## Summary

**Current Issue**: simulation_metadata.json has wrong field check for source_scenario
**Solution**: Fix line 266 to check for `"source_scenario"` instead of `"source_scenario_id"`
**Benefit**: Complete three-level metadata tracking (scenario → case → simulation → analysis)
**Effort**: ~1 hour
**Risk**: None (backward compatible)

**Ready to Implement**: ✅ Yes
**Blocking**: ❌ No (optional enhancement, case status display works without it)
**Urgency**: Can be done in Phase 2 Task 1.4
