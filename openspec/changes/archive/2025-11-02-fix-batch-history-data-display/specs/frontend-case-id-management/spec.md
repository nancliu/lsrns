# Spec: Frontend Case ID State Management

**Capability**: Frontend Case ID State Management

**Change ID**: `fix-batch-history-data-display`

**Status**: Proposed

---

## Overview

This capability fixes the missing `currentCaseId` global variable in the batch simulation frontend, enabling proper case context tracking throughout the batch simulation workflow. This is essential for loading batch history, which currently fails because `currentCaseId` is undefined.

---

## ADDED Requirements

### Requirement: Global Case ID Variable Declaration (REQ-FE-001)

The batch simulation module SHALL declare a global `currentCaseId` variable to track the currently selected case context.

**Priority**: P0 (Blocking)

**Location**: `frontend/control/js/batch_simulation.js:36`

**Implementation**:
```javascript
// Global state
let currentBatchId = null;
let progressPollInterval = null;
let currentView = 'config';
let currentCaseId = null;  // ← ADDED
```

#### Scenario: Page Load Without Case Context

**Given**: User navigates to batch simulation page directly (no URL parameters)

**When**: JavaScript initializes global state

**Then**:
- `currentCaseId` is declared and initialized to `null`
- No runtime errors (undefined variable)
- Batch history tab remains disabled until case is selected

---

### Requirement: Case Selection Handler Updates Case ID (REQ-FE-002)

The case selection handler MUST update `currentCaseId` whenever the user selects a case from the dropdown.

**Priority**: P0 (Blocking)

**Location**: `frontend/control/js/batch_simulation.js` (function `onCaseChange()` or equivalent)

**Implementation**:
```javascript
function onCaseChange(event) {
    const selectedCaseId = event.target.value;
    currentCaseId = selectedCaseId;  // ← ADDED

    // Existing logic: load case metadata, update UI, etc.
    loadCaseMetadata(selectedCaseId);
}
```

#### Scenario: User Selects Case from Dropdown

**Given**: User is on batch simulation page with case dropdown visible

**When**: User selects "case_20251028_091831" from dropdown

**Then**:
- `currentCaseId` is set to `"case_20251028_091831"`
- Console log shows: `console.log(currentCaseId)` → `"case_20251028_091831"`
- Batch history tab becomes enabled
- Clicking "Batch History" tab successfully loads historical batches

---

### Requirement: Persist Case ID After Batch Creation (REQ-FE-003)

The batch creation success handler SHALL save `currentCaseId` from the API response to maintain case context after batch is created.

**Priority**: P0 (Blocking)

**Location**: `frontend/control/js/batch_simulation.js` (function `createBatch()` success handler)

**Implementation**:
```javascript
async function createBatch(configData) {
    const response = await fetch('/api/v1/control/batch-optimization/batches', {
        method: 'POST',
        body: JSON.stringify(configData)
    });

    if (response.ok) {
        const result = await response.json();
        currentBatchId = result.batch_id;
        currentCaseId = result.case_id;  // ← ADDED (ensure backend returns case_id)

        switchView('progress');
        startProgressPolling();
    }
}
```

#### Scenario: Batch Creation Success

**Given**: User has configured batch parameters and clicked "Start Batch"

**When**: API returns `{"batch_id": "batch_20251102_143052", "case_id": "case_20251028_091831"}`

**Then**:
- `currentCaseId` is set to `"case_20251028_091831"`
- User can switch to "Batch History" tab without losing context
- `loadBatchHistory()` receives correct `case_id` parameter

---

### Requirement: Restore Case ID on Page Load (REQ-FE-004)

The page initialization logic SHALL restore `currentCaseId` from URL parameters or localStorage when the page loads to preserve case context across sessions.

**Priority**: P1 (High)

**Location**: `frontend/control/js/batch_simulation.js` (DOMContentLoaded event handler)

**Implementation**:
```javascript
document.addEventListener('DOMContentLoaded', () => {
    // Option 1: From URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const caseIdFromUrl = urlParams.get('case_id');
    if (caseIdFromUrl) {
        currentCaseId = caseIdFromUrl;
        // Pre-select case in dropdown
        document.getElementById('caseSelect').value = caseIdFromUrl;
        loadCaseMetadata(caseIdFromUrl);
    }

    // Option 2: From localStorage (fallback)
    if (!currentCaseId) {
        const savedCaseId = localStorage.getItem('lastSelectedCaseId');
        if (savedCaseId) {
            currentCaseId = savedCaseId;
            document.getElementById('caseSelect').value = savedCaseId;
        }
    }

    // Initialize UI based on currentCaseId state
    updateBatchHistoryTabState();
});
```

