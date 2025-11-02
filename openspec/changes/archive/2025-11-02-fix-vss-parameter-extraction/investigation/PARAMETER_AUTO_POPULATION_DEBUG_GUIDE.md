# Parameter Auto-Population Debug Guide

## Overview

This guide explains how to debug the parameter auto-population flow - verifying that default values from the API template are properly obtained and rendered to the frontend form interface.

**Issue**: User reported that when VSS strategies enter the parameter configuration interface, parameters should be automatically obtained from the selected strategy template and rendered to the frontend interface.

**Root Cause Investigation**: The API provides default values in the template schema, but we need to verify they're being:
1. Fetched from API ✅
2. Passed to rendering functions
3. Actually rendered in the DOM
4. Properly extracted when form is submitted

## Debugging Flow

### Step 1: Monitor API Response

**Where to check**: Browser DevTools > Network tab
**URL to watch**: `/api/v1/control/templates/{template_id}/`

**What to verify**:
- Response status: 200
- Response body contains `parameters_schema` array
- Each parameter has `default_value` field populated
- For VSS templates, `speed_steps` parameter should have:
  ```json
  {
    "parameter_name": "speed_steps",
    "parameter_type": "step_array",
    "default_value": [
      { "time_hours": 7, "speed_kmh": 100 },
      { "time_hours": 9, "speed_kmh": 80 },
      ...
    ]
  }
  ```

### Step 2: Monitor Template Generation Logs

**Where to check**: Browser DevTools > Console tab
**When**: After clicking a template card and reaching Step 3 (parameter configuration)

**Logs to look for**:

```
[generateParamsForm] Called with template: vss_moderate
[generateParamsForm] step_array param: {
  name: "speed_steps",
  hasDefaultValue: true,
  defaultValueType: "object",
  defaultValue: [
    { time_hours: 7, speed_kmh: 100 },
    { time_hours: 9, speed_kmh: 80 },
    { time_hours: 17, speed_kmh: 100 },
    { time_hours: 19, speed_kmh: 80 }
  ],
  defaultLength: 4,
  firstStep: { time_hours: 7, speed_kmh: 100 }
}
```

**If this log shows `hasDefaultValue: false` or `defaultLength: 0`**:
- ❌ Problem: API response doesn't contain default values
- **Action**: Check if API templates have `default_value` fields

### Step 3: Monitor Parameter Rendering Logs

**Where to check**: Browser DevTools > Console tab
**When**: Same time as Step 2

**Logs to look for**:

```
[renderStepArrayControl] Processing speed_steps {
  hasSchema: true,
  hasDefaultValue: true,
  defaultValueType: "object",
  defaultStepsCount: 4,
  defaultSteps: [
    { time_hours: 7, speed_kmh: 100 },
    { time_hours: 9, speed_kmh: 80 },
    { time_hours: 17, speed_kmh: 100 },
    { time_hours: 19, speed_kmh: 80 }
  ],
  firstStep: { time_hours: 7, speed_kmh: 100 },
  stepStructure: { ... }
}

[renderStepArrayControl] Adding default step 0: {
  step: { time_hours: 7, speed_kmh: 100 },
  timeVal: 7,
  speedVal: 100
}

[renderStepArrayControl] Adding default step 1: {
  step: { time_hours: 9, speed_kmh: 80 },
  timeVal: 9,
  speedVal: 80
}

[renderStepArrayControl] Adding default step 2: {
  step: { time_hours: 17, speed_kmh: 100 },
  timeVal: 17,
  speedVal: 100
}

[renderStepArrayControl] Adding default step 3: {
  step: { time_hours: 19, speed_kmh: 80 },
  timeVal: 19,
  speedVal: 80
}
```

**If step logs are missing or show 0 default steps**:
- ❌ Problem: Default values from API aren't being processed
- **Action**: Check generateParamsForm() is passing param object correctly

### Step 4: Monitor Row Creation Logs

**Where to check**: Browser DevTools > Console tab
**When**: Same time as Step 3

**Logs to look for**:

```
[addStepRow] Creating row for speed_steps {
  timeVal: 7,
  speedVal: 100,
  hasStepStructure: true
}

[addStepRow] Created timeInput: {
  className: "step-time",
  value: "7",
  htmlContent: "<input type=\"text\" class=\"step-time\" value=\"7\" ...>"
}

[addStepRow] Created speedInput: {
  className: "step-speed",
  value: "100",
  min: "30",
  max: "130"
}
```

