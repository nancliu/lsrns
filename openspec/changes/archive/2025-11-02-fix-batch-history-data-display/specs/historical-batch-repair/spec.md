# Spec: Historical Batch Status Repair

**Capability**: Historical Batch Status Repair

**Change ID**: `fix-batch-history-data-display`

**Status**: Proposed (Optional)

---

## Overview

This capability provides a one-time repair script to fix the status of 13 existing batches that are incorrectly marked as "pending" in `batches_index.json`. The script scans batch directories, reads actual status from `batch_metadata.json`, and updates the index file accordingly.

**Note**: This is an **optional** capability for cleaning up historical data. The core functionality (frontend and backend fixes) will prevent this issue from occurring in future batches.

---

## ADDED Requirements

### Requirement: Scan Batch Directories for Actual Status (REQ-REPAIR-001)

The repair script SHALL iterate through all batch directories under `cases/{case_id}/simulations/plan_opti/batches/` and read `batch_metadata.json` to determine the actual status of each batch.

**Priority**: P2 (Optional)

**Location**: New script `scripts/repair_batch_status.py`

**Implementation**:
```python
from pathlib import Path
import json
from typing import List, Dict, Any

def scan_batches(case_id: str) -> List[Dict[str, Any]]:
    """Scan all batches for a case and extract actual status"""
    batches_dir = Path(f"cases/{case_id}/simulations/plan_opti/batches")

    if not batches_dir.exists():
        print(f"Batches directory not found: {batches_dir}")
        return []

    batch_records = []

    for batch_dir in batches_dir.iterdir():
        if not batch_dir.is_dir():
            continue

        metadata_file = batch_dir / "batch_metadata.json"

        if not metadata_file.exists():
            print(f"Warning: {metadata_file} not found, skipping")
            continue

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        batch_records.append({
            'batch_id': metadata['batch_id'],
            'status': metadata.get('status', 'unknown'),
            'created_at': metadata.get('created_at'),
            'started_at': metadata.get('started_at'),
            'completed_at': metadata.get('completed_at'),
            'total_tasks': metadata.get('total_tasks', 0),
            'completed_tasks': metadata.get('completed_tasks', 0)
        })

    return batch_records
```

#### Scenario: Scan Existing Batches

**Given**: Case `case_20251028_091831` has 13 batches in directories

**When**: Script executes `scan_batches("case_20251028_091831")`

**Then**:
- Returns list of 13 batch records
- Each record contains actual status from `batch_metadata.json`
- Console shows: "Found 13 batches for case_20251028_091831"

---

### Requirement: Calculate Missing Success Rate (REQ-REPAIR-002)

The repair script MUST calculate `success_rate` for completed batches that are missing this field, using the formula (completed_tasks / total_tasks) * 100.

**Priority**: P2 (Optional)

**Location**: `scripts/repair_batch_status.py`

**Implementation**:
```python
def calculate_success_rate(batch_record: Dict[str, Any]) -> float:
    """Calculate success rate from task counts"""
    total = batch_record.get('total_tasks', 0)
    completed = batch_record.get('completed_tasks', 0)

    if total == 0:
        return 0.0

    return round((completed / total) * 100, 2)
```

#### Scenario: Completed Batch Missing Success Rate

**Given**: Batch `batch_20251030_170601` has:
- status: "completed"
- total_tasks: 10
- completed_tasks: 8
- success_rate: (missing field)

**When**: Script calculates success rate

**Then**:
- Returns `80.0`
- Adds `"success_rate": 80.0` to batch metadata

---

### Requirement: Backup Index Before Update (REQ-REPAIR-003)

The repair script SHALL create a timestamped backup of `batches_index.json` before applying any updates to ensure data can be recovered if needed.

**Priority**: P0 (Critical for data safety)

**Location**: `scripts/repair_batch_status.py`

**Implementation**:
```python
from datetime import datetime
import shutil

def backup_index_file(index_file: Path) -> Path:
    """Create timestamped backup of index file"""
    if not index_file.exists():
        raise FileNotFoundError(f"Index file not found: {index_file}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = index_file.with_suffix(f".backup_{timestamp}.json")

    shutil.copy2(index_file, backup_file)
    print(f"✓ Backup created: {backup_file}")

    return backup_file
```

#### Scenario: Backup Index File

**Given**: `batches_index.json` exists with 13 batch records

**When**: Script executes `backup_index_file()`

**Then**:
- Backup file created: `batches_index.backup_20251102_153045.json`
- Original file unchanged
- Console shows: "✓ Backup created: batches_index.backup_20251102_153045.json"

---

### Requirement: Update Batches Index with Actual Status (REQ-REPAIR-004)

The repair script SHALL update `batches_index.json` with the actual status from scanned batches while preserving all other fields and metadata.

**Priority**: P2 (Optional)