#### Scenario: Page Reload After Batch Creation

**Given**: User created a batch and page reloads (manual refresh or navigation)

**When**: Page loads with URL `?case_id=case_20251028_091831`

**Then**:
- `currentCaseId` is restored to `"case_20251028_091831"`
- Case dropdown pre-selects the correct case
- Batch history tab is enabled and functional
- No data loss or context reset

---

### Requirement: Pass Case ID to Batch History API (REQ-FE-005)

The batch history loading function MUST include `currentCaseId` as a query parameter when calling the batch history API endpoint.

**Priority**: P0 (Blocking)

**Location**: `frontend/control/js/batch_simulation.js` (function `loadBatchHistory()`)

**Implementation**:
```javascript
async function loadBatchHistory() {
    if (!currentCaseId) {
        console.warn('Cannot load batch history: currentCaseId is not set');
        displayEmptyBatchHistory('Please select a case first');
        return;
    }

    const response = await fetch(
        `/api/v1/control/batch-optimization/batches?case_id=${currentCaseId}`
    );

    if (response.ok) {
        const batches = await response.json();
        renderBatchHistoryList(batches);
    }
}
```

#### Scenario: Load Batch History Tab

**Given**: User has selected case "case_20251028_091831" and `currentCaseId` is set

**When**: User clicks "Batch History" tab

**Then**:
- API request is made to `/api/v1/control/batch-optimization/batches?case_id=case_20251028_091831`
- Backend returns list of 13 historical batches
- Batch cards are rendered with correct status icons (✓ Completed, ⏳ Running, ⏸ Pending)
- No "No batch history available" empty state

---

## Testing Requirements

### Unit Tests

- Test `currentCaseId` initialization to `null`
- Test `onCaseChange()` updates `currentCaseId`
- Test `createBatch()` persists `currentCaseId`
- Test `loadBatchHistory()` validation (fails gracefully if `currentCaseId` is `null`)

### E2E Tests

**Test File**: `tests/e2e/test_batch_history_case_id.spec.js`

```javascript
test('Batch history loads after case selection', async ({ page }) => {
  await page.goto('/simulations.html');

  // Select case
  await page.selectOption('#caseSelect', 'case_20251028_091831');

  // Switch to batch history tab
  await page.click('text=Batch History');

  // Verify API call includes case_id
  const apiRequest = await page.waitForRequest(request =>
    request.url().includes('/batches?case_id=case_20251028_091831')
  );

  expect(apiRequest).toBeTruthy();

  // Verify batch list renders
  await page.waitForSelector('.batch-card');
  const batchCount = await page.locator('.batch-card').count();
  expect(batchCount).toBeGreaterThan(0);
});
```

---

## Acceptance Criteria

- [ ] `currentCaseId` variable declared in global state
- [ ] Case selection updates `currentCaseId`
- [ ] Batch creation success handler saves `currentCaseId`
- [ ] Page reload restores `currentCaseId` from URL or localStorage
- [ ] `loadBatchHistory()` passes `currentCaseId` to API
- [ ] Console check: `console.log(currentCaseId)` outputs correct case ID after selection
- [ ] No "undefined variable" errors in browser console
- [ ] Batch history tab displays historical batches (not empty state)

---

## Dependencies

- **Backend API**: `/api/v1/control/batch-optimization/batches` must support `case_id` query parameter (already implemented ✅)
- **REQ-BE-001**: Backend status synchronization (for batch history to show correct status)

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| `currentCaseId` not initialized on some page entry paths | Medium | Medium | Add comprehensive page load checks and fallback logic |
| localStorage unavailable (privacy mode) | Low | Low | Use URL parameters as primary method, localStorage as fallback |
| Race condition between case selection and batch creation | Low | Low | Validate `currentCaseId` is set before allowing batch creation |

---

## Related Documents

- [Proposal: fix-batch-history-data-display](../../proposal.md)
- [Design Document](../../design.md)
- [Backend Status Synchronization Spec](../backend-status-synchronization/spec.md)
