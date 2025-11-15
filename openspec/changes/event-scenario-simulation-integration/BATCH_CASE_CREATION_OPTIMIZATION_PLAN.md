# Batch Case Creation - Warning Optimization Plan

**Date**: 2025-11-15
**Status**: 🟡 OPTIMIZATION IN PROGRESS
**Focus**: Eliminate warnings in batch event scenario case creation

---

## Executive Summary

Analysis of batch case creation logs reveals **4 categories of warnings** that can be eliminated through targeted optimizations:

1. **Edge ID Validation** - Invalid edge IDs in network
2. **Route File (.rou.xml) Resolution** - Late file resolution warning
3. **Additional File Auto-Discovery** - Missing configuration in simulation_params
4. **EdgeData Collection Mode** - Full network collection instead of event-specific

All warnings are non-critical (system continues functioning) but degrade user experience and log clarity.

---

## Warning Categories & Fixes

### 1. Edge ID Validation Warning
**Warning Log**:
```
边缘ID不存在于路网中: 3734
```

**Root Cause**: Edge ID 3734 from control strategy doesn't exist in network file

**Location**: Likely in edgedata configuration or control strategy validation

**Fix Strategy**:
- Validate edge IDs against network before including in config
- Silently skip invalid edges instead of warning
- Only warn if ALL edges are invalid

**Implementation**:
- Add validation in EdgeData config generation (sumo_utils.py:278-350)
- Check against network topology before collection

---

### 2. Route File (.rou.xml) Resolution Warning
**Warning Log**:
```
⚠️ 未找到 .rou.xml 文件，使用原始引用: config/dwd.dwd_od_weekly
```

**Root Cause**: OD file reference points to `dwd.dwd_od_weekly` (table name), but actual `.rou.xml` is named `dwd_od_weekly_20250610101348_20250610114450.rou.xml` (table + timestamps)

**Location**: `shared/utilities/sumo_utils.py:200-220`

**Current Behavior**:
1. Simulation_params contains `config/dwd.dwd_od_weekly` (database table reference)
2. Code looks for `.rou.xml` files matching pattern `{table_name}*.rou.xml`
3. If found, uses it (silent success)
4. If NOT found, warns and falls back to table reference

**Why Warning Occurs**:
- OD generation happens AFTER case creation
- Initial sumocfg generation happens when OD files don't exist yet
- Later, after OD is generated, sumocfg is regenerated correctly
- The first generation attempt shows warning, second regeneration is silent