**Location**: `scripts/repair_batch_status.py`

**Implementation**:
```python
def update_batches_index(
    case_id: str,
    batch_records: List[Dict[str, Any]],
    dry_run: bool = False
) -> Dict[str, Any]:
    """Update batches_index.json with actual status"""
    index_file = Path(f"cases/{case_id}/simulations/plan_opti/batches_index.json")

    if not index_file.exists():
        raise FileNotFoundError(f"Index file not found: {index_file}")

    # Backup first
    backup_file = backup_index_file(index_file)

    # Load current index
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    # Update each batch record
    updates_count = 0
    for scanned_batch in batch_records:
        batch_id = scanned_batch['batch_id']

        # Find matching record in index
        index_batch = next(
            (b for b in index_data['batches'] if b['batch_id'] == batch_id),
            None
        )

        if not index_batch:
            print(f"Warning: Batch {batch_id} not found in index, skipping")
            continue

        # Check if update needed
        if index_batch['status'] != scanned_batch['status']:
            print(f"Updating {batch_id}: {index_batch['status']} → {scanned_batch['status']}")
            index_batch['status'] = scanned_batch['status']
            index_batch['started_at'] = scanned_batch.get('started_at')
            index_batch['completed_at'] = scanned_batch.get('completed_at')

            # Add success_rate if completed
            if scanned_batch['status'] == 'completed':
                index_batch['success_rate'] = calculate_success_rate(scanned_batch)

            updates_count += 1

    # Save updated index (unless dry run)
    if not dry_run:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Updated {updates_count} batches in {index_file}")
    else:
        print(f"\n[DRY RUN] Would update {updates_count} batches")

    return {
        'total_scanned': len(batch_records),
        'updates_count': updates_count,
        'backup_file': str(backup_file),
        'dry_run': dry_run
    }
```

#### Scenario: Update Index with Actual Status

**Given**:
- `batches_index.json` has 13 batches all with status "pending"
- Scanned batches show 10 "completed", 2 "running", 1 "pending"

**When**: Script executes `update_batches_index()` with `dry_run=False`

**Then**:
- Backup created first
- 12 batches updated (10 to "completed", 2 to "running")
- 1 batch unchanged (already "pending")
- Console shows: "✓ Updated 12 batches in batches_index.json"
- Returns `{'total_scanned': 13, 'updates_count': 12, ...}`

---

### Requirement: Dry Run Mode for Safety (REQ-REPAIR-005)

The repair script MUST support a dry-run mode that shows what changes would be made without actually modifying any files.

**Priority**: P0 (Critical for data safety)

**Location**: `scripts/repair_batch_status.py`

**Implementation**: (Already included in REQ-REPAIR-004 via `dry_run` parameter)

**CLI Usage**:
```bash
# Dry run (preview changes only)
python scripts/repair_batch_status.py --case-id case_20251028_091831 --dry-run

# Actual execution
python scripts/repair_batch_status.py --case-id case_20251028_091831
```

#### Scenario: Dry Run Preview

**Given**: User wants to preview changes before applying

**When**: Script executes with `--dry-run` flag

**Then**:
- Console shows all proposed changes
- No files are modified (index file unchanged)
- Console shows: "[DRY RUN] Would update 12 batches"
- User can review changes before running actual update

---

### Requirement: Validation Report (REQ-REPAIR-006)

The repair script SHALL generate a validation report showing the before/after state and highlighting any remaining discrepancies after the repair operation.

**Priority**: P1 (High)

**Location**: `scripts/repair_batch_status.py`

**Implementation**:
```python
def generate_validation_report(
    case_id: str,
    before_index: Dict[str, Any],
    after_index: Dict[str, Any]
) -> None:
    """Generate before/after validation report"""
    print("\n" + "="*60)
    print("VALIDATION REPORT")
    print("="*60)

    before_batches = before_index.get('batches', [])
    after_batches = after_index.get('batches', [])

    # Status distribution before
    before_status_counts = {}
    for batch in before_batches:
        status = batch['status']
        before_status_counts[status] = before_status_counts.get(status, 0) + 1

    # Status distribution after
    after_status_counts = {}
    for batch in after_batches:
        status = batch['status']
        after_status_counts[status] = after_status_counts.get(status, 0) + 1

    print("\nStatus Distribution:")
    print(f"  BEFORE: {before_status_counts}")
    print(f"  AFTER:  {after_status_counts}")

    # List updated batches
    print("\nUpdated Batches:")
    for before, after in zip(before_batches, after_batches):
        if before['status'] != after['status']:
            print(f"  - {before['batch_id']}: {before['status']} → {after['status']}")

    # Check for missing success_rate
    missing_success_rate = [
        b['batch_id'] for b in after_batches
        if b['status'] == 'completed' and 'success_rate' not in b
    ]

    if missing_success_rate:
        print(f"\n⚠️ Warning: {len(missing_success_rate)} completed batches missing success_rate")

    print("\n" + "="*60 + "\n")
```

