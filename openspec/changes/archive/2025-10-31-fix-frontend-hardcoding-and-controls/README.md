# OpenSpec Change: Fix Frontend Hardcoding and Unified Control System

## Overview

This OpenSpec change addresses critical frontend code quality issues that violate **RULE-FE-001** (no hardcoded data) and prevent proper template configuration loading.

## Change Summary

| Aspect | Details |
|--------|---------|
| **Change ID** | `fix-frontend-hardcoding-and-controls` |
| **Status** | Proposal |
| **Priority** | P0 (Blocks core functionality) |
| **Scope** | Frontend parameter forms (templates.html, parameter_form.js, CSS) |
| **Estimated Time** | 8-10 hours |
| **Files Modified** | 3 (+ CSS refactoring) |

## Problem Overview

### 🔴 Issue 1: Hardcoded Default Values in HTML

```html
<!-- ❌ WRONG: Hardcoded values override template defaults -->
<input type="number" placeholder="如: 7" />        <!-- Should load template default -->
<input type="number" placeholder="如: 60" />       <!-- Should load template default -->
<input type="number" placeholder="500" />         <!-- Should load template default -->
```

**Impact**:
- Users see hardcoded examples instead of actual template defaults
- Template configuration data is ignored
- Difficult to debug which data comes from where
- Violates RULE-FE-001 (no hardcoded data)

**Root Cause**: HTML `placeholder` attributes contain hardcoded numeric values that take precedence over template `default_value` field.

### 🔴 Issue 2: Duplicate Control Functions

Functions exist in BOTH `templates.html` AND `parameter_form.js`:
- `addStepRow()` vs `addFlowIntervalRow()`
- `createFlowIntervalControl()` vs `renderStepArrayControl()`
- `addDHSIntervalRow()` in both files with different signatures
- `createVehicleTypeControl()` (partial implementation)

**Impact**:
- Code duplication makes maintenance difficult
- Changes to one don't propagate to the other
- Inconsistency in function signatures and behavior
- Increases bug risk

### 🔴 Issue 3: Incomplete Vehicle Type Control

Vehicle type restriction modes not properly integrated:
- "allow" mode: Allow selected vehicle types
- "disallow" mode: Prevent selected vehicle types
- "none" mode: No restrictions

**Current Problem**:
- No unified control combining all three modes
- Checkbox interactions not working
- Switching modes doesn't show/hide controls correctly
- No mutual exclusion logic

### 🔴 Issue 4: Layout & Styling Issues

- Hardcoded inline styles in JavaScript (scattered across functions)
- No responsive design for mobile devices
- Inconsistent spacing and alignment
- Required fields not visually distinguished

## Solution Architecture

### Phase 1️⃣: Remove Hardcoding
Load ALL template defaults from `paramSchema.default_value` instead of hardcoded values:

```javascript
// ✅ CORRECT: Load from template
const defaultValue = paramSchema.default_value ?? '';  // From template
if (defaultValue !== '') {
  input.value = defaultValue;  // Set as actual value
}
```

### Phase 2️⃣: Consolidate Functions
Move ALL control logic to `parameter_form.js` (single source of truth):

```
❌ templates.html: NO control functions
✅ parameter_form.js: ALL control functions
├── renderParameterControl() [Factory]
├── renderIntegerControl()
├── renderNumberControl()
├── renderStepArrayControl()
├── renderDHSIntervalControl()
└── renderUnifiedVehicleTypeControl()
```

### Phase 3️⃣: Unified Vehicle Type Control
Single control handling all modes with proper state management:

```
restriction_mode selector
  ├─ "none": Hide all vehicle type controls
  ├─ "allow": Show allowed_vehicle_types only
  └─ "disallow": Show disallowed_vehicle_types only
     (Auto-clear when mode switches)
```

### Phase 4️⃣: Responsive CSS
Move inline styles to CSS, implement responsive design:

```css
/* Responsive grid layout */
@media (max-width: 768px) {
  .param-table {
    overflow-x: auto;  /* Horizontal scroll on mobile */
  }
}
```

## Key Files

| File | Change | Purpose |
|------|--------|---------|
| `proposal.md` | **CREATE** | Problem statement, solution overview, success criteria |
| `design.md` | **CREATE** | Architecture, data flows, state machines, CSS strategy |
| `tasks.md` | **CREATE** | Detailed task breakdown with validation criteria |
| `frontend/control/templates.html` | **EDIT** | Remove hardcoding, remove duplicate functions |
| `frontend/control/js/parameter_form.js` | **EDIT** | Consolidate all control logic here |
| `frontend/control/css/templates-forms.css` | **EDIT** | Move inline styles, add responsive design |

## Success Criteria

✅ Zero hardcoded numeric values in HTML
✅ All template defaults properly loaded from schema
✅ No duplicate function definitions (1 location per function)
✅ Vehicle type controls show/hide per restriction mode
✅ Responsive design tested at 375px, 768px, 1920px
✅ E2E test suite 100% passing
✅ All functions documented with data sources

## Timeline

| Phase | Time | Dependencies |
|-------|------|--------------|
| 1: Audit & Hardcoding Removal | 1.5h | None |
| 2: Function Consolidation | 2.5h | Phase 1 |
| 3: Vehicle Type Control | 2h | Phase 2 |
| 4: CSS Optimization | 1.5h | Phase 2 |
| 5: Integration Testing | 1.5h | Phase 3-4 |
| 6: Quality & Docs | 1h | All phases |
| **Total** | **~10h** | Sequential |

## Risk Assessment

**Risk Level**: 🟢 **LOW**

**Justification**:
- Frontend-only change (no API/database impact)
- Isolated to parameter form rendering
- Existing E2E tests validate functionality
- Simple rollback: git revert changes

**Mitigation**:
- E2E tests run before merge
- Manual testing on multiple browsers
- Code review for data flow verification

## Next Steps

1. **Review**: Review proposal.md, design.md, tasks.md
2. **Clarify**: Ask questions if implementation details unclear
3. **Approve**: Confirm approach aligns with project standards
4. **Implement**: Execute tasks in order (phases 1-6)
5. **Test**: Run E2E tests, manual validation
6. **Merge**: Create PR, request code review, merge to main

## References

- **RULE-FE-001**: Frontend data rules (no hardcoding, single source of truth)
- **CLAUDE.md**: Project guidelines for frontend development
- **design.md**: Detailed architecture and implementation patterns
- **tasks.md**: Specific task breakdown with validation criteria

## Questions?

For clarification on:
- **Architecture**: See design.md for data flow diagrams
- **Implementation**: See tasks.md for detailed steps
- **Validation**: See success criteria section above

---

**Status**: 🟡 **Proposal** - Ready for review and discussion
**Created**: 2025-10-31
**Author**: Claude AI Assistant
