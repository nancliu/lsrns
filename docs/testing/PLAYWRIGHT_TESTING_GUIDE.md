# Playwright Testing Guide for Live Monitoring Feature

**Purpose**: Comprehensive guide for testing the in-network vehicle curve display feature using Playwright
**Status**: Testing Framework Ready
**Date**: 2025-10-30

---

## Overview

This guide provides step-by-step instructions for running and interpreting Playwright tests that debug the live monitoring feature of batch simulations.

---

## Test Files Created

### 1. `tests/e2e/test_live_monitoring_debug.spec.js`

**Purpose**: Basic debugging test that verifies API response structure

**Tests**:
- ✅ Live Monitoring Feature Debug Test
  - Navigates to batch simulation page
  - Polls batch progress API (if batch exists)
  - Analyzes API response structure
  - Checks for running_vehicles and live_time_series fields

- ✅ Check Frontend Dependencies
  - Verifies Chart.js library is loaded
  - Checks for jQuery (if used)
  - Confirms Fetch API is available

- ✅ Direct API Call Verification
  - Tests API response structure directly
  - Validates JSON schema
  - Checks field presence and types

**Runtime**: ~12 seconds

**Command**:
```bash
conda activate od_project
cd D:/projects/OD_SIM
npx playwright test tests/e2e/test_live_monitoring_debug.spec.js
```

**Expected Output**:
```
Running 3 tests using 1 worker

✓  1 tests/e2e/test_live_monitoring_debug.spec.js:121:1 › Live Monitoring Feature - Debug In-Network Vehicle Curve Display
✓  2 tests/e2e/test_live_monitoring_debug.spec.js:319:1 › Check Frontend Dependencies - Chart.js and Libraries
✓  3 tests/e2e/test_live_monitoring_debug.spec.js:352:1 › Direct API Call - Verify batch progress response structure

  3 passed (12.7s)
```

---

### 2. `tests/e2e/test_batch_live_monitoring_interactive.spec.js`

**Purpose**: Interactive test that starts and monitors a real batch simulation

**Tests**:
- ✅ Interactive Batch Live Monitoring
  - Finds an existing case
  - Checks for running batches
  - Monitors batch progress every 5 seconds for up to 3 minutes
  - Collects live_time_series and running_vehicles data
  - Verifies dynamic curve rendering

- ✅ API Response Format Verification
  - Tests API response against frontend expectations
  - Validates JSON schema
  - Checks all required fields present
  - Verifies data types

**Runtime**: 3-15 minutes (depending on whether a batch is running)

**Command**:
```bash
conda activate od_project
cd D:/projects/OD_SIM
npx playwright test tests/e2e/test_batch_live_monitoring_interactive.spec.js
```

**Expected Output** (when batch is running):
```
📘 [2025-10-30T...] === INTERACTIVE BATCH MONITORING TEST ===
📘 [2025-10-30T...] Step 1: Locating test case...
✅ [2025-10-30T...] Found case: case_20251016_113040
📘 [2025-10-30T...] Step 2: Navigating to batch simulation page...
...
📊 [2025-10-30T...] Poll 1/36 (0.0s)
📘 [2025-10-30T...] Status: running | Progress: 25.0%
📘 [2025-10-30T...] Tasks: 2 completed, 1 running
📊 [2025-10-30T...] Dynamic curve points: 45
...
🎉 [2025-10-30T...] Batch completed!
📊 [2025-10-30T...] === MONITORING SUMMARY ===
```

---

## Node.js Test Script

### `test_batch_live_monitoring_complete.js`

**Purpose**: Standalone Node.js script for testing without Playwright browser automation

**Features**:
- Direct HTTP API testing
- Live polling and monitoring
- Detailed console output
- No browser overhead

**Command**:
```bash
conda activate od_project
cd D:/projects/OD_SIM
node test_batch_live_monitoring_complete.js
```

**Output Sample**:
```
================================================================================
BATCH LIVE MONITORING DEBUG TEST
================================================================================

📍 Step 1: Find existing case with simulations
✅ Using case: case_20251016_113040

📍 Step 2: Check for existing batch optimizations
✅ Found batch: batch_20251028_085100 (status: completed)

📍 Step 3: Monitor batch progress
Polling API every 3 seconds...

🔄 [Attempt 1/10] Polling batch progress...
✅ API Response received
   - Status: completed
   - Progress: 100.0%
   - Tasks: 3
   📊 live_time_series detected:
      - time_points: 0 points ⚠️
      - total_running: 0 points
      - task_count: 3
```

