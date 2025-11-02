# Spec: Backend Batch Status Synchronization

**Capability**: Backend Batch Status Synchronization

**Change ID**: `fix-batch-history-data-display`

**Status**: Proposed

---

## Overview

This capability ensures that batch status updates are properly propagated to `batches_index.json` by invoking the existing `_update_batches_index_on_status_change()` method at critical lifecycle points. Currently, this method exists but is never called, causing all batches to remain in "pending" status indefinitely.

---

## MODIFIED Requirements

### Requirement: Call Status Update on Batch Start (REQ-BE-001)

The `start_batch()` method MUST invoke `_update_batches_index_on_status_change()` to update the index file when a batch transitions from `pending` to `running` status.

**Priority**: P0 (Blocking)

**Location**: `api/services/batch_optimization_service.py` (method `start_batch()`)

**Current Code** (line ~260-280):
```python
async def start_batch(self, case_id: str, batch_id: str) -> Dict[str, Any]:
    """Start batch simulation execution"""
    # Update batch_metadata.json status to "running"
    batch_dir = self._get_batch_dir(case_id, batch_id)
    metadata_file = batch_dir / "batch_metadata.json"
    metadata = self._load_json(metadata_file)
    metadata['status'] = 'running'
    metadata['started_at'] = datetime.now().isoformat()
    self._save_json(metadata_file, metadata)

    # Schedule batch execution
    self.scheduler.schedule_batch(case_id, batch_id, plans)

    return {"status": "running", "message": "Batch started successfully"}
```

**Modified Code**:
```python
async def start_batch(self, case_id: str, batch_id: str) -> Dict[str, Any]:
    """Start batch simulation execution"""
    # Update batch_metadata.json status to "running"
    batch_dir = self._get_batch_dir(case_id, batch_id)
    metadata_file = batch_dir / "batch_metadata.json"
    metadata = self._load_json(metadata_file)
    metadata['status'] = 'running'
    metadata['started_at'] = datetime.now().isoformat()
    self._save_json(metadata_file, metadata)

    # ✅ ADDED: Update batches_index.json
    self._update_batches_index_on_status_change(
        case_id=case_id,
        batch_id=batch_id,
        status='running',
        metadata=metadata
    )

    # Schedule batch execution
    self.scheduler.schedule_batch(case_id, batch_id, plans)

    return {"status": "running", "message": "Batch started successfully"}
```

#### Scenario: Batch Start Triggers Index Update

**Given**: Batch `batch_20251102_150000` exists with status `pending` in both `batch_metadata.json` and `batches_index.json`

**When**: API call `POST /api/v1/control/batch-optimization/batches/{batch_id}/start`

**Then**:
- `batch_metadata.json` status updated to `"running"`
- `batches_index.json` status updated to `"running"`
- `batches_index.json` includes `started_at` timestamp
- Frontend batch history shows batch as "Running ⏳"

---

### Requirement: Add Batch Completion Callback (REQ-BE-002)

The service SHALL implement a `_on_batch_completed()` callback method that handles batch completion events, updates metadata with completion timestamp and success rate, and synchronizes the index file.

**Priority**: P0 (Blocking)

**Location**: `api/services/batch_optimization_service.py` (new method)

**Implementation**:
```python
async def _on_batch_completed(
    self, case_id: str, batch_id: str
) -> None:
    """Callback invoked when batch completes all simulations"""
    try:
        # Load batch metadata
        batch_dir = self._get_batch_dir(case_id, batch_id)
        metadata_file = batch_dir / "batch_metadata.json"
        metadata = self._load_json(metadata_file)

        # Calculate success_rate
        total_tasks = metadata.get('total_tasks', 0)
        completed_tasks = metadata.get('completed_tasks', 0)
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Update metadata
        metadata['status'] = 'completed'
        metadata['completed_at'] = datetime.now().isoformat()
        metadata['success_rate'] = round(success_rate, 2)
        self._save_json(metadata_file, metadata)

        # Update batches_index.json
        self._update_batches_index_on_status_change(
            case_id=case_id,
            batch_id=batch_id,
            status='completed',
            metadata=metadata
        )

        logger.info(
            f"Batch {batch_id} completed: {completed_tasks}/{total_tasks} tasks "
            f"({success_rate:.2f}% success rate)"
        )

    except Exception as e:
        logger.error(f"Error in batch completion callback: {e}")
```

#### Scenario: Batch Completes All Simulations

**Given**: Batch `batch_20251102_150000` is running with 10 simulation tasks

**When**: Last simulation task finishes (scheduler detects all tasks done)

