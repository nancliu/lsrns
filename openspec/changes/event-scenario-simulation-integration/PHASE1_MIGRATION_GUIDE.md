# Phase 1 Migration Guide - API Endpoint Changes

**Date**: 2025-11-15
**Target**: Developers and API users
**Scope**: Case creation endpoint consolidation
**Breaking Changes**: Yes (old endpoints will be removed)

---

## Executive Summary

Phase 1 consolidates 4 redundant case creation endpoints into 2 clear workflows:

| Workflow | Old Endpoint(s) | New Endpoint | Effect |
|----------|-----------------|--------------|--------|
| OD Extraction | `POST /api/v1/case/create_case/` | `POST /api/v1/case/` | Renamed for RESTful style |
| Event Scenario | `/create-from-scenario` + `/quick-create-from-event` | `POST /api/v1/case/from-event-scenario` | Consolidated into one endpoint |

---

## API Changes

### 1. OD Workflow (Minimal Change)

**Old:**
```bash
POST /api/v1/case/create_case/
Content-Type: application/json

{
  "case_name": "My OD Case",
  "case_config": {...},
  "description": "..."
}
```

**New:**
```bash
POST /api/v1/case/
Content-Type: application/json

{
  "case_name": "My OD Case",
  "case_config": {...},
  "description": "..."
}
```

**Breaking**: Yes (endpoint path changed)
**Mitigation**: Simple rename in client code
**Impact Level**: Low (straightforward URL change)

### 2. Event Scenario Workflow (Consolidation)

**Old (Two Separate Endpoints):**
```bash
# Option A
POST /api/v1/case/create-from-scenario
Content-Type: application/json

{
  "scenario_id": "scenario_xxx",
  "simulation_duration_hours": 2.0,
  "output_config": {...}
}

# Option B (identical functionality)
POST /api/v1/case/quick-create-from-event
Content-Type: application/json

{
  "scenario_id": "scenario_xxx",
  ...
}
```

**New (Single Consolidated Endpoint):**
```bash
POST /api/v1/case/from-event-scenario
Content-Type: application/json

{
  "scenario_id": "scenario_xxx",
  "simulation_duration_hours": 2.0,
  "output_config": {...}
}
```

**Response Now Includes simulation_id:**
```json
{
  "code": 200,
  "message": "case_created_with_scenario",
  "data": {
    "case_id": "case_event_123",
    "case_type": "event_based",
    "simulation_id": "event_simulation_scenario_xxx",
    "metadata": {...},
    "status": "case_created_with_scenario"
  }
}
```

**Breaking**: Yes (both old endpoints removed, consolidation required)
**Mitigation**: Update to use single new endpoint
**Impact Level**: Medium (requires understanding consolidation)

### 3. Deleted Endpoints (No Longer Needed)

**Old Endpoints to Be Removed:**
```
❌ POST /api/v1/case/create-case-with-simulation
   Reason: Auto-simulation is now standard in event workflow

❌ POST /api/v1/simulation/
❌ GET  /api/v1/simulation/
❌ GET  /api/v1/simulation/{sim_id}
❌ POST /api/v1/simulation/{sim_id}/start
   Reason: Simulation creation now automatic; batch management in Phase 1.5
```

**Impact**: If you were calling these endpoints directly, they will return 404.

---

## Migration Checklist

### For OD Extraction Users

- [ ] Update endpoint from `/case/create_case/` to `/case/`
- [ ] Test case creation with OD data
- [ ] Verify existing OD cases still load
- [ ] **No other changes needed**

### For Event Scenario Users (Complex)

#### Option A: Using `/create-from-scenario`
- [ ] Rename endpoint to `/case/from-event-scenario`
- [ ] Test case creation with scenario ID
- [ ] Verify `simulation_id` is returned
- [ ] Update downstream code to use `simulation_id`

#### Option B: Using `/quick-create-from-event`
- [ ] Rename endpoint to `/case/from-event-scenario`
- [ ] Same as Option A

#### Option C: Using `/create-case-with-simulation`
- [ ] Switch to `/case/from-event-scenario` endpoint
- [ ] Same request format (scenario_id, simulation_duration_hours, output_config)
- [ ] Same response now includes all fields
- [ ] **No functional change**, just endpoint consolidation

### For Batch Simulation Users

If you were starting simulations with:
```
POST /api/v1/simulation/{sim_id}/start
```

**Migrate to Phase 1.5 (coming soon):**
```
POST /api/v1/event-simulation/batch-start
{
  "case_ids": ["case_event_1", "case_event_2", ...],
  "description": "My batch"
}
```

---

## Code Migration Examples

### Python - Event Scenario Workflow

**Before (Old Code Using Multiple Endpoints):**
```python
import requests

# Step 1: Create case (endpoint 1)
response = requests.post(
    "http://localhost:8000/api/v1/case/create-from-scenario",
    json={
        "scenario_id": "scenario_1234",
        "simulation_duration_hours": 2.0,
        "output_config": {"enable_edgedata": True}
    }
)
case_data = response.json()
case_id = case_data["data"]["case_id"]

# Step 2: Start simulation manually (endpoint 2)
response = requests.post(
    f"http://localhost:8000/api/v1/simulation/{case_id}/start"
)
```

