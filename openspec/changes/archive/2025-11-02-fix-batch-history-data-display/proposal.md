# Proposal: Fix Batch History Data Display

**Change ID**: `fix-batch-history-data-display`

**Status**: Proposed

**Priority**: High (P0 - Blocking user functionality)

**Created**: 2025-11-02

---

## Executive Summary

Batch simulation history and results are not visible to users after simulation completion. Only currently running batches can be monitored. This is caused by two critical integration defects:

1. **Frontend**: Missing `currentCaseId` global variable prevents batch history from loading
2. **Backend**: Batch status update method exists but is never called, causing all batches to remain in "pending" state

**Impact**: Users cannot view completed batch results, cannot distinguish batch states, and batch history functionality is completely unusable.

---

## Why

Batch history visibility is critical for production operations and analysis workflow. Users need to:

1. **Review completed batches** - Analyze performance trends, identify optimal parameter combinations, and learn from previous simulation runs
2. **Distinguish batch states** - Understand which batches are pending, running, or completed to manage system resources
3. **Access historical results** - View and compare results from past simulations without re-running expensive computations
4. **Audit simulation activity** - Track when batches were created, started, and completed for debugging and compliance

**Current Impact**: Without batch history functionality, users must:
- Keep browser tabs open during entire simulation runs (hours/days)
- Manually track batch IDs in external documents
- Re-run simulations to view results that were already computed
- Cannot distinguish between batches or filter by status

This creates severe workflow disruptions and wastes computational resources.

---

## Problem Statement

### Current Symptoms

Users report that after batch simulation completes:
- ❌ Progress view shows no data for completed batches
- ❌ Results view shows no data
- ❌ Batch history tab shows "No batch history available"
- ✅ Only currently running batches are visible

### Root Causes (Diagnosed)

#### Issue 1: Frontend `currentCaseId` Variable Missing

**Location**: `frontend/control/js/batch_simulation.js:36`

**Problem**:
```javascript
// Global state (line 36)
let currentBatchId = null;
let progressPollInterval = null;
let currentView = 'config';
// ❌ MISSING: let currentCaseId = null;
```

**Impact Chain**:
```
User clicks "Batch History" tab
  ↓
switchView('history') called
  ↓
Condition: if (view === 'history' && currentCaseId) ← currentCaseId is undefined
  ↓
loadBatchHistory() NOT called
  ↓
Empty state displayed: "No batch history available"
```

**Evidence**:
- Backend `batches_index.json` contains 13 batch records
- Frontend completely unable to load this data
- API endpoint `/api/v1/control/batch-optimization/batches` works correctly when called manually

#### Issue 2: Batch Status Never Updated to Index

**Location**: `api/services/batch_optimization_service.py:1375-1398`

**Problem**:
- Method `_update_batches_index_on_status_change()` is defined but **never called**
- No invocation when batch starts (status: pending → running)
- No invocation when batch completes (status: running → completed)

**Evidence** (from `batches_index.json`):
```json
{
  "batch_id": "batch_20251030_170601",
  "status": "pending",  // ❌ Should be "completed"
  "created_at": "2025-10-30T17:06:01",
  "completed_at": null  // ❌ Should have timestamp
}
```

**Impact**:
- All 13 batches show "pending" status
- Cannot distinguish completed/running/failed batches
- Status filters in batch history are useless
- User experience: all batches appear to be "waiting to run"

---

## Proposed Solution

### Capability 1: Frontend Case ID State Management

**Scope**: Add and initialize `currentCaseId` variable throughout batch simulation workflow

**Changes**:
1. Add `currentCaseId` to global state
2. Update `currentCaseId` when user selects a case
3. Save `currentCaseId` when batch is created
4. Restore `currentCaseId` from URL parameters or localStorage on page load
5. Pass `currentCaseId` to batch history API calls

### Capability 2: Backend Batch Status Synchronization

**Scope**: Ensure batch status updates are propagated to `batches_index.json`

**Changes**:
1. Call `_update_batches_index_on_status_change()` when batch starts (pending → running)
2. Call `_update_batches_index_on_status_change()` when batch completes (running → completed)
3. Add completion callback to `BatchSimulationScheduler`
4. Calculate and save success_rate when batch completes

### Capability 3: Historical Batch Status Repair (Optional)

**Scope**: One-time script to fix status of existing 13 batches

**Changes**:
1. Scan all batch directories for actual status
2. Read `batch_metadata.json` for each batch
3. Update `batches_index.json` with correct status
4. Preserve all other metadata fields

---

## Benefits

**User Experience**:
- ✅ Users can view all historical batches in batch history tab
- ✅ Completed batches show correct status (✓ Completed, not ⏸ Pending)
- ✅ Status filters work correctly (filter by completed/running/cancelled)
- ✅ Users can click completed batches to view results
- ✅ Complete workflow: configure → monitor → view results → manage history

**System Reliability**:
- ✅ Index file stays synchronized with actual batch state
- ✅ No stale or misleading status information
- ✅ Batch history provides accurate operational visibility

