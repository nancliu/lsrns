# Data Model: Control Strategy Instance Creator

**Feature**: Phase 1C - Control Strategy Instance Creator
**Date**: 2025-10-21
**Status**: Final

## Overview

This document defines the complete data model for strategy instance management, including entities, relationships, validation rules, state transitions, and file structures.

---

## Core Entities

### 1. StrategyInstance

Represents a concrete traffic control strategy configuration created from a template.

**Storage**: `control_data/strategies/{strategy_id}.json`

**Attributes**:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| strategy_id | string | Yes | Pattern: `strat_\d{14}_[a-f0-9]{6}` | Unique identifier (e.g., strat_20251021143025_a3f7b9) |
| strategy_name | string | Yes | Max 100 chars, non-empty | User-defined display name |
| template_id | string | Yes | Must exist in Phase 1A | Reference to ControlTemplate |
| template_name | string | Yes | - | Denormalized from template (for display) |
| strategy_type | enum | Yes | VSS \| DHS \| TEC | Denormalized from template |
| parameters | object | Yes | Validated against template schema | Key-value pairs of configured parameters |
| affected_edges | array[string] | Yes | Min 1 item, each edge must exist in DB | Array of edge_id strings |
| metadata | object | Yes | - | Creation/update tracking |

**Metadata Object**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| created_at | ISO8601 | Yes | UTC timestamp of creation |
| updated_at | ISO8601 | Yes | UTC timestamp of last update |
| created_by | string | Yes | System identifier (hostname or "system") |
| version | integer | Yes | Incremented on each update (starts at 1) |

**Full JSON Example**:
```json
{
  "strategy_id": "strat_20251021143025_a3f7b9",
  "strategy_name": "Morning Peak VSS Control - G4202",
  "template_id": "vss_moderate",
  "template_name": "VSS Moderate Speed Control",
  "strategy_type": "VSS",
  "parameters": {
    "speed_limit": 80,
    "time_intervals": ["07:00-09:00", "17:00-19:00"],
    "activation_threshold": 0.7,
    "min_spacing": 500
  },
  "affected_edges": [
    "1234567890",
    "1234567891",
    "1234567892"
  ],
  "metadata": {
    "created_at": "2025-10-21T14:30:25Z",
    "updated_at": "2025-10-21T15:45:10Z",
    "created_by": "WIN-SERVER-01",
    "version": 3
  }
}
```

**Relationships**:
- **Created From**: One ControlTemplate (Phase 1A) - Many StrategyInstances
- **References**: Many Road Edges (Phase 1B database)
- **Included In**: Many Plans (Phase 2 future) - Many StrategyInstances

**State Transitions**:
```
[Created] → version=1, created_at set
    ↓
[Updated] → version++, updated_at updated, parameters/edges modified
    ↓ (repeatable)
[Updated] → version++, updated_at updated
    ↓
[Deleted] → File removed, index updated (no soft delete in Phase 1C)
```

**Validation Rules**:
1. `strategy_id` must be unique across all strategies
2. `template_id` must reference existing template (validate via Phase 1A API)
3. `parameters` must pass `validate_strategy_parameters()` against template schema
4. Each `affected_edges` item must exist in database (validate via Phase 1B query)
5. `strategy_name` must be unique per user preference (warning, not enforced)
6. `version` must increment monotonically (concurrency check)

---

### 2. StrategyIndex

Maintains searchable metadata for all strategies (performance optimization).

**Storage**: `control_data/strategies/strategies_index.json`

**Structure**:
```json
{
  "strategies": [
    {
      "strategy_id": "strat_20251021143025_a3f7b9",
      "strategy_name": "Morning Peak VSS Control",
      "strategy_type": "VSS",
      "template_id": "vss_moderate",
      "template_name": "VSS Moderate Speed Control",
      "edges_count": 15,
      "created_at": "2025-10-21T14:30:25Z",
      "updated_at": "2025-10-21T15:45:10Z",
      "file_path": "control_data/strategies/strat_20251021143025_a3f7b9.json"
    }
  ],
  "last_updated": "2025-10-21T15:45:10Z",
  "total_count": 125
}
```

**Index Entry Attributes**:

| Field | Type | Description |
|-------|------|-------------|
| strategy_id | string | Unique identifier |
| strategy_name | string | Display name |
| strategy_type | enum | VSS \| DHS \| TEC |
| template_id | string | Template reference |
| template_name | string | Template display name |
| edges_count | integer | Number of affected edges |
| created_at | ISO8601 | Creation timestamp |
| updated_at | ISO8601 | Last update timestamp |
| file_path | string | Relative path to JSON file |

**Update Triggers**:
- Strategy created → Add entry
- Strategy updated → Update entry (name, edges_count, updated_at)
- Strategy deleted → Remove entry
- Index corrupted → Regenerate from all strategy files

