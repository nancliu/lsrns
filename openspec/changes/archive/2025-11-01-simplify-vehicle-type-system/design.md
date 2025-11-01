# Design: Two-Layer Vehicle Type System

## Context

The system currently has three unsynchronized vehicle type definitions:
1. SUMO configuration with 6 detailed types
2. Frontend hardcoded list with 11 mixed types
3. Enum definition with 6 high-level categories

**Problem**: Maintenance burden, no clear mapping, frontend can't update dynamically.

**Constraint**: Project uses only 3 fixed categories (客车/货车/特种车辆).

## Goals / Non-Goals

**Goals**:
- Single source of truth (vehicle_types.json)
- Simplified user experience (3 checkboxes)
- Automatic category → detailed type mapping
- Backward compatible with existing strategies

**Non-Goals**:
- Dynamic vehicle type creation
- Support for bus/emergency/authority types
- User-selectable abstraction levels

## Architecture Decisions

### Decision 1: Two-Layer Model

**Choice**: Fixed two-layer architecture
- Layer 1 (UI): 3 high-level categories for user selection
- Layer 2 (SUMO): 6 detailed types for simulation

**Alternatives Considered**:
- A: Keep current mixed system → **Rejected**: Too complex, maintenance burden
- B: Only detailed types (6 checkboxes) → **Rejected**: Poor UX
- C: Dynamic multi-tier hierarchy → **Rejected**: Overkill for fixed 3 categories

**Rationale**: Simplest solution that meets project requirements.

### Decision 2: Backend Expansion

**Choice**: Category expansion happens in backend during strategy creation

**Location**: `shared/utilities/vehicle_type_utils.py` (new module)

**Alternatives Considered**:
- Frontend expansion → **Rejected**: Single source of truth should be backend
- Database trigger → **Rejected**: Business logic belongs in application layer

**Rationale**:
- Validation and data integrity handled in backend
- Frontend stays simple, just displays UI
- Easier to test and maintain

### Decision 3: Preserve User Selection

**Choice**: Save both expanded types AND original user selection

**Format**:
```json
{
  "allowed_vehicle_types": ["passenger_small", "passenger_large", ...],
  "allowed_vehicle_types_user_selection": ["passenger", "truck"]
}
```

**Rationale**:
- Enables correct edit UI (show original 3 categories selected)
- Supports future analytics (what users actually chose)
- Minimal storage overhead

### Decision 4: API Contract

**Choice**: Template API returns enum_values in parameters_schema

**Format**:
```json
{
  "parameters_schema": [{
    "parameter_name": "allowed_vehicle_types",
    "enum_name": "vehicle_types_category",
    "enum_values": [
      {"value": "passenger", "label": "客车", "includes": [...], ...}
    ]
  }]
}
```

**Rationale**:
- Frontend becomes data-driven, no hardcoding
- Centralized enum management
- Supports future i18n and customization

## Data Model

### vehicle_types_enum.json (Updated)

```json
{
  "enums": {
    "vehicle_types_category": {
      "values": [
        {
          "value": "passenger",
          "label": "客车",
          "includes": ["passenger_small", "passenger_large"],
          "example_ids": ["k1", "k2", "k3", "k4"]
        },
        {
          "value": "truck",
          "label": "货车",
          "includes": ["truck_small", "truck_large"],
          "example_ids": ["h1", "h2", "h3", "h4", "h5", "h6"]
        },
        {
          "value": "delivery",
          "label": "特种车辆",
          "includes": ["special_small", "special_large"],
          "example_ids": ["t1", "t2", "t3", "t4", "t5", "t6"]
        }
      ]
    }
  }
}
```

### vehicle_types.json (Updated)

Add `category` field to each detailed type:

```json
{
  "vehicle_types": {
    "passenger_small": {
      "category": "passenger",
      "vClass": "passenger",
      ...
    },
    ...
  }
}
```

## Component Flow

```
┌─────────────────────────────────────────────────┐
│ Frontend (Step 3 - Parameter Configuration)    │
│                                                 │
│ 1. Load enum_values from template API          │
│ 2. Render 3 checkboxes (Layer 1)               │
│ 3. User selects: ["passenger", "truck"]        │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓ POST /strategies/instances
┌─────────────────────────────────────────────────┐
│ Backend (StrategyInstanceService)               │
│                                                 │
│ 1. Receive: {"allowed_vehicle_types":          │
│              ["passenger", "truck"]}            │
│ 2. Call: expand_vehicle_types()                │
│ 3. Result: ["passenger_small",                 │
│             "passenger_large",                  │
│             "truck_small",                      │
│             "truck_large"]                      │
│ 4. Save both expanded + user_selection         │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│ Strategy Instance (JSON)                        │
│                                                 │
│ {                                               │
│   "allowed_vehicle_types": [                    │
│     "passenger_small", "passenger_large",       │
│     "truck_small", "truck_large"                │
│   ],                                            │
│   "allowed_vehicle_types_user_selection": [    │
│     "passenger", "truck"                        │
│   ]                                             │
│ }                                               │
└─────────────────────────────────────────────────┘
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing strategies break | High | Expansion logic accepts detailed types as input |
| Frontend API call fails | Medium | Provide fallback default 3 categories |
| User confusion (categories vs detailed) | Medium | Clear UI hints, tooltips, documentation |
| Enum/SUMO config mismatch | Low | Validation checks at startup |

## Migration Plan

**Phase 1: Data Update**
- Update configuration files (vehicle_types_enum.json, vehicle_types.json)
- No user impact, no deployment needed

**Phase 2: Backend Deploy**
- Deploy expansion logic
- Template API starts returning enum_values
- Frontend still works with fallback

**Phase 3: Frontend Deploy**
- Remove hardcoded lists
- Switch to API-driven rendering
- Users see new 3-category UI

**Rollback**:
- Phase 3: Restore hardcoded list in frontend
- Phase 2: No rollback needed (backward compatible)

## Performance Considerations

- **Expansion Logic**: O(n) where n = number of categories (max 3) → negligible
- **API Response Size**: +200 bytes for enum_values → acceptable
- **Frontend Rendering**: No change (still 3-6 checkboxes)

## Open Questions

None - all decisions finalized based on:
- Fixed 3-category project requirement
- Backward compatibility constraint
- Single source of truth principle

## References

- [VEHICLE_TYPES_HIERARCHICAL_DESIGN.md](../../../docs/frontend_analysis/VEHICLE_TYPES_HIERARCHICAL_DESIGN.md)
- [VEHICLE_TYPES_UNIFICATION_ANALYSIS.md](../../../docs/frontend_analysis/VEHICLE_TYPES_UNIFICATION_ANALYSIS.md)
