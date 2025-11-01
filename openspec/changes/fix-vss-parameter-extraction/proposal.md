# Proposal: Fix VSS Strategy Instance Creation Parameter Extraction

**Change ID**: `fix-vss-parameter-extraction`
**Status**: Draft
**Created**: 2025-11-02
**Author**: Claude Code Analysis

## Executive Summary

E2E tests reveal that **all 11 strategy templates (5 VSS, 3 DHS, 3 TEC) are failing** during strategy instance creation due to a critical parameter extraction issue. The problem occurs at Step 2 ("下一步" button click) where the test cannot find the button to proceed from segment selection to parameter configuration.

**Impact**:
- 14 out of 20 tests failing in `test_strategy_template_parameters.spec.js`
- All VSS, DHS, and TEC templates affected
- Strategy instance creation workflow completely broken
- Users unable to create any control strategies

**Root Cause** (Preliminary):
The "下一步" (Next) button selector in tests is looking for `button:has-text("下一步")` but this button may:
1. Not exist with that exact text
2. Be disabled due to validation failures
3. Have a different selector ID/class
4. Not appear until某些conditions are met

## Problem Statement

### Current Behavior

**Test Output Analysis**:
```
Error: expect(locator).toBeEnabled() failed
Locator:  locator('button:has-text("下一步")').last()
Expected: enabled
Received: <element(s) not found>
Timeout:  5000ms
```

**Affected Tests**:
- `test_strategy_template_parameters.spec.js`: 14/20 tests failing
  - All 5 VSS templates (vss_moderate, vss_strict, vss_weather_based, vss_upstream_warning, vss_lane_differentiated)
  - All 3 DHS templates (dhs_peak_hours, dhs_passenger_only, dhs_peak_multi_interval)
  - All 3 TEC templates (tec_flow_metering, tec_vehicle_restriction, tec_emergency_closure)
  - 3 edge case tests (VSS Moderate speed_steps, DHS intervals, TEC flow_intervals)

**Working Tests**:
- `test_strategy_creation_workflow.spec.js`: 6/6 tests passing
  - Uses different button selector: `#step2-next-top` and `#step2-next-bottom`
  - Validates button is visible before clicking
  - Has better error handling and retry logic

### Expected Behavior

After selecting segments in Step 2, users should be able to:
1. Click the "下一步" button (or "进入配置参数" button)
2. Proceed to Step 3 (parameter configuration page)
3. See parameter form generated with all expected parameters
4. Fill in parameters and submit to create strategy instance

### Analysis from Root Cause Documents

Based on comprehensive investigation (CRITICAL_ROOT_CAUSE_ANALYSIS.md, CRITICAL_PARAMETER_EXTRACTION_ISSUE.md, PARAMETER_FLOW_DISCOVERY.md):

**Forward Data Flow** (API → Frontend):
1. ✅ API provides template with `default_value: [{ time_hours: 7, speed_kmh: 100 }, ...]`
2. ✅ `generateParamsForm()` receives template and logs `hasDefaultValue: true, defaultLength: 4`
3. ✅ `renderStepArrayControl()` logs `defaultStepsCount: 4` and processes default steps
4. ✅ For each step, calls `addStepRow(tbody, paramName, 7, 100, stepStructure)`
5. ✅ `createTimeInput("step-time", 7)` creates input with `input.value = String(7)`
6. ❓ **Potential Issue**: Browser cache might serve old `parameter_form.js` without the fix

**Backward Data Flow** (Form Submission → API):
1. User fills form → clicks "保存策略" or "创建策略" button
2. Event handler calls `collectParameterValues()` → `extractFormParameters()`
3. `extractTableParameters(paramName, 'step_array')` queries for `.step-row` elements
4. For each row, extracts `.step-time` and `.step-speed` input values
5. ❌ **Critical Issue**: Extracted values are **empty strings**, not the default values
6. API receives payload with `speed_steps: [{ time_hours: NaN, speed_kmh: NaN }, ...]`
7. API validation fails: `"Step 0: missing 'time_hours' or 'time_seconds' field"`

**Hypotheses**:
1. **Browser Cache Issue** ⚠️: Frontend serves cached `parameter_form.js` without the value-setting fix
2. **Value Lost After DOM Attachment** ⚠️: Input values become empty after `tbody.appendChild(row)`
3. **Timeline Visualizer Clears Values** 🔴: `updateTimelineByType(tbody, 'vss')` reconstructs DOM and loses values
4. **Form Reset Called** ⚠️: Some code calls `form.reset()` between creation and extraction

## Proposal

### Objectives

1. **Fix Button Selector Issue**: Ensure tests can find and click the "Next" button in Step 2
2. **Fix Parameter Extraction**: Ensure form values are properly populated and extracted
3. **Improve Test Robustness**: Make tests more resilient to UI changes
4. **Validate Data Flow**: Confirm parameters flow correctly from template → form → API

### Approach

#### Phase 1: Diagnosis & Root Cause Identification (Priority: P0)

1. **Test Button Selector Mismatch**:
   - Inspect actual HTML to find correct button selector in templates.html
   - Compare working test (`test_strategy_creation_workflow.spec.js`) vs failing test
   - Document actual button IDs/classes: `#step2-next-top`, `#step2-next-bottom`, or text-based selector

