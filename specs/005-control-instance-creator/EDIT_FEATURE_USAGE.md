# Strategy Edit Feature - Usage Guide

**Feature**: Control Strategy Instance Editing (Phase 1C - User Story 3)
**Status**: ✅ Implementation Complete (Tasks T082-T089)
**Date**: 2025-10-22

## Overview

The strategy edit feature allows traffic engineers to modify existing control strategy instances with full validation and concurrency control.

## Implementation Summary

### Backend (✅ Complete)

**Service Layer** (`api/services/strategy_instance_service.py`):
- ✅ `update_strategy()` - Handles strategy updates with optimistic concurrency control
  - Validates `original_updated_at` to detect concurrent modifications
  - Increments version number on each update
  - Returns updated strategy or raises ValueError for conflicts

**API Layer** (`api/routes/control_strategy_instance_routes.py`):
- ✅ `PUT /api/v1/control/strategy-instances/{strategy_id}` endpoint
  - Returns 200 OK with updated strategy details
  - Returns 404 if strategy not found
  - Returns 409 Conflict if concurrent modification detected
  - Returns 400 Bad Request if validation fails

**Request Model** (`api/models/requests/strategy_requests.py`):
```python
class StrategyUpdateRequest(BaseModel):
    strategy_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    affected_edges: Optional[List[str]] = None
    original_updated_at: str  # Required for concurrency check
```

### Frontend (✅ Complete)

**Strategy Manager** (`frontend/control/js/strategy_manager.js`):

1. **editStrategy(strategyId)** - T085
   - Fetches strategy details from API
   - Loads template schema for parameter types
   - Shows modal with pre-populated form
   - Stores `original_updated_at` for concurrency check

2. **saveStrategyUpdate()** - T086
   - Validates all form fields
   - Sends PUT request with updated data
   - Handles all response codes (200/400/404/409)
   - Shows success/error messages

3. **handleConcurrencyConflict()** - T087
   - Detects 409 Conflict responses
   - Shows warning modal to user
   - Suggests refreshing and retrying

4. **cancelEdit()** - T088
   - Asks for confirmation before discarding
   - Closes modal without saving
   - Clears editing state

5. **Edit Modal UI** - T089
   - Inline CSS styling (no separate stylesheet needed)
   - Clean, responsive design
   - Pre-populated form fields
   - Save/Cancel buttons

## Usage Examples

### Example 1: Basic Usage in Frontend

```javascript
// Access global instance
const manager = window.strategyManager;

// Edit a strategy by ID
manager.editStrategy('strat_20251021_a3f7b9');
```

### Example 2: API Usage via cURL

```bash
# 1. Get strategy to get current updated_at
curl -X GET http://localhost:8000/api/v1/control/strategy-instances/strat_20251021_a3f7b9

# 2. Update strategy
curl -X PUT http://localhost:8000/api/v1/control/strategy-instances/strat_20251021_a3f7b9 \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "Updated Morning VSS",
    "parameters": {
      "control_speed": 60,
      "time_intervals": ["07:00-09:00", "17:00-19:00"]
    },
    "affected_edges": ["-5880", "-5881"],
    "original_updated_at": "2025-10-22T06:30:00.000Z"
  }'
```

### Example 3: Python API Usage

```python
import requests
from datetime import datetime

# Base URL
API_BASE = "http://localhost:8000/api/v1/control/strategy-instances"

# 1. Fetch current strategy
strategy_id = "strat_20251021_a3f7b9"
response = requests.get(f"{API_BASE}/{strategy_id}")
strategy = response.json()

# 2. Prepare update
update_payload = {
    "strategy_name": "Updated Strategy Name",
    "parameters": {
        "control_speed": 60,
        "time_intervals": ["08:00-10:00"]
    },
    "affected_edges": strategy["affected_edges"],  # Keep existing edges
    "original_updated_at": strategy["metadata"]["updated_at"]
}

# 3. Send update request
response = requests.put(
    f"{API_BASE}/{strategy_id}",
    json=update_payload
)

if response.status_code == 200:
    updated = response.json()
    print(f"✅ Updated to version {updated['metadata']['version']}")
elif response.status_code == 409:
    print("⚠️ Concurrency conflict - strategy was modified by another user")
elif response.status_code == 404:
    print("❌ Strategy not found")
else:
    print(f"❌ Error: {response.json()}")
```

## Concurrency Control

### How It Works

