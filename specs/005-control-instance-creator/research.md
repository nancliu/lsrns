# Research & Technology Decisions: Phase 1C

**Feature**: Control Strategy Instance Creator
**Date**: 2025-10-21
**Status**: Resolved

## Overview

This document captures all technology decisions, design patterns, and best practices research conducted for Phase 1C implementation. All NEEDS CLARIFICATION items from Technical Context have been resolved.

---

## Decision 1: File-Based Storage Strategy

**Question**: How to efficiently manage 100-500 strategy JSON files with search/filter capabilities?

**Decision**: **Two-tier file structure with index file**

**Rationale**:
- Individual strategy files allow atomic operations (create/update/delete single strategy without affecting others)
- Index file (`strategies_index.json`) provides fast list/search operations without reading all files
- Proven pattern from Phase 1A template system (similar structure)
- Supports pagination by loading index first, then fetching detailed files on-demand
- Enables concurrent access (file locks prevent corruption, optimistic concurrency via timestamps)

**Implementation Details**:
```
control_data/strategies/
├── strat_20251021_a3f7b9.json          # Full strategy data
├── strat_20251021_b8k2m4.json
├── ...
└── strategies_index.json                # Lightweight metadata
```

**Index Structure**:
```json
{
  "strategies": [
    {
      "strategy_id": "strat_20251021_a3f7b9",
      "strategy_name": "Morning Peak VSS",
      "strategy_type": "VSS",
      "template_id": "vss_moderate",
      "template_name": "VSS Moderate Template",
      "edges_count": 15,
      "created_at": "2025-10-21T08:30:00Z",
      "updated_at": "2025-10-21T09:15:00Z",
      "file_path": "control_data/strategies/strat_20251021_a3f7b9.json"
    }
  ],
  "last_updated": "2025-10-21T09:15:00Z",
  "total_count": 125
}
```

**Alternatives Considered**:
1. **SQLite database** - Rejected: Violates Constitution Principle VI (File-Based Storage), adds dependency
2. **Single large JSON file** - Rejected: Poor concurrent access, entire file rewrite on every change
3. **No index (scan all files)** - Rejected: O(n) performance for list operations, unacceptable at 500+ files

**Best Practices Applied**:
- Atomic file writes using temp file + rename pattern (prevents corruption)
- Index regeneration capability (scan all files if index corrupted)
- pathlib.Path for cross-platform compatibility

---

## Decision 2: Dynamic Form Generation

**Question**: How to generate forms from template `parameters_schema` without hard-coding parameter types?

**Decision**: **Schema-driven form generator with type mapping**

**Rationale**:
- Template `parameters_schema` already provides metadata (type, min/max, required, etc.)
- JavaScript form builder maps schema types → HTML input elements
- Enables template changes without frontend code updates
- Supports all required input types (number, text, textarea, checkbox)

**Type Mapping Table**:

| Schema Type | Constraints | HTML Input | Validation |
|-------------|-------------|------------|------------|
| integer | min, max, required | `<input type="number">` | Range check, required |
| string | maxLength, pattern, required | `<input type="text">` | Length, regex, required |
| array | minItems, itemType, required | `<textarea>` or tag input | JSON parse, count |
| boolean | required | `<input type="checkbox">` | Boolean cast |
| enum | allowed_values, required | `<select>` dropdown | Value in list |

**Implementation Pattern** (JavaScript):
```javascript
function generateFormField(paramName, paramSchema) {
  const fieldType = paramSchema.type;
  switch(fieldType) {
    case 'integer':
      return createNumberInput(paramName, paramSchema.min, paramSchema.max, paramSchema.required);
    case 'string':
      return createTextInput(paramName, paramSchema.maxLength, paramSchema.pattern, paramSchema.required);
    case 'array':
      return createArrayInput(paramName, paramSchema.minItems, paramSchema.required);
    case 'boolean':
      return createCheckboxInput(paramName, paramSchema.required);
    default:
      return createTextInput(paramName, null, null, paramSchema.required); // Fallback
  }
}
```

**Alternatives Considered**:
1. **Hard-coded forms for each template** - Rejected: Violates Configuration Over Code, breaks when templates change
2. **JSON editor (raw JSON input)** - Rejected: Poor UX for non-technical users, no validation hints
3. **React/Vue form library** - Rejected: Adds frontend framework dependency, excessive for this scope

**Best Practices Applied**:
- Schema validation in frontend AND backend (defense in depth)
- Progressive enhancement (basic HTML forms work without JavaScript)
- Accessibility: proper labels, ARIA attributes, keyboard navigation

---

## Decision 3: Optimistic Concurrency Control

**Question**: How to handle concurrent edits without database locking?

**Decision**: **Timestamp-based optimistic concurrency with client-side warning**

