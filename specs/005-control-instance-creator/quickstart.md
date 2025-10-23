# Quick Start Guide: Control Strategy Instance Creator

**Feature**: Phase 1C - Control Strategy Instance Creator
**Target Audience**: Developers implementing this feature
**Estimated Reading Time**: 15 minutes

## Overview

This guide provides a quick introduction to implementing the Control Strategy Instance Creator. It covers the essential components, development workflow, and testing approach.

---

## Prerequisites

Before starting implementation, ensure you have:

- ✅ **Phase 1A Complete**: Strategy template system working with templates API
- ✅ **Phase 1B Complete**: Edge selector component available
- ✅ **Development Environment**: Python 3.10+, pytest, existing OD_SIM setup
- ✅ **Database Access**: PostgreSQL connection for edge validation
- ✅ **Documentation Read**: Reviewed [spec.md](./spec.md), [data-model.md](./data-model.md), [research.md](./research.md)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  /control/index.html (extended with Strategy Instances tab) │
│                  strategy_manager.js (new)                   │
└───────────────────┬─────────────────────────────────────────┘
                    │ HTTP REST API
┌───────────────────▼─────────────────────────────────────────┐
│                      API Layer (api/)                        │
│  control_strategy_routes.py → control_strategy_service.py   │
└───────────────────┬─────────────────────────────────────────┘
                    │ Function calls
┌───────────────────▼─────────────────────────────────────────┐
│                    Shared Layer (shared/)                    │
│  parameter_validator.py | strategy_file_manager.py          │
│          edge_query.py (Phase 1B, read-only)                │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴──────────┐
        ▼                      ▼