**Fix Strategy**:
- Change from warning to silent fallback (it's expected behavior)
- Replace `print(warning)` with logging at DEBUG level
- Document this as expected behavior in comments

**Implementation**:
```python
# BEFORE:
print(f"⚠️ 未找到 .rou.xml 文件，使用原始引用: {routes_file_ref}")

# AFTER:
logger.debug(f"Route file not yet generated, using table reference: {routes_file_ref}")
```

**Rationale**: This is normal workflow - .rou.xml files are generated after case metadata is set up. The fallback to table reference is correct and expected.

---

### 3. Scenario Additional File Auto-Discovery Warning
**Warning Log**:
```
⚠️ No scenario_additional_file in simulation_params, auto-discovering .add.xml files in simulation directory...
✓ Auto-discovered: scenario_accident_event_10754.add.xml
```

**Root Cause**: `scenario_additional_file` not set in `simulation_params` during initial creation

**Location**: `shared/utilities/sumo_utils.py` (generates sumocfg with auto-discovery)

**Current Behavior**:
1. Simulations created without explicit `scenario_additional_file` in params
2. During sumocfg generation, code auto-discovers `.add.xml` files in simulation directory
3. Prints warning that auto-discovery is happening

**Fix Strategy**:
- Explicitly set `scenario_additional_file` during simulation creation
- Remove auto-discovery fallback or make it silent
- Store discovered files in simulation metadata

**Implementation**:
- Modify `case_service.py` to detect and set `scenario_additional_file` during simulation creation
- Extract scenario `.add.xml` path from case metadata
- Pass it explicitly to sumocfg generation

---

### 4. EdgeData Collection Mode Warning
**Warning Log**:
```
⚠️ EdgeData 配置: 收集全路网数据（未检测到事件边信息）
  - 注意: 全路网模式会影响仿真性能（速度降低 15-30%）
```

**Root Cause**: Event edge information not found in case metadata during first iteration

**Location**: `shared/utilities/sumo_utils.py:280-295`

**Current Behavior**:
1. First sumocfg generation: Event scenario metadata might not be complete
2. Code checks `case_metadata['event_scenario']['event_location']['edge_id']`
3. If not found, falls back to full network collection (with warning)
4. Later regeneration finds the data correctly

**Fix Strategy**:
- Ensure event location data is set before sumocfg generation
- Remove warning or make it debug-level
- Document the expected behavior

**Implementation**:
- Ensure `case_metadata['event_scenario']` is fully populated before any sumocfg generation
- Move EdgeData configuration decision earlier in the workflow
- Use logging.debug instead of print for informational messages

---

## Files Requiring Changes

| File | Changes | Severity |
|------|---------|----------|
| `shared/utilities/sumo_utils.py` | Replace warnings with debug logging (Lines 216, ~295) | Medium |
| `api/services/case_service.py` | Ensure scenario_additional_file is set explicitly | Medium |
| `shared/utilities/sumo_utils.py` | Add edge ID validation before EdgeData config | High |

---

## Implementation Steps

### Step 1: Convert Warnings to Debug Logging
**File**: `shared/utilities/sumo_utils.py`

Replace 2 warning prints with logging.debug():
- Line 216: `.rou.xml` not found warning
- Line 295 area: EdgeData full network warning

**Benefit**: Reduces noise in logs, keeps diagnostic info in debug output

### Step 2: Explicit scenario_additional_file Setting
**File**: `api/services/case_service.py`

During simulation creation:
- Detect scenario `.add.xml` files from case
- Set `simulation_params['scenario_additional_file']` explicitly
- Store in simulation metadata

**Benefit**: Eliminates auto-discovery warning by providing explicit configuration

### Step 3: Edge ID Validation
**File**: `shared/utilities/sumo_utils.py`

Before EdgeData configuration:
- Validate each edge_id against network topology
- Skip invalid edges silently
- Only create EdgeData config for valid edges

**Benefit**: Prevents "edge ID not found" warnings by filtering invalid IDs

### Step 4: Consolidate Event Metadata
**File**: `api/services/case_service.py`

Ensure event_scenario metadata is fully populated:
- Event location with edge_id
- Event type
- Affected edges list

Before sumocfg regeneration, not after.

---

## Expected Results After Optimization

### Before:
```
⚠️ 未找到 .rou.xml 文件，使用原始引用: config/dwd.dwd_od_weekly       ← GONE
⚠️ No scenario_additional_file in simulation_params...              ← GONE
✓ Auto-discovered: scenario_accident_event_10754.add.xml            ← GONE (explicit instead)
⚠️ EdgeData 配置: 收集全路网数据（未检测到事件边信息）             ← GONE (event info present)
边缘ID不存在于路网中: 3734                                         ← FIXED (filtered)
```

### After:
```
✓ Route file will be generated: dwd_od_weekly_20250610101348_20250610114450.rou.xml
✓ Scenario additional file set: scenario_accident_event_10754.add.xml
✓ EdgeData configuration optimized for event edges: 2 event edges
✓ 批量创建完成: 3/3 成功, 耗时 1.79秒
```

**Net Result**: Clean, warning-free batch case creation logs with only success messages.

---

## Priority & Effort

| Fix | Priority | Effort | Impact |
|-----|----------|--------|--------|
| Step 1: Debug logging | Medium | 15 min | High (noise reduction) |
| Step 2: Explicit file setting | Medium | 30 min | Medium (auto-discovery removal) |
| Step 3: Edge validation | High | 1 hour | High (error elimination) |
| Step 4: Metadata consolidation | Medium | 30 min | Medium (warning prevention) |

**Total Effort**: ~2.5 hours
**Expected Impact**: ~95% warning reduction

---

## Risk Assessment

**Risk Level**: 🟢 **LOW**

- Changes are isolated to configuration and logging
- No API changes
- No breaking changes to existing workflows
- All changes maintain backward compatibility

**Validation Strategy**:
- Test batch case creation with same event scenario
- Verify no warnings in output logs
- Verify sumocfg files are correctly generated
- Run batch creation with multiple scenarios

---

## Success Criteria

- [ ] Step 1: Warnings converted to debug logging
- [ ] Step 2: scenario_additional_file explicitly set
- [ ] Step 3: Edge ID validation implemented
- [ ] Step 4: Event metadata consolidated
- [ ] Batch case creation produces clean logs
- [ ] All simulations complete successfully
- [ ] Generated sumocfg files are correct
- [ ] No breaking changes to existing workflows

---

## Next Steps

1. Read detailed implementations in sumo_utils.py and case_service.py
2. Implement Step 1 (logging conversion)
3. Implement Step 2 (explicit file setting)
4. Implement Step 3 (edge validation)
5. Implement Step 4 (metadata consolidation)
6. Test batch creation
7. Verify logs are clean
8. Commit changes

---

*Status*: Ready for implementation
*Estimated Start*: Immediate
*Estimated Completion*: 2-3 hours

