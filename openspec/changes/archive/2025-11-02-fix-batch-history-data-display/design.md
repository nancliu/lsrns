# Design Document: Fix Batch History Data Display

**Change ID**: `fix-batch-history-data-display`

**Version**: 1.0

**Date**: 2025-11-02

---

## 1. Architecture Overview

### 1.1 Problem Context

This change fixes a **frontend-backend integration defect** where completed batch simulation data cannot be viewed by users.

**Current State**:
```
User → Batch History Tab
         ↓
    if (currentCaseId)  ← undefined!
         ↓
    Empty State: "No batch history available"

Backend: batches_index.json
         ↓
    13 batches, all status="pending"  ← Never updated!
```

**Desired State**:
```
User → Batch History Tab
         ↓
    currentCaseId = "case_001"  ← Properly initialized
         ↓
    API: GET /batches?case_id=case_001
         ↓
    Display 13 batches with correct status

Backend: batches_index.json
         ↓
    Status synchronized: pending → running → completed
```

### 1.2 System Components

```
┌─────────────────────────────────────────────────┐
│           Frontend (batch_simulation.js)        │
│                                                  │
│  Global State:                                  │
│  - currentBatchId                               │
│  - currentCaseId  ← FIX: Add this variable     │
│  - currentView                                  │
│                                                  │
│  Functions:                                     │
│  - onCaseChange()     ← FIX: Update case_id    │
│  - createBatch()      ← FIX: Save case_id      │
│  - loadBatchHistory() ← Uses case_id in API    │
│  - switchView()       ← Checks case_id         │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/JSON
┌──────────────────┴──────────────────────────────┐
│      Backend (batch_optimization_service.py)    │
│                                                  │
│  Methods:                                       │
│  - start_batch()                                │
│    ↓ FIX: Call status update → "running"       │
│                                                  │
│  - _update_batches_index_on_status_change()     │
│    ← Already exists, just needs to be called    │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│    Scheduler (batch_simulation_scheduler.py)    │
│                                                  │
│  - start_batch()                                │
│  - _execute_tasks()                             │
│    ↓ FIX: Add completion callback               │
│  - _on_batch_completed()  ← NEW                 │
│    ↓ Call status update → "completed"           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│         File System (batches_index.json)        │
│                                                  │
│  Before Fix:                                    │
│  {                                              │
│    "batch_id": "batch_001",                     │
│    "status": "pending",  ← Never changes!       │
│    "completed_at": null                         │
│  }                                              │
│                                                  │
│  After Fix:                                     │
│  {                                              │
│    "batch_id": "batch_001",                     │
│    "status": "completed",  ← Updated!           │
│    "completed_at": "2025-11-02T10:30:00",       │
│    "success_rate": 1.0                          │
│  }                                              │
└─────────────────────────────────────────────────┘
```

---

## 2. Frontend Design

### 2.1 Global State Management

**Current State** (batch_simulation.js:36):
```javascript
// Global state
let currentBatchId = null;
let progressPollInterval = null;
let currentView = 'config';
let liveCurveVisible = true;
```

**After Fix**:
```javascript
// Global state
let currentBatchId = null;
let currentCaseId = null;  // ✅ NEW: Track selected case
let progressPollInterval = null;
let currentView = 'config';
let liveCurveVisible = true;
```

### 2.2 Case Selection Workflow

**Initialization Flow**:
```
Page Load (DOMContentLoaded)
    ↓
1. Try URL parameter: ?case_id=case_001
    ↓
2. If found: currentCaseId = urlParams.get('case_id')
    ↓
3. If not found: Load cases, user selects manually
    ↓
4. onCaseChange() triggered
    ↓
5. currentCaseId = caseSelector.value  ← Update variable
    ↓
6. Load plans for selected case
```

