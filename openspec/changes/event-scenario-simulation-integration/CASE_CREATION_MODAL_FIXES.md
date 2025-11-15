# Case Creation Modal Fixes

**Status**: ✅ COMPLETED
**Date**: 2025-11-14
**Related**: CASE_CREATION_MODAL_IMPLEMENTATION.md

---

## Issues Identified from Screenshot

Based on user feedback and screenshot analysis (`createcasefromscenario.png`), the following issues were identified:

1. **事件位置 (Event Location)**: All three fields showing "加载失败" (load failed)
2. **仿真时间 (Simulation Times)**: All three simulation time fields showing "配置文件不存在" (config file not found)
3. **OD表 (OD Table)**: Should be removed as it's fixed and not configurable
4. **车辆类型 (Vehicle Types)**: Should load from vehicle templates JSON file, not from traffic_input_config.json

---

## Root Causes

### 1. Event Location Loading Failure

**Problem**:
- Used `currentScenario.event_folder` which was undefined
- Directly used `eventType` parameter as folder name (Chinese text)
- Event folders are named in English (e.g., `01_accident`, `02_congestion`)

**Root Cause**:
```javascript
// WRONG - eventType is Chinese text like "交通事故"
const eventFolder = currentScenario.event_folder || eventType;
const eventDescUrl = `/output/scenarios/${eventType}/...`;
// Results in: /output/scenarios/交通事故/... (404 Not Found)
```

### 2. Simulation Time Loading Failure

**Problem**:
- Same root cause as event location - incorrect folder path
- Path construction failed because of Chinese text in URL

**Root Cause**:
```javascript
// WRONG - scenarioDir should be scenario_id, not undefined
const scenarioDir = currentScenario.scenario_dir || scenarioId;
// But scenario_dir doesn't exist in currentScenario object
```

### 3. OD Table Field

**Problem**:
- OD table is fixed and determined by the system
- Not a user-configurable parameter
- Should not be displayed in case creation modal

### 4. Vehicle Types Loading

**Problem**:
- Tried to load from `traffic_input_config.json`
- Vehicle types should come from vehicle template configuration
- Should reuse the same approach as OD simulation workflow

---

## Fixes Applied

### Fix 1: Event Location Extraction

**File**: `frontend/scenarios/scenario_browser.js` (Lines 942-946)

**Change**:
```javascript
// BEFORE
const eventFolder = currentScenario.event_folder || eventType;
const scenarioDir = currentScenario.scenario_dir || scenarioId;

// AFTER
// 使用 mapEventTypeToFolder 将中文事件类型映射到英文文件夹名称
const eventTypeChina = currentScenario.event_type || '交通事故';
const eventFolder = mapEventTypeToFolder(eventTypeChina);
const scenarioDir = currentScenario.scenario_id;
```

**Result**:
- ✅ Correctly maps "交通事故" → "01_accident"
- ✅ Correctly maps "交通阻塞" → "02_congestion"
- ✅ Uses `scenario_id` directly (which exists in currentScenario)
- ✅ Generates correct path: `/output/scenarios/01_accident/scenario_10762_no_control/event_description.json`

**Function Reference**:
```javascript
function mapEventTypeToFolder(eventType) {
    const eventTypeMap = {
        '交通事故': '01_accident',
        '交通阻塞': '02_congestion',
        '交通管制': '03_road_control',
        '恶劣天气': '06_weather',
        '路面异常': '06_weather',
        '拥堵': '02_congestion',
        '道路管制': '03_road_control',
        '车辆故障': '05_breakdown'
    };
    return eventTypeMap[eventType] || '01_accident';
}
```

### Fix 2: Simulation Time Extraction

**File**: `frontend/scenarios/scenario_browser.js` (Lines 992-1030)

**Change**:
- No code change needed for path construction (already fixed by Fix 1)
- Removed OD table loading logic
- Path now correctly uses `eventFolder` and `scenarioDir`

**Before**:
```javascript
// Used wrong eventFolder, resulted in 404
const trafficConfigUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/traffic_input_config.json`;
```

**After**:
```javascript
// Now uses correct eventFolder from mapEventTypeToFolder()
const trafficConfigUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/traffic_input_config.json`;
// Results in: /output/scenarios/01_accident/scenario_10762_no_control/traffic_input_config.json ✅
```

### Fix 3: Remove OD Table Field

