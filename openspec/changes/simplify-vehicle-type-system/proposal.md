# Proposal: Simplify Vehicle Type System to Fixed Three Categories

**Change ID**: `simplify-vehicle-type-system`
**Status**: Draft
**Created**: 2025-11-01
**Author**: AI Assistant

## Overview

Simplify the vehicle type configuration system to use only three fixed categories (客车/货车/特种车辆) for traffic control strategies, eliminating complexity while maintaining full SUMO simulation compatibility.

## Background

### Current State

The system currently has vehicle type definitions across three locations:

1. **SUMO Configuration** (`templates/config_templates/vehicle_templates/vehicle_types.json`)
   - 6 detailed types: passenger_small, passenger_large, truck_small, truck_large, special_small, special_large
   - Actual simulation vehicle types with physics parameters

2. **Frontend Hardcoded** (`frontend/control/templates.html:890-902`)
   - 11 mixed types (high-level + detailed)
   - Not synchronized with configuration files

3. **Enum Definition** (`control_data/templates/common/vehicle_types_enum.json`)
   - 6 high-level categories (passenger, truck, delivery, bus, emergency, authority)
   - Includes types not defined in SUMO configuration

### Problems

- ❌ Three unsynchronized vehicle type sources
- ❌ Frontend hardcoding prevents dynamic updates
- ❌ Enum includes vehicle types without SUMO definitions
- ❌ No clear mapping between user selections and simulation types
- ❌ Maintenance requires changes in three places

### Discovered During

Identified during Phase 10 of the `refactor-strategy-parameter-configuration` change while analyzing vehicle type configuration inconsistencies.

## Motivation

**User Requirement**: The project uses only three fixed high-level vehicle categories:
- 客车 (Passenger vehicles)
- 货车 (Trucks)
- 特种车辆 (Special vehicles)

This is a **fixed constraint** for this specific project - no need for complex hierarchy, dynamic expansion, or 6+ categories.

**Goals**:
1. Simplify to three categories only
2. Single source of truth from SUMO configuration
3. Automatic mapping to detailed simulation types
4. Remove frontend hardcoding
5. Maintain backward compatibility

**Non-Goals**:
- ✗ Support for bus, emergency, authority types (not used in this project)
- ✗ Complex two-tier hierarchy with user-selectable levels
- ✗ Dynamic vehicle type creation

## Proposed Solution

### Approach: Fixed Two-Layer System

**Core Principle**: Two layers - user-friendly categories (3) map directly to SUMO simulation types (6).

```
Layer 1: 用户界面层 (3 high-level categories)
├─ 客车 (passenger)
├─ 货车 (truck)
└─ 特种车辆 (delivery)

         ↓ (自动映射)

Layer 2: SUMO仿真层 (6 detailed types)
├─ passenger_small + passenger_large  ← 客车
├─ truck_small + truck_large          ← 货车
└─ special_small + special_large      ← 特种车辆
```

**Two layers, not three**:
- Layer 1 (User Interface): 3 fixed categories for simple selection
- Layer 2 (SUMO Simulation): 6 detailed types for actual simulation

### Key Changes

1. **Data Model**: Update `vehicle_types_enum.json` with fixed mapping
   ```json
   {
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
   ```

2. **Backend**: Auto-expand categories to detailed types
   ```python
   # When user selects: ["passenger", "truck"]
   # Backend expands to: ["passenger_small", "passenger_large", "truck_small", "truck_large"]
   ```

3. **Frontend**: Remove hardcoding, load from API
   ```javascript
   // OLD: hardcoded 11 vehicle types
   // NEW: Load from template.parameters_schema[].enum_values
   ```

### Success Criteria

- ✅ Only three vehicle type checkboxes in UI
- ✅ No frontend hardcoded vehicle lists
- ✅ User selection automatically maps to 6 SUMO types
- ✅ Single source of truth: vehicle_types.json
- ✅ All E2E tests pass
- ✅ Backward compatible with existing strategy instances

## Impact Analysis

### Components Affected

| Component | Type | Change |
|-----------|------|--------|
| `control_data/templates/common/vehicle_types_enum.json` | Data | Major - Replace with 3-category model |
| `frontend/control/templates.html` | Code | Major - Remove hardcoded list (lines 890-902) |
| `frontend/control/js/parameter_form.js` | Code | Minor - Read from API |
| `api/services/strategy_instance_service.py` | Code | Major - Add expansion logic |
| `shared/utilities/vehicle_type_utils.py` | Code | New - Expansion utilities |

### Risk Assessment

**Low Risk**:
- Change is additive (expansion happens in backend)
- Frontend simplification reduces complexity
- Existing strategy instances remain valid (already use detailed types)
- No database schema changes required

**Mitigation**:
- Maintain backward compatibility for existing instances
- Add validation to prevent invalid category selections
- Comprehensive E2E tests for all three categories

## Alternatives Considered

### Alternative A: Keep Current Mixed System
**Rejected**: Too complex for project needs, three locations, maintenance burden

### Alternative B: Two-Tier Hierarchy with User Choice
**Rejected**: Overkill for fixed three-category requirement

### Alternative C: Only Use Detailed Types (6 checkboxes)
**Rejected**: Poor UX, user wants simple three-category view

## Dependencies

### Upstream
- Requires `refactor-strategy-parameter-configuration` Phase 1-10 completed

### Downstream
- None (isolated change)

### External
- No external API changes
- No database migrations

## Open Questions

1. **Q**: Should we keep bus/emergency/authority for future use?
   **A**: No - project requirement is fixed three categories only. Remove to simplify.

2. **Q**: Where should the expansion logic live?
   **A**: Backend (`shared/utilities/vehicle_type_utils.py`) for single source of truth.

3. **Q**: How to handle existing strategy instances with old vehicle types?
   **A**: No changes needed - they already use detailed types compatible with mapping.

## Timeline Estimate

- **Scoping & Design**: 0.5 days (this proposal)
- **Implementation**: 3-4 days
- **Testing**: 1 day
- **Documentation**: 0.5 days

**Total**: 5-6 days

## Approval Checklist

- [ ] Proposal reviewed by team
- [ ] Design validated against requirements
- [ ] Timeline approved
- [ ] Ready for implementation

---

**Next Steps**:
1. Review and approve this proposal
2. Create detailed `tasks.md`
3. Implement Phase 11 tasks
4. Validate with E2E tests
