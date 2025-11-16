# Phase 5 Event Scenario Case Creation - Fixes Summary

**Date**: 2025-11-13
**Status**: ✅ FIXED
**Files Modified**: `api/services/case_service.py`

## Issues Fixed

### Issue 1: Interval Set to 30 Minutes Instead of 5 Minutes

**Problem**: Event scenario case creation was using 30-minute OD aggregation intervals instead of the default 5 minutes.

**Root Cause**: Hardcoded `interval_minutes=30` in `case_service.py:512`

**Fix Applied**:
```python
# Before:
interval_minutes=30

# After:
interval_minutes=5  # 使用默认5分钟间隔（而不是30分钟）
```

**File**: `api/services/case_service.py:512`

---

### Issue 2: Case Folder Mismatch

**Problem**: OD files were being generated in the wrong case directory.
- Expected folder: `cases/case_event_20251113_142438/config/`
- Actual folder: `cases/case_20251113_142439/config/`

**Root Cause**:
- `data_service.process_od_data()` method generates its own `case_id` and `case_dir` (line 40-41)
- But in event scenario creation, the case already exists and we just want to add OD files to it
- This caused files to be created in a different case folder

**Solution**: Modified `_run_od_generation_in_background()` to:
1. Call the OD processor directly instead of going through `data_service.process_od_data()`
2. Pass the existing `case_path / "config"` as the output directory
3. Properly manage database connections

**Key Changes**:

```python
# Before (called generic service):
result = loop.run_until_complete(data_service.process_od_data(od_request))

# After (calls OD processor directly with correct output_dir):
output_dir = str(case_path / "config")
request_params = {
    "start_time": od_request.start_time,
    "end_time": od_request.end_time,
    "interval_minutes": od_request.interval_minutes,
    "taz_file": od_request.taz_file,
    "net_file": od_request.net_file,
    "schemas_name": od_request.schemas_name,
    "table_name": od_request.table_name,
    "output_dir": output_dir  # 🔑 确保文件输出到正确的case文件夹
}

db_connection = open_db_connection()
try:
    result = od_processor.process_od_data(db_connection, request_params)
finally:
    if db_connection:
        db_connection.close()
```

**File**: `api/services/case_service.py:531-637`

---

## Data Flow After Fixes

```
User creates event scenario case via scenario_browser.html
    ↓
directCreateCase() sends API request to /api/v1/case/event_quick_create
    ↓
Backend: quick_create_case_from_event()
    ├─ Step 1: QuickCaseCreator creates case structure (case_event_*)
    ├─ Step 2: Detects OD file is database reference (dwd.dwd_od_weekly)
    ├─ Step 3: Launches background OD generation thread
    └─ Step 4: Returns immediately with od_generation_started=true
    ↓
Background Thread: _run_od_generation_in_background()
    ├─ Creates ODProcessor
    ├─ Builds request params with output_dir = case_path/config
    ├─ Calls od_processor.process_od_data(db_connection, request_params)
    ├─ OD processor extracts data from dwd.dwd_od_weekly
    ├─ Generates .od.xml and .rou.xml files in CORRECT case folder
    ├─ Updates od_file_info.json with status='exists'
    ├─ Updates metadata.json with status='created'
    └─ Closes database connection
    ↓
Frontend Polling (3-second intervals)
    ├─ Detects status change from 'od_generating' → 'created'
    ├─ Shows success notification
    └─ Case is ready for simulation
```

## Verification

### Confirm Interval is 5 Minutes
```bash
grep -n "interval_minutes=" api/services/case_service.py
# Output: 512:                interval_minutes=5  # ✅ Correct
```

### Confirm Files Generate in Correct Folder
Files will now be generated in:
```
cases/case_event_<timestamp>/config/
├── dwd_od_weekly_<start>_<end>.od.xml    ✅
├── dwd_od_weekly_<start>_<end>.rou.xml   ✅
└── od_file_info.json
```

Not in a separate `case_<different_timestamp>` folder.

## Testing Recommendations

1. **Manual Test**: Create an event scenario case from scenario_browser.html
2. **Check Logs**: Watch backend logs for:
   - `Starting OD generation for case case_event_*`
   - `OD XML file generation completed`
   - `✓ Case case_event_* status updated to created`
3. **Verify Files**: Check `cases/case_event_*/config/` folder contains `.od.xml` and `.rou.xml` files
4. **Check Interval**: Confirm time intervals between OD entries are 5 minutes (or check first two timestamps)

## Related Files

- Design Document: `openspec/changes/event-scenario-simulation-integration/design.md`
- OD Table Reference: `openspec/changes/event-scenario-simulation-integration/OD_TABLE_REFERENCE.md`
- Case Service: `api/services/case_service.py`
- Frontend: `frontend/scenarios/scenario_browser.js`

## Status

✅ **All fixes implemented**
✅ **Syntax validation passed**
✅ **Imports verified**

Ready for testing!