**Files Modified**:
1. `frontend/scenarios/scenario_browser.html` (Lines 305-311)
2. `frontend/scenarios/scenario_browser.js` (Lines 992-1030)

**HTML Changes**:
```html
<!-- BEFORE: 2-column grid with OD表 and 车辆类型 -->
<div class="form-grid">
    <div class="form-group">
        <label>OD表</label>
        <input type="text" id="caseCreation_odTable" readonly>
    </div>
    <div class="form-group">
        <label>车辆类型</label>
        <input type="text" id="caseCreation_vehicleTypes" readonly>
    </div>
</div>

<!-- AFTER: Single field for 车辆类型模板 -->
<div class="form-grid">
    <div class="form-group">
        <label>车辆类型模板</label>
        <input type="text" id="caseCreation_vehicleTypes" readonly>
    </div>
</div>
```

**JavaScript Changes**:
```javascript
// REMOVED - No longer populate OD table
document.getElementById('caseCreation_odTable').value = trafficConfig.od_table || '未知';
```

### Fix 4: Vehicle Types from API Templates

**File**: `frontend/scenarios/scenario_browser.js` (Lines 1032-1056)

**Change**:
```javascript
// BEFORE - Tried to load from traffic_input_config.json
document.getElementById('caseCreation_vehicleTypes').value =
    (trafficConfig.vehicle_types && trafficConfig.vehicle_types.length > 0) ?
    trafficConfig.vehicle_types.join(', ') : '未知';

// AFTER - Load from vehicle templates API
// 加载车辆类型配置（从 vehicle templates API）
try {
    const vehicleTemplatesResponse = await fetch('/api/v1/template/vehicle');

    if (vehicleTemplatesResponse.ok) {
        const vehicleTemplates = await vehicleTemplatesResponse.json();

        // 查找 vehicle_types.json 模板（默认模板）
        const defaultTemplate = vehicleTemplates.find(t => t.name === 'vehicle_types.json');

        if (defaultTemplate) {
            document.getElementById('caseCreation_vehicleTypes').value = 'vehicle_types.json';
        } else if (vehicleTemplates.length > 0) {
            // 如果没有默认模板，使用第一个可用模板
            document.getElementById('caseCreation_vehicleTypes').value = vehicleTemplates[0].name;
        } else {
            document.getElementById('caseCreation_vehicleTypes').value = '未知';
        }
    } else {
        document.getElementById('caseCreation_vehicleTypes').value = '加载失败';
    }
} catch (error) {
    console.warn('加载vehicle templates失败:', error);
    document.getElementById('caseCreation_vehicleTypes').value = '加载失败';
}
```

**Benefits**:
- ✅ Reuses same approach as OD simulation workflow (frontend/script.js)
- ✅ Defaults to `vehicle_types.json` (standard 6-type configuration)
- ✅ Fallback to first available template if default not found
- ✅ Proper error handling with user-friendly messages

---

## Validation

### JavaScript Syntax
```bash
node -c frontend/scenarios/scenario_browser.js
# ✅ No errors
```

### Expected Behavior After Fixes

**事件位置 (Event Location)**:
- 道路: "G4京港澳高速" (or actual road name)
- 方向: "北向" (or actual direction)
- 里程: "1234.5 KM" (or actual mileage)

**时间信息 (Time Information)**:
- 事件开始时间: "2025-06-10 15:12:57"
- 事件结束时间: "2025-06-10 17:14:35"
- 事件持续时长: "2.03小时"
- 仿真开始时间: "2025-06-10 14:42:57" (loaded from traffic_input_config.json)
- 仿真结束时间: "2025-06-10 17:44:35" (loaded from traffic_input_config.json)
- 仿真时长: "3.03小时" (loaded from traffic_input_config.json)

**仿真参数 (Simulation Parameters)**:
- 车辆类型模板: "vehicle_types.json" (loaded from API)
- ~~OD表~~: REMOVED (no longer displayed)

---

## Comparison: Before vs After

