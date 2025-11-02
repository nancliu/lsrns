# CRITICAL FINDING: Parameter Extraction Failing

## Summary

The VSS tests are all failing with the **same API error** on ALL 5 templates:

```
[API_ERROR] 400: Parameter validation failed: Step 0: missing 'time_hours' or 'time_seconds' field; ...
```

This means:
- ✅ Form is being submitted (API is receiving the request)
- ❌ The `time_hours` field is NOT being extracted from the form
- ❌ Parameters from the template are NOT being properly rendered AND extracted

## Test Results

### All 5 VSS Templates Failing

| Template | Status | Error |
|----------|--------|-------|
| 1. vss_moderate | FAILED 🔴 | Missing time_hours in Step 0, 1, 2, 3 |
| 2. vss_strict | FAILED 🔴 | Missing time_hours in Step 0, 1, 2, 3 |
| 3. vss_weather_based | FAILED 🔴 | Missing time_hours in Step 0, 1, 2, 3, 4, 5 |
| 4. vss_upstream_warning | FAILED 🔴 | Missing time_hours in Step 0, 1, 2 |
| 5. vss_lane_differentiated | FAILED 🔴 | Missing time_hours in Step 0, 1, 2, 3 |

**Pattern**: All failing at the same place - `time_hours` field extraction

## Current Test Flow Trace

```
✓ 策略名称填充成功: VSS中等控制-UI测试
  ℹ 页面中找到 14 个表单组
  ✓ 提交按钮可用
  ✓ 点击提交按钮
[API_RESPONSE] 400 http://localhost:8000/api/v1/control/strategy-instances/
[API_ERROR] 400: {"detail":"Parameter validation failed: Step 0: missing 'time_hours' or 'time_seconds' field..."}
```

**Key Observations**:
1. Test finds form groups (14 groups for vss_moderate) ✅
2. Test clicks submit button ✅
3. API receives the request ✅
4. API validates and finds missing `time_hours` ❌

## Root Cause Hypothesis

Based on the error message mentioning "Step 0", "Step 1", etc., the API is expecting an array of step objects, each with `time_hours`:

```json
[
  { "time_hours": 7, "speed_kmh": 100 },   // <- Step 0
  { "time_hours": 9, "speed_kmh": 80 },    // <- Step 1
  ...
]
```

But the form is probably submitting:
```json
[
  { "speed_kmh": 100 },                    // <- MISSING time_hours!
  { "speed_kmh": 80 },
  ...
]
```

## Debug Logging Now Added

Added comprehensive logging to trace the parameter flow:

### File: frontend/control/templates.html
- **Line 922-929**: Logs when processing step_array parameters
- Shows if API template has `hasDefaultValue: true`

### File: frontend/control/js/parameter_form.js
- **Line 704-713**: Logs when rendering step_array
- Shows `defaultStepsCount` and actual step objects
- **Line 774**: Logs when adding each default step
- **Line 1171-1204**: Logs when creating each row
- Shows CSS classes and input values
- **Line 2375-2396**: Logs detailed extraction info
- Shows row count and each row's field values

## Next Steps to Debug

### Option 1: Run Tests in Headed Mode
```bash
cd d:\projects\OD_SIM
npx playwright test tests/e2e/test_frontend_smart.spec.js -g "VSS: vss_moderate" --headed
```

This will show the browser and allow us to:
1. Open DevTools console (F12)
2. See all the logging output
3. Inspect the DOM to verify rows are created
4. Track the parameter flow in real-time

### Option 2: Add More Detailed Logging in Test
Add logging to the test's extractFormParameters() call to see what's being collected

### Option 3: Capture Console Output
Modify test to capture and log console output during form submission

## Critical Questions to Answer

1. **Are rows being created in the DOM?**
   - Look for `[renderStepArrayControl] Adding default step` logs
   - Should see 4 logs for vss_moderate (4 default steps)

2. **Are input CSS classes correct?**
   - Look for `[addStepRow] Created timeInput` logs
   - Should show `className: "step-time"`
   - Should show actual value from API

3. **Is extraction finding the rows?**
   - Look for `[extractFormParameters] step_array - found rows:` logs
   - Should show row count > 0

4. **Are extracted values correct?**
   - Look for `[extractFormParameters] step_array - extracted value:`
   - Should show array with time_hours and speed_kmh fields

5. **Is API request formatted correctly?**
   - Check Network tab request payload
   - Should include time_hours for each step

## Likely Issues

### Issue A: Default Values Not Passed Through
- **Symptom**: `[renderStepArrayControl] defaultStepsCount: 0`
- **Cause**: API template doesn't have default_value populated
- **Fix**: Check if API is returning proper template schema

### Issue B: Rows Not Created
- **Symptom**: `[extractFormParameters] step_array - found rows: 0`
- **Cause**: renderStepArrayControl() not calling addStepRow() for defaults
- **Fix**: Check rendering logic (lines 771-776 in parameter_form.js)

### Issue C: Extraction Finding Rows But Missing Fields
- **Symptom**: Logs show rows found but `hasTimeInput: false`
- **Cause**: Row elements don't have input with `class="step-time"`
- **Fix**: Check addStepRow() creates inputs with correct CSS classes (lines 1182, 1195)

### Issue D: Correct Extraction But Wrong Field Names
- **Symptom**: Extraction logs show correct values, but API error mentions wrong field
- **Cause**: Extraction creates wrong field name (not `time_hours`)
- **Fix**: Check line 2388-2391 in parameter_form.js

## Files to Examine Next

1. **[templates.html:854-987](frontend/control/templates.html#L854-L987)**
   - generateParamsForm() - Parameter rendering logic
   - Check if param object is passed correctly to renderStepArrayControl()

2. **[parameter_form.js:696-795](frontend/control/js/parameter_form.js#L696-L795)**
   - renderStepArrayControl() - Table creation logic
   - Check if defaultSteps are being iterated (line 771)

3. **[parameter_form.js:1169-1210](frontend/control/js/parameter_form.js#L1169-L1210)**
   - addStepRow() - Row creation logic
   - Check CSS class names: "step-time", "step-speed"

4. **[parameter_form.js:2347-2397](frontend/control/js/parameter_form.js#L2347-L2397)**
   - extractFormParameters() - Form extraction logic
   - Check CSS selectors match created elements

## Execution Plan

1. **Run VSS test with headed mode** to see browser and console
2. **Capture console logs** - Copy full output from debugging logs
3. **Inspect DOM** - Use DevTools to verify table structure
4. **Analyze log flow** - Trace from API response → rendering → extraction
5. **Identify missing link** - Find where parameter flow breaks
6. **Implement fix** - Modify code to complete the flow
7. **Re-test** - Run single VSS test to verify fix
8. **Verify database** - Check if strategy is created in DB

---

**Created**: 2025-11-02
**Status**: Debugging in progress
**Impact**: All 5 VSS templates failing, likely same root cause for DHS/TEC

