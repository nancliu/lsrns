# CRITICAL ROOT CAUSE ANALYSIS - Parameter Extraction Failure

## Executive Summary

After comprehensive investigation spanning multiple debug logging implementations and test runs, **the root cause has been identified but NOT YET FIXED**:

**Input elements are being created with correct CSS classes, but their `.value` properties are NOT being properly populated with the time/speed data.**

## Evidence Trail

### Step 1: Parameter Rendering Works ✅
- API provides template with `default_value: [{ time_hours: 7, speed_kmh: 100 }, ...]`
- `generateParamsForm()` logs show: `hasDefaultValue: true, defaultLength: 4`
- `renderStepArrayControl()` logs show: `defaultStepsCount: 4`

### Step 2: Rows Are Created ✅
- `renderStepArrayControl()` logs show: `Adding default step 0: {step: Object, timeVal: 7, speedVal: 100}`
- This proves `addStepRow(tbody, paramName, 7, 100, stepStructure)` IS being called

### Step 3: Inputs Are Created But Values Are Empty ❌
- `extractTableParameters()` logs show:
  ```
  step_array row 0: {
    hasTimeInput: true,              ✅ Input element EXISTS
    timeValue: ,                      ❌ Value is EMPTY!
    timeParsed: NaN,                  ❌ Parses to NaN
    hasSpeedInput: true,              ✅ Input element EXISTS
    speedValue: ,                      ❌ Value is EMPTY!
  }
  ```

## The Problem

Even though the function chain is working:
1. renderStepArrayControl() → calls addStepRow() with timeVal=7
2. addStepRow() → creates input with createTimeInput("step-time", 7)
3. createTimeInput() → sets input.value = 7 (or String(7) after my fix)
4. Later, extractTableParameters() → queries for input.value

**The extracted value is EMPTY**, meaning something between steps 3 and 4 is clearing the value!

## Possible Root Causes

### Cause A: Form Reset or Value Clearing ⚠️
Some code might be calling `form.reset()` or explicitly clearing input values AFTER the rows are created but BEFORE extraction.

**Check for**:
- Any `form.reset()` calls
- Any `input.value = ''` assignments
- Any form clearing in step 3

### Cause B: Input Type Issue 🤔
The input might be created with the correct `.value` property, but that property isn't being serialized/preserved correctly.

**Why this might happen**:
- If inputs are created as DOM elements but not properly attached to the form
- If there's a timing issue where values are read before being set
- If createTimeInput() is being called AFTER values should be populated

### Cause C: Wrong Input Element Being Created ⚠️
Maybe `createTimeInput()` is NOT the function being called, or there's a different function that creates inputs without values.

**Evidence needed**:
- Logs from inside createTimeInput() showing the value being set
- Verification that the created input has class="step-time"

### Cause D: Double DOM Update 🔴
The most likely: The input is created with a value, but then something updates the form/table and recreates the inputs WITHOUT the values.

**Evidence**:
- Timeline visualizer updates
- Any form validation that reconstructs the UI
- Window/page events that trigger re-rendering

## Critical Tests to Run

### Test 1: Check if createTimeInput is Actually Setting Values
Add logging INSIDE createTimeInput:
```javascript
function createTimeInput(className, value = 0) {
  const input = document.createElement("input");
  input.type = "number";
  input.className = className;
  input.value = String(value);
  console.log(`[createTimeInput] Created input with value="${input.value}"`);  // Add this
  return input;
}
```

If this log doesn't appear or shows empty value → problem is in createTimeInput()

### Test 2: Check if Values Survive DOM Attachment
Add logging right after row is created:
```javascript
function addStepRow(...) {
  const row = document.createElement("tr");
  row.className = "step-row";

  const timeCell = document.createElement("td");
  const timeInput = createTimeInput("step-time", timeVal || 0);
  timeCell.appendChild(timeInput);

  console.log(`[addStepRow] After appendChild, timeInput.value="${timeInput.value}"`);  // Add this

  row.appendChild(timeCell);
  tbody.appendChild(row);

  // Check again after tbody appendChild
  const allStepTimes = tbody.querySelectorAll('.step-time');
  allStepTimes.forEach((input, idx) => {
    console.log(`[addStepRow] Row ${idx} after tbody.appendChild: value="${input.value}"`);  // Add this
  });
}
```

If values become empty after appending to tbody → DOM manipulation is clearing values!

### Test 3: Check Timeline Visualizer Impact
After rows are created, check if TimelineVisualizer update is clearing values:
```javascript
// In renderStepArrayControl, after creating table:
console.log('[renderStepArrayControl] Before timeline update:');
tbody.querySelectorAll('.step-row').forEach((row, idx) => {
  const val = row.querySelector('.step-time')?.value;
  console.log(`  Row ${idx} step-time value: "${val}"`);
});

// Then after updateTimelineByType call:
updateTimelineByType(tbody, 'vss');

console.log('[renderStepArrayControl] After timeline update:');
tbody.querySelectorAll('.step-row').forEach((row, idx) => {
  const val = row.querySelector('.step-time')?.value;
  console.log(`  Row ${idx} step-time value: "${val}"`);
});
```

If values change after timeline update → Timeline visualizer is culprit!

## Implementation Strategy

1. **Add Test 1 logging** to verify createTimeInput() is setting values correctly
2. **Run test** and check if `[createTimeInput]` logs appear with non-empty values
3. If that works, add Test 2 logging to trace where values are lost
4. Based on findings, either:
   - Fix createTimeInput() to properly set values
   - Fix DOM handling in addStepRow()
   - Fix Timeline visualizer to not clear values
   - Find and fix the form reset call

## Code Locations to Check

- **createTimeInput()**: [parameter_form.js:1084](parameter_form.js#L1084) - Value assignment
- **addStepRow()**: [parameter_form.js:1169](parameter_form.js#L1169) - Row creation and DOM attachment
- **renderStepArrayControl()**: [parameter_form.js:696](parameter_form.js#L696) - Timeline visualizer integration
- **extractTableParameters()**: [templates.html:3176](templates.html#L3176) - Extraction logic
- **updateTimelineByType()**: Search for definition - may be clearing values

## Files That Need Logging

1. `frontend/control/js/parameter_form.js`:
   - createTimeInput() - Add log for value setting
   - addStepRow() - Add logs after appendChild operations
   - renderStepArrayControl() - Add logs before/after timeline update

2. `frontend/control/templates.html`:
   - extractTableParameters() - Already has logging (shows empty values)

## Next Session Priority

**CRITICAL**: Run tests with the Three Detailed Tests above to identify EXACTLY where values are being lost. This will pinpoint the root cause and allow for a targeted fix.

---

**Status**: Root cause narrowed to input value handling, but exact location TBD
**Next Action**: Implement detailed value tracking tests
**Timeline**: All tests show consistent failure - once root cause is fixed, all 5 VSS tests should pass