**Implementation**:
```javascript
// In DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', async () => {
    // Try to restore case_id from URL
    const urlParams = new URLSearchParams(window.location.search);
    const caseIdParam = urlParams.get('case_id');

    if (caseIdParam) {
        currentCaseId = caseIdParam;
        const caseSelector = document.getElementById('caseSelector');
        if (caseSelector) {
            caseSelector.value = caseIdParam;
        }
    }

    // Initialize UI
    await loadCases();
    // ... rest of initialization
});

// In onCaseChange()
async function onCaseChange() {
    const caseSelector = document.getElementById('caseSelector');
    currentCaseId = caseSelector.value;  // ✅ NEW: Save case_id

    // Clear plan list
    const planList = document.getElementById('planList');
    planList.innerHTML = '<p>加载中...</p>';

    // Reload plans for selected case
    await loadPlansForCase(currentCaseId);
}
```

### 2.3 Batch Creation Flow

**Before Fix**:
```javascript
const batch = await response.json();
currentBatchId = batch.batch_id;
// currentCaseId NOT saved ❌
```

**After Fix**:
```javascript
const batch = await response.json();
currentBatchId = batch.batch_id;
currentCaseId = caseId;  // ✅ NEW: Save case_id for later use

// Switch to progress view
switchView('progress');
```

### 2.4 Batch History Loading

**Before Fix** (always fails):
```javascript
function switchView(view) {
    // ...
    if (view === 'history' && currentCaseId) {  // ← currentCaseId is undefined!
        loadBatchHistory();
    }
}

async function loadBatchHistory() {
    if (!currentCaseId) {  // ← Always true (undefined)
        document.getElementById('batchHistoryEmpty').style.display = 'block';
        return;  // ← Early exit, no data loaded
    }
    // ... rest of function never executes
}
```

**After Fix** (works correctly):
```javascript
function switchView(view) {
    // ...
    if (view === 'history' && currentCaseId) {  // ← currentCaseId has value!
        loadBatchHistory();  // ← Function is called
    }
}

async function loadBatchHistory() {
    if (!currentCaseId) {
        document.getElementById('batchHistoryEmpty').style.display = 'block';
        return;
    }

    // API call now works
    const params = new URLSearchParams({
        case_id: currentCaseId,  // ← Has value!
        page: 1,
        limit: 100
    });

    const response = await fetch(`${API_BASE}/control/batch-optimization/batches?${params}`);
    // ... render batch history
}
```

---

## 3. Backend Design

### 3.1 Status Update Architecture

**Key Method** (already exists at line 1375-1398):
```python
def _update_batches_index_on_status_change(
    self,
    case_id: str,
    batch_id: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update batches_index.json when batch status changes

    This method is DEFINED but NEVER CALLED - FIX: Add invocations
    """
    plan_opti_dir = Path("cases") / case_id / "simulations" / "plan_opti"
    index_file = plan_opti_dir / "batches_index.json"

    # Load existing index
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"batches": [], "last_updated": datetime.now().isoformat()}

    # Find and update batch record
    for batch in index["batches"]:
        if batch["batch_id"] == batch_id:
            batch["status"] = status
            if metadata:
                batch["started_at"] = metadata.get("started_at")
                batch["completed_at"] = metadata.get("completed_at")
                batch["success_rate"] = metadata.get("success_rate", 0)
            break

    # Save updated index
    index["last_updated"] = datetime.now().isoformat()
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
```

### 3.2 Batch Start Status Update

**Location**: `api/services/batch_optimization_service.py:start_batch()`

**Current Code** (line ~133):
```python
async def start_batch(self, case_id: str, batch_id: str) -> Dict[str, Any]:
    """Start batch simulation"""
    logger.info(f"Starting batch {batch_id}")

    # Load batch metadata
    batch_dir = self._get_batch_directory(case_id, batch_id)
    metadata_file = batch_dir / "batch_metadata.json"

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Update status to running
    metadata["status"] = "running"
    metadata["started_at"] = datetime.now().isoformat()

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # ❌ MISSING: Status update to index

    # Start async simulations
    asyncio.create_task(self._execute_batch_simulations(case_id, batch_id, metadata))

    return {"status": "running", "message": "批量仿真已启动"}
```