**Rationale**:
- Assumption #4 states concurrent editing is rare (internal tool, small team)
- Timestamp check on save prevents silent data loss
- User-friendly warning if conflict detected
- No server-side locking infrastructure required
- Aligns with file-based storage constraints

**Implementation Flow**:
1. **Load strategy for editing**: Frontend captures `updated_at` timestamp
2. **User makes changes**: Local state only, no server lock
3. **Save request**: Include original `updated_at` in request body
4. **Backend validation**:
   ```python
   current_strategy = load_strategy(strategy_id)
   if current_strategy["metadata"]["updated_at"] != request.original_updated_at:
       raise HTTPException(409, "Strategy modified by another user. Refresh and retry.")
   ```
5. **Frontend handling**: Show diff modal, allow user to merge or overwrite

**Edge Cases Handled**:
- Deleted strategy: Return 404 Not Found
- Corrupted file: Return 500 Internal Server Error with recovery instructions
- Index out of sync: Regenerate index automatically

**Alternatives Considered**:
1. **Pessimistic locking (file locks)** - Rejected: Requires lock timeout management, adds complexity
2. **Last write wins (no check)** - Rejected: Silent data loss unacceptable
3. **Version vector (CRDT)** - Rejected: Overkill for internal tool with rare conflicts

**Best Practices Applied**:
- HTTP 409 Conflict for concurrency errors (standard REST pattern)
- Client-side diff display (helps users understand what changed)
- Auto-refresh list after conflict resolution

---

## Decision 4: Parameter Validation Strategy

**Question**: Where to validate parameters? Frontend only, backend only, or both?

**Decision**: **Dual-layer validation (frontend + backend)**

**Rationale**:
- **Frontend validation**: Immediate user feedback (<200ms), better UX, reduces unnecessary API calls
- **Backend validation**: Security/data integrity, handles API calls from other clients (future), enforces business rules
- Defense in depth: Both layers use same `parameters_schema` source of truth

**Validation Layers**:

| Layer | Purpose | Implementation | Error Handling |
|-------|---------|----------------|----------------|
| Frontend | UX, immediate feedback | JavaScript using template schema | Inline errors, disable Save button |
| Backend | Security, data integrity | Python `parameter_validator.py` | HTTP 400 with detailed JSON error list |

**Shared Validation Rules**:
1. **Type checking**: Integer, string, boolean, array
2. **Range validation**: min/max for numbers, minLength/maxLength for strings
3. **Required fields**: Non-empty check
4. **Format validation**: Time intervals (HH:MM-HH:MM), custom patterns
5. **Enum validation**: Value in allowed_values list
6. **Edge existence**: Database query for each edge_id (backend only)

**Backend Validator Function** (`shared/control_tools/parameter_validator.py`):
```python
from typing import Dict, List, Any
from pydantic import ValidationError

def validate_strategy_parameters(
    template_schema: Dict[str, Any],
    parameters: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Validate strategy parameters against template schema.

    Args:
        template_schema: Template's parameters_schema definition
        parameters: User-provided parameter values

    Returns:
        List of validation errors (empty if valid)
        Each error: {"parameter": "param_name", "message": "error detail"}
    """
    errors = []

    for param_name, param_schema in template_schema.items():
        value = parameters.get(param_name)

        # Required check
        if param_schema.get("required") and value is None:
            errors.append({"parameter": param_name, "message": f"{param_name} is required"})
            continue

        if value is not None:
            # Type-specific validation
            if param_schema["type"] == "integer":
                errors.extend(_validate_integer(param_name, value, param_schema))
            elif param_schema["type"] == "string":
                errors.extend(_validate_string(param_name, value, param_schema))
            elif param_schema["type"] == "array":
                errors.extend(_validate_array(param_name, value, param_schema))
            # ... more types

    return errors
```

**Alternatives Considered**:
1. **Frontend only** - Rejected: Security risk, trusts client input
2. **Backend only** - Rejected: Poor UX, slow feedback (network round-trip)
3. **Shared validation library** - Rejected: Complexity of Python ↔ JavaScript sharing

**Best Practices Applied**:
- DRY: Both layers use same schema source
- Fail fast: Frontend validation prevents unnecessary API calls
- Defensive programming: Backend never trusts client input

---

## Decision 5: Edge Selector Integration

**Question**: How to integrate Phase 1B edge selector component into strategy creation workflow?

**Decision**: **Step 2 modal overlay with edge selector iframe/component**

**Rationale**:
- Phase 1B already provides edge selector UI (`/control/edge_selector.html`)
- Modal overlay preserves strategy creation context (no page navigation)
- Component can return selected edge_ids via JavaScript callback
- Minimal coupling: Strategy manager receives edge array, doesn't need to know selection logic

**Integration Pattern**:

**Step 1: Select Template** → **Step 2: Select Edges (Modal)** → **Step 3: Fill Parameters** → **Step 4: Review & Save**

```javascript
// In strategy_manager.js
function openEdgeSelector() {
  const modal = createModal({
    title: "Select Target Edges",
    content: '<iframe src="/control/edge_selector.html" />',
    width: "90%",
    onClose: (selectedEdges) => {
      if (selectedEdges && selectedEdges.length > 0) {
        strategyForm.affectedEdges = selectedEdges;
        proceedToStep3();
      }
    }
  });
  modal.show();
}
```

**Data Contract** (Phase 1B → Phase 1C):
```json
{
  "selected_edges": [
    {
      "edge_id": "1234567890",
      "route_code": "G4202",
      "stake_range": "K10+000-K15+000",
      "length": 5000
    }
  ]
}
```

**Alternatives Considered**:
1. **Copy-paste edge selector code** - Rejected: Violates Module Isolation, code duplication
2. **Redirect to edge selector page** - Rejected: Loses strategy creation context
3. **Inline edge selector in Step 2** - Rejected: Complex page layout, harder to maintain

**Best Practices Applied**:
- Loose coupling: Message-passing via callbacks
- Reusability: Phase 1B component unchanged
- Progressive disclosure: Only show edge selector when needed

---

## Decision 6: Index Regeneration Strategy

**Question**: How to recover when `strategies_index.json` is corrupted or missing?

**Decision**: **Automatic regeneration on startup + manual API endpoint**

**Rationale**:
- Safety net for file corruption or accidental deletion
- Startup check minimizes user-facing errors
- Manual endpoint allows admin intervention
- Scan operation is O(n) but acceptable for 100-500 files

**Implementation**:

**Automatic** (on API startup):
```python
# In api/main.py
@app.on_event("startup")
async def verify_strategy_index():
    index_path = Path("control_data/strategies/strategies_index.json")
    if not index_path.exists():
        logger.warning("Strategy index missing - regenerating...")
        await regenerate_strategy_index()
```

**Manual Endpoint**:
```python
# In api/routes/control_strategy_routes.py
@router.post("/api/v1/control/strategies/reindex")
async def regenerate_index():
    """Scan all strategy files and rebuild index."""
    strategy_dir = Path("control_data/strategies")
    strategies = []

    for file_path in strategy_dir.glob("strat_*.json"):
        strategy = json.loads(file_path.read_text())
        strategies.append({
            "strategy_id": strategy["strategy_id"],
            "strategy_name": strategy["strategy_name"],
            "strategy_type": strategy["strategy_type"],
            "template_id": strategy["template_id"],
            "template_name": strategy["template_name"],
            "edges_count": len(strategy["affected_edges"]),
            "created_at": strategy["metadata"]["created_at"],
            "updated_at": strategy["metadata"]["updated_at"],
            "file_path": str(file_path)
        })

    index = {
        "strategies": strategies,
        "last_updated": datetime.utcnow().isoformat(),
        "total_count": len(strategies)
    }

    index_path = strategy_dir / "strategies_index.json"
    index_path.write_text(json.dumps(index, indent=2))

    return {"message": f"Regenerated index with {len(strategies)} strategies"}
```

**Alternatives Considered**:
1. **No regeneration** - Rejected: Permanent data loss on corruption
2. **Regeneration on every request** - Rejected: Performance impact
3. **Periodic background task** - Rejected: Adds complexity, startup check sufficient

**Best Practices Applied**:
- Defensive programming: Handle missing/corrupted index gracefully
- Logging: Warn when regeneration triggered
- Admin tools: Manual endpoint for troubleshooting

---

## Decision 7: Strategy ID Generation

**Question**: How to generate unique, collision-free strategy_ids?

**Decision**: **Timestamp + random suffix pattern: `strat_{timestamp}_{random}`**

**Rationale**:
- Timestamp provides chronological ordering (helpful for debugging)
- Random suffix prevents collisions when multiple strategies created simultaneously
- Format: `strat_20251021143025_a3f7b9` (YYYYMMDDHHMMSS + 6-char random)
- Human-readable, URL-safe, sortable

**Implementation**:
```python
import secrets
from datetime import datetime

def generate_strategy_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(3)  # 6 hex characters
    return f"strat_{timestamp}_{random_suffix}"
```

**Collision Probability**:
- 16^6 = 16.7 million possible suffixes
- At 1000 strategies/second, collision risk < 0.006% (birthday paradox)
- Acceptable for internal tool with ~10 strategies/day

**Alternatives Considered**:
1. **UUID** - Rejected: Not human-readable, too long for URLs
2. **Auto-increment** - Rejected: Requires centralized counter (file lock), harder in distributed scenarios
3. **Timestamp only** - Rejected: Collisions when rapid creation