#### Scenario: Validation Report Generation

**Given**: Index repair completed for 13 batches

**When**: Script generates validation report

**Then**:
- Console displays before/after status distribution
- Shows list of updated batches
- Highlights any remaining issues (e.g., missing success_rate)
- Example output:
  ```
  VALIDATION REPORT
  ==================
  Status Distribution:
    BEFORE: {'pending': 13}
    AFTER:  {'completed': 10, 'running': 2, 'pending': 1}

  Updated Batches:
    - batch_20251030_170601: pending → completed
    - batch_20251030_180215: pending → completed
    ...
  ```

---

## CLI Interface

### Script Entry Point

**File**: `scripts/repair_batch_status.py`

```python
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Repair batch status in batches_index.json"
    )
    parser.add_argument(
        '--case-id',
        required=True,
        help='Case ID to repair (e.g., case_20251028_091831)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    # Execute repair
    print(f"Repairing batch status for case: {args.case_id}")
    print(f"Dry run: {args.dry_run}\n")

    batch_records = scan_batches(args.case_id)
    print(f"Found {len(batch_records)} batches\n")

    if args.verbose:
        for batch in batch_records:
            print(f"  - {batch['batch_id']}: {batch['status']}")

    result = update_batches_index(
        case_id=args.case_id,
        batch_records=batch_records,
        dry_run=args.dry_run
    )

    print(f"\nSummary:")
    print(f"  Total batches: {result['total_scanned']}")
    print(f"  Updated: {result['updates_count']}")
    print(f"  Backup: {result['backup_file']}")

if __name__ == '__main__':
    main()
```

### Usage Examples

```bash
# Preview changes for case
python scripts/repair_batch_status.py --case-id case_20251028_091831 --dry-run

# Preview with verbose output
python scripts/repair_batch_status.py --case-id case_20251028_091831 --dry-run --verbose

# Actually apply repairs
python scripts/repair_batch_status.py --case-id case_20251028_091831

# Verify after repair
python scripts/repair_batch_status.py --case-id case_20251028_091831 --dry-run
```

---

## Testing Requirements

### Unit Tests

**Test File**: `tests/unit/test_repair_batch_status.py`

```python
def test_scan_batches():
    """Test that scan_batches reads all batch directories"""
    batches = scan_batches("case_test_001")
    assert len(batches) > 0
    assert all('batch_id' in b for b in batches)
    assert all('status' in b for b in batches)

def test_calculate_success_rate():
    """Test success rate calculation"""
    batch = {'total_tasks': 10, 'completed_tasks': 8}
    assert calculate_success_rate(batch) == 80.0

    # Edge case: no tasks
    batch = {'total_tasks': 0, 'completed_tasks': 0}
    assert calculate_success_rate(batch) == 0.0

def test_backup_index_file():
    """Test that backup is created before modification"""
    index_file = Path("test_batches_index.json")
    backup_file = backup_index_file(index_file)

    assert backup_file.exists()
    assert 'backup_' in backup_file.name
    assert backup_file.suffix == '.json'

def test_dry_run_no_changes():
    """Test that dry run makes no file modifications"""
    index_file = Path("test_batches_index.json")
    original_mtime = index_file.stat().st_mtime

    update_batches_index("case_test_001", batch_records, dry_run=True)

    # File should not be modified
    assert index_file.stat().st_mtime == original_mtime
```

---

## Acceptance Criteria

- [ ] Script can scan all batch directories and read metadata
- [ ] Success rate is calculated for completed batches
- [ ] Backup is created before any index updates
- [ ] Dry run mode shows changes without modifying files
- [ ] Index file is updated with actual status from metadata
- [ ] Validation report shows before/after status distribution
- [ ] CLI supports `--case-id`, `--dry-run`, and `--verbose` flags
- [ ] All 13 existing batches show correct status after repair
- [ ] No data loss or corruption during repair process

---

## Dependencies

- **REQ-BE-001 to REQ-BE-004**: Backend status synchronization prevents future issues
- **Python Standard Library**: `pathlib`, `json`, `shutil`, `argparse`

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Index file corruption during repair | Low | High | **Mandatory backup before update**, atomic write pattern |
| Incorrect status detection | Low | Medium | Validate by checking simulation output files (summary.xml) |
| User forgets to run backup first | Medium | High | **Automatic backup in script**, not optional |
| Script run multiple times | Low | Low | Idempotent design (re-running has no side effects) |

---

## Related Documents

- [Proposal: fix-batch-history-data-display](../../proposal.md)
- [Design Document](../../design.md)
- [Frontend Case ID Management Spec](../frontend-case-id-management/spec.md)
- [Backend Status Synchronization Spec](../backend-status-synchronization/spec.md)