**Verify for each default step**:
- `className: "step-time"` - ✅ CSS class is correct
- `className: "step-speed"` - ✅ CSS class is correct
- `value` - ✅ Contains the actual numeric value from API

**If row creation logs are missing**:
- ❌ Problem: addStepRow() isn't being called
- **Action**: Check renderStepArrayControl() calls forEach over defaultSteps

### Step 5: Verify DOM Structure

**Where to check**: Browser DevTools > Elements tab or right-click element > Inspect

**What to look for** in the rendered form:

1. **Form Group Container** - Should have data attributes:
   ```html
   <div class="form-group"
        data-parameter-name="speed_steps"
        data-parameter-type="step_array">
   ```

2. **Table Structure** - Should exist and have tbody:
   ```html
   <table class="steps-table">
     <tbody class="steps-tbody" data-parameter-name="speed_steps">
       <tr class="step-row">
         <td>
           <input class="step-time" type="text" value="7">
         </td>
         <td>
           <input class="step-speed" type="number" value="100">
         </td>
         <td><!-- Remove button --></td>
       </tr>
       <!-- Repeat for each default step -->
     </tbody>
   </table>
   ```

3. **Input Values** - Each row should have:
   - `class="step-time"` with numeric value (e.g., "7")
   - `class="step-speed"` with numeric value (e.g., "100")

**If DOM structure is missing or wrong**:
- ❌ Problem: renderStepArrayControl() not creating table properly
- **Action**: Check table creation code in parameter_form.js (lines 745-778)

### Step 6: Monitor Form Submission Logs

**Where to check**: Browser DevTools > Console tab
**When**: Click "生成策略实例" (Submit button) on parameter configuration form

**Logs to look for**:

```
[extractFormParameters] Found form groups: 3
[extractFormParameters] Processing: {
  paramName: "strategy_name",
  paramType: "string"
}
[extractFormParameters] Processing: {
  paramName: "strategy_description",
  paramType: "string"
}
[extractFormParameters] Processing: {
  paramName: "speed_steps",
  paramType: "step_array"
}

[extractFormParameters] step_array - found tbody: <tbody class="steps-tbody" ...>

[extractFormParameters] step_array - found rows: 4

[extractFormParameters] step_array - row 0: {
  rowClass: "step-row",
  hasTimeInput: true,
  timeValue: "7",
  hasSpeedInput: true,
  speedValue: "100"
}

[extractFormParameters] step_array - row 1: {
  rowClass: "step-row",
  hasTimeInput: true,
  timeValue: "9",
  hasSpeedInput: true,
  speedValue: "80"
}

[extractFormParameters] step_array - row 2: {
  rowClass: "step-row",
  hasTimeInput: true,
  timeValue: "17",
  hasSpeedInput: true,
  speedValue: "100"
}

[extractFormParameters] step_array - row 3: {
  rowClass: "step-row",
  hasTimeInput: true,
  timeValue: "19",
  hasSpeedInput: true,
  speedValue: "80"
}

[extractFormParameters] step_array - extracted value: [
  { time_hours: 7, speed_kmh: 100 },
  { time_hours: 9, speed_kmh: 80 },
  { time_hours: 17, speed_kmh: 100 },
  { time_hours: 19, speed_kmh: 80 }
]
```

**If extraction shows 0 rows or missing values**:
- ❌ Problem: Form data not being collected properly
- **Action**: Verify DOM structure in Step 5

### Step 7: Monitor API Request Body

**Where to check**: Browser DevTools > Network tab > Request payload
**URL**: POST `/api/v1/control/strategy-instances/`

**What to verify**:

The request body should include the extracted parameters with proper structure:

```json
{
  "strategy_name": "VSS中等控制-前端UI",
  "strategy_description": "...",
  "speed_steps": [
    { "time_hours": 7, "speed_kmh": 100 },
    { "time_hours": 9, "speed_kmh": 80 },
    { "time_hours": 17, "speed_kmh": 100 },
    { "time_hours": 19, "speed_kmh": 80 }
  ],
  "affected_edges": [...]
}
```

**Critical**: Each step MUST have both:
- `time_hours` - numeric value
- `speed_kmh` - numeric value

**If request body is missing `time_hours` or `speed_kmh`**:
- ❌ Problem: Extraction logic isn't creating proper structure
- **Action**: Check extractFormParameters() at line 2388-2391

## Common Issues and Solutions

### Issue 1: No Default Rows Appear