**Regeneration Logic**:
```python
def regenerate_index():
    """Scan all strategy files and rebuild index."""
    strategies = []
    for file_path in Path("control_data/strategies").glob("strat_*.json"):
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
        "strategies": sorted(strategies, key=lambda x: x["updated_at"], reverse=True),
        "last_updated": datetime.utcnow().isoformat(),
        "total_count": len(strategies)
    }

    Path("control_data/strategies/strategies_index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False)
    )
```

---

### 3. StrategyParameter (Logical Entity)

Represents a single configured parameter within a strategy instance. Not stored separately, but part of `StrategyInstance.parameters` object.

**Attributes**:

| Field | Type | Description |
|-------|------|-------------|
| parameter_name | string | Key in parameters object (matches template schema) |
| parameter_value | any | Actual configured value (type depends on schema) |
| parameter_unit | string | Display unit from template schema (e.g., "km/h") |

**Type Mapping**:

| Template Type | Storage Type | Example Value |
|---------------|--------------|---------------|
| integer | number | `80` |
| string | string | `"07:00-09:00"` |
| array | array | `["edge1", "edge2"]` |
| boolean | boolean | `true` |
| enum | string | `"moderate"` |

**Validation**:
- Type must match template schema
- Integer: min ≤ value ≤ max
- String: length ≤ maxLength, matches pattern if specified
- Array: length ≥ minItems, items match itemType
- Enum: value in allowed_values list

---

### 4. StrategyEdgeAssociation (Logical Entity)

Represents the relationship between a strategy and affected road edges. Stored as array in `StrategyInstance.affected_edges`, enriched with edge details when displayed.

**Storage**: Array of edge_id strings in strategy JSON

**Display Enhancement**: Joined with database edge data

| Field | Source | Type | Description |
|-------|--------|------|-------------|
| edge_id | Strategy JSON | string | Primary key |
| route_code | Database (sim_edges) | string | Route identifier (e.g., "G4202") |
| stake_range | Database (sim_edges) | string | Kilometer range (e.g., "K10+000-K15+000") |
| length | Database (sim_edges) | float | Edge length in meters |

**Query Pattern**:
```python
def get_edge_details(edge_ids: List[str]) -> List[Dict]:
    """Fetch edge details from database."""
    from shared.data_access.edge_query import query_edges_by_ids

    return query_edges_by_ids(edge_ids)
    # Returns: [{"edge_id": "...", "route_code": "...", "stake_range": "...", "length": ...}]
```

**Validation**:
- All edge_ids must exist in database
- Warning if some edges not found: "X of Y selected edges not found in network"
- User can choose to remove invalid edges or cancel

---

## Request/Response Models

### API Request Models

**StrategyCreateRequest** (`api/models/requests/strategy_requests.py`):
```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List

class StrategyCreateRequest(BaseModel):
    strategy_name: str = Field(..., min_length=1, max_length=100)
    template_id: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(...)
    affected_edges: List[str] = Field(..., min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "Morning Peak VSS - G4202",
                "template_id": "vss_moderate",
                "parameters": {
                    "speed_limit": 80,
                    "time_intervals": ["07:00-09:00"]
                },
                "affected_edges": ["1234567890", "1234567891"]
            }
        }
```

**StrategyUpdateRequest** (`api/models/requests/strategy_requests.py`):
```python
class StrategyUpdateRequest(BaseModel):
    strategy_name: str | None = Field(None, min_length=1, max_length=100)
    parameters: Dict[str, Any] | None = None
    affected_edges: List[str] | None = Field(None, min_items=1)
    original_updated_at: str = Field(...)  # For optimistic concurrency

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "Updated Strategy Name",
                "parameters": {"speed_limit": 85},
                "affected_edges": ["1234567890"],
                "original_updated_at": "2025-10-21T14:30:25Z"
            }
        }
```

### API Response Models

**StrategyListResponse** (`api/models/responses/strategy_responses.py`):
```python
from pydantic import BaseModel
from typing import List

class StrategyListItem(BaseModel):
    strategy_id: str
    strategy_name: str
    strategy_type: str
    template_name: str
    edges_count: int
    created_at: str
    updated_at: str

class StrategyListResponse(BaseModel):
    strategies: List[StrategyListItem]
    total_count: int
    page: int
    page_size: int

    class Config:
        json_schema_extra = {
            "example": {
                "strategies": [
                    {
                        "strategy_id": "strat_20251021143025_a3f7b9",
                        "strategy_name": "Morning Peak VSS",
                        "strategy_type": "VSS",
                        "template_name": "VSS Moderate",
                        "edges_count": 15,
                        "created_at": "2025-10-21T14:30:25Z",
                        "updated_at": "2025-10-21T15:45:10Z"
                    }
                ],
                "total_count": 125,
                "page": 1,
                "page_size": 20
            }
        }
```