**After Fix**:
```python
async def start_batch(self, case_id: str, batch_id: str) -> Dict[str, Any]:
    """Start batch simulation"""
    logger.info(f"Starting batch {batch_id}")

    # Load batch metadata
    batch_dir = self._get_batch_directory(case_id, batch_id)
    metadata_file = batch_dir / "batch_metadata.json"

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Update status to running
    metadata["status"] = "running"
    metadata["started_at"] = datetime.now().isoformat()

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # ✅ NEW: Synchronize to index
    self._update_batches_index_on_status_change(
        case_id=case_id,
        batch_id=batch_id,
        status="running",
        metadata=metadata
    )

    # Start async simulations
    asyncio.create_task(self._execute_batch_simulations(case_id, batch_id, metadata))

    return {"status": "running", "message": "批量仿真已启动"}
```

### 3.3 Batch Completion Callback

**Location**: `shared/control_tools/batch_simulation_scheduler.py`

**New Method** (to be added):
```python
async def _on_batch_completed(self, case_id: str, batch_id: str) -> None:
    """
    Callback when batch completes

    Responsibilities:
    1. Update batch_metadata.json status to "completed"
    2. Calculate success_rate
    3. Call BatchOptimizationService to update index
    """
    logger.info(f"Batch {batch_id} completed")

    # Load batch metadata
    batch_dir = Path("cases") / case_id / "simulations" / "plan_opti" / batch_id
    metadata_file = batch_dir / "batch_metadata.json"

    if not metadata_file.exists():
        logger.error(f"Metadata not found for batch {batch_id}")
        return

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Update status and calculate success rate
    metadata["status"] = "completed"
    metadata["completed_at"] = datetime.now().isoformat()

    total_tasks = len(self.tasks)
    completed_tasks = sum(1 for t in self.tasks if t.status == "completed")
    metadata["success_rate"] = completed_tasks / total_tasks if total_tasks > 0 else 0

    # Save updated metadata
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # Update index (call service method)
    from api.services.batch_optimization_service import BatchOptimizationService
    service = BatchOptimizationService()
    service._update_batches_index_on_status_change(
        case_id=case_id,
        batch_id=batch_id,
        status="completed",
        metadata=metadata
    )

    logger.info(f"Batch {batch_id} completed with success rate {metadata['success_rate']:.2%}")
```

**Integration Point** (in `start_batch()` method):
```python
async def start_batch(self, case_id: str, batch_id: str) -> None:
    """Start batch simulation execution"""
    # ... existing setup code ...

    # Execute all tasks
    await asyncio.gather(*task_futures)

    # ✅ NEW: Call completion callback
    await self._on_batch_completed(case_id, batch_id)
```

---

## 4. Data Flow

### 4.1 Batch Lifecycle State Transitions

```
User creates batch
    ↓
batch_metadata.json: status="pending"
batches_index.json: status="pending"  ← Created at batch creation
    ↓
User starts batch
    ↓
start_batch() called
    ↓
batch_metadata.json: status="running", started_at=timestamp
    ↓ ✅ NEW CALL
_update_batches_index_on_status_change(status="running")
    ↓
batches_index.json: status="running", started_at=timestamp
    ↓
All tasks complete
    ↓
_on_batch_completed() callback
    ↓
batch_metadata.json: status="completed", completed_at=timestamp, success_rate=1.0
    ↓ ✅ NEW CALL
_update_batches_index_on_status_change(status="completed")
    ↓
batches_index.json: status="completed", completed_at=timestamp, success_rate=1.0
```

### 4.2 Index Synchronization Pattern

```
┌─────────────────────────────────────┐
│  Source of Truth:                   │
│  batch_metadata.json (per batch)    │
└──────────────┬──────────────────────┘
               │ Synchronize on status change
               ↓
┌──────────────────────────────────────┐
│  Index File:                         │
│  batches_index.json (aggregate)      │
│                                      │
│  - Fast query without scanning dirs  │
│  - Contains summary fields only      │
│  - Updated atomically                │
└──────────────────────────────────────┘
```

---

## 5. Historical Data Repair

### 5.1 Repair Script Design

**Purpose**: One-time fix for existing 13 batches with incorrect "pending" status

**Script**: `fix_batch_status.py`

