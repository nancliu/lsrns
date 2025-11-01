# Fix VSS Parameter Extraction - OpenSpec Change

**Status**: ✅ Validated | Draft - Awaiting Approval
**Created**: 2025-11-02
**Change ID**: `fix-vss-parameter-extraction`

## Quick Summary

This OpenSpec change proposes fixes for a critical parameter extraction issue affecting **all 11 strategy templates** (VSS, DHS, TEC). E2E tests are failing because:

1. **Button Selector Mismatch**: Tests look for `button:has-text("下一步")` but actual HTML uses `#step2-next-bottom`
2. **Parameter Value Loss**: Form inputs are created with default values but become empty during extraction
3. **Browser Cache**: Old JavaScript may be served instead of latest fixes

**Impact**: Users unable to create any control strategy instances (0% success rate).

## Files in This Change

```
fix-vss-parameter-extraction/
├── README.md                          # This file
├── proposal.md                        # Detailed proposal with diagnosis plan
├── tasks.md                           # Implementation checklist (5 phases, 23 tasks)
├── specs/
│   └── strategy-templates/
│       └── spec.md                    # Spec deltas (4 modified requirements)
└── investigation/                      # Root cause analysis documents (moved from project root)
    ├── CRITICAL_ROOT_CAUSE_ANALYSIS.md
    ├── CRITICAL_PARAMETER_EXTRACTION_ISSUE.md
    ├── PARAMETER_FLOW_DISCOVERY.md
    ├── FRONTEND_UI_TEST_ANALYSIS_REPORT.md
    ├── FRONTEND_TEST_ACTION_PLAN.md
    ├── PARAMETER_AUTO_POPULATION_DEBUG_GUIDE.md
    ├── DHS_MINIMUM_LANES_FIX.md
    ├── SESSION_SUMMARY.md
    ├── FRONTEND_TEST_INDEX.md
    ├── TEST_STRATEGY_CREATION_REPORT.md
    └── COMPREHENSIVE_STRATEGY_CREATION_TEST_REPORT.md
```

## Test Failures

**Failing**: 14/20 tests in `test_strategy_template_parameters.spec.js`
- All 5 VSS templates
- All 3 DHS templates
- All 3 TEC templates
- 3 edge case tests

**Passing**: 6/6 tests in `test_strategy_creation_workflow.spec.js` (uses correct button selectors)

## Root Cause Analysis

### Forward Data Flow (✅ Working)
1. API provides template with `default_value: [{ time_hours: 7, speed_kmh: 100 }, ...]`
2. `renderStepArrayControl()` processes default steps
3. `addStepRow()` creates inputs with `input.value = String(7)`
4. Rows appended to tbody

### Backward Data Flow (❌ Broken)
1. User submits form
2. `extractTableParameters()` queries for `.step-time` and `.step-speed` inputs
3. **Problem**: Input values are empty strings (not `"7"`, `"100"`)
4. Extracted as `{ time_hours: NaN, speed_kmh: NaN }`
5. API validation fails: `"Step 0: missing 'time_hours' field"`

### Hypotheses
1. **Browser Cache** ⚠️: Serving old `parameter_form.js` without value-setting fix
2. **Timeline Visualizer** 🔴: DOM updates clearing input values
3. **DOM Attachment** ⚠️: Values lost after `tbody.appendChild(row)`
4. **Button Selector** 🔴: Test can't find button to proceed to Step 3

## Proposed Solution

### Phase 1: Diagnosis (4 tasks)
- Run test in headed mode to observe actual button selectors
- Verify browser cache is serving latest code
- Trace parameter value flow with console logs

### Phase 2: Fixes (6 tasks)
- **Option A**: Update test selectors to `#step2-next-bottom` ← Quick Win
- **Option B**: Standardize button IDs in HTML
- **Option C**: Fix value persistence (investigate Timeline Visualizer impact)

### Phase 3: Validation (5 tasks)
- Run all 20 tests → expect 100% pass
- Manual smoke test: Create VSS strategy instance
- Verify API receives correct payload structure

### Phase 4: Documentation (4 tasks)
- Investigation docs moved to `investigation/` subdirectory
- Update CLAUDE.md with patterns
- Clean up debug logging

### Phase 5: Pre-Merge Validation (3 tasks)
- Full E2E test suite
- Visual regression check
- Code review against RULE-FE-001, STANDARD-CODE-001

## Expected Outcomes

**Success Criteria**:
- [ ] All 14 failing tests pass
- [ ] API receives `{ time_hours: 7, speed_kmh: 100 }` (NOT `{ time_hours: NaN, speed_kmh: NaN }`)
- [ ] Form inputs show pre-filled default values
- [ ] No console errors during form generation
- [ ] All 11 templates work end-to-end

**Estimated Effort**: 1-2 days (14-18 hours)

## Next Steps

1. **Review & Approve**: Technical lead reviews `proposal.md`
2. **Begin Phase 1**: Run diagnostic tests in headed mode
3. **Implement Fix**: Based on Phase 1 findings
4. **Validate**: Run full test suite
5. **Archive**: After deployment, move to `changes/archive/2025-11-02-fix-vss-parameter-extraction/`

## Related Files

**Tests**:
- `tests/e2e/test_strategy_template_parameters.spec.js` (failing)
- `tests/e2e/test_strategy_creation_workflow.spec.js` (working - reference for correct patterns)

**Frontend**:
- `frontend/control/js/parameter_form.js` (lines 696-807, 1169-1244, 1084-1092)
- `frontend/control/templates.html` (lines 3176-3209)

**API**:
- `api/routes/control_strategy_instance_routes.py` (validation logic)
- `shared/control_tools/parameter_validator.py` (field validation)

## Validation Command

```bash
# Validate this OpenSpec change
openspec validate fix-vss-parameter-extraction --strict

# Show deltas
openspec show fix-vss-parameter-extraction --json --deltas-only
```

---

**Status**: ✅ OpenSpec validation passed
**Ready for**: Technical review and approval
