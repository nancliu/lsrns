# Phase 0: Research - Strategy Template System

**Date**: 2025-10-19
**Feature**: Strategy Template System (Phase 1A)
**Status**: Completed

## Research Summary

All technical unknowns resolved. No NEEDS CLARIFICATION markers in Technical Context. This research documents key technical decisions and best practices for implementation.

## Research Areas

### 1. JSON Template Schema Design

**Decision**: Use self-describing JSON schema with embedded parameter type information

**Rationale**:
- Pydantic can validate against JSON schemas natively
- Self-describing schemas enable dynamic frontend form generation (Phase 1C)
- Aligns with existing vehicle template pattern in `templates/config_templates/vehicle_templates/vehicle_types.json`
- Parameter types (integer, float, string, boolean, array) map directly to JSON types and Python types

**Schema Structure**:
```json
{
  "template_id": "vss_moderate",
  "template_name": "可变限速 - 中等控制",
  "description": "适用于高峰期的中等强度限速控制...",
  "strategy_type": "VSS",
  "version": "1.0",
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      "parameter_type": "array",
      "description": "受限速影响的路段列表",
      "required": true,
      "default_value": [],
      "unit": null
    },
    {
      "parameter_name": "speed_limit",
      "parameter_type": "integer",
      "description": "限速值（公里/小时）",
      "required": true,
      "default_value": 80,
      "min_value": 40,
      "max_value": 120,
      "unit": "km/h"
    }
  ],
  "created_at": "2025-10-19T00:00:00",
  "updated_at": "2025-10-19T00:00:00"
}
```

**Alternatives Considered**:
- JSON Schema standard (RFC 8927): Too complex for Phase 1A, no dynamic form generation capability
- XML with XSD: Incompatible with existing JSON-based configuration pattern
- Python dataclasses: Not portable, requires code changes for schema modifications

### 2. FastAPI Routing Patterns for Control Module

**Decision**: Use APIRouter with `/api/v1/control/` prefix, separate route file for templates

**Rationale**:
- Follows existing pattern (`api/routes/simulation_routes.py`, `api/routes/case_routes.py`)
- Module Isolation principle: control routes independent of simulation routes
- Prefix `/api/v1/control/` clearly identifies control module endpoints
- APIRouter enables easy testing with FastAPI TestClient

**Implementation Pattern**:
```python
# api/routes/control_template_routes.py
from fastapi import APIRouter, HTTPException
from api.services.control_template_service import ControlTemplateService

router = APIRouter(prefix="/api/v1/control", tags=["control"])

@router.get("/templates/")
async def list_templates():
    """List all available strategy templates"""
    service = ControlTemplateService()
    return service.list_templates()

@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get detailed information about a specific template"""
    service = ControlTemplateService()
    template = service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return template
```

**Alternatives Considered**:
- Function-based routing: Less structured, harder to test, incompatible with existing API architecture
- Class-based views: FastAPI doesn't natively support, would introduce new pattern

### 3. Template Validation Strategy

**Decision**: Multi-layer validation (JSON syntax → structure → schema → business rules)

**Rationale**:
- Early validation at startup prevents runtime errors
- Layered validation provides clear error messages
- Graceful degradation: reject invalid templates, keep valid ones
- Pydantic provides built-in validation for structure and types

**Validation Layers**:
1. **JSON Syntax**: `json.loads()` with try-except
2. **Structure**: Pydantic model validation (required fields, types)
3. **Schema**: Parameter schema validation (supported types, min/max ranges)
4. **Business Rules**: Custom validators (e.g., duplicate template IDs)

**Implementation**:
```python
# shared/control_tools/template_loader.py
def validate_template(template_data: dict) -> tuple[bool, str]:
    """Validate template structure and schema"""
    # Layer 2: Structure validation via Pydantic
    try:
        template = ControlTemplate(**template_data)
    except ValidationError as e:
        return False, f"Structure validation failed: {e}"

    # Layer 3: Schema validation
    for param in template.parameters_schema:
        if param.parameter_type not in SUPPORTED_TYPES:
            return False, f"Unsupported type: {param.parameter_type}"

    # Layer 4: Business rules
    # (e.g., check for duplicate IDs in index)

    return True, "Valid"
```

**Alternatives Considered**:
- Single-pass validation: Less clear error messages, harder to debug
- No validation: High risk of runtime errors, violates Test-First principle

### 4. Frontend Modal Dialog Implementation

**Decision**: Vanilla JavaScript with CSS-only modal, no external libraries

**Rationale**:
- Follows existing frontend pattern (no React/Vue dependencies in current system)
- CSS modal is lightweight (<50 lines CSS, <30 lines JS)
- Native browser support for modal semantics via `<dialog>` element (fallback to div+overlay)
- Accessibility: Keyboard navigation (ESC to close), focus management