**Then**:
- `_on_batch_completed()` is invoked
- `batch_metadata.json` status updated to `"completed"`
- `batch_metadata.json` includes `completed_at` timestamp and `success_rate`
- `batches_index.json` synchronized with new status and metadata
- Frontend batch history shows "Completed ✓" with success rate

---

### Requirement: Register Completion Callback in Scheduler (REQ-BE-003)

The `BatchSimulationScheduler` MUST accept a `completion_callback` parameter and invoke it asynchronously when a batch finishes all simulations.

**Priority**: P0 (Blocking)

**Location**: `shared/control_tools/batch_simulation_scheduler.py`

**Current Code** (method `_mark_batch_completed()`):
```python
def _mark_batch_completed(self, case_id: str, batch_id: str) -> None:
    """Mark batch as completed in internal state"""
    batch_key = f"{case_id}_{batch_id}"
    if batch_key in self.active_batches:
        self.active_batches[batch_key]['status'] = 'completed'
        logger.info(f"Batch {batch_id} marked as completed")
```

**Modified Code**:
```python
def _mark_batch_completed(self, case_id: str, batch_id: str) -> None:
    """Mark batch as completed in internal state"""
    batch_key = f"{case_id}_{batch_id}"
    if batch_key in self.active_batches:
        self.active_batches[batch_key]['status'] = 'completed'
        logger.info(f"Batch {batch_id} marked as completed")

        # ✅ ADDED: Invoke completion callback
        if self.completion_callback:
            asyncio.create_task(
                self.completion_callback(case_id, batch_id)
            )
```

**Constructor Modification**:
```python
class BatchSimulationScheduler:
    def __init__(
        self,
        max_concurrent: int = None,
        completion_callback: Optional[Callable] = None  # ← ADDED
    ):
        self.max_concurrent = max_concurrent or self._get_default_concurrency()
        self.active_batches = {}
        self.task_queue = asyncio.Queue()
        self.completion_callback = completion_callback  # ← ADDED
```

**Service Initialization** (`api/services/batch_optimization_service.py`):
```python
class BatchOptimizationService:
    def __init__(self):
        self.scheduler = BatchSimulationScheduler(
            completion_callback=self._on_batch_completed  # ← ADDED
        )
```

#### Scenario: Scheduler Invokes Completion Callback

**Given**: Batch `batch_20251102_150000` has 5 tasks, all completed

**When**: Scheduler detects last task finished and calls `_mark_batch_completed()`

**Then**:
- `completion_callback` is invoked with `(case_id, batch_id)`
- `_on_batch_completed()` executes asynchronously
- Batch status transitions to "completed" in both metadata files
- No blocking of scheduler's main loop

---

### Requirement: Calculate Success Rate on Completion (REQ-BE-004)

The completion callback SHALL calculate `success_rate` as (completed_tasks / total_tasks) * 100 and store it in both batch metadata and index files.

**Priority**: P1 (High)

**Location**: `api/services/batch_optimization_service.py` (method `_on_batch_completed()`)

**Formula**:
```python
success_rate = (completed_tasks / total_tasks) * 100
```

**Implementation**: (Already included in REQ-BE-002)

#### Scenario: Success Rate Calculation

**Given**: Batch has 10 total tasks, 8 completed successfully, 2 failed

**When**: Batch completes and `_on_batch_completed()` executes

**Then**:
- `success_rate` = `(8 / 10) * 100` = `80.0`
- `batch_metadata.json` contains `"success_rate": 80.0`
- `batches_index.json` includes success rate in batch record
- Frontend displays "80% success rate" badge

---

## ADDED Requirements

### Requirement: Validate Index Synchronization (REQ-BE-005)

The service SHALL provide a validation method that verifies `batches_index.json` is synchronized with `batch_metadata.json` and reports any discrepancies.

**Priority**: P1 (High)

**Location**: `api/services/batch_optimization_service.py` (new method)

**Implementation**:
```python
def _validate_batch_index_sync(self, case_id: str) -> Dict[str, Any]:
    """Validate that batches_index.json is synchronized with batch_metadata.json"""
    index_file = self._get_batches_index_file(case_id)
    index_data = self._load_json(index_file)

    discrepancies = []

    for batch_record in index_data.get('batches', []):
        batch_id = batch_record['batch_id']
        metadata_file = self._get_batch_dir(case_id, batch_id) / "batch_metadata.json"

        if not metadata_file.exists():
            discrepancies.append({
                'batch_id': batch_id,
                'issue': 'metadata_file_missing'
            })
            continue

        metadata = self._load_json(metadata_file)

        # Compare critical fields
        if batch_record['status'] != metadata['status']:
            discrepancies.append({
                'batch_id': batch_id,
                'issue': 'status_mismatch',
                'index_status': batch_record['status'],
                'metadata_status': metadata['status']
            })

    return {
        'synchronized': len(discrepancies) == 0,
        'discrepancies': discrepancies
    }
```