---

## How to Run Tests

### Prerequisites

```bash
# Activate conda environment
conda activate od_project

# Ensure API is running
python api/main.py

# In another terminal, run the tests
```

### Option 1: Run All Tests

```bash
conda activate od_project
cd D:/projects/OD_SIM
npx playwright test tests/e2e/test_live_monitoring_debug.spec.js tests/e2e/test_batch_live_monitoring_interactive.spec.js
```

### Option 2: Run Specific Test

```bash
# Just the debug test (10 seconds)
npx playwright test tests/e2e/test_live_monitoring_debug.spec.js

# Just the interactive test (3-15 minutes)
npx playwright test tests/e2e/test_batch_live_monitoring_interactive.spec.js
```

### Option 3: Run with Detailed Output

```bash
npx playwright test tests/e2e/test_live_monitoring_debug.spec.js --reporter=list
```

### Option 4: Run Node.js Script

```bash
node test_batch_live_monitoring_complete.js
```

---

## Interpreting Test Results

### Success Indicators

✅ **API Response Includes live_time_series**:
```json
{
  "live_time_series": {
    "time_points": [0, 100, 200, ...],      // Data points present
    "total_running": [320, 350, ...],       // Vehicle counts
    "task_count": 3,
    "last_update": "2025-10-30T..."
  }
}
```

✅ **Running Tasks Have live_status**:
```json
{
  "task_id": "task_001",
  "status": "running",
  "live_status": {
    "running_vehicles": 320,         // Vehicle data present
    "current_step": 1500,
    "total_steps": 14400,
    "progress_percent": 10.4
  }
}
```

✅ **Dynamic Curve Section Visible**:
```
liveCurveSection: ✅ VISIBLE
liveCurveChart canvas: ✅ FOUND
```

### Warning Indicators

⚠️ **Empty live_time_series**:
```json
{
  "live_time_series": {
    "time_points": [],              // ⚠️ NO DATA
    "total_running": [],
    "task_count": 0
  }
}
```

⚠️ **Missing running_vehicles**:
```json
{
  "live_status": {
    "current_step": 0,
    "total_steps": 14400,
    "progress_percent": 0.0,
    "message": "仿真正在初始化..."    // ⚠️ No vehicle data
  }
}
```

⚠️ **Curve Section Not Found**:
```
liveCurveSection: ❌ NOT FOUND
liveCurveChart canvas: ❌ NOT FOUND
```

### Error Indicators

❌ **API Not Responding**:
```
❌ API returned status 500
```

❌ **No Batches Found**:
```
⚠️ No running batches found, skipping direct API test
```

---

## Test Scenario: Live Batch Monitoring

### Best Case Scenario (Everything Works)

1. **Start a Batch** (via UI or API)
   - Navigate to `/control/simulations.html`
   - Click "Configure" tab
   - Select 2-3 strategies
   - Set 2-3 seeds (total 4-9 tasks)
   - Click "Start Batch"

2. **Run Interactive Test** (immediately after starting)
   ```bash
   npx playwright test tests/e2e/test_batch_live_monitoring_interactive.spec.js
   ```

3. **Expected Results**:
   - ✅ Poll 1: Status=running, Progress=0-5%
   - ✅ Poll 2-10: Curve points increase (0 → 10 → 50 → 100...)
   - ✅ Running tasks show running_vehicles count
   - ✅ Frontend displays dynamic curve
   - ✅ Curve updates every 10 seconds
   - ✅ Final: Status=completed, Progress=100%

### Failure Scenario (Curve Not Displaying)

1. **Symptoms**:
   - API returns empty `live_time_series`
   - Frontend shows no curve
   - `running_vehicles` is missing from `live_status`

2. **Diagnosis** (using test output):
   - Check: "No aggregated data found, returning empty"
   - Check: "File does not exist" in summary.xml logs
   - Check: "No step elements found in tail"

3. **Next Steps**:
   - Verify summary.xml is being created
   - Check if SUMO is still running
   - Review API server logs for errors
   - Run debug script: `python debug_batch_progress.py case_id batch_id`

---

## Debug Workflow

### Step 1: Check API Response

```bash
# Get any running batch
curl "http://localhost:8000/api/v1/control/optimization/batch/batch_ID/progress" | python -m json.tool
```

**Key things to check**:
- Is `live_time_series` present?
- Does `live_time_series.time_points` have data?
- Do tasks have `live_status`?
- Does `live_status` include `running_vehicles`?

