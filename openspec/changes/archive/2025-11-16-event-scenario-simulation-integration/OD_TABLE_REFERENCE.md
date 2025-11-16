# OD Table Reference for Event Scenario Cases

**Document Date**: 2025-11-13
**OpenSpec Change**: event-scenario-simulation-integration
**Purpose**: Document the correct OD data source tables for event scenario case creation

---

## OD Data Source Configuration

### Table Details

| Property | Value |
|----------|-------|
| **Schema** | `dwd` |
| **Table Name** | `dwd_od_weekly` |
| **Full Qualified Name** | `dwd.dwd_od_weekly` |
| **Data Type** | Weekly OD matrix |
| **Geographic Area** | Sichuan Province (四川) |
| **Records** | OD pairs with time-based aggregation |

### How It's Used

**Frontend** (`frontend/scenarios/scenario_browser.js`):
```javascript
const requestData = {
    od_file: 'dwd_od_weekly',  // Table name only (schema added by backend)
    // ... other fields
};
```

**Backend** (`api/services/case_service.py`):
```python
od_request = TimeRangeRequest(
    table_name=od_table,           # 'dwd_od_weekly'
    schemas_name="dwd",             # ✅ Schema explicitly set to 'dwd'
    # ... other fields
)
```

---

## Why `dwd` Schema?

The system has two schemas containing OD data:

| Schema | Usage | Status |
|--------|-------|--------|
| `baseline` | Legacy OD extraction workflow | ⚠️ Deprecated for event scenarios |
| `dwd` | Modern OD data (weekly aggregated) | ✅ **Use for event scenarios** |

### Important Notes

- **DO NOT use** `baseline.od_data_sichuan_202507` for event scenarios
- **DO use** `dwd.dwd_od_weekly` for event scenarios
- The frontend sends only the table name (`dwd_od_weekly`)
- The backend adds the schema prefix (`schemas_name="dwd"`)
- This prevents the doubling error: `baseline.baseline.od_data_sichuan_202507`

---

## Implementation in Code

### Places Where This Is Configured

1. **Frontend Selection** (Complete schema.table reference)
   - File: `frontend/scenarios/scenario_browser.js:756`
   - Variable: `od_file: 'dwd.dwd_od_weekly'` (includes schema prefix)

2. **Backend Parsing**
   - File: `api/services/case_service.py:496-502`
   - Parses `dwd.dwd_od_weekly` into schema (`dwd`) and table (`dwd_od_weekly`)
   - Creates TimeRangeRequest with parsed values

3. **OD Processor Execution**
   - The OD processor combines them: `dwd.dwd_od_weekly`
   - Location: `shared/data_processors/od_processor.py`

---

## Data Flow

```
User creates event scenario case
    ↓
Frontend sends: { od_file: 'dwd.dwd_od_weekly' }
    ↓
Backend API receives request
    ↓
QuickCaseCreator detects as database reference:
    └─ is_database_ref = True (has dot, no slash, no .xml)
    └─ Does NOT try to copy file
    ↓
case_service._start_od_generation_async() parses:
    ├─ schema_name = 'dwd'
    └─ table_name = 'dwd_od_weekly'
    ↓
TimeRangeRequest object created with:
    ├─ table_name: 'dwd_od_weekly'
    └─ schemas_name: 'dwd'
    ↓
OD Processor builds full table reference:
    └─ dwd.dwd_od_weekly
    ↓
Database query executes against correct table ✅
```

---

## Testing

To verify the correct table is being used:

1. **Check Backend Logs**:
   ```
   INFO:shared.data_processors.od_processor:执行单SQL聚合查询...
   # Should query: dwd.dwd_od_weekly (NOT baseline.baseline.*)
   ```

2. **Verify No Doubling Error**:
   ```
   ❌ WRONG: relation "baseline.baseline.od_data_sichuan_202507" does not exist
   ✅ RIGHT: Successfully retrieves OD data from dwd.dwd_od_weekly
   ```

3. **Generated Files**:
   ```
   cases/case_event_xxx/config/
   ├─ dwd_od_weekly_20250610104348_20250610114450.od.xml  ✅
   └─ dwd_od_weekly_20250610104348_20250610114450.rou.xml ✅
   ```

---

## Historical Context

### Previous Implementation Issues

**Round 1 - Schema/Table Name Error**:
- Frontend hardcoded: `od_file: 'baseline.od_data_sichuan_202507'`
- Backend set: `schemas_name="baseline"`
- Result: `baseline.baseline.od_data_sichuan_202507` (doubled schema)
- Error: ❌ Table does not exist

**Round 2 - Incomplete Solution**:
- Frontend changed to: `od_file: 'dwd_od_weekly'` (table name only)
- Backend set: `schemas_name="dwd"`
- Problem: QuickCaseCreator tries to copy file (no dot = file path detection)
- Error: ❌ OD file not found: dwd_od_weekly

**Final Fix - Complete schema.table Format**:
- Frontend now sends: `od_file: 'dwd.dwd_od_weekly'` (complete reference)
- Backend parses: Splits on dot to extract schema and table
- QuickCaseCreator detects: `is_database_ref = True` (has dot, no slash)
- Result: No file copy attempt, proper database reference detection
- Status: ✅ Works correctly

---

## Related Files

- Design: `openspec/changes/event-scenario-simulation-integration/design.md`
- Tasks: `openspec/changes/event-scenario-simulation-integration/tasks.md`
- Frontend Code: `frontend/scenarios/scenario_browser.js`
- Backend Code: `api/services/case_service.py`
- OD Processor: `shared/data_processors/od_processor.py`

---

**Last Updated**: 2025-11-13
**Status**: ✅ Implemented and Tested