┌───────────────┐    ┌──────────────────┐
│  File System  │    │  PostgreSQL DB   │
│  (JSON files) │    │  (edge data)     │
└───────────────┘    └──────────────────┘
```

---

## Implementation Checklist

### Phase 1: Backend - Shared Layer (TDD Required)

**Priority**: P1 (Foundation)
**Estimated Time**: 2-3 days

1. **Create `shared/control_tools/parameter_validator.py`**
   - [ ] Write test: `tests/unit/test_parameter_validator.py`
   - [ ] Implement: `validate_strategy_parameters(template_schema, parameters) -> List[ValidationError]`
   - [ ] Test edge cases: missing required, out of range, invalid format
   - [ ] Coverage target: ≥80%

2. **Create `shared/control_tools/strategy_file_manager.py`**
   - [ ] Write test: `tests/unit/test_strategy_file_manager.py`
   - [ ] Implement: `save_strategy()`, `load_strategy()`, `delete_strategy()`
   - [ ] Implement: `update_index()`, `regenerate_index()`
   - [ ] Implement: `generate_strategy_id()`
   - [ ] Test concurrency scenarios (optimistic locking)
   - [ ] Coverage target: ≥80%

**Key Functions**:

```python
# shared/control_tools/parameter_validator.py
def validate_strategy_parameters(
    template_schema: Dict[str, Any],
    parameters: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Validate parameters against template schema.

    Returns:
        List of errors: [{"parameter": "speed_limit", "message": "..."}]
        Empty list if valid.
    """
    pass

# shared/control_tools/strategy_file_manager.py
def save_strategy(strategy: Dict[str, Any]) -> None:
    """Save strategy to JSON file and update index."""
    pass

def load_strategy(strategy_id: str) -> Dict[str, Any]:
    """Load strategy from JSON file."""
    pass

def generate_strategy_id() -> str:
    """Generate unique ID: strat_{timestamp}_{random}."""
    pass
```

### Phase 2: Backend - API Layer (TDD Required)

**Priority**: P1 (Core API)
**Estimated Time**: 3-4 days

1. **Create `api/models/requests/strategy_requests.py`**
   - [ ] Define: `StrategyCreateRequest`, `StrategyUpdateRequest`
   - [ ] Add Pydantic validation (min_length, max_length, pattern)

2. **Create `api/models/responses/strategy_responses.py`**
   - [ ] Define: `StrategyListResponse`, `StrategyDetailResponse`
   - [ ] Add example schemas for OpenAPI docs

3. **Create `api/services/control_strategy_service.py`**
   - [ ] Write test: `tests/integration/test_control_strategy_api.py`
   - [ ] Implement: `create_strategy()`, `list_strategies()`, `get_strategy()`
   - [ ] Implement: `update_strategy()`, `delete_strategy()`
   - [ ] Implement: `reindex_strategies()`
   - [ ] Call shared layer functions (parameter_validator, strategy_file_manager)
   - [ ] Call Phase 1A API for template loading
   - [ ] Call Phase 1B edge_query for edge validation
   - [ ] Test target: 100% endpoint coverage

4. **Create `api/routes/control_strategy_routes.py`**
   - [ ] Define 7 endpoints (see [contracts/strategy_api.yaml](./contracts/strategy_api.yaml))
   - [ ] Add FastAPI dependency injection
   - [ ] Add error handling (400, 404, 409, 500)
   - [ ] Register routes in `api/main.py`

5. **Modify `api/services/__init__.py`**
   - [ ] Register `ControlStrategyService`
   - [ ] Add to service locator pattern

**Key Service Methods**:

```python
# api/services/control_strategy_service.py
class ControlStrategyService:
    async def create_strategy(
        self,
        request: StrategyCreateRequest
    ) -> StrategyCreateResponse:
        # 1. Load template from Phase 1A API
        # 2. Validate parameters using parameter_validator
        # 3. Validate edges using edge_query
        # 4. Generate strategy_id
        # 5. Save strategy using strategy_file_manager
        # 6. Return response
        pass

    async def list_strategies(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = None,
        strategy_type: str = None
    ) -> StrategyListResponse:
        # 1. Load index from strategy_file_manager
        # 2. Apply filters (search, strategy_type)
        # 3. Apply pagination
        # 4. Return response
        pass
```

### Phase 3: Frontend (Manual Testing)

**Priority**: P2 (User Interface)
**Estimated Time**: 2-3 days

1. **Extend `frontend/control/index.html`**
   - [ ] Add tab navigation: "Strategy Templates" | "Strategy Instances"
   - [ ] Add container div for strategy management UI
   - [ ] Link new JavaScript file: `strategy_manager.js`

2. **Create `frontend/control/js/strategy_manager.js`**
   - [ ] Implement: `loadStrategyList()` (GET /strategies)
   - [ ] Implement: `openCreateStrategyModal()` (4-step wizard)
   - [ ] Implement: `generateFormFromSchema()` (dynamic form builder)
   - [ ] Implement: `validateParameters()` (frontend validation)
   - [ ] Implement: `saveStrategy()` (POST /strategies)
   - [ ] Implement: `viewStrategyDetails()` (GET /strategies/{id})
   - [ ] Implement: `editStrategy()` (PUT /strategies/{id})
   - [ ] Implement: `deleteStrategy()` (DELETE /strategies/{id})
   - [ ] Integrate: Phase 1B edge selector (modal overlay)

3. **Extend `frontend/control/styles.css`**
   - [ ] Add styles for strategy list table
   - [ ] Add styles for strategy creation wizard
   - [ ] Add styles for detail/edit modals

**Key Frontend Functions**:

```javascript
// frontend/control/js/strategy_manager.js

async function loadStrategyList(page = 1, search = '', type = '') {
    const response = await fetch(
        `/api/v1/control/strategies?page=${page}&search=${search}&strategy_type=${type}`
    );
    const data = await response.json();
    renderStrategyTable(data.strategies);
    renderPagination(data.total_count, data.page, data.page_size);
}

function generateFormFromSchema(templateSchema) {
    const form = document.createElement('form');
    for (const [paramName, paramSchema] of Object.entries(templateSchema)) {
        const field = createFormField(paramName, paramSchema);
        form.appendChild(field);
    }
    return form;
}

async function saveStrategy(strategyData) {
    const response = await fetch('/api/v1/control/strategies', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(strategyData)
    });

    if (response.ok) {
        const result = await response.json();
        showSuccessMessage(`Strategy ${result.strategy_id} created`);
        loadStrategyList(); // Refresh list
    } else {
        const error = await response.json();
        showValidationErrors(error.detail.errors);
    }
}
```

### Phase 4: Testing (Critical)

**Priority**: P1 (Quality Gate)
**Estimated Time**: 1-2 days

1. **Unit Tests** (≥80% coverage)
   - [ ] `tests/unit/test_parameter_validator.py`
     - Test all validation types (integer, string, array, boolean, enum)
     - Test edge cases (empty, null, out of range, invalid format)
   - [ ] `tests/unit/test_strategy_file_manager.py`
     - Test CRUD operations
     - Test index management
     - Test concurrency scenarios (optimistic locking)
     - Test error handling (file corruption, missing index)

2. **Integration Tests** (100% endpoint coverage)
   - [ ] `tests/integration/test_control_strategy_api.py`
     - Test POST /strategies (valid, invalid parameters, missing template)
     - Test GET /strategies (pagination, search, filter)
     - Test GET /strategies/{id} (valid, not found)
     - Test PUT /strategies/{id} (valid, concurrency conflict)
     - Test DELETE /strategies/{id} (valid, not found, used in plans)
     - Test POST /strategies/reindex

3. **Manual E2E Testing**
   - [ ] Create strategy through UI (all 4 steps)
   - [ ] View strategy list with search/filter
   - [ ] View strategy details
   - [ ] Edit strategy (verify optimistic locking warning)
   - [ ] Delete strategy
   - [ ] Test edge selector integration (Phase 1B modal)

**Test Example**:

```python
# tests/integration/test_control_strategy_api.py
import pytest
from fastapi.testclient import TestClient

def test_create_strategy_success(client: TestClient, sample_template):
    request_data = {
        "strategy_name": "Test VSS Strategy",
        "template_id": "vss_moderate",
        "parameters": {"speed_limit": 80, "time_intervals": ["07:00-09:00"]},
        "affected_edges": ["1234567890", "1234567891"]
    }

    response = client.post("/api/v1/control/strategies", json=request_data)

    assert response.status_code == 201
    data = response.json()
    assert "strategy_id" in data
    assert data["strategy_id"].startswith("strat_")

def test_create_strategy_invalid_parameter(client: TestClient):
    request_data = {
        "strategy_name": "Test",
        "template_id": "vss_moderate",
        "parameters": {"speed_limit": 150},  # Out of range
        "affected_edges": ["1234567890"]
    }

    response = client.post("/api/v1/control/strategies", json=request_data)

    assert response.status_code == 400
    data = response.json()
    assert "errors" in data["detail"]
    assert any(e["parameter"] == "speed_limit" for e in data["detail"]["errors"])
```

---

## Development Workflow (TDD)

Follow this workflow for **every component**:

1. **Write Test First**
   ```bash
   # Create test file
   touch tests/unit/test_parameter_validator.py

   # Write failing test
   def test_validate_integer_out_of_range():
       errors = validate_strategy_parameters(
           {"speed_limit": {"type": "integer", "min": 40, "max": 120}},
           {"speed_limit": 150}
       )
       assert len(errors) == 1
       assert "speed_limit" in errors[0]["parameter"]
   ```

2. **Run Test (Expect Failure)**
   ```bash
   pytest tests/unit/test_parameter_validator.py::test_validate_integer_out_of_range
   # Expected: FAILED (function not implemented)
   ```

3. **Implement Minimum Code**
   ```python
   # shared/control_tools/parameter_validator.py
   def validate_strategy_parameters(template_schema, parameters):
       errors = []
       for param_name, param_schema in template_schema.items():
           value = parameters.get(param_name)
           if param_schema["type"] == "integer":
               if value < param_schema["min"] or value > param_schema["max"]:
                   errors.append({
                       "parameter": param_name,
                       "message": f"{param_name} must be between {param_schema['min']} and {param_schema['max']}"
                   })
       return errors
   ```

4. **Run Test (Expect Success)**
   ```bash
   pytest tests/unit/test_parameter_validator.py::test_validate_integer_out_of_range
   # Expected: PASSED
   ```

5. **Refactor & Repeat**

---

## Running the Application

### 1. Start Backend API

```powershell
# From project root
.\start_api.ps1

# Or directly
python api/main.py

# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### 2. Access Frontend

```
http://localhost:8000/control/index.html

# Click "Strategy Instances" tab
```

### 3. Test Endpoints (curl examples)

**Create Strategy**:
```bash
curl -X POST "http://localhost:8000/api/v1/control/strategies" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "Test VSS Strategy",
    "template_id": "vss_moderate",
    "parameters": {"speed_limit": 80},
    "affected_edges": ["1234567890"]
  }'
```

**List Strategies**:
```bash
curl "http://localhost:8000/api/v1/control/strategies?page=1&page_size=20"
```

**Get Strategy Details**:
```bash
curl "http://localhost:8000/api/v1/control/strategies/strat_20251021143025_a3f7b9"
```

---

## Common Development Tasks

### Add New Parameter Type

1. **Update validator** (`shared/control_tools/parameter_validator.py`):
   ```python
   elif param_schema["type"] == "float":
       if not isinstance(value, (int, float)):
           errors.append({...})
   ```

2. **Add test** (`tests/unit/test_parameter_validator.py`):
   ```python
   def test_validate_float():
       # Test valid float
       # Test out of range
       # Test wrong type
   ```

3. **Update frontend form generator** (`strategy_manager.js`):
   ```javascript
   case 'float':
       return createNumberInput(paramName, schema.min, schema.max, schema.step);
   ```

### Debug Validation Errors

1. **Check backend logs**:
   ```python
   logger.warning(f"Validation failed for {strategy_id}: {errors}")
   ```

2. **Inspect template schema**:
   ```bash
   curl "http://localhost:8000/api/v1/control/templates/vss_moderate"
   # Check parameters_schema field
   ```

3. **Test validator directly**:
   ```python
   from shared.control_tools.parameter_validator import validate_strategy_parameters

   errors = validate_strategy_parameters(template_schema, parameters)
   print(errors)
   ```

### Handle Index Corruption

1. **Manual regeneration**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/control/strategies/reindex"
   ```

2. **Automatic on startup**: Already implemented in `api/main.py::startup` event

---

## Troubleshooting

### Issue: Template Not Found (404)

**Symptoms**: POST /strategies returns 404 "Template not found"

**Solution**:
1. Verify Phase 1A is running
2. Check template exists:
   ```bash
   curl "http://localhost:8000/api/v1/control/templates/"
   ```
3. Use correct template_id from Phase 1A response

### Issue: Edge Validation Fails

**Symptoms**: POST /strategies returns 400 "X of Y edges not found"

**Solution**:
1. Verify database connection
2. Check edge_ids are correct:
   ```sql
   SELECT edge_id, route_code FROM sim_edges WHERE edge_id IN ('1234567890', '...');
   ```
3. Use valid edge_ids from Phase 1B edge selector

### Issue: Concurrency Conflict (409)

**Symptoms**: PUT /strategies returns 409 "Strategy modified by another user"

**Solution**:
1. Refresh strategy detail to get latest `updated_at`
2. Send updated `original_updated_at` in request
3. Consider showing diff to user before overwriting

### Issue: Index Out of Sync

**Symptoms**: Strategy appears in index but file doesn't exist (or vice versa)

**Solution**:
```bash
# Regenerate index
curl -X POST "http://localhost:8000/api/v1/control/strategies/reindex"
```

---

## File Structure Reference

```
project_root/
├── api/
│   ├── models/
│   │   ├── requests/
│   │   │   └── strategy_requests.py       ← NEW
│   │   └── responses/
│   │       └── strategy_responses.py      ← NEW
│   ├── services/
│   │   ├── __init__.py                    ← MODIFY (register service)
│   │   └── control_strategy_service.py    ← NEW
│   └── routes/
│       └── control_strategy_routes.py     ← NEW
│
├── shared/
│   └── control_tools/
│       ├── parameter_validator.py         ← NEW
│       └── strategy_file_manager.py       ← NEW
│
├── frontend/control/
│   ├── index.html                         ← EXTEND (add tab)
│   ├── js/
│   │   ├── app.js                         ← EXTEND (tab logic)
│   │   └── strategy_manager.js            ← NEW
│   └── styles.css                         ← EXTEND
│
├── control_data/strategies/               ← NEW (auto-created)
│   ├── strat_*.json
│   └── strategies_index.json
│
└── tests/
    ├── unit/
    │   ├── test_parameter_validator.py    ← NEW
    │   └── test_strategy_file_manager.py  ← NEW
    └── integration/
        └── test_control_strategy_api.py   ← NEW
```

---

## Next Steps

After completing Phase 1C implementation:

1. ✅ **Verify Constitution Compliance**: Re-run constitution check
2. ✅ **Run Full Test Suite**: `pytest tests/` (100% API, ≥80% unit)
3. ✅ **Manual E2E Testing**: Test complete workflow in browser
4. ✅ **Code Review**: Verify no existing files modified (Module Isolation)
5. ✅ **Documentation**: Update CLAUDE.md if needed
6. → **Proceed to `/speckit.tasks`**: Generate detailed task breakdown for implementation

---

## Key Resources

- **Specification**: [spec.md](./spec.md) - Complete functional requirements
- **Data Model**: [data-model.md](./data-model.md) - Entity definitions and validation
- **Research**: [research.md](./research.md) - Technology decisions and patterns
- **API Contract**: [contracts/strategy_api.yaml](./contracts/strategy_api.yaml) - OpenAPI specification
- **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) - Architecture principles

---

**Status**: ✅ Quick start guide complete. Ready for implementation!
