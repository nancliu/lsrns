# Phase 2B.2 Analysis Page - Revised Design

**Date**: 2025-11-16
**Status**: 🔄 Design Revised
**Key Change**: Analysis entry point moved to case-simulation-center.html

---

## 🔄 Design Changes

### Original Design (Discarded)
❌ Users select cases in analysis_viewer.html via modal
❌ Separate UI for multi-case selection in analysis page
❌ Case selector modal with checkboxes

### New Design (Approved)
✅ Case selection happens in case-simulation-center.html
✅ Analysis page receives pre-selected cases via URL
✅ analysis_viewer.html focuses on display only
✅ Simpler, cleaner separation of concerns

---

## 📊 New Data Flow

```
case-simulation-center.html (Case Selection)
│
├─ Monitoring panel shows simulations
├─ User selects cases via checkboxes
├─ User clicks "📊 查看分析" button
│
└─→ analysis_viewer.html?case_ids=case1,case2,case3 (Display)
    │
    ├─ Load comparison data
    ├─ Display comparison analysis
    ├─ Show strategy rankings
    └─ Allow switching between cases
```

---

## 🎯 Revised Task List for Phase 2B.2

### Task 2.1: Multi-Select in Monitoring Panel
**Priority**: HIGH
**Estimated**: 2 hours
**Location**: case-simulation-center.html

Add checkboxes to monitoring table rows:
- Select individual simulations for analysis
- "View Analysis" button for single or multiple
- Track selected case IDs

**Current state**:
- Single case view exists via case_id parameter
- Monitoring table shows simulations
- Need to add multi-select capability

### Task 2.2: "View Analysis" Multi-Case Button
**Priority**: HIGH
**Estimated**: 1.5 hours
**Location**: case-simulation-center.html

Enhance "查看分析" button:
- Single case: Direct navigation to analysis_viewer
- Multiple cases: Navigate with multi-case URL
- Build URL: `analysis_viewer.html?case_ids=case1,case2`

```javascript
function viewAnalysis() {
  const selectedCases = getSelectedCases(); // From checkboxes
  if (selectedCases.length === 0) {
    alert('请选择至少 1 个案例');
    return;
  }

  if (selectedCases.length === 1) {
    // Single case - direct navigation
    window.location.href = `analysis_viewer.html?case_id=${selectedCases[0]}`;
  } else {
    // Multi-case comparison
    const caseIds = selectedCases.join(',');
    window.location.href = `analysis_viewer.html?case_ids=${caseIds}`;
  }
}
```

### Task 2.3: Parse Multi-Case URL Parameters
**Priority**: HIGH
**Estimated**: 1 hour
**Location**: analysis_viewer.html

Parse and handle URL parameters:
- Single case: `?case_id=xxx`
- Multi-case: `?case_ids=xxx,yyy,zzz`
- Store in state for rendering

```javascript
function parseAnalysisParams() {
  const params = new URLSearchParams(window.location.search);

  if (params.has('case_ids')) {
    // Multi-case comparison
    return params.get('case_ids').split(',');
  } else if (params.has('case_id')) {
    // Single case
    return [params.get('case_id')];
  }

  return [];
}
```

### Task 2.4: Load Comparison Data
**Priority**: HIGH
**Estimated**: 2 hours
**Location**: analysis_viewer.html

Load analysis for selected cases:
- Fetch individual case analyses
- Merge into comparison format
- Handle errors gracefully

```javascript
async function loadComparisonData(caseIds) {
  const analyses = [];

  for (const caseId of caseIds) {
    try {
      const response = await api.request(`/analysis/results/${caseId}`);
      analyses.push(response.data);
    } catch (error) {
      console.warn(`Failed to load ${caseId}:`, error);
    }
  }

  return mergeAnalyses(analyses);
}
```

### Task 2.5: Comparison Table Rendering
**Priority**: HIGH
**Estimated**: 2 hours
**Location**: analysis_viewer.html

Render comparison table with:
- Case columns (1 column per selected case)
- Metric rows (avg speed, completion %, etc.)
- Improvement indicators (color coding)
- Rankings