### Step 2: Check Browser Console

Open browser DevTools (F12) and look for:
- JavaScript errors in console
- `renderLiveCurve()` function calls
- Chart.js initialization messages
- API fetch errors

### Step 3: Check Server Logs

Look for DEBUG/ERROR messages:
```
[_extract_summary_last_step] File does not exist
[_aggregate_live_time_series] No aggregated data found
[_get_simulation_live_status] Failed to read progress.json
```

### Step 4: Verify File System

```bash
# Check if summary.xml exists and has content
ls -lh cases/case_ID/simulations/plan_opti/batch_ID/plan_ID/sim_SEED/summary.xml

# Check file size
du -h cases/case_ID/simulations/plan_opti/batch_ID/plan_ID/sim_SEED/summary.xml

# View first few lines
head -20 cases/case_ID/simulations/plan_opti/batch_ID/plan_ID/sim_SEED/summary.xml

# Count step elements
grep -c '<step' cases/case_ID/simulations/plan_opti/batch_ID/plan_ID/sim_SEED/summary.xml
```

### Step 5: Run Diagnostic Script

```bash
python debug_batch_progress.py case_20251016_113040 batch_20251028_085100
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "No batches found" | No batch running | Start a batch simulation first |
| Empty `time_points` | summary.xml has no <step> | Wait for SUMO to start writing to summary.xml |
| Missing `running_vehicles` | live_status extraction failed | Check if summary.xml is valid XML |
| Curve not displaying | Empty `time_points` data | Verify data is flowing from API |
| API timeout | Server overloaded | Check if batch is using too much CPU |
| "仿真正在初始化..." message | summary.xml still being created | Wait 10-30 seconds for first data |

---

## Performance Notes

### Expected Response Times

| Scenario | Response Time | Notes |
|----------|---------------|-------|
| Cache hit (< 5 seconds) | <50ms | Cached progress data |
| Cache miss | <200ms | 60 tasks, reading summary.xml files |
| Large summary.xml (>10MB) | <10ms | Incremental parsing (8KB tail) |
| Polling interval | 10 seconds | Reduced from 2 seconds (original design) |

### Test Duration

- **Debug Test**: ~12 seconds (API structure check only)
- **Interactive Test**: 3-15 minutes (depends on batch completion time)
- **Node.js Script**: 30-60 seconds (polling 10 times)

---

## Advanced: Running in Headed Mode

To see the browser during testing:

```bash
npx playwright test tests/e2e/test_batch_live_monitoring_interactive.spec.js --headed
```

This will:
1. Open real Chrome browser
2. Navigate to the UI
3. Display all interactions
4. Show final UI state

---

## Troubleshooting

### Issue: "Module not found: playwright"

```bash
npm install -g playwright
# OR
npx playwright install
```

### Issue: "Port 8000 already in use"

```bash
# Kill existing process
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill
# OR
# Start API on different port
python api/main.py --port 8001
```

### Issue: "Timeout waiting for batch"

- Increase timeout in test (currently 900000ms = 15 minutes)
- Check if batch is actually running
- Check SUMO process: `ps aux | grep sumo`

### Issue: "Cannot connect to localhost:8000"

```bash
# Verify API is running
curl http://localhost:8000/docs

# If not, start it
cd D:/projects/OD_SIM
conda activate od_project
python api/main.py
```

---

## Next Steps

1. **Run Basic Test**:
   ```bash
   npx playwright test tests/e2e/test_live_monitoring_debug.spec.js
   ```

2. **Start a Batch** (in UI or via API):
   - Go to http://localhost:8000/control/simulations.html
   - Start batch with 2-3 plans, 2-3 seeds

3. **Run Interactive Test**:
   ```bash
   npx playwright test tests/e2e/test_batch_live_monitoring_interactive.spec.js
   ```

4. **Analyze Results**:
   - Check if curve data is being generated
   - Verify frontend can access the data
   - Validate that chart.js renders the curve

5. **Review Findings**:
   - See `LIVE_MONITORING_DEBUG_REPORT.md`
   - Check browser console logs
   - Check server logs for errors

---

## References

- Playwright Documentation: https://playwright.dev
- Test File: `tests/e2e/test_live_monitoring_debug.spec.js`
- Interactive Test: `tests/e2e/test_batch_live_monitoring_interactive.spec.js`
- Debug Script: `test_batch_live_monitoring_complete.js`
- Debug Report: `LIVE_MONITORING_DEBUG_REPORT.md`