**StrategyDetailResponse** (`api/models/responses/strategy_responses.py`):
```python
class EdgeDetail(BaseModel):
    edge_id: str
    route_code: str
    stake_range: str
    length: float

class StrategyMetadata(BaseModel):
    created_at: str
    updated_at: str
    created_by: str
    version: int

class StrategyDetailResponse(BaseModel):
    strategy_id: str
    strategy_name: str
    template_id: str
    template_name: str
    strategy_type: str
    parameters: Dict[str, Any]
    affected_edges: List[EdgeDetail]  # Enriched with DB data
    metadata: StrategyMetadata
    is_used_in_plans: bool = False  # Phase 2 placeholder

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strat_20251021143025_a3f7b9",
                "strategy_name": "Morning Peak VSS",
                "template_id": "vss_moderate",
                "template_name": "VSS Moderate Speed Control",
                "strategy_type": "VSS",
                "parameters": {"speed_limit": 80},
                "affected_edges": [
                    {
                        "edge_id": "1234567890",
                        "route_code": "G4202",
                        "stake_range": "K10+000-K15+000",
                        "length": 5000.0
                    }
                ],
                "metadata": {
                    "created_at": "2025-10-21T14:30:25Z",
                    "updated_at": "2025-10-21T15:45:10Z",
                    "created_by": "WIN-SERVER-01",
                    "version": 3
                },
                "is_used_in_plans": false
            }
        }
```

---

## File Structure & Organization

### Directory Layout

```
control_data/strategies/
├── strat_20251021143025_a3f7b9.json
├── strat_20251021150032_b8k2m4.json
├── strat_20251021161547_c1n5p7.json
├── ... (up to 500 files)
└── strategies_index.json
```

### File Naming Convention

**Pattern**: `strat_{timestamp}_{random}.json`

- `timestamp`: YYYYMMDDHHMMSS (14 digits, UTC)
- `random`: 6 hexadecimal characters (cryptographic random via `secrets.token_hex(3)`)

**Example**: `strat_20251021143025_a3f7b9.json`

**Collision Probability**:
- 16^6 = 16,777,216 possible suffixes
- At 1000 strategies/second: < 0.006% collision risk
- Acceptable for internal tool with ~10 strategies/day

### File Operations

**Create Strategy**:
1. Generate strategy_id
2. Validate parameters & edges
3. Create strategy JSON object
4. Write to temp file: `{strategy_id}.tmp`
5. Rename to final: `{strategy_id}.json` (atomic operation)
6. Update index

**Update Strategy**:
1. Read existing strategy
2. Check concurrency (updated_at match)
3. Merge updates
4. Increment version
5. Write to temp file
6. Rename to final (atomic)
7. Update index

**Delete Strategy**:
1. Check if used in plans (Phase 2)
2. Delete file
3. Update index
4. Log deletion

**Index Update** (all operations):
```python
def update_index_after_create(strategy: Dict):
    index = load_index()
    index["strategies"].append({
        "strategy_id": strategy["strategy_id"],
        "strategy_name": strategy["strategy_name"],
        # ... other fields
    })
    index["total_count"] += 1
    index["last_updated"] = datetime.utcnow().isoformat()
    save_index(index)

def update_index_after_update(strategy: Dict):
    index = load_index()
    entry = next(s for s in index["strategies"] if s["strategy_id"] == strategy["strategy_id"])
    entry["strategy_name"] = strategy["strategy_name"]
    entry["updated_at"] = strategy["metadata"]["updated_at"]
    entry["edges_count"] = len(strategy["affected_edges"])
    index["last_updated"] = datetime.utcnow().isoformat()
    save_index(index)

def update_index_after_delete(strategy_id: str):
    index = load_index()
    index["strategies"] = [s for s in index["strategies"] if s["strategy_id"] != strategy_id]
    index["total_count"] -= 1
    index["last_updated"] = datetime.utcnow().isoformat()
    save_index(index)
```

---

## Validation Rules

### Parameter Validation

**Function**: `shared/control_tools/parameter_validator.py::validate_strategy_parameters()`

**Rules by Type**:

| Type | Validation Rules | Error Examples |
|------|------------------|----------------|
| integer | Required, min ≤ value ≤ max | "speed_limit must be between 40 and 120" |
| string | Required, length ≤ maxLength, matches pattern | "time_interval must match HH:MM-HH:MM format" |
| array | Required, length ≥ minItems, items valid | "At least 1 time interval required" |
| boolean | Required, true/false | "activation_flag must be boolean" |
| enum | Required, value in allowed_values | "control_type must be one of [VSS, DHS, TEC]" |

