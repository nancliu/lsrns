# TAZ 文件重复引入问题修复

**Date**: 2025-11-14
**Status**: ✅ FIXED
**Priority**: P1
**Issue**: TAZ file duplicated in sumocfg additional-files list

---

## Problem

### Observed Issue

用户创建案例后，sumocfg 中 TAZ 文件被重复引入：

```xml
<additional-files value="TAZ_6.add.xml,edgeData.add.xml,../../config/scenario_accident_vss_10807.add.xml,../../config/TAZ_6.add.xml"/>
```

**问题分析**:
- `TAZ_6.add.xml` (第1个) - 从 `taz_files` 列表来（正确）
- `../../config/TAZ_6.add.xml` (第4个) - 从 `case_additional_files` 列表来（错误）

### Root Cause

**问题1**: 元数据创建时包含所有 .add.xml 文件

**位置**: `scripts/initialize_scenario_library.py:474-477`

```python
# Find .add.xml files in case config
config_dir = case_path / "config"
add_xml_files = list(config_dir.glob("*.add.xml"))
additional_files = [f"config/{f.name}" for f in add_xml_files]
# ❌ 这会包含：
#    1. scenario_accident_vss_10807.add.xml ✅ (事件场景文件，应该包含)
#    2. TAZ_6.add.xml ❌ (TAZ 文件，不应该包含，已有 taz_file 字段)
```

**问题2**: sumocfg 生成时没有去重

**位置**: `shared/utilities/sumo_utils.py:336`

```python
# 构建 additional 文件列表（TAZ + edgeData + 管控策略 + 事件场景）
additional_files = taz_files + edgedata_files + control_files + case_additional_files
# ❌ 如果 TAZ 文件同时在 taz_files 和 case_additional_files 中，会重复
```

---

## Solution

### Fix 1: 元数据创建时过滤 TAZ 文件

**File**: `scripts/initialize_scenario_library.py` (Lines 474-484)

```python
# Find .add.xml files in case config
config_dir = case_path / "config"
add_xml_files = list(config_dir.glob("*.add.xml"))

# Filter out TAZ files (they should be handled via taz_file field, not additional_files)
# TAZ files typically named: TAZ_*.add.xml
taz_filename = Path(taz_file).name if taz_file else None
additional_files = [
    f"config/{f.name}" for f in add_xml_files
    if not (taz_filename and f.name == taz_filename)  # ✅ Exclude TAZ file to avoid duplication
]
```

**效果**: 新创建的案例 metadata 中 `additional_files` 只包含事件场景文件，不包含 TAZ 文件。

### Fix 2: sumocfg 生成时去重

**File**: `shared/utilities/sumo_utils.py` (Lines 335-351)

```python
# 构建 additional 文件列表（TAZ + edgeData + 管控策略 + 事件场景）
additional_files_raw = taz_files + edgedata_files + control_files + case_additional_files

# 去重：防止同一文件被多次引入（如 TAZ 文件可能在 taz_files 和 case_additional_files 中都存在）
seen = set()
additional_files = []
for file_path in additional_files_raw:
    # 标准化路径用于比较（去除路径分隔符差异）
    normalized = file_path.replace('\\', '/').lower()
    file_basename = Path(normalized).name

    # 检查是否已经添加过相同的文件（通过文件名判断）
    if file_basename not in seen:
        seen.add(file_basename)
        additional_files.append(file_path)
    else:
        print(f"⚠️ 跳过重复文件: {file_path} (已通过其他路径引入)")
```

**效果**:
- 防止重复引入（基于文件名去重）
- 保护已有的案例（在 metadata 中仍有 TAZ 的老案例）
- 输出警告日志，便于调试

---

## Expected Behavior After Fix

### 新创建的案例

**metadata.json**:
```json
{
  "files": {
    "taz_file": "config/TAZ_6.add.xml",
    "additional_files": [
      "config/scenario_accident_vss_10807.add.xml"  // ✅ 只有事件场景文件
    ]
  }
}
```

**sumocfg**:
```xml
<additional-files value="TAZ_6.add.xml,edgeData.add.xml,../../config/scenario_accident_vss_10807.add.xml"/>
```

**文件列表**:
1. `TAZ_6.add.xml` - TAZ + E1 detectors (从 taz_files)
2. `edgeData.add.xml` - Edge data collection (从 edgedata_files)
3. `../../config/scenario_accident_vss_10807.add.xml` - Event scenario (从 case_additional_files)

✅ **无重复，顺序清晰**

### 已有的案例（向后兼容）

对于已创建的案例（metadata 中 additional_files 包含 TAZ 文件）：

**sumocfg 生成时**:
```
TAZ文件已复制到仿真目录: TAZ_6.add.xml
Adding event scenario additional file: ../../config/scenario_accident_vss_10807.add.xml
Adding event scenario additional file: ../../config/TAZ_6.add.xml
⚠️ 跳过重复文件: ../../config/TAZ_6.add.xml (已通过其他路径引入)  // ✅ 去重生效
```

**sumocfg**:
```xml
<additional-files value="TAZ_6.add.xml,edgeData.add.xml,../../config/scenario_accident_vss_10807.add.xml"/>
```

✅ **向后兼容，去重生效**

---

## Testing

### Test Case 1: 新案例创建

**步骤**:
1. 重启 API 服务
2. 从场景浏览器创建新案例
3. 检查 metadata.json
4. 检查 sumocfg

**预期**:
- metadata 中 `additional_files` 不包含 TAZ 文件 ✅
- sumocfg 中 TAZ 文件只出现一次 ✅

### Test Case 2: 已有案例重新生成 sumocfg

**步骤**:
1. 使用已有案例（metadata 中包含 TAZ）
2. 重新生成 sumocfg
3. 检查日志和 sumocfg

**预期**:
- 日志显示 "⚠️ 跳过重复文件" ✅
- sumocfg 中 TAZ 文件只出现一次 ✅

---

## Files Modified

1. **scripts/initialize_scenario_library.py** (Lines 474-484)
   - Added TAZ file filtering in metadata creation

2. **shared/utilities/sumo_utils.py** (Lines 335-351)
   - Added deduplication logic for additional files

---

## Related Issues

- **Original Fix**: SUMOCFG_ADDITIONAL_FILES_FIX.md (事件场景文件缺失)
- **Performance Fix**: PHASE3_CRITICAL_FIXES_SUMMARY.md (EdgeData 优化)
- **TAZ Configuration**: ADD_XML_FILES_ANALYSIS.md (TAZ 文件分析)

---

**Implementation Date**: 2025-11-14
**Status**: Ready for testing
**Backward Compatible**: ✅ Yes