**Visual Example**:
```
| Metric          | Case 1 | Case 2 | Case 3 | Best  |
|-----------------|--------|--------|--------|-------|
| Avg Speed       | 45 kmh | 52 kmh | 48 kmh | Case2 |
| Completion %    | 89%    | 95%    | 92%    | Case2 |
| Trip Time       | 12 min | 10 min | 11 min | Case2 |
```

### Task 2.6: Display Control (Single vs Multi)
**Priority**: MEDIUM
**Estimated**: 1 hour
**Location**: analysis_viewer.html

Show different content based on case count:
- 1 case: Show full detailed analysis (summary, edgedata, details tabs)
- 2+ cases: Show comparison tab by default
- Allow tab switching between views

### Task 2.7: Case Quick Switcher
**Priority**: MEDIUM
**Estimated**: 1.5 hours
**Location**: analysis_viewer.html

Dropdown to switch between selected cases:
- List all passed cases
- Quick view of individual case metrics
- Switch without returning to case manager

### Task 2.8: Return Navigation
**Priority**: MEDIUM
**Estimated**: 1 hour
**Location**: analysis_viewer.html

Enhance return button:
- Navigate back to case-simulation-center.html
- Restore previous selections if possible
- Use sessionStorage for state preservation

### Task 2.9: Error Handling & Loading States
**Priority**: MEDIUM
**Estimated**: 1.5 hours
**Location**: analysis_viewer.html

Add:
- Loading spinner during data fetch
- Error messages with actionable info
- Empty states for missing data
- Graceful degradation

---

## 📝 Implementation Order

1. **Task 2.1** - Multi-select in monitoring panel
2. **Task 2.2** - Multi-case view analysis button
3. **Task 2.3** - Parse URL parameters
4. **Task 2.4** - Load comparison data
5. **Task 2.5** - Render comparison table
6. **Task 2.6** - Display control logic
7. **Task 2.7** - Case switcher
8. **Task 2.8** - Return navigation
9. **Task 2.9** - Error handling

---

## 📂 Files to Modify

| File | Tasks | Changes |
|------|-------|---------|
| case-simulation-center.html | 2.1, 2.2 | Add checkboxes to monitoring table, enhance view analysis button |
| analysis_viewer.html | 2.3-2.9 | Parse params, load data, render comparison, case switcher |
| event-scenario-comparison.css | 2.5-2.7 | Comparison table styles, case switcher dropdown |

---

## ✨ Key Differences from Original Design

| Aspect | Original | Revised |
|--------|----------|---------|
| **Case Selection** | In analysis page (modal) | In case manager (checkboxes) |
| **Entry Point** | "Select Cases" button | "View Analysis" button |
| **URL Parameter** | ?case_ids=... on entry | ?case_ids=... passed from case manager |
| **Case Selector UI** | Modal in analysis page | Checkboxes in monitoring table |
| **Analysis Focus** | Multi-case comparison | Display pre-selected comparison |

---

## 🎯 Benefits of Revised Design

1. **Cleaner separation**: Case selection ↔ Analysis display
2. **Better UX**: User stays in familiar case manager for selection
3. **Simpler analysis page**: No modal management
4. **Faster implementation**: Less UI code in analysis page
5. **Consistent patterns**: Matches existing UI patterns

---

## 📋 Estimated Total Time

- Task 2.1: 2h (multi-select in monitoring)
- Task 2.2: 1.5h (view analysis button)
- Task 2.3: 1h (URL parsing)
- Task 2.4: 2h (load data)
- Task 2.5: 2h (render table)
- Task 2.6: 1h (display control)
- Task 2.7: 1.5h (case switcher)
- Task 2.8: 1h (return navigation)
- Task 2.9: 1.5h (error handling)

**Total**: ~14 hours (slightly less than original estimate)

---

## ✅ Success Criteria

- [ ] Can select cases in monitoring panel
- [ ] "View Analysis" button appears for selected cases
- [ ] Single case analysis works (existing functionality)
- [ ] Multi-case URL properly formatted
- [ ] Comparison analysis loads without errors
- [ ] Comparison table displays correctly
- [ ] Case switcher functional
- [ ] Return button works
- [ ] Error messages clear and helpful
- [ ] No console errors
- [ ] Mobile responsive

---

**Status**: Ready for implementation using revised design
**Next Step**: Start with Task 2.1 (multi-select in monitoring panel)
