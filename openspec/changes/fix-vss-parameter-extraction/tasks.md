# Implementation Tasks: Fix VSS Parameter Extraction

**Change ID**: `fix-vss-parameter-extraction`
**Status**: Not Started
**Priority**: P0 (Critical - Blocks strategy creation)

## Task Checklist

### Phase 1: Diagnosis & Root Cause Identification

- [ ] **Task 1.1**: Run failing test in headed mode with DevTools
  - Command: `npx playwright test tests/e2e/test_strategy_template_parameters.spec.js -g "vss_moderate" --headed`
  - Observe: Browser window, button elements, console logs
  - Document: Actual button selector (ID, class, text)

- [ ] **Task 1.2**: Inspect templates.html Step 2 button HTML
  - File: `frontend/control/templates.html`
  - Search for: "进入配置参数", "下一步", button elements in Step 2
  - Document: All button IDs and classes for Step 2 → Step 3 transition
  - Compare: With working test `test_strategy_creation_workflow.spec.js` (uses `#step2-next-top`, `#step2-next-bottom`)

- [ ] **Task 1.3**: Verify browser cache issue
  - Add cache-busting to script imports: `<script src="js/parameter_form.js?v=TIMESTAMP">`
  - Clear browser cache before test run
  - Re-run test to see if issue persists

- [ ] **Task 1.4**: Trace parameter value flow with console logs
  - Run test with browser console open
  - Check for logs from:
    - `[renderStepArrayControl] Adding default step`
    - `[addStepRow] Created timeInput`
    - `[extractTableParameters] step_array - row 0`
  - Document: Which logs appear, which are missing

### Phase 2: Fix Implementation

#### Option A: Fix Test Selectors (Quick Win)

- [ ] **Task 2.1**: Update test button selectors
  - File: `tests/e2e/test_strategy_template_parameters.spec.js`
  - Line: 212-214 (nextBtn selector)
  - Change from: `page.locator('button:has-text("下一步")').last()`
  - Change to: `page.locator('#step2-next-bottom')`
  - Add fallback: Try `#step2-next-top` first, then `#step2-next-bottom`

- [ ] **Task 2.2**: Verify button exists before clicking
  - Add: `await expect(nextBtn).toBeVisible({ timeout: 10000 })`
  - Add: `await expect(nextBtn).toBeEnabled()`
  - Handle error: If not found, log helpful diagnostic message

#### Option B: Fix Frontend Button Consistency (if needed)

- [ ] **Task 2.3**: Standardize Step 2 next button IDs
  - Files: `frontend/control/templates.html`, `frontend/control/js/edge_selector_embedded.js`
  - Ensure all "Next" buttons have ID: `step2-next-bottom` or `step2-next-top`
  - Add consistent CSS classes: `btn`, `btn-primary`, `step-transition-btn`

#### Option C: Fix Parameter Value Persistence

- [ ] **Task 2.4**: Investigate Timeline Visualizer impact
  - File: `frontend/control/js/parameter_form.js`
  - Line: 794 (`updateTimelineByType(tbody, 'vss')`)
  - Test: Comment out this line and re-run test
  - If test passes: Timeline Visualizer is clearing values

- [ ] **Task 2.5**: Fix value persistence (if Task 2.4 confirms issue)
  - Option 1: Set input values AFTER timeline update
  - Option 2: Ensure Timeline Visualizer reads existing values instead of recreating DOM
  - Option 3: Add feature flag to disable timeline during tests: `if (!window.__TESTING__) { updateTimeline(); }`

- [ ] **Task 2.6**: Add defensive value restoration
  - After `tbody.appendChild(row)`, re-verify input values are set
  - If empty, restore from parameters: `timeInput.value = timeInput.value || timeVal`

### Phase 3: Validation & Testing

- [ ] **Task 3.1**: Run single VSS template test
  - Command: `npx playwright test tests/e2e/test_strategy_template_parameters.spec.js -g "vss_moderate"`
  - Expected: Test passes, moves to Step 3, finds parameter form

- [ ] **Task 3.2**: Run all 11 template tests
  - Command: `npx playwright test tests/e2e/test_strategy_template_parameters.spec.js`
  - Expected: All 20 tests pass (11 templates + 3 edge cases + 1 summary + 5 other)
  - Document: Any remaining failures with error messages

- [ ] **Task 3.3**: Run workflow tests (regression check)
  - Command: `npx playwright test tests/e2e/test_strategy_creation_workflow.spec.js`
  - Expected: All 6 tests continue to pass
  - Ensure: VSS, DHS, TEC workflows still work