**Best Practices Applied**:
- `secrets` module for cryptographic randomness
- URL-safe characters only (alphanumeric + underscore)
- Predictable length (fixed-width timestamp + 6-char suffix)

---

## Decision 8: Logging Strategy

**Question**: What should be logged for operational monitoring?

**Decision**: **Standard operational logging (Clarification Answer)**

**Implementation**:
- **Error logging**: Exceptions, validation failures
- **Key operation logging**: Strategy create/update/delete with strategy_id
- **Performance metrics**: API response times (warn if >2s)
- **Index regeneration events**

**Log Levels**:
| Event | Level | Example |
|-------|-------|---------|
| Strategy created | INFO | `Strategy strat_20251021_a3f7b9 created by system` |
| Strategy updated | INFO | `Strategy strat_20251021_a3f7b9 updated (version 2→3)` |
| Strategy deleted | WARNING | `Strategy strat_20251021_a3f7b9 deleted by system` |
| Validation error | WARNING | `Validation failed for strat_20251021_a3f7b9: speed_limit out of range` |
| Performance warning | WARNING | `API response time 2.5s (threshold: 2s) for GET /strategies/` |
| Index regeneration | WARNING | `Strategy index missing - regenerating from 125 files` |
| File corruption | ERROR | `Failed to read strat_20251021_a3f7b9.json: JSONDecodeError` |
| Unexpected exception | ERROR | `Unhandled exception in create_strategy: {traceback}` |

**Logger Configuration** (use existing OD_SIM logging):
```python
import logging

logger = logging.getLogger("api.control_strategy")
logger.setLevel(logging.INFO)

# Example usage
logger.info(f"Strategy {strategy_id} created by {created_by}")
logger.warning(f"Validation failed for {strategy_id}: {errors}")
```

**Best Practices Applied**:
- Structured logging: Include strategy_id, operation, user in every log
- Performance tracking: Measure and log slow operations
- Security: Never log sensitive data (none in this system)

---

## Technology Stack Summary

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Backend API** | FastAPI | 0.104+ | Existing OD_SIM stack, async support |
| **Data Validation** | Pydantic | 2.0+ | Existing OD_SIM stack, schema validation |
| **File I/O** | pathlib | stdlib | Cross-platform, Python 3.10+ stdlib |
| **JSON** | json | stdlib | Lightweight, no external dependency |
| **Logging** | logging | stdlib | Existing OD_SIM logging infrastructure |
| **ID Generation** | secrets | stdlib | Cryptographic randomness |
| **Edge Validation** | PostgreSQL | Existing | Phase 1B dependency, read-only queries |
| **Frontend** | Vanilla JS | ES6+ | No framework overhead, existing OD_SIM pattern |
| **Testing** | pytest | Existing | OD_SIM test infrastructure |

**No new external dependencies introduced** ✅

---

## Performance Considerations

**File I/O Optimization**:
- Index-first loading: Read lightweight index (few KB) before detailed files
- Lazy loading: Load strategy details only when user clicks "View"
- Pagination: Load 20 items per page (configurable)
- Caching: Browser caching for static resources (CSS/JS), no server-side cache for JSON files

**Expected Performance**:
- Strategy list (100 items): <1 second (index read + 20 detail files)
- Strategy create: <500ms (1 file write + 1 index update)
- Strategy update: <500ms (1 file rewrite + 1 index update)
- Strategy delete: <500ms (1 file delete + 1 index update)
- Index regeneration (500 files): <5 seconds (acceptable for recovery operation)

**Scalability Limits**:
- Target: 100-500 strategies (comfortable)
- Hard limit: ~2000 strategies (performance degrades, consider database migration)
- Mitigation: Archival mechanism in Phase 2 (move old strategies to archive directory)

---

## Security Considerations

**Authentication**: None (internal tool, system identifier for created_by)

**Authorization**: None (all users have full CRUD access)

**Input Validation**: All user inputs validated against template schemas

**File System Security**:
- No path traversal: Use pathlib.Path.resolve() to prevent `../` attacks
- No arbitrary file write: Strategy IDs validated with regex before file operations
- No code execution: JSON parsing only, no eval() or exec()

**Threat Model**: Low risk (internal tool, trusted users, no PII/sensitive data)

---

## Open Questions / Future Research

*None remaining. All technical decisions resolved.*

---

## References

- Phase 1A Template System: `specs/002-strategy-template-system/`
- Phase 1B Edge Selector: `specs/004-database-edge-selector/`
- OD_SIM Constitution: `.specify/memory/constitution.md`
- FastAPI Best Practices: https://fastapi.tiangolo.com/tutorial/
- JSON Schema Validation: https://json-schema.org/understanding-json-schema/

---

**Status**: ✅ Research complete. Ready for Phase 1 (Data Model & Contracts).
