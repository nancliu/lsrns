# Tasks: Fix Simulations Page CSS Import

**Change ID**: fix-simulations-page-css-import

## Task List

### 1. Add Missing CSS Imports to simulations.html ✅ COMPLETED
**Priority**: P0
**Estimated Time**: 2 minutes
**Dependencies**: None

**Description**:
Add the three missing CSS file imports to `frontend/control/simulations.html` in the correct order.

**Steps**:
1. ✅ Open `frontend/control/simulations.html`
2. ✅ Locate line 11: `<link rel="stylesheet" href="css/simulations.css">`
3. ✅ Add three lines BEFORE line 11:
   ```html
   <link rel="stylesheet" href="css/variables.css">
   <link rel="stylesheet" href="css/templates-base.css">
   <link rel="stylesheet" href="css/templates-layout.css">
   ```
4. ✅ Final result should be:
   ```html
   <link rel="stylesheet" href="css/variables.css">
   <link rel="stylesheet" href="css/templates-base.css">
   <link rel="stylesheet" href="css/templates-layout.css">
   <link rel="stylesheet" href="css/simulations.css">
   ```

**Validation**:
- ✅ All 4 CSS files imported in correct order
- ✅ `variables.css` is first (other files depend on it)
- ✅ No syntax errors in HTML

**Result**: Successfully added 3 CSS imports to `frontend/control/simulations.html` at lines 11-13.

---

### 2. Manual Testing - Visual Verification
**Priority**: P0
**Estimated Time**: 5 minutes
**Dependencies**: Task 1

**Description**:
Verify the page displays correctly with full styling.

**Steps**:
1. Start API server: `.\start_api.ps1`
2. Open browser: `http://localhost:8000/control/simulations.html`
3. Verify visual elements:
   - Top bar: Gradient purple-blue background with white text
   - Sidebar: Dark background (#2c3e50) with navigation links
   - Content area: Light background (#f5f7fa) with proper padding
   - Buttons: Primary (blue), Secondary (gray) with proper styling
   - Config sections: White cards with shadows
   - Form inputs: Borders, padding, proper spacing
   - View tabs: Styled with hover and active states
   - All text: Proper fonts and colors
4. Check browser console (F12): No CSS-related errors

**Validation**:
- ✅ Page looks identical to `templates.html` in terms of base layout
- ✅ No console errors
- ✅ All colors display correctly (not transparent/missing)

---

### 3. Cross-Browser Testing
**Priority**: P1
**Estimated Time**: 3 minutes
**Dependencies**: Task 2

**Description**:
Verify styling works across different browsers.

**Steps**:
1. Test in Chrome/Edge (primary browser)
2. Test in Firefox (if available)
3. Test in Safari (if available)
4. Verify CSS variables are supported (all modern browsers)

**Validation**:
- ✅ Styling consistent across all tested browsers
- ✅ No browser-specific CSS issues

---

### 4. Update Documentation (Optional)
**Priority**: P2
**Estimated Time**: 5 minutes
**Dependencies**: Task 1

**Description**:
Document CSS import requirements to prevent future issues.

**Steps**:
1. Open `CLAUDE.md`
2. Locate "Frontend Development Standards" section
3. Add note under "CSS 文件" subsection:
   ```markdown
   **CSS Import Order Requirements**:
   - All HTML pages MUST import `variables.css` first (defines CSS custom properties)
   - Then import base styles: `templates-base.css` (reset, common elements)
   - Then import layout: `templates-layout.css` (top-bar, sidebar, containers)
   - Finally import page-specific styles
   - Example order: variables.css → templates-base.css → templates-layout.css → page-specific.css
   ```

**Validation**:
- ✅ Documentation updated
- ✅ Clear guidance provided for future HTML pages

---

## Summary

**Total Tasks**: 4 (3 required, 1 optional)
**Total Estimated Time**: 15 minutes
**Critical Path**: Tasks 1 → 2 → 3

**Status**: Implementation Complete ✅

**Completed**:
- ✅ Task 1: CSS imports added to simulations.html
- ⏳ Task 2: Manual testing (requires user to start server and verify)
- ⏳ Task 3: Cross-browser testing (requires user verification)
- ⏳ Task 4: Documentation update (optional)

**Next Steps for User**:
1. Start API server: `.\start_api.ps1`
2. Open browser: `http://localhost:8000/control/simulations.html`
3. Verify the page now displays with full styling (colors, layout, buttons)
4. Check browser console for any errors (should be none)

**Completion Criteria**:
- ✅ Task 1 completed - CSS imports added
- ⏳ User verification needed - Page displays with full styling
- ⏳ User verification needed - No console errors
- ⏳ User verification needed - Verified in at least one browser