**Validation Flow**:
```
Template Schema → Parameter Validator → Validation Errors (if any)
                                      ↓
                                  Valid Parameters → Save Strategy
```

### Edge Validation

**Function**: `shared/data_access/edge_query.py::validate_edges_exist()`

**Rules**:
1. Query database for all edge_ids
2. Identify missing edges
3. Return validation result

**Possible Outcomes**:
- ✅ All edges found → Proceed
- ⚠️ Some edges missing → Warning with choice (remove invalid or cancel)
- ❌ No edges found → Error, cannot create strategy

---

## Concurrency Control

### Optimistic Concurrency Pattern

**Mechanism**: Timestamp-based version checking

**Update Flow**:
```
1. Frontend loads strategy → Captures updated_at: "2025-10-21T14:30:25Z"
2. User edits → Local state only
3. User saves → Send original_updated_at in request
4. Backend checks:
   current_strategy["metadata"]["updated_at"] == request.original_updated_at

   If match:
     → Update strategy
     → Increment version
     → Set new updated_at

   If mismatch:
     → Return 409 Conflict
     → Error message: "Strategy modified by another user. Refresh and retry."
```

**Conflict Resolution**:
- Frontend displays warning modal
- Show diff between current and user's changes (if applicable)
- Options: Refresh & lose changes, or Overwrite (force update)

---

## Performance Considerations

### Query Patterns

**List View** (most common):
1. Read strategies_index.json (~10-50 KB)
2. Paginate in memory (20 items)
3. Return metadata only
4. **Performance**: <100ms for 500 strategies

**Detail View** (on demand):
1. Read specific strategy file (~5 KB)
2. Query database for edge details (batch query)
3. Combine and return
4. **Performance**: <500ms for 15 edges

**Search/Filter** (client-side):
1. Read index
2. JavaScript filter by name/type
3. No server round-trip
4. **Performance**: <50ms client-side

### Optimization Strategies

1. **Lazy Loading**: Load details only when "View" clicked
2. **Index First**: Always query index before reading files
3. **Batch Edge Queries**: Single DB query for all edges (not N queries)
4. **Client Caching**: Browser cache for static resources (JS/CSS)
5. **Pagination**: Limit 20 items per page (configurable)

---

## Error Handling

### Error Codes

| HTTP Code | Scenario | Response |
|-----------|----------|----------|
| 200 OK | Success | Strategy data |
| 201 Created | Strategy created | {strategy_id, message} |
| 400 Bad Request | Validation failed | {errors: [{parameter, message}]} |
| 404 Not Found | Strategy not found | {message: "Strategy not found"} |
| 409 Conflict | Concurrency conflict or used in plans | {message: "Strategy modified..."} |
| 500 Internal Server Error | File corruption, DB error | {message: "Internal error", details} |

### Validation Error Format

```json
{
  "detail": {
    "message": "Validation failed",
    "errors": [
      {
        "parameter": "speed_limit",
        "message": "Speed limit must be between 40 and 120 km/h",
        "constraint": {"min": 40, "max": 120},
        "provided_value": 150
      },
      {
        "parameter": "affected_edges",
        "message": "3 of 15 selected edges not found in network",
        "invalid_edges": ["1234567899", "1234567900", "1234567901"]
      }
    ]
  }
}
```

---

## Database Schema (Read-Only)

**Phase 1B Edge Table** (existing, no modifications):

```sql
-- Table: sim_edges (simplified)
CREATE TABLE sim_edges (
    edge_id VARCHAR PRIMARY KEY,
    route_code VARCHAR,
    stake_start VARCHAR,
    stake_end VARCHAR,
    stake_range VARCHAR GENERATED ALWAYS AS (stake_start || '-' || stake_end) STORED,
    length FLOAT,
    -- ... other fields
);
```

**Query Usage**:
```python
# In shared/data_access/edge_query.py (existing Phase 1B code, no changes)
def query_edges_by_ids(edge_ids: List[str]) -> List[Dict]:
    """Fetch edge details by IDs."""
    query = """
        SELECT edge_id, route_code, stake_range, length
        FROM sim_edges
        WHERE edge_id = ANY(%s)
    """
    return execute_query(query, (edge_ids,))
```

---

## Migration & Backward Compatibility

**Phase 1C Initial Release**: No migration needed (greenfield)

**Future Considerations** (Phase 2):
- If `is_used_in_plans` becomes real field: Add to metadata, default false
- If archival needed: Add `archived` boolean field, filter from normal list
- If database migration needed: Export all JSON → INSERT INTO strategies table

**Versioning Strategy**: Use `metadata.version` field for future schema changes

---

**Status**: ✅ Data model complete. Ready for API contract generation.