- [ ] **Task 3.4**: Manual smoke test - VSS strategy creation
  - Navigate: http://localhost:8000/control/templates.html
  - Select: VSS Moderate template
  - Route: G4202, Section: G4202001, Direction: counterclockwise
  - Query: Min stake 33, Max stake 44
  - Select: 3 segments, click "Next" button
  - Verify: Parameter form appears with speed_steps table pre-filled
  - Check: Input values show `7`, `100`, etc. (not empty)
  - Fill: Strategy name, adjust parameters if needed
  - Submit: Click "创建策略" button
  - Expected: 201 response, strategy instance created in database

- [ ] **Task 3.5**: Verify API payload correctness
  - Open: Browser DevTools → Network tab
  - Submit: VSS strategy form
  - Inspect: Request payload to `/api/v1/control/strategy-instances/`
  - Verify: `configured_params.speed_steps` contains array with `time_hours` and `speed_kmh` fields
  - Expected: `[{ time_hours: 7, speed_kmh: 100 }, ...]` (NOT `[{ time_hours: NaN, speed_kmh: NaN }]`)

### Phase 4: Documentation & Cleanup

- [ ] **Task 4.1**: Move investigation documents to proposal directory
  - From: Project root (`D:\projects\OD_SIM`)
  - To: `openspec/changes/fix-vss-parameter-extraction/investigation/`
  - Files:
    - CRITICAL_ROOT_CAUSE_ANALYSIS.md
    - CRITICAL_PARAMETER_EXTRACTION_ISSUE.md
    - PARAMETER_FLOW_DISCOVERY.md
    - FRONTEND_UI_TEST_ANALYSIS_REPORT.md
    - FRONTEND_TEST_ACTION_PLAN.md
    - PARAMETER_AUTO_POPULATION_DEBUG_GUIDE.md
    - DHS_MINIMUM_LANES_FIX.md (if related)
    - SESSION_SUMMARY.md
    - Other related test reports

- [ ] **Task 4.2**: Update proposal.md with findings
  - Document: Actual root cause discovered in Phase 1
  - Update: Solution approach based on what actually worked
  - Add: Performance impact (if any)

- [ ] **Task 4.3**: Clean up debug logging (if added temporarily)
  - Remove or comment out excessive console.log statements
  - Keep critical logs for future debugging
  - Ensure production build has minimal logging

- [ ] **Task 4.4**: Update CLAUDE.md if patterns changed
  - If button selector pattern was standardized, document it
  - Add to "Common Pitfalls" if this was a common issue
  - Update E2E testing best practices section

### Phase 5: Validation Before Merge

- [ ] **Task 5.1**: Full E2E test suite
  - Command: `npx playwright test tests/e2e/`
  - Expected: All tests pass (or only known flaky tests fail)
  - Document: Any new failures introduced by changes

- [ ] **Task 5.2**: Visual regression check
  - Open: templates.html in browser
  - Test: All 11 templates (VSS, DHS, TEC)
  - Verify: No visual regressions (buttons, forms, tables look correct)
  - Check: Timeline visualizer still works (if kept enabled)

- [ ] **Task 5.3**: Code review checklist
  - [ ] No hardcoded values introduced
  - [ ] No inline styles added to HTML
  - [ ] Functions follow Single Responsibility Principle
  - [ ] CSS changes in separate files (not inline)
  - [ ] All debug logs have clear prefixes
  - [ ] No `console.log` without context

## Rollback Procedure

If any task fails critically:

1. **Stop immediately** - Do not proceed to next phase
2. **Document failure** - Add details to proposal.md "Risks & Mitigation" section
3. **Revert changes** - Use git to restore previous working state
4. **Re-analyze** - Return to Phase 1 with new hypothesis
5. **Update tasks** - Revise this task list based on new findings

## Dependencies

- [ ] API server running: `.\start_api.ps1` or `python api\main.py`
- [ ] Conda environment active: `conda activate od_project`
- [ ] Database accessible: PostgreSQL on 10.149.235.123
- [ ] Test data available: G4202 route segments in database
- [ ] Browser installed: Playwright browsers (Chromium)

## Progress Tracking

**Started**: [DATE]
**Completed**: [DATE]
**Total Time**: [HOURS]

**Phase 1 Complete**: [ ] Yes / [ ] No
**Phase 2 Complete**: [ ] Yes / [ ] No
**Phase 3 Complete**: [ ] Yes / [ ] No
**Phase 4 Complete**: [ ] Yes / [ ] No
**Phase 5 Complete**: [ ] Yes / [ ] No

## Notes

- Add any discoveries, blockers, or important observations here during implementation
- Document any deviations from planned approach
- Record actual time spent per phase for future estimation
