# Spec Delta: Strategy Templates - Parameter Extraction Fix

**Capability**: `strategy-templates`
**Change Type**: MODIFIED
**Change ID**: `fix-vss-parameter-extraction`

## MODIFIED Requirements

### Requirement: Template Instance Creation Workflow

The system SHALL reliably transition users between workflow steps with consistent button selectors and parameter value persistence, ensuring all 11 strategy templates (VSS, DHS, TEC) can successfully move from segment selection (Step 2) to parameter configuration (Step 3) with pre-filled default values.

#### Scenario: User creates VSS strategy instance

**Given** user has selected a VSS template (vss_moderate, vss_strict, etc.)
**And** user has selected route G4202, section G4202001, direction counterclockwise
**And** user has queried segments with stake range 33-44 km
**And** user has selected 1-3 segments from results table

**When** user clicks the "Next" button (ID: `#step2-next-bottom` or `#step2-next-top`)

**Then** system must:
1. Transition to Step 3 (parameter configuration page)
2. Display parameter form with all template parameters
3. Pre-fill default values in form inputs (e.g., speed_steps table with time_hours and speed_kmh)
4. Ensure button has consistent ID across all templates
5. Ensure button is visible and enabled when segments are selected

**And** when user submits the form
**Then** API must receive payload with correctly populated parameters:
```json
{
  "strategy_name": "...",
  "template_id": "vss_moderate",
  "configured_params": {
    "affected_edges": ["edge1", "edge2", "edge3"],
    "speed_steps": [
      { "time_hours": 7, "speed_kmh": 100 },
      { "time_hours": 9, "speed_kmh": 80 },
      { "time_hours": 17, "speed_kmh": 100 },
      { "time_hours": 19, "speed_kmh": 80 }
    ]
  }
}
```

**Expected**: NOT `{ "time_hours": NaN, "speed_kmh": NaN }`

### Requirement: Parameter Form Value Persistence

The system SHALL preserve parameter default values from template schema through DOM rendering and manipulation until form submission, ensuring input field values remain populated and extractable as non-empty, valid numeric values.

#### Scenario: VSS template default values populate form inputs

**Given** API returns template with `default_value`:
```json
{
  "parameter_name": "speed_steps",
  "parameter_type": "step_array",
  "default_value": [
    { "time_hours": 7, "speed_kmh": 100 },
    { "time_hours": 9, "speed_kmh": 80 }
  ]
}
```

**When** `renderStepArrayControl()` is called with this schema

**Then** system must:
1. Call `addStepRow(tbody, "speed_steps", 7, 100)` for each default step
2. Create input elements with class `step-time` and `step-speed`
3. Set `input.value = String(timeVal)` and `input.value = String(speedVal)`
4. Append rows to tbody
5. Preserve input values after Timeline Visualizer updates (if enabled)
6. Preserve input values after any other DOM manipulation

**And** when `extractTableParameters("speed_steps", "step_array")` is called

**Then** system must:
1. Query for rows with class `step-row`
2. For each row, find inputs with class `step-time` and `step-speed`
3. Extract `parseFloat(timeInput.value)` and `parseFloat(speedInput.value)`
4. Return array: `[{ time_hours: 7, speed_kmh: 100 }, { time_hours: 9, speed_kmh: 80 }]`

**Expected**: Input values are populated and extractable (NOT empty strings)

### Requirement: E2E Test Button Selector Consistency

E2E tests SHALL use consistent and reliable button selectors (`#step2-next-bottom`, `#step2-next-top`) that match actual HTML implementation across all 11 strategy templates, with proper visibility and enabled state verification before interaction.

#### Scenario: E2E test transitions from Step 2 to Step 3

**Given** test has completed Step 2 (segment selection)
**And** segments have been selected (checkboxes checked)

**When** test looks for "Next" button using selector

**Then** test must use one of these selectors (in order of preference):
1. `#step2-next-bottom` (preferred, bottom of results table)
2. `#step2-next-top` (alternative, top of results table)
3. Fallback: `button:has-text("进入配置参数")` or `button:has-text("下一步")`

**And** test must verify button is visible AND enabled before clicking:
```javascript
await expect(nextBtn).toBeVisible({ timeout: 10000 });
await expect(nextBtn).toBeEnabled();
await nextBtn.click();
```

**Expected**: Test reliably finds and clicks button across all 11 templates

### Requirement: Browser Cache Handling

The system SHALL implement cache-busting mechanisms (query parameters or cache headers) to ensure browsers load the latest version of JavaScript files (`parameter_form.js`) after updates, preventing stale code from causing parameter extraction failures.

#### Scenario: Updated parameter_form.js is served to browser

**Given** `parameter_form.js` has been updated with a fix

**When** browser requests the page

**Then** HTML must include cache-busting query parameter:
```html
<script src="js/parameter_form.js?v=20251102"></script>
```

**Or** server must send appropriate cache headers:
```
Cache-Control: no-cache, must-revalidate
```

**Expected**: Browser loads latest version of JavaScript files, not cached version

## Implementation Notes

### Files Modified

1. **tests/e2e/test_strategy_template_parameters.spec.js**
   - Update button selector on line 212-214
   - Add button visibility/enabled check before clicking

2. **frontend/control/js/parameter_form.js**
   - Verify `createTimeInput()` sets `input.value = String(value)` (already implemented on line 1091)
   - Ensure `addStepRow()` doesn't lose values after `tbody.appendChild(row)`
   - Investigate Timeline Visualizer impact on input values (line 794)

3. **frontend/control/templates.html**
   - Add cache-busting query parameter to script imports
   - Verify `extractTableParameters()` correctly queries for `.step-time` and `.step-speed`
   - Ensure button IDs are consistent: `#step2-next-top` and `#step2-next-bottom`

### Testing Requirements

- [ ] All 11 template tests pass in `test_strategy_template_parameters.spec.js`
- [ ] All workflow tests pass in `test_strategy_creation_workflow.spec.js`
- [ ] Manual test: VSS strategy creation works end-to-end
- [ ] API receives correct payload with populated `time_hours` and `speed_kmh` fields
- [ ] No console errors during form generation or submission

### Backward Compatibility

- ✅ Existing working tests (`test_strategy_creation_workflow.spec.js`) continue to use `#step2-next-top` selector
- ✅ Frontend button IDs remain unchanged for existing functionality
- ⚠️ Test selectors updated to match actual HTML implementation
- ⚠️ Cache-busting may require server configuration changes (or manual cache clearing)

## Acceptance Criteria

- [ ] All 14 failing tests now pass
- [ ] Parameter extraction returns non-NaN values for `time_hours` and `speed_kmh`
- [ ] Button selectors work across all 11 templates (VSS, DHS, TEC)
- [ ] Form default values are visible in UI before user interaction
- [ ] API validation passes with correct parameter payload structure

## Related Issues

- Root cause documents (moved to `investigation/`):
  - CRITICAL_ROOT_CAUSE_ANALYSIS.md
  - CRITICAL_PARAMETER_EXTRACTION_ISSUE.md
  - PARAMETER_FLOW_DISCOVERY.md
- Test failures: 14/20 tests in `test_strategy_template_parameters.spec.js`
- Working reference: `test_strategy_creation_workflow.spec.js` (6/6 passing)
