# Phase 2B.2 Analysis Page Features - Readiness Assessment

**Date**: 2025-11-16
**Status**: 🟡 Partially Ready
**Current Stage**: Ready to Begin Implementation

---

## Executive Summary

The analysis_viewer.html already has a **comparison tab** structure in place, but it **lacks the JavaScript implementation** for multi-case selection, data aggregation, and comparison rendering.

### Current State
✅ HTML structure - READY (tabs, containers exist)
⏳ Case selector UI - NEEDS IMPLEMENTATION
⏳ Case selector JS - NEEDS IMPLEMENTATION
⏳ API data loading - PARTIAL (framework exists)
⏳ Comparison rendering - PARTIAL (functions exist, need calls)
⏳ URL parameter support - PARTIAL
⏳ Case switcher - NOT IMPLEMENTED
⏳ Return navigation - BASIC SUPPORT
⏳ Error handling - NEEDS IMPLEMENTATION

---

## Task Breakdown - Phase 2B.2

### Task 2.1: Comparison Tab HTML
**Status**: ✅ COMPLETE
**Location**: analysis_viewer.html:279-294

Structure exists for comparison, but case selector modal not yet added.

### Task 2.2: Case Selector - HTML & CSS
**Status**: ⏳ NEEDS IMPLEMENTATION
**Priority**: HIGH
**Estimated**: 2 hours

Create modal/panel for multi-case selection with:
- Case list with checkboxes
- Confirm/Cancel buttons
- Selected count display
- Responsive design

### Task 2.3: Case Selector - JavaScript
**Status**: ⏳ NEEDS IMPLEMENTATION
**Priority**: HIGH
**Estimated**: 1.5 hours

Implement functions:
- `openCaseSelector()` - Fetch and display available cases
- `selectCase(caseId)` - Toggle checkbox
- `confirmCaseSelection()` - Validate and proceed
- `closeCaseSelector()` - Close modal

### Task 2.4: Comparison Data API & Processing
**Status**: ⏳ NEEDS IMPLEMENTATION
**Priority**: HIGH
**Estimated**: 2.5 hours

Implement:
- `loadComparisonData(caseIds)` - Fetch data for selected cases
- Data merging/normalization logic
- Handle both API response and fallback client-side merge
- Calculate improvement percentages

### Task 2.5: Comparison Table Rendering
**Status**: ⏳ PARTIAL (framework exists)
**Priority**: HIGH
**Estimated**: 2 hours

Complete rendering with:
- Multi-case columns
- Color coding (green for improvement, red for deterioration)
- Percentage changes
- Ranking badges
- Mobile-friendly scrolling

### Task 2.6: URL Parameter Support
**Status**: ⏳ PARTIAL
**Priority**: MEDIUM
**Estimated**: 1.5 hours

Add support for:
- `?case_ids=case1,case2,case3` - Multi-case comparison
- Update URL when selection changes
- Parse multi-case parameters on page load

### Task 2.7: Case Quick Switcher
**Status**: ⏳ NOT IMPLEMENTED
**Priority**: LOW
**Estimated**: 1.5 hours

Add dropdown to switch between cases in current batch without re-selecting.

### Task 2.8: Return Navigation
**Status**: ⏳ BASIC SUPPORT
**Priority**: MEDIUM
**Estimated**: 1 hour

Enhance with:
- Proper referrer tracking
- State restoration using sessionStorage
- Smooth navigation back to case-simulation-center.html

### Task 2.9: Loading & Error Handling
**Status**: ⏳ NEEDS IMPLEMENTATION
**Priority**: MEDIUM
**Estimated**: 1.5 hours

Add:
- Loading spinner
- Error messages with retry
- Empty state messages
- Graceful degradation

---

## Recommended Implementation Order

1. **Task 2.2** - Case Selector HTML/CSS (foundation)
2. **Task 2.3** - Case Selector JS (interaction)
3. **Task 2.4** - Data API (core logic)
4. **Task 2.5** - Rendering (display results)
5. **Task 2.6** - URL Parameters (bookmarkability)
6. **Task 2.7** - Case Switcher (enhancement)
7. **Task 2.8** - Return Navigation (UX)
8. **Task 2.9** - Error Handling (polish)

---

## Files to Modify

| File | Type | Scope |
|------|------|-------|
| analysis_viewer.html | HTML/JS | Case selector modal + main logic |
| event-scenario-comparison.css | CSS | Modal, selector, switcher styles |
| event-scenario-comparison.js | JS | Enhance existing render functions |

---

## Key Implementation Notes

1. **API Strategy**:
   - Try new batch comparison endpoint first
   - Fall back to loading individual case analyses if needed
   - Merge data client-side

2. **Data Structure**:
   - Input: Array of case_ids
   - Process: Fetch each case's analysis
   - Output: Merged comparison table

3. **Performance**:
   - Cache results to avoid re-fetching
   - Use pagination if too many cases
   - Show loading state during fetch

4. **Mobile UX**:
   - Comparison table scrollable horizontally
   - Modal responsive on small screens
   - Touch-friendly buttons (44px+)

---

## Success Criteria

- [ ] Can select 2+ cases for comparison
- [ ] Comparison data loads without errors
- [ ] Comparison table displays correctly
- [ ] URL parameters work (single & multi-case)
- [ ] Case switcher functional
- [ ] Return navigation works
- [ ] Error handling graceful
- [ ] No console errors
- [ ] Mobile responsive

---

**Status**: Ready to Begin
**Total Estimated Time**: 12-15 hours
**Next Step**: Start with Task 2.2 (Case Selector UI)