---

## Scope

### In Scope

**Frontend**:
- `frontend/control/js/batch_simulation.js` - Add `currentCaseId` variable and initialization logic

**Backend**:
- `api/services/batch_optimization_service.py` - Call status update method at appropriate lifecycle points
- `shared/control_tools/batch_simulation_scheduler.py` - Add completion callback

**Optional**:
- One-time repair script for existing 13 batches

### Out of Scope

- Batch result visualization improvements (already working if batch is correctly loaded)
- Performance optimizations (not blocking users)
- New features or enhancements

---

## Success Criteria

### Functional Acceptance

**AC1: Batch History Loads Historical Batches**
- [ ] Open batch simulation page
- [ ] Select a case
- [ ] Switch to "Batch History" tab
- [ ] **Expected**: See list of all historical batches (13 batches)
- [ ] **Actual**: ✅ List displays correctly

**AC2: Batch Status Displays Correctly**
- [ ] View batch cards in batch history
- [ ] **Expected**: Completed batches show "Completed ✓", running show "Running ⏳"
- [ ] **Actual**: ✅ Status icons and text are correct

**AC3: Batch Status Updates in Real-Time**
- [ ] Create and start new batch
- [ ] Check `batches_index.json`
- [ ] **Expected**: Status is "running"
- [ ] Wait for batch completion
- [ ] Check `batches_index.json` again
- [ ] **Expected**: Status is "completed" with completion timestamp and success_rate
- [ ] **Actual**: ✅ Status correctly updated

**AC4: View Completed Batch Results**
- [ ] Click completed batch in batch history
- [ ] **Expected**: Switch to Results tab, display comparison table and peak curve
- [ ] **Actual**: ✅ Results display correctly

### Technical Acceptance

**TA1: Frontend Variable Initialization**
```javascript
// Console check
console.log(currentCaseId);  // Should output "case_20251028_091831" etc.
```

**TA2: Backend Status Update Calls**
- [ ] Batch start triggers status update to "running"
- [ ] Batch completion triggers status update to "completed"
- [ ] `batches_index.json` synchronized with `batch_metadata.json`

**TA3: Historical Batch Repair (if script executed)**
- [ ] All 13 existing batches have correct status
- [ ] No data loss or corruption

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| `currentCaseId` initialization fails | Low | Medium | Add default fallback logic (select first case) |
| Concurrent batch status updates conflict | Low | Low | Use file locking or atomic writes |
| Historical repair script corrupts data | Low | High | **Backup `batches_index.json` before repair** |
| Frontend/backend version mismatch | Medium | Medium | Deploy both simultaneously, ensure API compatibility |

---

## Implementation Phases

### Phase 1: Frontend Fix (1-2 hours)

**Tasks**:
- Add `currentCaseId` global variable
- Update in `onCaseChange()`
- Save in `createBatch()` success handler
- Restore from URL/localStorage in `DOMContentLoaded`

**Validation**: Console log shows correct case_id, batch history tab loads data

### Phase 2: Backend Fix (2-3 hours)

**Tasks**:
- Call `_update_batches_index_on_status_change()` in `start_batch()`
- Add `_on_batch_completed()` callback in `BatchSimulationScheduler`
- Call status update method when batch completes
- Calculate success_rate on completion

**Validation**: New batches show correct status transitions (pending → running → completed)

### Phase 3: Historical Repair (1 hour, optional)

**Tasks**:
- Write `fix_batch_status.py` script
- Backup `batches_index.json`
- Scan batch directories and update index
- Verify no data corruption

**Validation**: All 13 historical batches show correct status

---

## Time Estimate

| Phase | Development | Testing | Total |
|-------|------------|---------|-------|
| Phase 1: Frontend | 1-2h | 0.5h | 1.5-2.5h |
| Phase 2: Backend | 2-3h | 1h | 3-4h |
| Phase 3: Repair (optional) | 1h | 0.5h | 1.5h |
| **Total** | **4-6h** | **2h** | **6-8h** |

---

## Dependencies

### Prerequisites
- ✅ All batch-optimization APIs already implemented
- ✅ Frontend batch history UI already exists
- ✅ Backend status update method already defined

### Blocking Issues
- None

### Related Changes
- Built on top of archived changes:
  - `implement-plan-management-and-batch-optimization`
  - `enhance-batch-simulation-monitoring`
  - `fix-batch-simulation-chart-issues`

---

## References

- **Diagnostic Report**: Analysis identifying the two root causes
- **Existing Implementation**:
  - `api/services/batch_optimization_service.py:1375-1398` - Status update method
  - `frontend/control/js/batch_simulation.js:1131-1200` - Batch history UI
- **Archived Changes**:
  - `openspec/changes/archive/2025-10-29-implement-plan-management-and-batch-optimization/`
  - `openspec/changes/archive/2025-10-30-enhance-batch-simulation-monitoring/`

---

## Approval

**Stakeholders**: Development Team, QA Team

**Approval Required**: Yes (impacts user-facing functionality)

**Approval Status**: Pending Review