**After (New Code Using Consolidated Endpoint):**
```python
import requests

# Single call: Create case + auto-create simulation
response = requests.post(
    "http://localhost:8000/api/v1/case/from-event-scenario",
    json={
        "scenario_id": "scenario_1234",
        "simulation_duration_hours": 2.0,
        "output_config": {"enable_edgedata": True}
    }
)
case_data = response.json()
case_id = case_data["data"]["case_id"]
simulation_id = case_data["data"]["simulation_id"]  # NEW: Auto-created!

# Simulation is now ready to start in Phase 1.5
```

### JavaScript - OD Workflow

**Before:**
```javascript
const response = await fetch('/api/v1/case/create_case/', {
  method: 'POST',
  body: JSON.stringify({
    case_name: 'My OD Case',
    case_config: {...}
  })
});
```

**After:**
```javascript
const response = await fetch('/api/v1/case/', {  // Just remove "create_case/"
  method: 'POST',
  body: JSON.stringify({
    case_name: 'My OD Case',
    case_config: {...}
  })
});
```

### Frontend - Case Creation Modal

**Before (Multiple Event Endpoints):**
```javascript
// Check which endpoint to use
if (useQuickCreate) {
  endpoint = '/api/v1/case/quick-create-from-event';
} else {
  endpoint = '/api/v1/case/create-from-scenario';
}

// Post to whichever endpoint
fetch(endpoint, { ... });
```

**After (Single Event Endpoint):**
```javascript
// Always use this endpoint
const endpoint = '/api/v1/case/from-event-scenario';

fetch(endpoint, {
  method: 'POST',
  json: {
    scenario_id: selectedScenarioId,
    simulation_duration_hours: durationHours,
    output_config: outputConfig
  }
}).then(res => {
  const caseId = res.data.case_id;
  const simId = res.data.simulation_id;  // NEW: Always included for event cases
  // Update UI to show both IDs
});
```

---

## Testing Your Migration

### Unit Tests

```python
# Test 1: OD workflow still works
def test_od_case_creation():
    response = client.post('/api/v1/case/', json={
        'case_name': 'Test OD',
        'case_config': {...}
    })
    assert response.status_code == 200
    assert 'case_id' in response.json()['data']

# Test 2: Event workflow returns simulation_id
def test_event_case_creation():
    response = client.post('/api/v1/case/from-event-scenario', json={
        'scenario_id': 'scenario_123',
        'simulation_duration_hours': 2.0
    })
    assert response.status_code == 200
    data = response.json()['data']
    assert data['case_id'].startswith('case_event_')
    assert 'simulation_id' in data
    assert data['simulation_id'].startswith('event_simulation_')
```

### Integration Tests

```python
# Test 3: Old endpoints return 404
def test_old_endpoints_deprecated():
    response = client.post('/api/v1/case/create_case/', json={...})
    assert response.status_code == 404

    response = client.post('/api/v1/case/quick-create-from-event', json={...})
    assert response.status_code == 404
```

### Manual Testing Checklist

- [ ] Can create OD case via `POST /api/v1/case/`
- [ ] Can create event case via `POST /api/v1/case/from-event-scenario`
- [ ] Event case response includes both `case_id` and `simulation_id`
- [ ] Old endpoints return 404 (properly removed)
- [ ] Existing cases still load (backward compatible)
- [ ] Case listing shows both OD and event cases

---

## Rollback Plan

If issues are discovered after deployment:

### Quick Rollback (< 5 minutes)

```bash
# Revert to previous commit
git revert <commit_hash>

# Or revert specific files
git checkout HEAD~1 api/routes/case_routes.py
git checkout HEAD~1 api/services/case_service.py
```

### Data Safety

✅ **Safe to rollback** - No data structure changes
✅ **No database migrations** required
✅ **Existing cases preserved** - Can load with old code

### Communication

If you need to rollback:
1. Notify users in #api-changes Slack channel
2. Publish rollback message: "Case creation endpoints temporarily reverted to previous version"
3. No action needed by API users (code will continue working)

---

## Support & FAQs

### Q: Can I still use the old endpoints?
**A:** No, Phase 1 removes them. Update your code to use new endpoints before the deadline.

### Q: Will my existing cases break?
**A:** No, existing cases continue to work regardless of which endpoint created them.

### Q: What if I'm using multiple old endpoints?
**A:** Consolidate to the single new endpoint (`/case/from-event-scenario`).

### Q: When is the deadline to migrate?
**A:** Phase 1 removal is scheduled for 2025-11-16. Update code ASAP.

### Q: How do I monitor simulations after Phase 1?
**A:** Phase 1.5 (coming soon) will provide `POST /api/v1/event-simulation/batch-start` for batch management.

---

## Summary Table

| Aspect | Old | New | Action Required |
|--------|-----|-----|-----------------|
| OD Case | `/case/create_case/` | `/case/` | Update endpoint URL |
| Event Case | `/create-from-scenario` or `/quick-create-from-event` | `/case/from-event-scenario` | Consolidate to one endpoint |
| Simulation Creation | Manual (separate `/simulation/` call) | Automatic (included in case response) | Remove manual sim creation code |
| Response | case_id only | case_id + simulation_id (for event) | Update response parsing |

---

## Timeline

| Date | Event | Action |
|------|-------|--------|
| 2025-11-15 | Phase 1 preparation | Review this guide |
| 2025-11-15 EOD | Phase 1 deployment | Update your code |
| 2025-11-16 | Phase 1 complete | Old endpoints removed |
| 2025-11-17+ | Phase 1.5 starts | Batch simulation features |

---

**Questions or Issues?** → Open an issue in the openspec change tracker or contact the team.