2. **Trace Parameter Extraction Flow**:
   - Add debug logging to `extractTableParameters()` in templates.html
   - Add debug logging to `addStepRow()` and `createTimeInput()` in parameter_form.js
   - Run test in headed mode with DevTools console open to see logs

3. **Test Browser Cache Hypothesis**:
   - Clear browser cache before test runs
   - Add cache-busting query parameter to script imports: `<script src="parameter_form.js?v=20251102">`
   - Verify latest code is being served

#### Phase 2: Fix Implementation (Priority: P0)

**Option A: Fix Test Selectors** (Quick Win)
- Update `test_strategy_template_parameters.spec.js` to use correct button selectors
- Change from `button:has-text("下一步")` to `#step2-next-bottom` (consistent with working tests)
- Add fallback selectors: try `#step2-next-top` first, then `#step2-next-bottom`

**Option B: Fix Frontend Button Consistency** (Long-term)
- Ensure all "Next" buttons have consistent IDs across all templates
- Add `id="step2-next-button"` to button elements
- Update both templates.html and edge_selector_embedded.js

**Option C: Fix Parameter Value Persistence** (Critical)
- Investigate why input values become empty after DOM attachment
- Possible fixes:
  1. Set values AFTER appending to tbody: `tbody.appendChild(row); timeInput.value = timeVal;`
  2. Disable Timeline Visualizer temporarily during form generation
  3. Ensure Timeline Visualizer doesn't recreate DOM elements
  4. Add defensive value restoration after timeline updates

#### Phase 3: Validation & Testing (Priority: P0)

1. **Verify All 11 Templates**:
   - Run full test suite: `npx playwright test tests/e2e/test_strategy_template_parameters.spec.js`
   - Expected: All 20 tests pass
   - Verify each template type (VSS, DHS, TEC) works end-to-end

2. **Manual Smoke Test**:
   - Open templates.html in browser
   - Select VSS template → G4202 route → select segments → click "Next"
   - Verify parameter form loads with pre-filled default values
   - Submit form and verify strategy instance is created in database

3. **Regression Testing**:
   - Run `test_strategy_creation_workflow.spec.js` to ensure working tests still pass
   - Test all 3 strategy types (VSS, DHS, TEC)

### Success Criteria

- [ ] All 14 failing tests in `test_strategy_template_parameters.spec.js` pass
- [ ] All 6 tests in `test_strategy_creation_workflow.spec.js` continue to pass
- [ ] Manual test: Can create VSS strategy instance through UI without errors
- [ ] API receives correct parameter payload with `time_hours` and `speed_kmh` fields populated
- [ ] No browser console errors during form generation or submission
- [ ] Parameter default values visible in form inputs before user edits

### Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Browser cache serves old code | High | High | Add cache-busting query params, clear cache in test setup |
| Timeline Visualizer breaks form | High | Medium | Add feature flag to disable timeline during tests, or fix DOM updates |
| Multiple button IDs cause confusion | Medium | High | Standardize on single button ID pattern across all templates |
| Fix breaks other templates (DHS, TEC) | High | Low | Run full test suite on all 11 templates before merging |

## Implementation Plan

See `tasks.md` for detailed implementation checklist.

**Estimated Effort**: 1-2 days
- Phase 1 (Diagnosis): 4-6 hours
- Phase 2 (Fix Implementation): 4-8 hours
- Phase 3 (Validation): 2-4 hours

**Dependencies**:
- Access to production database for manual testing
- API server running on localhost:8000
- Playwright test environment configured

## Rollback Plan

If fix causes regressions:
1. Revert changes to `test_strategy_template_parameters.spec.js`
2. Revert changes to `parameter_form.js` if value-setting logic was modified
3. Keep diagnostic logging in place for future debugging
4. Document findings in investigation directory

## Related Documents

- Investigation: `openspec/changes/fix-vss-parameter-extraction/investigation/`
  - CRITICAL_ROOT_CAUSE_ANALYSIS.md
  - CRITICAL_PARAMETER_EXTRACTION_ISSUE.md
  - PARAMETER_FLOW_DISCOVERY.md
  - Other test reports moved from project root
- Working Test: `tests/e2e/test_strategy_creation_workflow.spec.js` (reference for correct patterns)
- Failing Test: `tests/e2e/test_strategy_template_parameters.spec.js`
- Frontend Code:
  - `frontend/control/js/parameter_form.js` (lines 696-807: renderStepArrayControl, lines 1169-1244: addStepRow, lines 1084-1092: createTimeInput)
  - `frontend/control/templates.html` (lines 3176-3209: extractTableParameters for step_array)

## Questions for Review

1. Should we prioritize fixing the tests (Option A) or fixing the frontend (Option B)?
2. Is the Timeline Visualizer a required feature, or can we disable it temporarily?
3. Do we have a pattern for cache-busting in this project (query params, headers, build process)?
4. Should we add a systematic test to verify all template button selectors match?

## Approval

- [ ] Technical Lead Review
- [ ] Product Owner Approval
- [ ] Security Review (if applicable)
- [ ] Ready for Implementation

---

**Next Steps**: After approval, begin Phase 1 diagnosis with headed browser test to observe actual button elements and console logs.