**Symptom**: Form opens but all fields are empty, need to manually click "+ 添加限速步骤"

**Debug Steps**:
1. Check Step 2 logs - is `hasDefaultValue: true`?
2. Check Step 3 logs - is `defaultStepsCount > 0`?
3. Check Step 4 logs - are row creation logs appearing?
4. Check Step 5 - does DOM have `<tr class="step-row">`?

**If Step 2 fails**:
- API response missing `default_value`
- **Fix**: Check API template endpoint returns proper data

**If Steps 3-4 fail**:
- renderStepArrayControl() not processing defaults
- **Fix**: Check parameter_form.js line 771-776

**If Step 5 fails**:
- DOM not created properly
- **Fix**: Check parameter_form.js line 745-778

### Issue 2: API Returns "Missing time_hours" Error

**Symptom**: Submission fails with 400 error "Parameter validation failed: missing 'time_hours' or 'time_seconds' field"

**Debug Steps**:
1. Check Step 6 logs - does it show `step_array - found rows: X`?
2. Check Step 6 logs - do rows have `hasTimeInput: true` and `timeValue` populated?
3. Check Step 7 logs - does request include `time_hours` field?

**If Step 6 shows 0 rows**:
- Form extraction not finding rows
- **Fix**: Check Step 5 DOM structure

**If Step 6 shows rows but missing values**:
- Extraction logic not reading CSS classes properly
- **Fix**: Verify row elements have `class="step-time"` and `class="step-speed"`

**If Step 7 request missing `time_hours`**:
- Extraction creating wrong field names
- **Fix**: Check extractFormParameters() at line 2388-2391:
  ```javascript
  time_hours: parseFloat(row.querySelector(".step-time").value),
  speed_kmh: parseFloat(row.querySelector(".step-speed").value)
  ```

### Issue 3: Default Values Show But API Request Fails

**Symptom**: Form shows correct values from API template, but submission fails with validation error

**Debug Steps**:
1. Check Step 6 logs - are extracted values correct?
2. Check Step 7 request payload - do field names match API expectations?
3. Check API response - what's the specific validation error?

**Common problems**:
- Field name mismatch (e.g., `time` vs `time_hours`)
- Data type mismatch (e.g., string instead of number)
- Missing required fields

**Fix**: Compare extracted values in Step 6 logs with API documentation

## Files Modified

### frontend/control/templates.html
- **Line 922-929**: Added logging when processing step_array parameters
- **Logs**: Shows if default_value is present and its contents

### frontend/control/js/parameter_form.js
- **Line 704-713**: Added logging in renderStepArrayControl() to show parameter processing
- **Line 774**: Added logging when adding default steps
- **Line 1171-1204**: Added detailed logging in addStepRow() for row creation
- **Line 2375-2396**: Enhanced extractFormParameters() to log each row's contents

## Testing Workflow

1. **Open browser DevTools**: F12 (Windows) or Cmd+Option+I (Mac)
2. **Switch to Console tab**: Click "Console" tab
3. **Navigate to template**:
   - Go to http://localhost:8000/control/templates.html
   - Click template card (e.g., "VSS中等控制")
   - Follow UI steps to reach parameter configuration
4. **Monitor logs**:
   - Step 1: Watch Network tab during template selection
   - Steps 2-6: Watch Console tab for parameter flow logs
5. **Fill and submit**:
   - Click "生成策略实例" to submit
   - Watch Step 6-7 logs for extraction and request

## Success Criteria

When everything is working correctly, you should see:

✅ **Step 2 logs show**: `hasDefaultValue: true`, `defaultLength: > 0`
✅ **Step 3 logs show**: `defaultStepsCount: 4` or expected count
✅ **Step 4 logs show**: Creating rows with proper timeVal and speedVal
✅ **Step 5 (DOM)**: Table rows visible with filled input fields
✅ **Step 6 logs show**: Extracting correct number of rows with values
✅ **Step 7 (Network)**: Request includes `time_hours` and `speed_kmh` for each step
✅ **API Response**: 201 Created with strategy_id

## Next Investigation

If issues persist after following this guide:

1. **Screenshot the console logs**: Capture full output from Steps 2-7
2. **Check form-group structure**: Use DevTools Elements tab to inspect exact HTML
3. **Verify API response**: Use Network tab to see full template JSON
4. **Compare parameter types**: Check if param object has correct property names

---

**Document Created**: 2025-11-02
**Related Issue**: Parameter auto-population from API templates to frontend form
**Status**: Investigation in progress