**Implementation Pattern**:
```html
<!-- Modal structure -->
<div id="templateModal" class="modal">
  <div class="modal-content">
    <span class="modal-close">&times;</span>
    <h2 id="modalTitle"></h2>
    <div id="modalBody"></div>
  </div>
</div>
```

```javascript
// Modal control
function showTemplateDetail(templateId) {
  fetch(`/api/v1/control/templates/${templateId}`)
    .then(response => response.json())
    .then(template => {
      document.getElementById('modalTitle').textContent = template.template_name;
      document.getElementById('modalBody').innerHTML = renderTemplateDetail(template);
      document.getElementById('templateModal').style.display = 'block';
    });
}
```

**Alternatives Considered**:
- Bootstrap modal: Introduces dependency, overkill for simple use case
- HTML `<dialog>` element only: Limited browser support on Windows (IE11/older Edge)
- React/Vue component: Incompatible with existing vanilla JS frontend

### 5. Testing Strategy

**Decision**: Test pyramid (unit → integration → E2E) with pytest + FastAPI TestClient + Playwright

**Rationale**:
- Constitution requirement: API tests 100%, unit tests ≥80%
- FastAPI TestClient enables fast integration tests without server startup
- Playwright MCP can test modal interaction (E2E layer)
- pytest fixtures enable shared test data (template fixtures)

**Test Structure**:
```python
# Unit tests (shared/control_tools/template_loader.py)
def test_load_valid_template():
    """Verify template loading from valid JSON file"""

def test_validate_template_missing_required_field():
    """Verify validation rejects template missing required field"""

def test_list_templates_auto_generates_index():
    """Verify index file is auto-generated on first load"""

# Integration tests (api/routes/control_template_routes.py)
def test_get_templates_returns_all_valid_templates():
    """Verify GET /templates/ returns all valid templates"""
    client = TestClient(app)
    response = client.get("/api/v1/control/templates/")
    assert response.status_code == 200
    assert len(response.json()) == 5  # All 5 Phase 1A templates

def test_get_template_by_id_returns_full_details():
    """Verify GET /templates/{id} returns complete template"""

def test_get_template_invalid_id_returns_404():
    """Verify 404 for non-existent template ID"""
```

**Test Data Management**:
- Use `tests/fixtures/templates/` for test template files
- pytest fixtures for common template objects
- Separate test directory from production `templates/control_strategies/`

**Alternatives Considered**:
- Manual testing only: Violates Test-First principle, no regression protection
- unittest instead of pytest: Less flexible fixtures, more verbose
- Mock-based testing only: Misses integration issues (e.g., file path errors)

## Technology Decisions Summary

| Decision Point | Choice | Primary Reason |
|----------------|--------|----------------|
| Template format | Self-describing JSON with embedded schemas | Enables dynamic form generation (Phase 1C), aligns with existing patterns |
| API routing | FastAPI APIRouter with `/api/v1/control/` prefix | Module isolation, follows existing architecture |
| Validation strategy | Multi-layer (JSON → structure → schema → business) | Clear error messages, graceful degradation |
| Frontend modal | Vanilla JS + CSS modal | No dependencies, follows existing pattern |
| Testing framework | pytest + FastAPI TestClient + Playwright | Meets constitution requirements (100% API, ≥80% unit) |
| Template storage | File-based in `templates/control_strategies/` | Constitution VI (File-Based Storage), no DB overhead |
| Index generation | Auto-generated at startup | Prevents manual sync errors, always consistent |

## Implementation Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Invalid template prevents startup | High | Graceful degradation: log error, reject invalid template, load valid templates |
| Template ID collision | Medium | Validation checks for duplicates, reject with clear error message |
| Large template count slows startup | Low (5 templates Phase 1A) | Index caching (future), lazy loading (if needed >50 templates) |
| Frontend modal accessibility | Low | Use semantic HTML, keyboard navigation, focus management |

## Best Practices Applied

1. **Fail Fast**: Template validation at startup, not at runtime
2. **Explicit > Implicit**: Self-describing schemas, no magic values
3. **DRY**: Reusable validation functions, shared test fixtures
4. **YAGNI**: No premature optimization (e.g., template caching), implement when needed
5. **Separation of Concerns**: Template loading (shared) vs. template serving (API) vs. template display (frontend)

## References

- Existing patterns: `templates/config_templates/vehicle_templates/vehicle_types.json`
- FastAPI routing: `api/routes/simulation_routes.py`, `api/routes/case_routes.py`
- Pydantic validation: `api/models/entities/`, `api/models/requests/`, `api/models/responses/`
- Frontend patterns: `frontend/index.html`, `frontend/app.js`
- Strategy model design: `docs/design/strategy_model_design.md`
