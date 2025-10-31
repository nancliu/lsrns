# Proposal: Fix Simulations Page CSS Import

**Change ID**: fix-simulations-page-css-import
**Created**: 2025-10-31
**Status**: Completed
**Priority**: P0 (Critical - Page is non-functional)

## Why

The batch simulation page (`frontend/control/simulations.html`) has **completely lost its CSS styling**. All visual elements appear unstyled, making the page unusable. This critical bug prevents users from accessing the batch simulation functionality, which is a core feature of the traffic control optimization system.

## What Changes

This change fixes the missing CSS styling by:
1. Adding missing CSS import statements to `simulations.html`
2. Adding view display control CSS rules to enable tab switching
3. Removing inline styles and replacing with CSS classes (CSS separation principle)
4. Refactoring JavaScript to use CSS classes instead of inline style manipulation

## Problem Statement

The batch simulation page (`frontend/control/simulations.html`) has **completely lost its CSS styling**. All visual elements appear unstyled, making the page unusable.

### Root Cause

The `simulations.html` page references `css/simulations.css`, which heavily uses CSS custom properties (CSS variables) defined in `css/variables.css`. However, **`simulations.html` does not import `variables.css`**, causing all variable references to be undefined and resulting in no styling.

**Evidence**:
- `simulations.css` uses variables like `--color-primary`, `--spacing-20`, `--font-size-base`, etc.
- `variables.css` defines these variables in `:root { ... }`
- `templates.html` correctly imports both `variables.css` and other CSS files
- `simulations.html` only imports `simulations.css` (missing `variables.css`)

**Current HTML head** (simulations.html:11):
```html
<link rel="stylesheet" href="css/simulations.css">
```

**Expected HTML head** (reference from templates.html:12-18):
```html
<link rel="stylesheet" href="css/variables.css">
<link rel="stylesheet" href="css/templates-base.css">
<link rel="stylesheet" href="css/templates-layout.css">
<link rel="stylesheet" href="css/simulations.css">
```

## Context

This issue was introduced during the CSS optimization effort (see archived change `enhance-batch-simulation-monitoring`), where:
1. CSS variables were consolidated into `variables.css`
2. Layout styles were extracted to `templates-layout.css` and `templates-base.css`
3. Page-specific styles were moved to individual files (e.g., `simulations.css`)
4. **However, the HTML import statements were not updated** in `simulations.html`

The archived design document (`openspec/changes/archive/2025-10-30-enhance-batch-simulation-monitoring/design.md`) shows the intended CSS architecture with modular CSS files, but the actual implementation was incomplete.

## Proposed Solution

Add the missing CSS imports to `simulations.html` in the correct order:

1. **`variables.css`** - First (defines all CSS custom properties)
2. **`templates-base.css`** - Base styles (reset, common button styles, badges)
3. **`templates-layout.css`** - Layout styles (top-bar, sidebar, main-container, content-area)
4. **`simulations.css`** - Page-specific styles (already present)

**Rationale for import order**:
- Variables must load first (other files depend on them)
- Base styles before layout (reset → common → structure)
- Layout before page-specific (general → specific)

## Impact Analysis

**Affected Files**:
- `frontend/control/simulations.html` (1 file, 3 new lines)

**User Impact**:
- **Before**: Page completely unstyled, unusable
- **After**: Page displays correctly with full styling

**Risk Level**: **Low**
- Change is minimal (3 line addition)
- No logic changes
- No API changes
- No data model changes

## Dependencies

**No dependencies** - This is a standalone HTML fix.

**Related Changes**:
- Reference: `openspec/changes/archive/2025-10-30-enhance-batch-simulation-monitoring` (archived CSS architecture design)

## Testing Strategy

### Manual Testing
1. Open `http://localhost:8000/control/simulations.html`
2. Verify:
   - ✅ Top bar displays with gradient background
   - ✅ Sidebar navigation styled correctly
   - ✅ Content area has proper padding and layout
   - ✅ Buttons have colors (primary=blue, secondary=gray)
   - ✅ Config sections have white backgrounds with shadows
   - ✅ Form inputs have borders and proper spacing
   - ✅ View tabs styled correctly
   - ✅ All color variables resolve correctly

### Visual Regression
Compare with `templates.html` (which has correct imports):
- Both should have similar top bar, sidebar, button styles
- Layout structure should be consistent

### Browser Compatibility
- Chrome/Edge (primary)
- Firefox (secondary)
- Safari (if available)

## Acceptance Criteria

1. ✅ `simulations.html` imports `variables.css` before other CSS files
2. ✅ `simulations.html` imports `templates-base.css` and `templates-layout.css`
3. ✅ Page displays with full styling in browser
4. ✅ No console errors related to CSS
5. ✅ Visual appearance matches `templates.html` base layout

## Follow-up Actions

**None required** - This is a complete fix.

**Future Prevention**:
- Consider adding E2E test that verifies CSS is loaded (check computed styles)
- Document CSS import order requirements in `CLAUDE.md`

## References

- **Archived Design**: `openspec/changes/archive/2025-10-30-enhance-batch-simulation-monitoring/design.md`
- **CSS Architecture**: Section "关注点分离原则" in `CLAUDE.md`
- **Working Example**: `frontend/control/templates.html` (lines 12-18)
- **Variables Definition**: `frontend/control/css/variables.css`