#### Scenario: Detect Synchronization Discrepancy

**Given**: `batches_index.json` shows batch status as "pending", but `batch_metadata.json` shows "completed"

**When**: Admin runs validation check

**Then**:
- Validation returns `synchronized: false`
- Discrepancies list includes batch ID and mismatch details
- Admin can trigger repair script to fix inconsistencies

---

## Testing Requirements

### Unit Tests

**Test File**: `tests/unit/test_batch_status_synchronization.py`

```python
def test_start_batch_updates_index():
    """Test that starting batch updates batches_index.json"""
    service = BatchOptimizationService()
    service.start_batch("case_001", "batch_001")

    index_file = service._get_batches_index_file("case_001")
    index_data = service._load_json(index_file)

    batch_record = next(
        b for b in index_data['batches'] if b['batch_id'] == 'batch_001'
    )

    assert batch_record['status'] == 'running'
    assert 'started_at' in batch_record

def test_completion_callback_updates_status():
    """Test that completion callback updates status to completed"""
    service = BatchOptimizationService()
    asyncio.run(service._on_batch_completed("case_001", "batch_001"))

    metadata_file = service._get_batch_dir("case_001", "batch_001") / "batch_metadata.json"
    metadata = service._load_json(metadata_file)

    assert metadata['status'] == 'completed'
    assert 'completed_at' in metadata
    assert 'success_rate' in metadata

def test_success_rate_calculation():
    """Test that success_rate is correctly calculated"""
    # Setup: batch with 10 total, 7 completed
    # ... setup code ...
    asyncio.run(service._on_batch_completed("case_001", "batch_001"))

    metadata = service._load_json(metadata_file)
    assert metadata['success_rate'] == 70.0
```

### Integration Tests

**Test File**: `tests/integration/test_batch_lifecycle_status.py`

```python
async def test_full_batch_lifecycle_status_updates():
    """Test status updates throughout batch lifecycle"""
    service = BatchOptimizationService()

    # Create batch
    result = await service.create_batch(case_id="case_001", config=batch_config)
    batch_id = result['batch_id']

    # Verify initial status: pending
    index = service._load_json(service._get_batches_index_file("case_001"))
    assert index['batches'][0]['status'] == 'pending'

    # Start batch
    await service.start_batch("case_001", batch_id)

    # Verify status: running
    index = service._load_json(service._get_batches_index_file("case_001"))
    assert index['batches'][0]['status'] == 'running'

    # Wait for batch completion
    await service.scheduler.wait_for_batch(batch_id)

    # Verify status: completed
    index = service._load_json(service._get_batches_index_file("case_001"))
    assert index['batches'][0]['status'] == 'completed'
    assert 'success_rate' in index['batches'][0]
```

---

## Acceptance Criteria

- [ ] `start_batch()` calls `_update_batches_index_on_status_change()` with status "running"
- [ ] `_on_batch_completed()` method implemented and updates status to "completed"
- [ ] Scheduler invokes completion callback when batch finishes
- [ ] `success_rate` calculated and stored in both metadata files
- [ ] `batches_index.json` synchronized with `batch_metadata.json` at all lifecycle stages
- [ ] New batches show correct status transitions (pending → running → completed)
- [ ] All unit tests pass
- [ ] All integration tests pass

---

## Dependencies

- **REQ-FE-005**: Frontend must call batch history API with correct case_id
- **Scheduler**: `BatchSimulationScheduler` must support completion callback parameter

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Callback not invoked due to scheduler exception | Medium | High | Wrap callback in try/except, log failures |
| Race condition: multiple status updates | Low | Medium | Use file locking or atomic writes for index updates |
| Async callback blocks scheduler | Low | Medium | Use `asyncio.create_task()` for non-blocking execution |
| Index file corruption during write | Very Low | High | Write to temp file first, then atomic rename |

---

## Related Documents

- [Proposal: fix-batch-history-data-display](../../proposal.md)
- [Design Document](../../design.md)
- [Frontend Case ID Management Spec](../frontend-case-id-management/spec.md)
- [Historical Batch Repair Spec](../historical-batch-repair/spec.md)