```python
"""
One-time script to repair historical batch status in batches_index.json

Usage:
    python fix_batch_status.py case_20251028_091831

Safety:
    - Backs up batches_index.json before modification
    - Reads status from source of truth (batch_metadata.json)
    - No data creation or deletion
"""

import json
from pathlib import Path
from datetime import datetime
import shutil

def fix_historical_batches(case_id: str):
    """Repair batch status for a case"""
    plan_opti_dir = Path("cases") / case_id / "simulations" / "plan_opti"
    index_file = plan_opti_dir / "batches_index.json"

    if not index_file.exists():
        print(f"❌ Index file not found: {index_file}")
        return

    # Backup original file
    backup_file = index_file.with_suffix('.json.backup')
    shutil.copy2(index_file, backup_file)
    print(f"✅ Backup created: {backup_file}")

    # Load index
    with open(index_file, "r", encoding="utf-8") as f:
        index = json.load(f)

    print(f"\n📋 Processing {len(index['batches'])} batches...")

    fixed_count = 0
    for batch_summary in index["batches"]:
        batch_id = batch_summary["batch_id"]
        batch_dir = plan_opti_dir / batch_id
        metadata_file = batch_dir / "batch_metadata.json"

        if not metadata_file.exists():
            print(f"⚠️  Skipping {batch_id}: metadata not found")
            continue

        # Read source of truth
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Update index from metadata
        old_status = batch_summary.get("status", "unknown")
        new_status = metadata.get("status", "pending")

        if old_status != new_status:
            batch_summary["status"] = new_status
            batch_summary["started_at"] = metadata.get("started_at")
            batch_summary["completed_at"] = metadata.get("completed_at")
            batch_summary["success_rate"] = metadata.get("success_rate", 0)
            fixed_count += 1
            print(f"✅ Fixed {batch_id}: {old_status} → {new_status}")
        else:
            print(f"ℹ️  {batch_id}: status already correct ({new_status})")

    # Save updated index
    index["last_updated"] = datetime.now().isoformat()
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Repair complete: {fixed_count} batches updated")
    print(f"📁 Original backed up to: {backup_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fix_batch_status.py <case_id>")
        sys.exit(1)

    case_id = sys.argv[1]
    fix_historical_batches(case_id)
```

### 5.2 Repair Execution Plan

1. **Pre-execution**:
   - Backup `batches_index.json`
   - Verify all `batch_metadata.json` files are readable
   - Log batch IDs to be processed

2. **Execution**:
   - For each batch in index:
     - Read `batch_metadata.json` (source of truth)
     - Compare status with index
     - Update index if different
     - Log changes

3. **Post-execution**:
   - Verify index file is valid JSON
   - Check all batches have status
   - Compare before/after statistics

4. **Rollback** (if needed):
   - Restore from `.json.backup` file
   - Investigate root cause before retry

---

## 6. Testing Strategy

### 6.1 Frontend Testing

**Unit Tests** (optional, manual verification sufficient):
- `currentCaseId` initialization from URL
- `currentCaseId` update on case selection
- `currentCaseId` saved on batch creation

**Manual Testing**:
```javascript
// Browser console
console.log(currentCaseId);  // Should output case ID

// Network tab
// Check API request includes case_id parameter:
// GET /api/v1/control/batch-optimization/batches?case_id=case_001&page=1&limit=100
```

### 6.2 Backend Testing

**Unit Tests**:
```python
def test_update_batches_index_on_status_change():
    """Test status update synchronization"""
    service = BatchOptimizationService()
    case_id = "test_case"
    batch_id = "test_batch_001"

    # Create test index
    # ... setup ...

    # Call update method
    service._update_batches_index_on_status_change(
        case_id=case_id,
        batch_id=batch_id,
        status="running",
        metadata={"started_at": "2025-11-02T10:00:00"}
    )

    # Verify index updated
    index = load_index(case_id)
    batch = find_batch(index, batch_id)
    assert batch["status"] == "running"
    assert batch["started_at"] == "2025-11-02T10:00:00"
```

**Integration Testing**:
1. Create new batch
2. Verify index shows "pending"
3. Start batch
4. Verify index shows "running" with started_at
5. Wait for completion
6. Verify index shows "completed" with completed_at and success_rate

### 6.3 E2E Testing