1. **Optimistic Locking**: Uses timestamp-based concurrency control
2. **Check**: Backend compares `original_updated_at` with current `updated_at`
3. **Conflict Detection**: If timestamps don't match, returns 409 Conflict
4. **User Action**: Frontend shows warning, suggests refresh and retry

### Conflict Scenario

```
Time  | User A                    | User B
------|---------------------------|---------------------------
T1    | GET strategy (v1)         |
T2    |                           | GET strategy (v1)
T3    | PUT strategy (success)    |
      | → v2, updated_at = T3     |
T4    |                           | PUT strategy (CONFLICT!)
      |                           | → original_updated_at ≠ current
      |                           | → Returns 409
```

## Error Handling

### Response Codes

| Code | Meaning | Frontend Action |
|------|---------|-----------------|
| 200 | Success | Show success message, close modal |
| 400 | Validation error | Show validation message |
| 404 | Strategy not found | Show error message |
| 409 | Concurrency conflict | Show conflict warning modal |
| 500 | Server error | Show generic error message |

### Validation Rules

All existing validation from create flow applies:
- Strategy name: 1-100 characters
- Parameters: Must match template schema
- Parameter types: integer, float, string, boolean, array
- Range checks: min/max values enforced
- Required fields: Must be provided

## Metadata Behavior

### Preserved Fields

- `created_at` - Never changes
- `created_by` - Never changes
- `template_id` - Never changes (cannot change template)
- `strategy_type` - Never changes (derived from template)

### Updated Fields

- `strategy_name` - Can be updated
- `parameters` - Can be updated (individual parameters)
- `affected_edges` - Can be updated (entire list replacement)
- `metadata.updated_at` - Auto-updated to current timestamp
- `metadata.version` - Auto-incremented (v1 → v2 → v3...)

## Testing

### Manual Testing Checklist

- [ ] Edit a strategy via UI
- [ ] Modify strategy name
- [ ] Modify parameter values
- [ ] Verify validation errors shown for invalid inputs
- [ ] Cancel edit and verify no changes saved
- [ ] Save changes and verify success message
- [ ] Verify version incremented in response
- [ ] Simulate concurrent edit (two tabs) and verify 409 conflict

### Integration Tests (Pending - T090)

The following tests need to be written in `tests/integration/test_control_strategy_api.py`:

- **T078**: PUT success - valid update returns 200, version incremented
- **T079**: PUT validation fail - invalid parameters return 400
- **T080**: PUT concurrency conflict - mismatched updated_at returns 409
- **T081**: PUT not found - non-existent strategy returns 404

## Known Limitations

1. **Edge Selection**: Current implementation shows selected edges as read-only. To enable edge modification, integrate with Phase 1B edge selector in modal.

2. **Template Change**: Cannot change the underlying template of a strategy. To use a different template, create a new strategy.

3. **Batch Updates**: API only supports single strategy updates. For bulk updates, call API multiple times.

## Future Enhancements (Out of Scope)

- **Edit History**: Track all versions and changes
- **Rollback**: Revert to previous version
- **Diff View**: Show what changed between versions
- **Lock Mechanism**: Explicit locking instead of optimistic concurrency
- **Edge Selector Integration**: Allow modifying affected edges in edit modal

## Files Modified

### Backend
- `api/services/strategy_instance_service.py` (lines 454-519)
- `api/routes/control_strategy_instance_routes.py` (lines 194-254)
- `api/models/requests/strategy_requests.py` (StrategyUpdateRequest)

### Frontend
- `frontend/control/js/strategy_manager.js` (added 470+ lines)
  - editStrategy()
  - loadTemplateById()
  - showEditModal()
  - createEditModal()
  - generateEditForm()
  - populateEditForm()
  - saveStrategyUpdate()
  - handleConcurrencyConflict()
  - cancelEdit()
  - closeEditModal()

### Documentation
- `specs/005-control-instance-creator/tasks.md` (marked T082-T089 complete)
- `specs/005-control-instance-creator/EDIT_FEATURE_USAGE.md` (this file)

## Contact & Support

For questions or issues:
1. Check `specs/005-control-instance-creator/spec.md` for requirements
2. Review `specs/005-control-instance-creator/data-model.md` for data structures
3. See `api/routes/control_strategy_instance_routes.py` for API documentation

---

**Last Updated**: 2025-10-22
**Implementation Status**: ✅ Complete (T082-T089)
**Next Steps**: Write integration tests (T090), then deploy