| Field | Before (Round 1) | After Round 1 | After Round 2 (Final) |
|-------|------------------|---------------|----------------------|
| **道路** | 加载失败 | ✅ G5京昆高速（成雅段） | ✅ G5京昆高速（成雅段） |
| **方向** | 加载失败 | ✅ 下行 | ✅ 下行 |
| **里程** | 加载失败 | ❌ 加载失败 (wrong field) | ✅ K1834.3+000 |
| **仿真开始时间** | 配置文件不存在 | ✅ 2025-06-10 10:13:48 | ✅ 2025-06-10 10:13:48 |
| **仿真结束时间** | 配置文件不存在 | ✅ 2025-06-10 11:44:50 | ✅ 2025-06-10 11:44:50 |
| **仿真时长** | 配置文件不存在 | ✅ 1.52小时 | ✅ 1.52小时 |
| **OD表** | 配置文件不存在 | ❌ REMOVED | ❌ REMOVED |
| **车辆类型模板** | 配置文件不存在 | ❌ 加载失败 (wrong path) | ✅ vehicle_types.json |

---

## Additional Fixes (Round 2)

### Fix 5: Mileage Field Name Correction

**Problem**:
- Used `eventDesc.location?.mileage_km` but actual field is `mileage`
- Added unnecessary " KM" suffix when data already includes format like "K1834.3+000"

**File**: `frontend/scenarios/scenario_browser.js` (Line 959)

**Change**:
```javascript
// BEFORE
document.getElementById('caseCreation_mileage').value = eventDesc.location?.mileage_km ?
    `${eventDesc.location.mileage_km} KM` : '未知';

// AFTER
document.getElementById('caseCreation_mileage').value = eventDesc.location?.mileage || '未知';
```

**Data Format**:
- Field: `location.mileage`
- Format: "K1834.3+000" (already includes prefix and format)
- Example from `event_description.json`:
```json
{
  "location": {
    "road": "G5京昆高速（成雅段）",
    "direction": "下行",
    "mileage": "K1834.3+000"
  }
}
```

### Fix 6: Vehicle Templates API Path Correction

**Problem**:
- Used singular `/api/v1/template/vehicle` but correct path is plural `/api/v1/templates/vehicle`
- Caused 404 Not Found error when loading vehicle templates

**File**: `frontend/scenarios/scenario_browser.js` (Line 1033)

**Change**:
```javascript
// BEFORE
const vehicleTemplatesResponse = await fetch('/api/v1/template/vehicle');

// AFTER
const vehicleTemplatesResponse = await fetch('/api/v1/templates/vehicle');
```

**Reference**:
- OD Simulation uses: `apiFetch('${API_BASE_URL}/templates/vehicle')` (frontend/script.js:1230)
- API_BASE_URL = `/api/v1`
- Correct path: `/api/v1/templates/vehicle` (plural)

---

## Files Modified

1. **frontend/scenarios/scenario_browser.js**
   - Lines 942-946: Fixed event folder mapping
   - Line 959: Fixed mileage field name (mileage_km → mileage)
   - Lines 992-1030: Fixed simulation time loading, removed OD table
   - Line 1033: Fixed vehicle templates API path (template → templates)
   - Lines 1032-1056: Added vehicle templates API loading

2. **frontend/scenarios/scenario_browser.html**
   - Lines 305-311: Removed OD table field, updated label

---

## Related Functions

### Reused from Scenario Details Modal
- `mapEventTypeToFolder(eventType)` - Maps Chinese event types to English folder names

### Reused from OD Simulation Workflow
- Vehicle template API: `/api/v1/template/vehicle`
- Default template selection: `vehicle_types.json`

---

## Testing Checklist

- [x] JavaScript syntax validation passed
- [x] Event location fields correctly mapped using mapEventTypeToFolder()
- [x] Mileage field uses correct field name (mileage, not mileage_km)
- [x] Mileage format preserved (e.g., "K1834.3+000")
- [x] Simulation times correctly loaded from traffic_input_config.json
- [x] OD table field removed from display
- [x] Vehicle templates API uses correct path (/api/v1/templates/vehicle)
- [x] Vehicle types loaded from API templates
- [x] Error handling for missing files
- [x] Fallback values for unavailable data

---

## User Impact

### Before Fixes
- ❌ Users saw error messages instead of actual data
- ❌ Could not verify event location before creating case
- ❌ Could not see simulation time parameters
- ❌ Confusing OD table field (not user-configurable)

### After Fixes
- ✅ Complete event location information displayed
- ✅ Accurate simulation time parameters from config
- ✅ Clean interface without unnecessary fields
- ✅ Proper vehicle template configuration
- ✅ Users can make informed decisions before case creation

---

**Implementation Status**: ✅ COMPLETE
**Ready for**: User acceptance testing and deployment