**Test Scenario**: Complete batch simulation workflow
```javascript
test('Batch history shows completed batches', async ({ page }) => {
    // 1. Open batch simulation page
    await page.goto('http://localhost:8000/control/simulations.html');

    // 2. Select case
    await page.selectOption('#caseSelector', 'case_20251028_091831');
    await page.waitForTimeout(500);

    // 3. Verify currentCaseId is set (via console)
    const caseId = await page.evaluate(() => currentCaseId);
    expect(caseId).toBeTruthy();

    // 4. Switch to batch history tab
    await page.click('text=批次历史');
    await page.waitForSelector('#batchHistoryList', { timeout: 5000 });

    // 5. Verify batch cards displayed
    const batchCards = await page.locator('.batch-card').count();
    expect(batchCards).toBeGreaterThan(0);
    console.log(`✅ Found ${batchCards} historical batches`);

    // 6. Verify at least one batch shows "completed" status
    const completedBatches = await page.locator('.batch-status:has-text("完成")').count();
    expect(completedBatches).toBeGreaterThan(0);
    console.log(`✅ ${completedBatches} batches show completed status`);
});
```

---

## 7. Risk Assessment

### 7.1 Technical Risks

| Risk | Mitigation |
|------|-----------|
| `currentCaseId` undefined on page refresh | Add localStorage persistence or URL parameter fallback |
| Race condition on index file writes | Use file locking or atomic writes with temp file + rename |
| Historical repair script corrupts data | **Mandatory backup before execution** |
| Circular import (scheduler → service) | Use lazy import: `from api.services import ...` inside method |

### 7.2 Operational Risks

| Risk | Mitigation |
|------|-----------|
| Users have browsers cached old JavaScript | Clear browser cache or add cache-busting query param to JS file |
| Batches mid-execution during deploy | Deploy during maintenance window or accept graceful degradation |
| Index file missing or corrupted | Add recovery logic: rebuild from scanning batch directories |

---

## 8. Performance Considerations

**No Performance Impact**:
- `currentCaseId` is a simple variable assignment (O(1))
- Status update writes ~100 bytes to index file (<1ms)
- Historical repair script runs once (not performance-critical)

**Actual Performance**:
- Index update: <5ms (JSON read + modify + write)
- Batch history load: <300ms (already optimized with index)

---

## 9. Security Considerations

**No Security Impact**:
- No new API endpoints
- No authentication changes
- No external data access
- File operations use existing security model

**Validation**:
- `case_id` already validated by existing API layer
- `batch_id` format validation already present
- No user input directly written to files

---

## 10. Deployment Plan

### 10.1 Deployment Steps

1. **Pre-deployment**:
   - Backup all `batches_index.json` files
   - Note current batch states for verification

2. **Deploy**:
   - Deploy backend changes first
   - Deploy frontend changes second
   - Restart API server

3. **Post-deployment**:
   - Verify no running batches were disrupted
   - Check one completed batch shows correct status
   - Run E2E smoke test

4. **Historical Repair** (optional):
   - Run `fix_batch_status.py` script
   - Verify batch history shows correct data

### 10.2 Rollback Plan

**If frontend issues**:
- Revert `batch_simulation.js` to previous version
- Clear browser caches

**If backend issues**:
- Revert service files
- Restore `batches_index.json` from backup
- Restart API server

---

## 11. Monitoring

**Post-deployment Checks**:
- ✅ Batch history tab loads without errors
- ✅ New batches show correct status transitions
- ✅ Completed batches clickable in history
- ✅ No JavaScript console errors related to `currentCaseId`

**Metrics to Monitor**:
- Batch history API call success rate
- Index file write errors (should be 0)
- User reports of "no data" (should decrease to 0)

---

## References

- **Diagnostic Report**: Root cause analysis document
- **Existing Specs**:
  - `openspec/specs/batch-management/spec.md`
  - `openspec/specs/batch-optimization/spec.md`
- **Archived Changes**:
  - `openspec/changes/archive/2025-10-29-implement-plan-management-and-batch-optimization/`
  - `openspec/changes/archive/2025-10-30-enhance-batch-simulation-monitoring/`
